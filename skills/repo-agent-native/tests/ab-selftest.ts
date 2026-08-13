#!/usr/bin/env bun
import { cpSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { fixtureRepo, runAbCli } from "../scripts/run-ab.ts";
import { runScoreCli, scoreOutput } from "../scripts/score-ab-output.ts";
import { compareAb } from "../scripts/compare-ab.ts";

type JsonObject = Record<string, unknown>;

const TEST_ROOT = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(TEST_ROOT, "..");
const tempRoot = mkdtempSync(resolve(tmpdir(), "repo-agent-native-ab-selftest-"));
let positive = 0;
let mutations = 0;

function expect(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

function git(repo: string, args: string[]): string {
  const result = Bun.spawnSync(["git", "-C", repo, ...args], { stdout: "pipe", stderr: "pipe" });
  expect(result.exitCode === 0, `git ${args.join(" ")} failed: ${result.stderr.toString()}`);
  return result.stdout.toString().trim();
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function ref(path: string, start_line: number, end_line: number): JsonObject {
  return { path, start_line, end_line };
}

function record(id: string, claim: string, source: JsonObject, extra: JsonObject = {}): JsonObject {
  return { id, claim, evidence_level: "A", source_refs: [source], verification: ["source-read"], ...extra };
}

try {
  const fixture = resolve(tempRoot, "fixture");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), fixture, { recursive: true });
  git(fixture, ["init", "-q"]);
  git(fixture, ["add", "src"]);
  git(fixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture"]);
  const head = git(fixture, ["rev-parse", "HEAD"]);
  const retryRef = ref("src/retry-policy.ts", 1, 30);
  const apiRef = ref("src/api-client.ts", 8, 23);
  const report: JsonObject = {
    schema: "repo-agent-native/invariant-report/v2",
    subject: { repository: "eval/retry-service", observed_commit: head, observed_tree: null, scope: ["src"], task: "AB-RETRY-01" },
    routes: [],
    tools: ["FALLBACK: optional providers not invoked; direct source-read used"],
    facts: [
      record("INV-1", "RetryResult contains success, failure, and attempts", retryRef),
      record("INV-2", "The maximum is 3 attempts", retryRef),
      record("INV-3", "sleep waits 25 milliseconds between attempts", retryRef),
    ],
    negative_invariants: [
      record("NEG-1", "A metrics failure does not replace the domain result", apiRef, { search_boundary: ["src/api-client.ts"], counterexample_sought: "metrics error returned to caller" }),
      record("NEG-2", "There is no exponential backoff", retryRef, { search_boundary: ["src/retry-policy.ts"], counterexample_sought: "attempt-dependent delay" }),
    ],
    implicit_dependencies: [
      record("DEP-1", "loadAccount calls recordRetryFailure as best-effort telemetry", apiRef, { evidence_level: "C" }),
    ],
    open_questions: [],
    named_exclusions: [],
    state: "PASS",
  };
  const expected = JSON.parse(await Bun.file(resolve(SKILL_ROOT, "evals/fixtures/retry-service/expected.json")).text());
  const evals = JSON.parse(await Bun.file(resolve(SKILL_ROOT, "evals/evals.json")).text());
  const score = scoreOutput(fixture, report, expected, evals.metrics);
  expect(score.hard_gate === "PASS", `positive hard gate failed: ${JSON.stringify(score.hard_failures)}`);
  for (const [name, value] of Object.entries(score.metrics as JsonObject)) {
    if (name !== "unsupported_claim_penalty") expect(value === 1, `${name} expected 1, got ${String(value)}`);
  }
  expect((score.metrics as JsonObject).unsupported_claim_penalty === 0, "positive observed forbidden claim");
  positive += 1;

  const forbidden = structuredClone(report);
  (forbidden.facts as JsonObject[]).push(record("INV-X", "jitter is implemented", retryRef));
  const forbiddenScore = scoreOutput(fixture, forbidden, expected, evals.metrics);
  expect((forbiddenScore.forbidden_claims_observed as string[]).includes("jitter is implemented"), "forbidden-claim mutation survived");
  mutations += 1;

  const unanchored = structuredClone(report);
  (unanchored.facts as JsonObject[])[0]!.source_refs = [];
  const unanchoredScore = scoreOutput(fixture, unanchored, expected, evals.metrics);
  expect(unanchoredScore.hard_gate === "FAIL", "unanchored mutation survived");
  mutations += 1;

  const memoryPromotion = structuredClone(report);
  const memoryFact = (memoryPromotion.facts as JsonObject[])[0]!;
  memoryFact.provider_lane = "mem0";
  memoryFact.verification = [];
  const memoryScore = scoreOutput(fixture, memoryPromotion, expected, evals.metrics);
  expect(memoryScore.hard_gate === "FAIL", "memory-without-readback mutation survived");
  mutations += 1;

  const reportPath = resolve(tempRoot, "report.json");
  const scorePath = resolve(tempRoot, "score.json");
  writeJson(reportPath, report);
  expect(runScoreCli([
    "--repo", fixture,
    "--report", reportPath,
    "--expected", resolve(SKILL_ROOT, "evals/fixtures/retry-service/expected.json"),
    "--evals", resolve(SKILL_ROOT, "evals/evals.json"),
    "--output", scorePath,
  ]) === 0, "score CLI positive failed");
  positive += 1;

  const dryRoot = resolve(tempRoot, "dry-run");
  expect(await runAbCli([
    "--carrier", "codex",
    "--condition", "candidate_skill",
    "--case", "AB-RETRY-01",
    "--output", dryRoot,
  ]) === 0, "A/B dry-run failed");
  const dry = JSON.parse(await Bun.file(resolve(dryRoot, "dry-run.json")).text());
  expect(dry.state === "NOT_EXERCISED", "dry-run fabricated execution state");
  positive += 1;

  const deterministicA = resolve(tempRoot, "deterministic-a");
  const deterministicB = resolve(tempRoot, "deterministic-b");
  mkdirSync(deterministicA);
  mkdirSync(deterministicB);
  expect(fixtureRepo(deterministicA) === fixtureRepo(deterministicB), "A/B fixture commit is not deterministic");
  positive += 1;

  const baseReceipt = {
    state: "PASS",
    fixture_commit: head,
    scenario: "AB-RETRY-01",
    carrier: { id: "test", version: "1" },
    evaluator: { scorer_sha256: "same" },
    subject_bundle: { sha256: "same" },
    score: { hard_gate: "PASS", weighted_quality: 0.8 },
    skill: { name: "repo-agent-native", instruction_digest: "current", entrypoint_bytes: 100 },
  };
  const comparison = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", weighted_quality: 0.9 }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 80 } },
    current: baseReceipt,
    no_skill: { ...baseReceipt, score: { hard_gate: "PASS", weighted_quality: 0.5 }, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, score: { hard_gate: "PASS", weighted_quality: 0.6 }, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(comparison.state === "PASS", `comparison positive failed: ${JSON.stringify(comparison.failures)}`);
  positive += 1;

  const regressed = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", weighted_quality: 0.7 }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 120 } },
    current: baseReceipt,
    no_skill: { ...baseReceipt, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(comparison.state === "PASS" && regressed.state === "FAIL", "quality/context regression mutation survived");
  mutations += 1;

  console.log(`AB SELFTEST GREEN positive=${positive} mutations=${mutations}`);
} finally {
  rmSync(tempRoot, { recursive: true, force: true });
}
