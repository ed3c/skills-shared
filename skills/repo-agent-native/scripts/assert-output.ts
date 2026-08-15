#!/usr/bin/env bun
import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";

export type Failure = { id: string; detail: string };
type JsonObject = Record<string, unknown>;

const STATES = new Set(["PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY"]);
const SOURCE_LEVELS = new Set(["A", "A-"]);
const CANDIDATE_LANES = new Set(["memory", "semantic", "search", "graph", "grepai", "mem0", "code-graph-rag"]);
const GIT_TIMEOUT_MS = 10_000;
const MAX_REPORT_BYTES = 4 * 1024 * 1024;

class UsageError extends Error {}

function object(value: unknown, label: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new UsageError(`${label} must be an object`);
  return value as JsonObject;
}

function sha256(data: string | Buffer): string {
  return createHash("sha256").update(data).digest("hex");
}

function string(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim());
}

function inside(root: string, target: string): boolean {
  const rel = relative(root, target);
  return rel === "" || (!rel.startsWith("..") && !isAbsolute(rel));
}

function gitHead(repo: string): string {
  const result = Bun.spawnSync(["git", "-C", repo, "rev-parse", "HEAD"], { stdout: "pipe", stderr: "pipe", timeout: GIT_TIMEOUT_MS });
  if (result.exitCode !== 0) throw new UsageError(`repository subject is not a readable Git worktree: ${repo}`);
  return result.stdout.toString().trim();
}

function gitFileAtHead(repo: string, path: string): Buffer | null {
  const result = Bun.spawnSync(["git", "-C", repo, "show", `HEAD:${path}`], { stdout: "pipe", stderr: "pipe", timeout: GIT_TIMEOUT_MS });
  return result.exitCode === 0 ? Buffer.from(result.stdout) : null;
}

function validateSourceRefs(
  repo: string,
  record: JsonObject,
  label: string,
  failures: Failure[],
): void {
  const refs = record.source_refs;
  if (!Array.isArray(refs) || refs.length === 0) {
    failures.push({ id: "SOURCE_REF_MISSING", detail: `${label} has no source_refs` });
    return;
  }
  for (const [index, raw] of refs.entries()) {
    let ref: JsonObject;
    try {
      ref = object(raw, `${label}.source_refs[${index}]`);
    } catch (error) {
      failures.push({ id: "SOURCE_REF_INVALID", detail: error instanceof Error ? error.message : label });
      continue;
    }
    if (!string(ref.path) || isAbsolute(ref.path)) {
      failures.push({ id: "SOURCE_REF_INVALID", detail: `${label} source path must be repository-relative` });
      continue;
    }
    const path = resolve(repo, ref.path);
    if (!inside(repo, path)) {
      failures.push({ id: "SOURCE_REF_ESCAPE", detail: `${label} source path escapes repository: ${ref.path}` });
      continue;
    }
    const sourceBytes = gitFileAtHead(repo, ref.path);
    if (sourceBytes === null) {
      failures.push({ id: "SOURCE_REF_ABSENT", detail: `${label} source path absent: ${ref.path}` });
      continue;
    }
    const start = ref.start_line;
    const end = ref.end_line;
    const sourceText = sourceBytes.toString("utf8").replace(/\r?\n$/, "");
    const lineCount = sourceText ? sourceText.split(/\r?\n/).length : 0;
    if (!Number.isInteger(start) || !Number.isInteger(end) || (start as number) < 1 || (end as number) < (start as number) || (end as number) > lineCount) {
      failures.push({ id: "SOURCE_RANGE_INVALID", detail: `${label} invalid range for ${ref.path}` });
    }
    if (ref.blob_sha256 !== undefined && ref.blob_sha256 !== sha256(sourceBytes)) {
      failures.push({ id: "SOURCE_DIGEST_MISMATCH", detail: `${label} digest mismatch for ${ref.path}` });
    }
  }
}

function checkRecords(repo: string, report: JsonObject, failures: Failure[]): void {
  for (const group of ["facts", "negative_invariants", "implicit_dependencies"] as const) {
    const records = report[group];
    if (!Array.isArray(records)) {
      failures.push({ id: "REPORT_FIELD_INVALID", detail: `${group} must be an array` });
      continue;
    }
    for (const [index, raw] of records.entries()) {
      let record: JsonObject;
      try {
        record = object(raw, `${group}[${index}]`);
      } catch (error) {
        failures.push({ id: "REPORT_FIELD_INVALID", detail: error instanceof Error ? error.message : group });
        continue;
      }
      const label = `${group}[${index}]`;
      if (!string(record.id) || !string(record.class) || !string(record.claim)) failures.push({ id: "REPORT_FIELD_INVALID", detail: `${label} requires id, class, and claim` });
      if (typeof record.predicate !== "object" || record.predicate === null || Array.isArray(record.predicate)) {
        failures.push({ id: "STRUCTURED_PREDICATE_INVALID", detail: `${label} requires a predicate object` });
      } else {
        const predicate = record.predicate as JsonObject;
        const valueType = predicate.value === null ? "null" : typeof predicate.value;
        if (!string(predicate.id) || predicate.operator !== "equals" || !["string", "number", "boolean", "null"].includes(valueType)) {
          failures.push({ id: "STRUCTURED_PREDICATE_INVALID", detail: `${label} predicate requires id, equals operator, and a scalar value` });
        }
      }
      if (record.evidence_level === "D") failures.push({ id: "UNSUPPORTED_CLAIM", detail: `${label} accepts evidence level D` });
      validateSourceRefs(repo, record, label, failures);
      const verification = Array.isArray(record.verification) ? record.verification.filter(string) : [];
      const lane = string(record.provider_lane) ? record.provider_lane.toLowerCase() : "";
      if ((SOURCE_LEVELS.has(String(record.evidence_level)) || CANDIDATE_LANES.has(lane)) && !verification.includes("source-read")) {
        failures.push({ id: "SOURCE_READBACK_MISSING", detail: `${label} requires source-read verification` });
      }
      if (group === "negative_invariants") {
        if (!Array.isArray(record.search_boundary) || record.search_boundary.length === 0 || !string(record.counterexample_sought)) {
          failures.push({ id: "ABSENCE_BOUNDARY_UNDECLARED", detail: `${label} requires search_boundary and counterexample_sought` });
        }
      }
    }
  }
}

export function assertOutput(repoInput: string, reportValue: unknown): { failures: Failure[]; observedCommit: string } {
  const repo = resolve(repoInput);
  if (!existsSync(repo) || !statSync(repo).isDirectory()) throw new UsageError(`repository subject absent: ${repo}`);
  const observedCommit = gitHead(repo);
  const report = object(reportValue, "report");
  if (report.schema !== "repo-agent-native/invariant-report/v2") throw new UsageError("report schema is absent or unsupported");
  const failures: Failure[] = [];
  const subject = object(report.subject, "report.subject");
  if (!string(subject.repository) || !Array.isArray(subject.scope) || subject.scope.length === 0 || subject.scope.some((item) => !string(item))) {
    failures.push({ id: "SUBJECT_INVALID", detail: "subject repository and non-empty scope are required" });
  }
  if (subject.observed_commit !== null && subject.observed_commit !== observedCommit) {
    failures.push({ id: "SUBJECT_IDENTITY_MISMATCH", detail: `report ${String(subject.observed_commit)} != repository ${observedCommit}` });
  }
  if (report.state === "PASS" && subject.observed_commit === null) {
    failures.push({ id: "SUBJECT_IDENTITY_ABSENT", detail: "a PASS report requires the exact observed commit" });
  }
  if (!STATES.has(String(report.state))) failures.push({ id: "EVIDENCE_STATE_INVALID", detail: `unknown state ${String(report.state)}` });
  for (const field of ["routes", "tools", "open_questions", "named_exclusions"]) {
    if (!Array.isArray(report[field])) failures.push({ id: "REPORT_FIELD_INVALID", detail: `${field} must be an array` });
  }
  checkRecords(repo, report, failures);
  const recordCount = ["facts", "negative_invariants", "implicit_dependencies"]
    .map((field) => Array.isArray(report[field]) ? report[field].length : 0)
    .reduce((sum, count) => sum + count, 0);
  if (report.state === "PASS" && recordCount === 0) {
    failures.push({ id: "EMPTY_PASS", detail: "a PASS report requires at least one source-anchored record" });
  }
  const serialized = JSON.stringify(report);
  for (const [pattern, label] of [
    [/(?:\/Users\/|\/home\/|[A-Za-z]:\\)/, "machine-local path"],
    [/(?:api[_-]?key|password|access[_-]?token)["']?\s*:\s*["'][^"']+["']/i, "secret-shaped value"],
  ] as Array<[RegExp, string]>) {
    if (pattern.test(serialized)) failures.push({ id: "SENSITIVE_OR_LOCAL_VALUE", detail: label });
  }
  return { failures: failures.sort((a, b) => `${a.id}:${a.detail}`.localeCompare(`${b.id}:${b.detail}`)), observedCommit };
}

type CliOptions = { repo: string; report: string; receipt: string };

function parseArgs(args: string[]): CliOptions {
  const options: Partial<CliOptions> = {};
  for (let index = 0; index < args.length; index += 1) {
    const key = args[index];
    const value = args[++index];
    if (!value) throw new UsageError(`missing value for ${key}`);
    if (key === "--repo") options.repo = value;
    else if (key === "--report") options.report = value;
    else if (key === "--receipt") options.receipt = value;
    else throw new UsageError(`unknown argument: ${key}`);
  }
  if (!options.repo || !options.report || !options.receipt) {
    throw new UsageError("usage: assert-output.ts --repo <repo> --report <report.json> --receipt <receipt.json>");
  }
  return options as CliOptions;
}

function readJson(path: string): unknown {
  if (!existsSync(path)) throw new UsageError(`report absent: ${path}`);
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new UsageError(`report is not valid JSON: ${error instanceof Error ? error.message : path}`);
  }
}

export function runAssertCli(args: string[]): number {
  try {
    const options = parseArgs(args);
    const reportValue = readJson(options.report);
    const reportText = readFileSync(options.report, "utf8");
    if (Buffer.byteLength(reportText) > MAX_REPORT_BYTES) throw new UsageError(`report exceeds ${MAX_REPORT_BYTES} bytes`);
    const result = assertOutput(options.repo, reportValue);
    const parent = dirname(resolve(options.receipt));
    if (!existsSync(parent)) throw new UsageError(`receipt parent absent: ${parent}`);
    writeFileSync(options.receipt, `${JSON.stringify({
      schema: "repo-agent-native/output-assertion-receipt/v1",
      subject: {
        repository_root: resolve(options.repo),
        observed_commit: result.observedCommit,
        report_sha256: sha256(reportText),
      },
      state: result.failures.length ? "FAIL" : "PASS",
      failures: result.failures,
    }, null, 2)}\n`);
    return result.failures.length ? 2 : 0;
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(error.message);
      return 64;
    }
    console.error(error instanceof Error ? error.message : "internal assertion error");
    return 70;
  }
}

if (import.meta.main) process.exitCode = runAssertCli(Bun.argv.slice(2));
