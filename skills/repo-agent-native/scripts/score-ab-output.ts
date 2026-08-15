#!/usr/bin/env bun
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { assertOutput, type Failure } from "./assert-output.ts";
import { observeRetryPredicates } from "./evaluate-retry-predicates.ts";

type JsonObject = Record<string, unknown>;
type ExpectedRecord = { id: string; class?: string; claim_concepts: string[][]; source?: string; bounded_scope?: string[] };
type Expected = {
  required_invariants: ExpectedRecord[];
  negative_invariants: ExpectedRecord[];
  forbidden_claims: string[];
  structured_predicates: Array<{ id: string; group: "facts" | "negative_invariants" | "implicit_dependencies"; source: string }>;
  procedure_requirements: { required_record_groups: string[] };
};

class UsageError extends Error {}

function object(value: unknown, label: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new UsageError(`${label} must be an object`);
  return value as JsonObject;
}

function readJson(path: string, label: string): unknown {
  if (!existsSync(path)) throw new UsageError(`${label} absent: ${path}`);
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new UsageError(`${label} invalid JSON: ${error instanceof Error ? error.message : path}`);
  }
}

function normalize(value: unknown): string {
  return String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (typeof value === "object" && value !== null) {
    return `{${Object.entries(value as JsonObject).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value: unknown): string {
  return createHash("sha256").update(stable(value)).digest("hex");
}

function records(report: JsonObject, field: string): JsonObject[] {
  return Array.isArray(report[field]) ? report[field].filter((item): item is JsonObject => typeof item === "object" && item !== null && !Array.isArray(item)) : [];
}

function sourcePaths(record: JsonObject): string[] {
  return Array.isArray(record.source_refs)
    ? record.source_refs.flatMap((item) => typeof item === "object" && item !== null && !Array.isArray(item) && typeof (item as JsonObject).path === "string" ? [(item as JsonObject).path as string] : [])
    : [];
}

function lexicalMatches(record: JsonObject, expected: ExpectedRecord): boolean {
  const claim = normalize(record.claim);
  if (!Array.isArray(expected.claim_concepts) || !expected.claim_concepts.every((aliases) =>
    Array.isArray(aliases) && aliases.some((alias) => claim.includes(normalize(alias))),
  )) return false;
  return !expected.source || sourcePaths(record).includes(expected.source);
}

function ratio(numerator: number, denominator: number): number {
  return denominator === 0 ? 1 : numerator / denominator;
}

function lexicalAdvisory(report: JsonObject, expected: Expected, weights: JsonObject): JsonObject {
  const facts = records(report, "facts");
  const negatives = records(report, "negative_invariants");
  const dependencies = records(report, "implicit_dependencies");
  const requiredFacts = expected.required_invariants.filter((item) => item.class !== "implicit-dependency");
  const requiredDependencies = expected.required_invariants.filter((item) => item.class === "implicit-dependency");
  const matchedFacts = requiredFacts.filter((item) => facts.some((record) => lexicalMatches(record, item)));
  const matchedDependencies = requiredDependencies.filter((item) => dependencies.some((record) => lexicalMatches(record, item)));
  const matchedNegatives = expected.negative_invariants.filter((item) => negatives.some((record) => lexicalMatches(record, item)));
  const allRecords = [...facts, ...negatives, ...dependencies];
  const allClaims = allRecords.map((record) => normalize(record.claim)).join("\n");
  const forbidden = expected.forbidden_claims.filter((claim) => allClaims.includes(normalize(claim)));
  const forbiddenRecordCount = allRecords.filter((record) => expected.forbidden_claims.some((claim) => normalize(record.claim).includes(normalize(claim)))).length;
  const metrics = {
    lexical_nonforbidden_coverage_proxy: ratio(allRecords.length - forbiddenRecordCount, allRecords.length),
    lexical_required_recall: ratio(matchedFacts.length, requiredFacts.length),
    lexical_negative_recall: ratio(matchedNegatives.length, expected.negative_invariants.length),
    lexical_dependency_recall: ratio(matchedDependencies.length, requiredDependencies.length),
    lexical_forbidden_claim_count: forbidden.length,
  };
  let weightedQuality = 0;
  for (const [name, value] of Object.entries(metrics)) weightedQuality += Number(weights[name] ?? 0) * value;
  return {
    schema: "repo-agent-native/lexical-advisory/v1",
    authority: "advisory-only",
    admission_effect: "none",
    metrics,
    weighted_quality: Number(weightedQuality.toFixed(6)),
    matched: {
      required_invariants: matchedFacts.map((item) => item.id),
      negative_invariants: matchedNegatives.map((item) => item.id),
      implicit_dependencies: matchedDependencies.map((item) => item.id),
    },
    forbidden_claims_observed: forbidden,
    limitation: "Substring aliases do not establish semantic entailment, procedure execution, or fact precision.",
  };
}

function predicate(record: JsonObject): JsonObject | null {
  return typeof record.predicate === "object" && record.predicate !== null && !Array.isArray(record.predicate)
    ? record.predicate as JsonObject
    : null;
}

function procedureAssessment(report: JsonObject, baseFailures: Failure[], expected: Expected): { failures: Failure[]; coverage: number; receipt: JsonObject } {
  const failures: Failure[] = [];
  const checks: JsonObject[] = [];
  for (const group of expected.procedure_requirements.required_record_groups) {
    const passed = records(report, group).length > 0;
    checks.push({ id: `artifact:${group}-nonempty`, evidence_origin: "artifact_asserted", passed });
    if (!passed) failures.push({ id: "PROCEDURE_ARTIFACT_MISSING", detail: `${group} is required by the case contract` });
  }
  for (const [id, passed] of [
    ["subject-bound", !baseFailures.some((failure) => failure.id.startsWith("SUBJECT_"))],
    ["source-anchored", !baseFailures.some((failure) => failure.id.startsWith("SOURCE_"))],
    ["absence-bounded", !baseFailures.some((failure) => failure.id === "ABSENCE_BOUNDARY_UNDECLARED")],
  ] as Array<[string, boolean]>) {
    checks.push({ id: `verifier:${id}`, evidence_origin: "verifier_observed", passed });
    if (!passed) failures.push({ id: "PROCEDURE_VERIFIER_FAILED", detail: id });
  }
  const toolText = Array.isArray(report.tools) ? report.tools.map(String).join("\n") : "";
  return {
    failures,
    coverage: ratio(checks.filter((item) => item.passed === true).length, checks.length),
    receipt: {
      schema: "repo-agent-native/procedure-receipt/v1",
      verifier_observed: checks.filter((item) => item.evidence_origin === "verifier_observed"),
      artifact_asserted: checks.filter((item) => item.evidence_origin === "artifact_asserted"),
      model_reported_advisory: {
        evidence_origin: "model_reported_advisory",
        routes_count: Array.isArray(report.routes) ? report.routes.length : 0,
        tools_count: Array.isArray(report.tools) ? report.tools.length : 0,
        named_fallback_text: /fallback|source read|direct source/i.test(toolText),
        admission_effect: "none",
      },
    },
  };
}

function structuredAssessment(repo: string, report: JsonObject, expected: Expected): { failures: Failure[]; recall: number; observed: JsonObject[]; matched: string[] } {
  const failures: Failure[] = [];
  const observed = observeRetryPredicates(repo);
  const observedById = new Map(observed.map((item) => [item.id, item]));
  const allRecords = [
    ...records(report, "facts").map((record) => ({ group: "facts", record })),
    ...records(report, "negative_invariants").map((record) => ({ group: "negative_invariants", record })),
    ...records(report, "implicit_dependencies").map((record) => ({ group: "implicit_dependencies", record })),
  ];
  const seen = new Set<string>();
  for (const { record } of allRecords) {
    const id = predicate(record)?.id;
    if (typeof id !== "string" || !id) failures.push({ id: "STRUCTURED_PREDICATE_MISSING", detail: `${String(record.id)} has no predicate identity` });
    else if (seen.has(id)) failures.push({ id: "STRUCTURED_PREDICATE_DUPLICATE", detail: id });
    else seen.add(id);
  }
  const matched: string[] = [];
  for (const declaration of expected.structured_predicates) {
    const sourceObservation = observedById.get(declaration.id);
    if (!sourceObservation) {
      failures.push({ id: "PREDICATE_EVALUATOR_INCOMPLETE", detail: declaration.id });
      continue;
    }
    const candidates = allRecords.filter(({ group, record }) => group === declaration.group && predicate(record)?.id === declaration.id);
    if (candidates.length !== 1) {
      failures.push({ id: "STRUCTURED_PREDICATE_MISSING", detail: `${declaration.group}:${declaration.id}` });
      continue;
    }
    const record = candidates[0]!.record;
    const value = predicate(record)!;
    if (value.operator !== "equals" || stable(value.value) !== stable(sourceObservation.value) || !sourcePaths(record).includes(declaration.source)) {
      failures.push({ id: "STRUCTURED_PREDICATE_MISMATCH", detail: `${declaration.id}: reported=${stable(value.value)} observed=${stable(sourceObservation.value)}` });
      continue;
    }
    matched.push(declaration.id);
  }
  return { failures, recall: ratio(matched.length, expected.structured_predicates.length), observed, matched };
}

export function scoreOutput(repo: string, reportValue: unknown, expectedValue: unknown, evalConfigValue: unknown): JsonObject {
  const report = object(reportValue, "report");
  const expected = object(expectedValue, "ground truth") as unknown as Expected;
  const evalConfig = object(evalConfigValue, "eval config");
  if (!Array.isArray(expected.required_invariants) || !Array.isArray(expected.negative_invariants) || !Array.isArray(expected.forbidden_claims)
    || !Array.isArray(expected.structured_predicates) || !expected.procedure_requirements || !Array.isArray(expected.procedure_requirements.required_record_groups)) {
    throw new UsageError("ground truth fields are invalid");
  }
  const base = assertOutput(repo, report);
  const procedure = procedureAssessment(report, base.failures, expected);
  const structured = structuredAssessment(repo, report, expected);
  const procedureFailures = [...procedure.failures];
  if (structured.failures.length > 0) procedureFailures.push({ id: "PROCEDURE_VERIFIER_FAILED", detail: "structured-source-predicates" });
  const hardFailures = [...base.failures, ...procedureFailures, ...structured.failures]
    .sort((a, b) => `${a.id}:${a.detail}`.localeCompare(`${b.id}:${b.detail}`));
  const admissionMetrics = {
    structured_predicate_recall: structured.recall,
    procedure_contract_coverage: procedure.coverage,
  };
  const weights = object(evalConfig.admission_metrics, "admission metrics");
  let admissionQuality = 0;
  for (const [name, value] of Object.entries(admissionMetrics)) admissionQuality += Number(weights[name] ?? 0) * value;
  return {
    schema: "repo-agent-native/ab-score/v2",
    hard_gate: hardFailures.length === 0 ? "PASS" : "FAIL",
    procedure_hard_gate: procedureFailures.length === 0 ? "PASS" : "FAIL",
    hard_failures: hardFailures,
    admission_metrics: admissionMetrics,
    admission_quality: Number(admissionQuality.toFixed(6)),
    procedure_receipt: procedure.receipt,
    structured_predicates: {
      evaluator: "retry-service-static/v1",
      evaluator_input_digest: sha256(structured.observed),
      observed: structured.observed,
      matched: structured.matched,
    },
    lexical_advisory: lexicalAdvisory(report, expected, object(evalConfig.lexical_advisory_metrics, "lexical advisory metrics")),
  };
}

type Options = { repo: string; report: string; expected: string; evals: string; output: string };

function parseArgs(args: string[]): Options {
  const options: Partial<Options> = {};
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    const value = args[index + 1];
    if (!value) throw new UsageError(`missing value for ${key}`);
    if (key === "--repo") options.repo = value;
    else if (key === "--report") options.report = value;
    else if (key === "--expected") options.expected = value;
    else if (key === "--evals") options.evals = value;
    else if (key === "--output") options.output = value;
    else throw new UsageError(`unknown argument: ${key}`);
  }
  if (!options.repo || !options.report || !options.expected || !options.evals || !options.output) {
    throw new UsageError("usage: score-ab-output.ts --repo <repo> --report <json> --expected <json> --evals <json> --output <json>");
  }
  return options as Options;
}

export function runScoreCli(args: string[]): number {
  try {
    const options = parseArgs(args);
    const evals = object(readJson(options.evals, "evals"), "evals");
    const score = scoreOutput(options.repo, readJson(options.report, "report"), readJson(options.expected, "ground truth"), evals);
    const parent = dirname(resolve(options.output));
    if (!existsSync(parent)) throw new UsageError(`output parent absent: ${parent}`);
    writeFileSync(options.output, `${JSON.stringify(score, null, 2)}\n`);
    return score.hard_gate === "PASS" ? 0 : 2;
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(error.message);
      return 64;
    }
    console.error(error instanceof Error ? error.message : "internal scoring error");
    return 70;
  }
}

if (import.meta.main) process.exitCode = runScoreCli(Bun.argv.slice(2));
