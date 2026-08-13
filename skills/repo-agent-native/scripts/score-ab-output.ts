#!/usr/bin/env bun
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { assertOutput, type Failure } from "./assert-output.ts";

type JsonObject = Record<string, unknown>;
type ExpectedRecord = { id: string; class?: string; claim_concepts: string[][]; source?: string; bounded_scope?: string[] };
type Expected = {
  required_invariants: ExpectedRecord[];
  negative_invariants: ExpectedRecord[];
  forbidden_claims: string[];
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

function records(report: JsonObject, field: string): JsonObject[] {
  return Array.isArray(report[field]) ? report[field].filter((item): item is JsonObject => typeof item === "object" && item !== null && !Array.isArray(item)) : [];
}

function sourcePaths(record: JsonObject): string[] {
  return Array.isArray(record.source_refs)
    ? record.source_refs.flatMap((item) => typeof item === "object" && item !== null && !Array.isArray(item) && typeof (item as JsonObject).path === "string" ? [(item as JsonObject).path as string] : [])
    : [];
}

function matches(record: JsonObject, expected: ExpectedRecord): boolean {
  const claim = normalize(record.claim);
  if (!Array.isArray(expected.claim_concepts) || !expected.claim_concepts.every((aliases) =>
    Array.isArray(aliases) && aliases.some((alias) => claim.includes(normalize(alias))),
  )) return false;
  return !expected.source || sourcePaths(record).includes(expected.source);
}

function ratio(numerator: number, denominator: number): number {
  return denominator === 0 ? 1 : numerator / denominator;
}

export function scoreOutput(repo: string, reportValue: unknown, expectedValue: unknown, weightsValue: unknown): JsonObject {
  const report = object(reportValue, "report");
  const expected = object(expectedValue, "ground truth") as unknown as Expected;
  const weights = object(weightsValue, "weights");
  if (!Array.isArray(expected.required_invariants) || !Array.isArray(expected.negative_invariants) || !Array.isArray(expected.forbidden_claims)) {
    throw new UsageError("ground truth fields are invalid");
  }
  const hard = assertOutput(repo, report);
  const facts = records(report, "facts");
  const negatives = records(report, "negative_invariants");
  const dependencies = records(report, "implicit_dependencies");
  const requiredFacts = expected.required_invariants.filter((item) => item.class !== "implicit-dependency");
  const requiredDependencies = expected.required_invariants.filter((item) => item.class === "implicit-dependency");
  const matchedFacts = requiredFacts.filter((item) => facts.some((record) => matches(record, item)));
  const matchedDependencies = requiredDependencies.filter((item) => dependencies.some((record) => matches(record, item)));
  const matchedNegatives = expected.negative_invariants.filter((item) => negatives.some((record) => matches(record, item)));
  const allRecords = [...facts, ...negatives, ...dependencies];
  const allClaims = allRecords.map((record) => normalize(record.claim)).join("\n");
  const forbidden = expected.forbidden_claims.filter((claim) => allClaims.includes(normalize(claim)));
  const forbiddenRecordCount = allRecords.filter((record) =>
    expected.forbidden_claims.some((claim) => normalize(record.claim).includes(normalize(claim))),
  ).length;
  const totalRecords = allRecords.length;
  const toolText = Array.isArray(report.tools) ? normalize(report.tools.join("\n")) : "";
  const namedFallback = toolText.includes("fallback") && (toolText.includes("source read") || toolText.includes("direct source"));
  const metrics = {
    anchored_nonforbidden_precision_proxy: ratio(totalRecords - forbiddenRecordCount, totalRecords),
    required_invariant_recall: ratio(matchedFacts.length, requiredFacts.length),
    negative_invariant_recall: ratio(matchedNegatives.length, expected.negative_invariants.length),
    implicit_dependency_recall: ratio(matchedDependencies.length, requiredDependencies.length),
    source_anchor_validity: hard.failures.some((failure) => failure.id.startsWith("SOURCE_") || failure.id === "SUBJECT_IDENTITY_MISMATCH") ? 0 : 1,
    tool_fallback_correctness: hard.failures.some((failure) => failure.id === "SOURCE_READBACK_MISSING") || !namedFallback ? 0 : 1,
    unsupported_claim_penalty: forbidden.length,
  };
  let weightedQuality = 0;
  for (const [name, value] of Object.entries(metrics)) {
    const weight = Number(weights[name] ?? 0);
    weightedQuality += weight < 0 ? weight * Number(value) : weight * Number(value);
  }
  return {
    schema: "repo-agent-native/ab-score/v1",
    hard_gate: hard.failures.length === 0 ? "PASS" : "FAIL",
    hard_failures: hard.failures,
    metrics,
    weighted_quality: Number(weightedQuality.toFixed(6)),
    matched: {
      required_invariants: matchedFacts.map((item) => item.id),
      negative_invariants: matchedNegatives.map((item) => item.id),
      implicit_dependencies: matchedDependencies.map((item) => item.id),
    },
    forbidden_claims_observed: forbidden,
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
    const score = scoreOutput(options.repo, readJson(options.report, "report"), readJson(options.expected, "ground truth"), evals.metrics);
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
