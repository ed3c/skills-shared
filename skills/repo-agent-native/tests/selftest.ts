#!/usr/bin/env bun
import { createHash } from "node:crypto";
import {
  cpSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { assertOutput, runAssertCli } from "../scripts/assert-output.ts";
import { runValidateCli, validateSkill } from "../scripts/validate-skill.ts";

type JsonObject = Record<string, unknown>;

const TEST_ROOT = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(TEST_ROOT, "..");
const tempRoot = mkdtempSync(resolve(tmpdir(), "repo-agent-native-selftest-"));
let positiveCount = 0;
let mutationCount = 0;
let exitContractCount = 0;

function expect(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

function expectFailureIds(actual: { failures: Array<{ id: string }> }, ids: string[], label: string): void {
  const observed = new Set(actual.failures.map((failure) => failure.id));
  for (const id of ids) expect(observed.has(id), `${label}: expected ${id}, observed ${[...observed].join(", ") || "none"}`);
  mutationCount += 1;
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function git(repo: string, args: string[]): string {
  const result = Bun.spawnSync(["git", "-C", repo, ...args], { stdout: "pipe", stderr: "pipe" });
  expect(result.exitCode === 0, `git ${args.join(" ")} failed: ${result.stderr.toString()}`);
  return result.stdout.toString().trim();
}

function makeRepo(root: string): { head: string; report: JsonObject; sourceDigest: string } {
  mkdirSync(resolve(root, "src"), { recursive: true });
  const source = [
    "export function retry(limit: number): number {",
    "  if (limit > 3) throw new Error('retry limit');",
    "  return limit;",
    "}",
  ].join("\n") + "\n";
  writeFileSync(resolve(root, "src/retry.ts"), source);
  git(root, ["init", "-q"]);
  git(root, ["add", "src/retry.ts"]);
  git(root, ["-c", "user.name=Selftest", "-c", "user.email=selftest@example.invalid", "commit", "-qm", "fixture"]);
  const head = git(root, ["rev-parse", "HEAD"]);
  const sourceDigest = createHash("sha256").update(source).digest("hex");
  const sourceRef = { path: "src/retry.ts", start_line: 1, end_line: 4, blob_sha256: sourceDigest };
  return {
    head,
    sourceDigest,
    report: {
      schema: "repo-agent-native/invariant-report/v2",
      subject: { repository: "selftest/retry", observed_commit: head, observed_tree: null, scope: ["src"], task: "retry contract" },
      routes: ["README absent and recorded"],
      tools: [{ lane: "tier-0", state: "PASS" }],
      facts: [{ id: "INV-001", claim: "Retries reject limits above three", evidence_level: "A", source_refs: [sourceRef], verification: ["source-read"] }],
      negative_invariants: [{ id: "NEG-001", claim: "The source does not silently clamp a limit above three", evidence_level: "A", source_refs: [sourceRef], verification: ["source-read"], search_boundary: ["src"], counterexample_sought: "a clamp before the throw" }],
      implicit_dependencies: [{ id: "DEP-001", claim: "Callers must keep the retry limit at three or below", evidence_level: "C", source_refs: [sourceRef], verification: ["source-read"] }],
      open_questions: [],
      named_exclusions: ["runtime timing"],
      state: "PASS",
    },
  };
}

function skillMutation(name: string, mutate: (root: string) => void): string {
  const root = resolve(tempRoot, `skill-${name}`);
  cpSync(SKILL_ROOT, root, { recursive: true });
  mutate(root);
  return root;
}

try {
  const structuralPositive = validateSkill(SKILL_ROOT);
  expect(structuralPositive.failures.length === 0, `canonical skill failed: ${JSON.stringify(structuralPositive.failures)}`);
  positiveCount += 1;

  const hostField = skillMutation("host-field", (root) => {
    const path = resolve(root, "SKILL.md");
    writeFileSync(path, readFileSync(path, "utf8").replace("license: MIT", "license: MIT\nargument-hint: '[scope]'"));
  });
  expectFailureIds(validateSkill(hostField), ["NON_PORTABLE_FRONTMATTER"], "host-only frontmatter");

  const invalidMetadata = skillMutation("invalid-metadata", (root) => {
    const path = resolve(root, "SKILL.md");
    writeFileSync(path, readFileSync(path, "utf8").replace('version: "2.0.0"', "version: 2"));
  });
  let metadataRejected = false;
  try {
    validateSkill(invalidMetadata);
  } catch (error) {
    metadataRejected = error instanceof Error && error.message.includes("metadata values must be strings");
  }
  expect(metadataRejected, "metadata values must follow the portable string-map contract");
  mutationCount += 1;

  const oversized = skillMutation("oversized", (root) => {
    const path = resolve(root, "SKILL.md");
    writeFileSync(path, `${readFileSync(path, "utf8")}\n${Array.from({ length: 221 }, (_, index) => `padding ${index}`).join("\n")}\n`);
  });
  expectFailureIds(validateSkill(oversized), ["SKILL_CORE_BUDGET"], "core line budget");

  const brokenLink = skillMutation("broken-link", (root) => {
    const path = resolve(root, "SKILL.md");
    writeFileSync(path, `${readFileSync(path, "utf8")}\n[missing](references/absent.md)\n`);
  });
  expectFailureIds(validateSkill(brokenLink), ["BROKEN_RELATIVE_REFERENCE"], "broken reference");

  const absolutePath = skillMutation("absolute-path", (root) => {
    const path = resolve(root, "SKILL.md");
    const plantedPath = ["", "Users", "example", "private", "tool"].join("/");
    writeFileSync(path, `${readFileSync(path, "utf8")}\nUse ${plantedPath}.\n`);
  });
  expectFailureIds(validateSkill(absolutePath), ["NON_PORTABLE_BODY"], "absolute path");

  const providerInCore = skillMutation("provider-in-core", (root) => {
    const path = resolve(root, "SKILL.md");
    writeFileSync(path, `${readFileSync(path, "utf8")}\nUse Serena for symbol lookup.\n`);
  });
  expectFailureIds(validateSkill(providerInCore), ["DOMAIN_INSTANCE_IN_CORE"], "provider instance in portable core");

  const missingModule = skillMutation("missing-module", (root) => rmSync(resolve(root, "modules/mem0.md")));
  expectFailureIds(validateSkill(missingModule), ["MODULE_CONTRACT_INCOMPLETE"], "missing provider module");

  const missingModuleStateMachine = skillMutation("missing-module-state-machine", (root) => {
    const path = resolve(root, "modules/grepai.md");
    writeFileSync(path, readFileSync(path, "utf8").replace("## State machine", "## State flow"));
  });
  expectFailureIds(validateSkill(missingModuleStateMachine), ["MODULE_CONTRACT_INCOMPLETE"], "missing provider state machine");

  const lawOverride = skillMutation("law-override", (root) => {
    const path = resolve(root, "modules/grepai.md");
    writeFileSync(path, `${readFileSync(path, "utf8")}\nThis module may override the core law.\n`);
  });
  expectFailureIds(validateSkill(lawOverride), ["MODULE_LAW_OVERRIDE"], "module law override");

  const missingRoutingCase = skillMutation("missing-routing-case", (root) => {
    const path = resolve(root, "evals/fixtures/module-routing-cases.json");
    const fixture = JSON.parse(readFileSync(path, "utf8")) as { cases: JsonObject[] };
    fixture.cases = fixture.cases.filter((item) => item.id !== "MODULE-CORE-ONLY");
    writeJson(path, fixture);
  });
  expectFailureIds(validateSkill(missingRoutingCase), ["MODULE_ROUTING_CASE_INVALID"], "missing routing control");

  const unknownRoutingModule = skillMutation("unknown-routing-module", (root) => {
    const path = resolve(root, "evals/fixtures/module-routing-cases.json");
    const fixture = JSON.parse(readFileSync(path, "utf8")) as { cases: JsonObject[] };
    fixture.cases[0]!.expected_modules = ["unknown-provider"];
    writeJson(path, fixture);
  });
  expectFailureIds(validateSkill(unknownRoutingModule), ["MODULE_ROUTING_CASE_INVALID"], "unknown routing module");

  const fixtureRepo = resolve(tempRoot, "fixture-repo");
  const fixture = makeRepo(fixtureRepo);
  const outputPositive = assertOutput(fixtureRepo, fixture.report);
  expect(outputPositive.failures.length === 0, `valid report failed: ${JSON.stringify(outputPositive.failures)}`);
  positiveCount += 1;
  writeFileSync(resolve(fixtureRepo, "src/retry.ts"), "uncommitted bytes must not replace the recorded Git subject\n");
  const committedSubjectPositive = assertOutput(fixtureRepo, fixture.report);
  expect(committedSubjectPositive.failures.length === 0, `HEAD-bound report was polluted by working-tree bytes: ${JSON.stringify(committedSubjectPositive.failures)}`);
  positiveCount += 1;

  const mutateReport = (label: string, mutate: (report: JsonObject) => void, ids: string[]): void => {
    const report = clone(fixture.report);
    mutate(report);
    expectFailureIds(assertOutput(fixtureRepo, report), ids, label);
  };

  mutateReport("missing source ref", (report) => { (report.facts as JsonObject[])[0]!.source_refs = []; }, ["SOURCE_REF_MISSING"]);
  mutateReport("absolute source ref", (report) => { ((report.facts as JsonObject[])[0]!.source_refs as JsonObject[])[0]!.path = ["", "Users", "example", "retry.ts"].join("/"); }, ["SOURCE_REF_INVALID", "SENSITIVE_OR_LOCAL_VALUE"]);
  mutateReport("source traversal", (report) => { ((report.facts as JsonObject[])[0]!.source_refs as JsonObject[])[0]!.path = "../retry.ts"; }, ["SOURCE_REF_ESCAPE"]);
  mutateReport("source range", (report) => { ((report.facts as JsonObject[])[0]!.source_refs as JsonObject[])[0]!.end_line = 5; }, ["SOURCE_RANGE_INVALID"]);
  mutateReport("source digest", (report) => { ((report.facts as JsonObject[])[0]!.source_refs as JsonObject[])[0]!.blob_sha256 = "0".repeat(64); }, ["SOURCE_DIGEST_MISMATCH"]);
  mutateReport("unsupported D", (report) => { (report.facts as JsonObject[])[0]!.evidence_level = "D"; }, ["UNSUPPORTED_CLAIM"]);
  mutateReport("graph without readback", (report) => { const fact = (report.facts as JsonObject[])[0]!; fact.evidence_level = "B+"; fact.provider_lane = "code-graph-rag"; fact.verification = []; }, ["SOURCE_READBACK_MISSING"]);
  mutateReport("memory without readback", (report) => { const fact = (report.facts as JsonObject[])[0]!; fact.provider_lane = "mem0"; fact.verification = []; }, ["SOURCE_READBACK_MISSING"]);
  mutateReport("head mismatch", (report) => { (report.subject as JsonObject).observed_commit = "0".repeat(40); }, ["SUBJECT_IDENTITY_MISMATCH"]);
  mutateReport("head absent", (report) => { (report.subject as JsonObject).observed_commit = null; }, ["SUBJECT_IDENTITY_ABSENT"]);
  mutateReport("absence boundary", (report) => { (report.negative_invariants as JsonObject[])[0]!.search_boundary = []; }, ["ABSENCE_BOUNDARY_UNDECLARED"]);
  mutateReport("empty pass", (report) => { report.facts = []; report.negative_invariants = []; report.implicit_dependencies = []; }, ["EMPTY_PASS"]);

  const receiptRoot = resolve(tempRoot, "receipts");
  mkdirSync(receiptRoot);
  const validReportPath = resolve(tempRoot, "valid-report.json");
  const invalidReportPath = resolve(tempRoot, "invalid-report.json");
  writeJson(validReportPath, fixture.report);
  const invalidReport = clone(fixture.report);
  (invalidReport.facts as JsonObject[])[0]!.source_refs = [];
  writeJson(invalidReportPath, invalidReport);

  expect(runValidateCli([]) === 64, "validate CLI usage must exit 64");
  expect(runValidateCli(["--skill-root", SKILL_ROOT, "--json", resolve(receiptRoot, "skill-pass.json")]) === 0, "validate CLI positive must exit 0");
  expect(runValidateCli(["--skill-root", hostField, "--json", resolve(receiptRoot, "skill-fail.json")]) === 2, "validate CLI assertion must exit 2");
  expect(runAssertCli(["--repo", fixtureRepo, "--report", resolve(tempRoot, "absent.json"), "--receipt", resolve(receiptRoot, "absent.json")]) === 64, "assert CLI absent input must exit 64");
  expect(runAssertCli(["--repo", fixtureRepo, "--report", validReportPath, "--receipt", resolve(receiptRoot, "output-pass.json")]) === 0, "assert CLI positive must exit 0");
  expect(runAssertCli(["--repo", fixtureRepo, "--report", invalidReportPath, "--receipt", resolve(receiptRoot, "output-fail.json")]) === 2, "assert CLI assertion must exit 2");
  exitContractCount = 6;

  console.log(`SELFTEST GREEN repo-agent-native positive=${positiveCount} mutations=${mutationCount} exit-contracts=${exitContractCount}`);
} finally {
  rmSync(tempRoot, { recursive: true, force: true });
}
