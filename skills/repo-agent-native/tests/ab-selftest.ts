#!/usr/bin/env bun
import { cpSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { fixtureRepo, instructionDigest, runAbCli } from "../scripts/run-ab.ts";
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

function record(id: string, claim: string, predicateId: string, value: unknown, source: JsonObject, extra: JsonObject = {}): JsonObject {
  return {
    id,
    class: "fixture-contract",
    claim,
    predicate: { id: predicateId, operator: "equals", value },
    evidence_level: "A",
    source_refs: [source],
    verification: ["source-read"],
    ...extra,
  };
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
  const metricsRef = ref("src/metrics.ts", 1, 8);
  const report: JsonObject = {
    schema: "repo-agent-native/invariant-report/v2",
    subject: { repository: "eval/retry-service", observed_commit: head, observed_tree: null, scope: ["src"], task: "AB-RETRY-01" },
    routes: [],
    tools: ["FALLBACK: optional providers not invoked; direct source-read used"],
    facts: [
      record("INV-1", "RetryResult contains success, failure, and attempts", "retry.result_contract", "discriminated-success-failure-attempts", retryRef),
      record("INV-2", "The maximum is 3 attempts", "retry.max_attempts", 3, retryRef),
      record("INV-3", "sleep waits 25 milliseconds between attempts", "retry.delay_ms", 25, retryRef),
    ],
    negative_invariants: [
      record("NEG-1", "A metrics failure does not replace the domain result", "metrics.failure_mode", "swallowed", apiRef, { search_boundary: ["src/api-client.ts"], counterexample_sought: "metrics error returned to caller" }),
      record("NEG-2", "There is no exponential backoff", "retry.delay_strategy", "fixed", retryRef, { search_boundary: ["src/retry-policy.ts"], counterexample_sought: "attempt-dependent delay" }),
    ],
    implicit_dependencies: [
      record("DEP-1", "recordRetryFailure has no durable observability sink", "metrics.observability_sink", "none", metricsRef, { evidence_level: "C" }),
    ],
    open_questions: [],
    named_exclusions: [],
    state: "PASS",
  };
  const expected = JSON.parse(await Bun.file(resolve(SKILL_ROOT, "evals/fixtures/retry-service/expected.json")).text());
  const evals = JSON.parse(await Bun.file(resolve(SKILL_ROOT, "evals/evals.json")).text());
  const outputSchema = JSON.parse(await Bun.file(resolve(SKILL_ROOT, "evals/fixtures/invariant-report.schema.json")).text()) as JsonObject;
  const schemaDefs = outputSchema.$defs as JsonObject;
  const factSchema = schemaDefs.fact as JsonObject;
  const factProperties = factSchema.properties as JsonObject;
  const verificationSchema = factProperties.verification as JsonObject;
  const verificationItems = verificationSchema.items as JsonObject;
  expect(Array.isArray(verificationItems.enum) && verificationItems.enum.includes("source-read"), "output schema does not expose the hard verification vocabulary");
  positive += 1;
  const score = scoreOutput(fixture, report, expected, evals);
  expect(score.hard_gate === "PASS", `positive hard gate failed: ${JSON.stringify(score.hard_failures)}`);
  expect(score.procedure_hard_gate === "PASS", "positive procedure gate failed");
  expect(score.admission_quality === 1, `positive admission quality expected 1, got ${String(score.admission_quality)}`);
  expect((score.lexical_advisory as JsonObject).authority === "advisory-only", "lexical signal gained admission authority");
  expect((score.lexical_advisory as JsonObject).admission_effect === "none", "lexical signal can affect admission");
  positive += 1;

  const forbidden = structuredClone(report);
  (forbidden.facts as JsonObject[]).push(record("INV-X", "jitter is implemented", "unregistered.claim", true, retryRef));
  const forbiddenScore = scoreOutput(fixture, forbidden, expected, evals);
  expect(((forbiddenScore.lexical_advisory as JsonObject).forbidden_claims_observed as string[]).includes("jitter is implemented"), "forbidden-claim advisory mutation survived");
  mutations += 1;

  const unanchored = structuredClone(report);
  (unanchored.facts as JsonObject[])[0]!.source_refs = [];
  const unanchoredScore = scoreOutput(fixture, unanchored, expected, evals);
  expect(unanchoredScore.hard_gate === "FAIL" && unanchoredScore.procedure_hard_gate === "FAIL", "unanchored mutation survived the procedure gate");
  mutations += 1;

  const memoryPromotion = structuredClone(report);
  const memoryFact = (memoryPromotion.facts as JsonObject[])[0]!;
  memoryFact.provider_lane = "mem0";
  memoryFact.verification = [];
  const memoryScore = scoreOutput(fixture, memoryPromotion, expected, evals);
  expect(memoryScore.hard_gate === "FAIL", "memory-without-readback mutation survived");
  mutations += 1;

  const wrongPredicate = structuredClone(report);
  ((wrongPredicate.facts as JsonObject[])[1]!.predicate as JsonObject).value = 99;
  const wrongPredicateScore = scoreOutput(fixture, wrongPredicate, expected, evals);
  expect(wrongPredicateScore.hard_gate === "FAIL" && (wrongPredicateScore.hard_failures as JsonObject[]).some((failure) => failure.id === "STRUCTURED_PREDICATE_MISMATCH"), "source-contradicting structured predicate survived");
  mutations += 1;

  const noFallbackWords = structuredClone(report);
  noFallbackWords.tools = ["optional providers unavailable; repository source was read directly"];
  const noFallbackScore = scoreOutput(fixture, noFallbackWords, expected, evals);
  expect(noFallbackScore.admission_quality === score.admission_quality, "model-reported fallback wording changed hard admission quality");
  expect((noFallbackScore.procedure_receipt as JsonObject).model_reported_advisory !== undefined, "procedure receipt did not separate model-reported advisory evidence");
  positive += 1;

  const noDependency = structuredClone(report);
  noDependency.implicit_dependencies = [];
  const noDependencyScore = scoreOutput(fixture, noDependency, expected, evals);
  expect(noDependencyScore.procedure_hard_gate === "FAIL" && noDependencyScore.hard_gate === "FAIL", "missing required procedural artifact survived");
  mutations += 1;

  const mutatedFixture = resolve(tempRoot, "fixture-max-five");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), mutatedFixture, { recursive: true });
  const retryPath = resolve(mutatedFixture, "src/retry-policy.ts");
  const retrySource = await Bun.file(retryPath).text();
  writeFileSync(retryPath, retrySource.replace("MAX_ATTEMPTS = 3", "MAX_ATTEMPTS = 5"));
  git(mutatedFixture, ["init", "-q"]);
  git(mutatedFixture, ["add", "src"]);
  git(mutatedFixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture max five"]);
  const mutatedHead = git(mutatedFixture, ["rev-parse", "HEAD"]);
  const staleMutationReport = structuredClone(report);
  (staleMutationReport.subject as JsonObject).observed_commit = mutatedHead;
  const staleMutationScore = scoreOutput(mutatedFixture, staleMutationReport, expected, evals);
  expect(staleMutationScore.hard_gate === "FAIL", "unchanged predicate survived a source mutation");
  const adaptedMutationReport = structuredClone(staleMutationReport);
  ((adaptedMutationReport.facts as JsonObject[])[1]!.predicate as JsonObject).value = 5;
  const adaptedMutationScore = scoreOutput(mutatedFixture, adaptedMutationReport, expected, evals);
  expect(adaptedMutationScore.hard_gate === "PASS", `adapted mutation report failed: ${JSON.stringify(adaptedMutationScore.hard_failures)}`);
  positive += 1;
  mutations += 1;

  const strategyFixture = resolve(tempRoot, "fixture-exponential-delay");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), strategyFixture, { recursive: true });
  const strategyPath = resolve(strategyFixture, "src/retry-policy.ts");
  const strategySource = await Bun.file(strategyPath).text();
  writeFileSync(strategyPath, strategySource.replace("sleep(RETRY_DELAY_MS)", "sleep(RETRY_DELAY_MS * 2 ** (attempt - 1))"));
  git(strategyFixture, ["init", "-q"]);
  git(strategyFixture, ["add", "src"]);
  git(strategyFixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture exponential delay"]);
  const strategyHead = git(strategyFixture, ["rev-parse", "HEAD"]);
  const staleStrategyReport = structuredClone(report);
  (staleStrategyReport.subject as JsonObject).observed_commit = strategyHead;
  expect(scoreOutput(strategyFixture, staleStrategyReport, expected, evals).hard_gate === "FAIL", "fixed-delay report survived exponential-delay mutation");
  const adaptedStrategyReport = structuredClone(staleStrategyReport);
  ((adaptedStrategyReport.negative_invariants as JsonObject[])[1]!.predicate as JsonObject).value = "exponential";
  expect(scoreOutput(strategyFixture, adaptedStrategyReport, expected, evals).hard_gate === "PASS", "adapted exponential-delay predicate failed");
  positive += 1;
  mutations += 1;

  const sinkFixture = resolve(tempRoot, "fixture-observability-sink");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), sinkFixture, { recursive: true });
  const metricsPath = resolve(sinkFixture, "src/metrics.ts");
  const metricsSource = await Bun.file(metricsPath).text();
  writeFileSync(metricsPath, metricsSource.replace("  }\n}", "  }\n  console.warn(operation, attempts);\n}"));
  git(sinkFixture, ["init", "-q"]);
  git(sinkFixture, ["add", "src"]);
  git(sinkFixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture observability sink"]);
  const sinkHead = git(sinkFixture, ["rev-parse", "HEAD"]);
  const staleSinkReport = structuredClone(report);
  (staleSinkReport.subject as JsonObject).observed_commit = sinkHead;
  expect(scoreOutput(sinkFixture, staleSinkReport, expected, evals).hard_gate === "FAIL", "no-sink report survived observability-sink mutation");
  const adaptedSinkReport = structuredClone(staleSinkReport);
  ((adaptedSinkReport.implicit_dependencies as JsonObject[])[0]!.predicate as JsonObject).value = "present";
  expect(scoreOutput(sinkFixture, adaptedSinkReport, expected, evals).hard_gate === "PASS", "adapted observability-sink predicate failed");
  positive += 1;
  mutations += 1;

  const propagatedFixture = resolve(tempRoot, "fixture-propagated-metrics-failure");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), propagatedFixture, { recursive: true });
  const apiPath = resolve(propagatedFixture, "src/api-client.ts");
  const apiSource = await Bun.file(apiPath).text();
  writeFileSync(apiPath, apiSource.replace("} catch {\n      // Metrics are best-effort and must not replace the domain result.\n    }", "} catch (error) {\n      throw error;\n    }"));
  git(propagatedFixture, ["init", "-q"]);
  git(propagatedFixture, ["add", "src"]);
  git(propagatedFixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture propagated metrics failure"]);
  const propagatedHead = git(propagatedFixture, ["rev-parse", "HEAD"]);
  const stalePropagatedReport = structuredClone(report);
  (stalePropagatedReport.subject as JsonObject).observed_commit = propagatedHead;
  expect(scoreOutput(propagatedFixture, stalePropagatedReport, expected, evals).hard_gate === "FAIL", "swallowed-failure report survived propagation mutation");
  const adaptedPropagatedReport = structuredClone(stalePropagatedReport);
  ((adaptedPropagatedReport.negative_invariants as JsonObject[])[0]!.predicate as JsonObject).value = "propagated";
  expect(scoreOutput(propagatedFixture, adaptedPropagatedReport, expected, evals).hard_gate === "PASS", "adapted propagated-failure predicate failed");
  positive += 1;
  mutations += 1;

  const formattedFixture = resolve(tempRoot, "fixture-equivalent-formatting");
  cpSync(resolve(SKILL_ROOT, "evals/fixtures/retry-service"), formattedFixture, { recursive: true });
  const formattedPath = resolve(formattedFixture, "src/retry-policy.ts");
  const formattedSource = await Bun.file(formattedPath).text();
  writeFileSync(formattedPath, formattedSource.replace("export type RetryResult<T> =", "export type RetryResult<T>    ="));
  git(formattedFixture, ["init", "-q"]);
  git(formattedFixture, ["add", "src"]);
  git(formattedFixture, ["-c", "user.name=AB Selftest", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture equivalent formatting"]);
  const formattedReport = structuredClone(report);
  (formattedReport.subject as JsonObject).observed_commit = git(formattedFixture, ["rev-parse", "HEAD"]);
  expect(scoreOutput(formattedFixture, formattedReport, expected, evals).hard_gate === "PASS", "semantically equivalent formatting broke predicate observation");
  positive += 1;

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
    "--model", "test-model",
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

  expect(instructionDigest(resolve(SKILL_ROOT, "../knowledge-continuity")).length === 64, "optional Skill directories were treated as mandatory");
  positive += 1;

  const baseReceipt = {
    state: "PASS",
    fixture_commit: head,
    scenario: "AB-RETRY-01",
    carrier: { id: "test", version: "1" },
    evaluator: { scorer_sha256: "same" },
    subject_bundle: { sha256: "same" },
    score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.8, lexical_advisory: { weighted_quality: 0.1 } },
    skill: { name: "repo-agent-native", instruction_digest: "current", entrypoint_bytes: 100 },
  };
  const comparison = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.9, lexical_advisory: { weighted_quality: 0.1 } }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 80 } },
    current: baseReceipt,
    no_skill: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.5, lexical_advisory: { weighted_quality: 0.9 } }, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.6, lexical_advisory: { weighted_quality: 0.9 } }, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(comparison.state === "PASS", `comparison positive failed: ${JSON.stringify(comparison.failures)}`);
  positive += 1;

  const regressed = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.7, lexical_advisory: { weighted_quality: 1 } }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 120 } },
    current: baseReceipt,
    no_skill: { ...baseReceipt, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(comparison.state === "PASS" && regressed.state === "FAIL", "quality/context regression mutation survived");
  mutations += 1;

  const carrierFailed = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.9, lexical_advisory: { weighted_quality: 0 } }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 80 } },
    current: { ...baseReceipt, state: "FAIL", score: null },
    no_skill: { ...baseReceipt, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(carrierFailed.state === "FAIL" && (carrierFailed.failures as string[]).some((failure) => failure.includes("evaluable score is absent")), "carrier-failure comparison did not fail closed");
  mutations += 1;

  const ineffectiveTreatment = compareAb({
    candidate: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.9, lexical_advisory: { weighted_quality: 0 } }, skill: { name: "repo-agent-native", instruction_digest: "candidate", entrypoint_bytes: 80 } },
    current: baseReceipt,
    no_skill: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.5, lexical_advisory: { weighted_quality: 1 } }, skill: { name: null, instruction_digest: null, entrypoint_bytes: null } },
    wrong_skill: { ...baseReceipt, score: { hard_gate: "PASS", procedure_hard_gate: "PASS", admission_quality: 0.9, lexical_advisory: { weighted_quality: 0 } }, skill: { name: "knowledge-continuity", instruction_digest: "wrong", entrypoint_bytes: 90 } },
  }, evals);
  expect(ineffectiveTreatment.state === "FAIL" && (ineffectiveTreatment.failures as string[]).some((failure) => failure.includes("candidate minus wrong_skill")), "ineffective wrong-skill treatment survived");
  mutations += 1;

  console.log(`AB SELFTEST GREEN positive=${positive} mutations=${mutations}`);
} finally {
  rmSync(tempRoot, { recursive: true, force: true });
}
