#!/usr/bin/env bun
import { createHash } from "node:crypto";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { scoreOutput } from "./score-ab-output.ts";

type JsonObject = Record<string, unknown>;
type Carrier = "codex" | "claude";
type Condition = "no_skill" | "current_skill" | "candidate_skill" | "wrong_skill";

const SCRIPT_ROOT = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(SCRIPT_ROOT, "..");
const REPO_ROOT = resolve(SKILL_ROOT, "../..");
const BASELINE_COMMIT = "d277e56870c0cc18455c9dd5e572a43ca08b444b";
const MAX_REPETITIONS = 3;
const MAX_CARRIER_OUTPUT_BYTES = 4 * 1024 * 1024;
const CARRIER_TIMEOUT_MS = 5 * 60 * 1000;

class UsageError extends Error {}

type Options = {
  carrier: Carrier;
  condition: Condition;
  caseId: string;
  output: string;
  repetitions: number;
  execute: boolean;
};

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

function sha256(data: string | Buffer): string {
  return createHash("sha256").update(data).digest("hex");
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function git(repo: string, args: string[], env?: Record<string, string>): string {
  const result = Bun.spawnSync(["git", "-C", repo, ...args], {
    stdout: "pipe",
    stderr: "pipe",
    timeout: 15_000,
    env: env ? { ...process.env, ...env } : undefined,
  });
  if (result.exitCode !== 0) throw new UsageError(`git ${args.join(" ")} failed: ${result.stderr.toString().trim()}`);
  return result.stdout.toString().trim();
}

function copyGitTree(commit: string, prefix: string, destination: string): void {
  const files = git(REPO_ROOT, ["ls-tree", "-r", "--name-only", commit, "--", prefix]).split("\n").filter(Boolean);
  if (!files.length) throw new UsageError(`baseline tree absent: ${commit}:${prefix}`);
  for (const sourcePath of files) {
    const target = resolve(destination, relative(prefix, sourcePath));
    mkdirSync(dirname(target), { recursive: true });
    const result = Bun.spawnSync(["git", "-C", REPO_ROOT, "show", `${commit}:${sourcePath}`], { stdout: "pipe", stderr: "pipe", timeout: 15_000 });
    if (result.exitCode !== 0) throw new UsageError(`baseline file unreadable: ${commit}:${sourcePath}`);
    writeFileSync(target, result.stdout);
  }
}

function packageDigest(root: string): string {
  const entries: string[] = [];
  const pending = [root];
  while (pending.length) {
    const directory = pending.pop()!;
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) pending.push(path);
      else if (entry.isFile()) entries.push(path);
    }
  }
  const digest = createHash("sha256");
  for (const path of entries.sort()) {
    digest.update(relative(root, path));
    digest.update("\0");
    digest.update(readFileSync(path));
    digest.update("\0");
  }
  return digest.digest("hex");
}

export function instructionDigest(root: string): string {
  const paths = [resolve(root, "SKILL.md")];
  for (const optionalPath of ["agents/openai.yaml", "evals/fixtures/invariant-report.schema.json"]) {
    const path = resolve(root, optionalPath);
    if (existsSync(path)) paths.push(path);
  }
  for (const directoryName of ["references", "modules"]) {
    const directory = resolve(root, directoryName);
    if (!existsSync(directory)) continue;
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (entry.isFile() && entry.name.endsWith(".md")) paths.push(resolve(directory, entry.name));
    }
  }
  const digest = createHash("sha256");
  for (const path of paths.sort()) {
    digest.update(relative(root, path));
    digest.update("\0");
    digest.update(readFileSync(path));
    digest.update("\0");
  }
  return digest.digest("hex");
}

function installCondition(fixture: string, condition: Condition): { name: string | null; digest: string | null; instruction_digest: string | null; entrypoint_bytes: number | null; source: string } {
  if (condition === "no_skill") return { name: null, digest: null, instruction_digest: null, entrypoint_bytes: null, source: "none" };
  const agentsRoot = resolve(fixture, ".agents/skills");
  mkdirSync(agentsRoot, { recursive: true });
  let name: string;
  let target: string;
  let source: string;
  if (condition === "wrong_skill") {
    name = "knowledge-continuity";
    target = resolve(agentsRoot, name);
    cpSync(resolve(REPO_ROOT, "skills", name), target, { recursive: true });
    source = "current-tree:skills/knowledge-continuity";
  } else {
    name = "repo-agent-native";
    target = resolve(agentsRoot, name);
    if (condition === "current_skill") {
      copyGitTree(BASELINE_COMMIT, "skills/repo-agent-native", target);
      source = `${BASELINE_COMMIT}:skills/repo-agent-native`;
    } else {
      cpSync(SKILL_ROOT, target, { recursive: true });
      source = "candidate-worktree:skills/repo-agent-native";
    }
  }
  const claudeSkills = resolve(fixture, ".claude/skills");
  mkdirSync(claudeSkills, { recursive: true });
  symlinkSync(resolve("../../.agents/skills", name), resolve(claudeSkills, name));
  return {
    name,
    digest: packageDigest(target),
    instruction_digest: instructionDigest(target),
    entrypoint_bytes: readFileSync(resolve(target, "SKILL.md")).byteLength,
    source,
  };
}

export function fixtureRepo(root: string): string {
  const source = resolve(SKILL_ROOT, "evals/fixtures/retry-service");
  cpSync(source, root, { recursive: true });
  git(root, ["init", "-q"]);
  git(root, ["add", "src"]);
  git(
    root,
    ["-c", "user.name=AB Runner", "-c", "user.email=ab@example.invalid", "commit", "-qm", "fixture subject"],
    {
      GIT_AUTHOR_DATE: "2000-01-01T00:00:00Z",
      GIT_COMMITTER_DATE: "2000-01-01T00:00:00Z",
    },
  );
  return git(root, ["rev-parse", "HEAD"]);
}

function findScenario(caseId: string): JsonObject {
  const scenarios = object(readJson(resolve(SKILL_ROOT, "evals/fixtures/scenarios.json"), "scenarios"), "scenarios");
  if (!Array.isArray(scenarios.scenarios)) throw new UsageError("scenario inventory has no cases");
  const found = scenarios.scenarios.find((item) => typeof item === "object" && item !== null && !Array.isArray(item) && (item as JsonObject).id === caseId);
  if (!found) throw new UsageError(`unknown scenario: ${caseId}`);
  return found as JsonObject;
}

function promptFor(carrier: Carrier, condition: Condition, scenario: JsonObject, head: string): string {
  const invocation = condition === "current_skill" || condition === "candidate_skill"
    ? carrier === "codex" ? "Use $repo-agent-native. " : "Use /repo-agent-native. "
    : condition === "wrong_skill"
      ? carrier === "codex" ? "Use $knowledge-continuity. " : "Use /knowledge-continuity. "
      : "";
  return `${invocation}Analyze only the current repository fixture. ${String(scenario.prompt)}\n\n` +
    `The exact Git subject is ${head}. Read current source under src/. Do not edit files, use network access, or invoke optional providers. ` +
    "Return only the requested repo-agent-native/invariant-report/v2 JSON. Use repository='eval/retry-service', observed_commit exactly as given, observed_tree=null, scope=['src'], and task equal to the scenario id. " +
    "Every facts/negative_invariants/implicit_dependencies record must contain id, claim, evidence_level, repository-relative source_refs with exact 1-based line ranges, and verification including source-read. " +
    "Every negative invariant must also contain non-empty search_boundary and counterexample_sought. Keep routes, tools, open_questions, and named_exclusions as arrays. Use state PASS only when at least one source-anchored record is present.";
}

function claudeSchema(path: string): string {
  const schema = object(readJson(path, "output schema"), "output schema");
  delete schema.$schema;
  return JSON.stringify(schema);
}

function carrierVersion(carrier: Carrier): string {
  const result = Bun.spawnSync([carrier, "--version"], { stdout: "pipe", stderr: "pipe", timeout: 10_000 });
  if (result.exitCode !== 0) throw new UsageError(`${carrier} executable unavailable`);
  return result.stdout.toString().trim();
}

async function spawnCarrier(argv: string[], cwd: string): Promise<{ exit: number | null; timedOut: boolean; stdout: Buffer; stderr: Buffer; durationMs: number }> {
  const started = performance.now();
  const process = Bun.spawn(argv, { cwd, stdin: "ignore", stdout: "pipe", stderr: "pipe" });
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    process.kill();
  }, CARRIER_TIMEOUT_MS);
  const [exit, stdout, stderr] = await Promise.all([
    process.exited,
    new Response(process.stdout).arrayBuffer().then((value) => Buffer.from(value)),
    new Response(process.stderr).arrayBuffer().then((value) => Buffer.from(value)),
  ]);
  clearTimeout(timer);
  if (stdout.length > MAX_CARRIER_OUTPUT_BYTES || stderr.length > MAX_CARRIER_OUTPUT_BYTES) {
    throw new UsageError(`carrier output exceeds ${MAX_CARRIER_OUTPUT_BYTES} bytes`);
  }
  return { exit, timedOut, stdout, stderr, durationMs: Math.round(performance.now() - started) };
}

function extractClaudeReport(stdout: Buffer): unknown {
  const wrapper = object(JSON.parse(stdout.toString("utf8")), "Claude output");
  if (wrapper.structured_output !== undefined) return wrapper.structured_output;
  if (typeof wrapper.result === "string") return JSON.parse(wrapper.result);
  throw new UsageError("Claude output has no structured_output/result JSON");
}

function operational(carrier: Carrier, stdout: Buffer): JsonObject {
  if (carrier === "claude") {
    try {
      const wrapper = object(JSON.parse(stdout.toString("utf8")), "Claude output");
      return {
        duration_ms: wrapper.duration_ms ?? null,
        duration_api_ms: wrapper.duration_api_ms ?? null,
        num_turns: wrapper.num_turns ?? null,
        total_cost_usd: wrapper.total_cost_usd ?? null,
        usage: wrapper.usage ?? null,
      };
    } catch {
      return {};
    }
  }
  let usage: unknown = null;
  for (const line of stdout.toString("utf8").split("\n")) {
    try {
      const event = object(JSON.parse(line), "Codex event");
      if (event.type === "turn.completed" && typeof event.usage === "object") usage = event.usage;
    } catch {
      continue;
    }
  }
  return { usage };
}

async function runOne(options: Options, repetition: number, scenario: JsonObject, outputRoot: string, version: string): Promise<JsonObject> {
  const temp = mkdtempSync(resolve(tmpdir(), "repo-agent-native-ab-"));
  const runId = `${options.carrier}-${options.condition}-${options.caseId}-r${repetition}`;
  const runRoot = resolve(outputRoot, runId);
  if (existsSync(runRoot)) throw new UsageError(`run receipt already exists; choose a fresh output directory: ${runRoot}`);
  mkdirSync(runRoot, { recursive: true });
  try {
    const fixture = resolve(temp, "repo");
    mkdirSync(fixture);
    const fixtureCommit = fixtureRepo(fixture);
    const subjectBundle = resolve(runRoot, "subject.bundle");
    const bundleResult = Bun.spawnSync(["git", "-C", fixture, "bundle", "create", subjectBundle, "HEAD"], {
      stdout: "pipe",
      stderr: "pipe",
      timeout: 15_000,
    });
    if (bundleResult.exitCode !== 0) throw new UsageError(`subject bundle failed: ${bundleResult.stderr.toString().trim()}`);
    const skill = installCondition(fixture, options.condition);
    const prompt = promptFor(options.carrier, options.condition, scenario, fixtureCommit);
    const schemaPath = resolve(SKILL_ROOT, "evals/fixtures/invariant-report.schema.json");
    const expectedPath = resolve(SKILL_ROOT, "evals/fixtures/retry-service/expected.json");
    const evalsPath = resolve(SKILL_ROOT, "evals/evals.json");
    const reportPath = resolve(runRoot, "report.json");
    let argv: string[];
    if (options.carrier === "codex") {
      argv = [
        "codex", "exec", "--ignore-user-config", "--ephemeral", "--sandbox", "read-only", "--color", "never",
        "--json", "--output-schema", schemaPath, "--output-last-message", reportPath, "-C", fixture, prompt,
      ];
    } else {
      argv = [
        "claude", "-p", "--no-session-persistence", "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--permission-mode", "dontAsk", "--tools", "Read,Grep,Glob,Bash", "--allowedTools", "Read,Grep,Glob,Bash(git rev-parse *)",
        "--max-budget-usd", "1.00", "--output-format", "json", "--json-schema", claudeSchema(schemaPath), prompt,
      ];
      if (options.condition === "no_skill") argv.splice(2, 0, "--safe-mode");
    }
    const result = await spawnCarrier(argv, fixture);
    writeFileSync(resolve(runRoot, "carrier.stdout"), result.stdout);
    writeFileSync(resolve(runRoot, "carrier.stderr"), result.stderr);
    let reportValue: unknown = null;
    let parseError: string | null = null;
    try {
      reportValue = options.carrier === "codex" ? readJson(reportPath, "Codex report") : extractClaudeReport(result.stdout);
      writeJson(reportPath, reportValue);
    } catch (error) {
      parseError = error instanceof Error ? error.message : "unparseable report";
    }
    let score: JsonObject | null = null;
    if (reportValue !== null) {
      const evals = object(readJson(evalsPath, "evals"), "evals");
      score = scoreOutput(
        fixture,
        reportValue,
        readJson(expectedPath, "ground truth"),
        evals.metrics,
      );
      writeJson(resolve(runRoot, "score.json"), score);
    }
    const receipt = {
      schema: "repo-agent-native/ab-run-receipt/v1",
      run_id: runId,
      carrier: { id: options.carrier, version },
      condition: options.condition,
      carrier_isolation: {
        settings_sources: options.carrier === "claude" ? ["project"] : [],
        strict_empty_mcp: options.carrier === "claude",
        no_skill_safe_mode: options.carrier === "claude" && options.condition === "no_skill",
        user_level_skill_discovery_proven_absent: options.carrier === "claude" && options.condition === "no_skill",
      },
      scenario: options.caseId,
      repetition,
      fixture_commit: fixtureCommit,
      subject_bundle: {
        path: "subject.bundle",
        sha256: sha256(readFileSync(subjectBundle)),
      },
      skill,
      evaluator: {
        schema_sha256: sha256(readFileSync(schemaPath)),
        ground_truth_sha256: sha256(readFileSync(expectedPath)),
        eval_config_sha256: sha256(readFileSync(evalsPath)),
        scorer_sha256: sha256(readFileSync(resolve(SCRIPT_ROOT, "score-ab-output.ts"))),
      },
      execution: {
        exit: result.exit,
        timed_out: result.timedOut,
        duration_ms: result.durationMs,
        stdout_sha256: sha256(result.stdout),
        stderr_sha256: sha256(result.stderr),
        parse_error: parseError,
      },
      operational: operational(options.carrier, result.stdout),
      score: score ? { hard_gate: score.hard_gate, weighted_quality: score.weighted_quality } : null,
      state: result.exit === 0 && !result.timedOut && parseError === null && score?.hard_gate === "PASS" ? "PASS" : "FAIL",
    };
    writeJson(resolve(runRoot, "receipt.json"), receipt);
    return receipt;
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

function parseArgs(args: string[]): Options {
  const options: Partial<Options> = { repetitions: 1, execute: false };
  for (let index = 0; index < args.length; index += 1) {
    const key = args[index];
    if (key === "--execute") {
      options.execute = true;
      continue;
    }
    const value = args[++index];
    if (!value) throw new UsageError(`missing value for ${key}`);
    if (key === "--carrier" && (value === "codex" || value === "claude")) options.carrier = value;
    else if (key === "--condition" && ["no_skill", "current_skill", "candidate_skill", "wrong_skill"].includes(value)) options.condition = value as Condition;
    else if (key === "--case") options.caseId = value;
    else if (key === "--output") options.output = value;
    else if (key === "--repetitions") options.repetitions = Number(value);
    else throw new UsageError(`unknown or invalid argument: ${key} ${value}`);
  }
  if (!options.carrier || !options.condition || !options.caseId || !options.output) {
    throw new UsageError("usage: run-ab.ts --carrier <codex|claude> --condition <condition> --case <id> --output <dir> [--repetitions 1-3] [--execute]");
  }
  if (!Number.isInteger(options.repetitions) || options.repetitions! < 1 || options.repetitions! > MAX_REPETITIONS) {
    throw new UsageError(`repetitions must be 1-${MAX_REPETITIONS}`);
  }
  return options as Options;
}

export async function runAbCli(args: string[]): Promise<number> {
  try {
    const options = parseArgs(args);
    const scenario = findScenario(options.caseId);
    const outputRoot = resolve(options.output);
    mkdirSync(outputRoot, { recursive: true });
    const version = carrierVersion(options.carrier);
    if (!options.execute) {
      writeJson(resolve(outputRoot, "dry-run.json"), {
        schema: "repo-agent-native/ab-dry-run/v1",
        state: "NOT_EXERCISED",
        carrier: { id: options.carrier, version },
        condition: options.condition,
        scenario: options.caseId,
        repetitions: options.repetitions,
        note: "Pass --execute to authorize physical carrier calls.",
      });
      console.log("NOT_EXERCISED: dry-run only; pass --execute for physical carrier calls");
      return 0;
    }
    const receipts: JsonObject[] = [];
    for (let repetition = 1; repetition <= options.repetitions; repetition += 1) {
      receipts.push(await runOne(options, repetition, scenario, outputRoot, version));
    }
    const pass = receipts.every((receipt) => receipt.state === "PASS");
    writeJson(resolve(outputRoot, "summary.json"), {
      schema: "repo-agent-native/ab-run-summary/v1",
      carrier: { id: options.carrier, version },
      condition: options.condition,
      scenario: options.caseId,
      repetitions: options.repetitions,
      pass_count: receipts.filter((receipt) => receipt.state === "PASS").length,
      state: pass ? "PASS" : "FAIL",
      runs: receipts.map((receipt) => ({ run_id: receipt.run_id, state: receipt.state })),
    });
    return pass ? 0 : 2;
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(error.message);
      return 64;
    }
    console.error(error instanceof Error ? error.message : "internal A/B runner error");
    return 70;
  }
}

if (import.meta.main) process.exitCode = await runAbCli(Bun.argv.slice(2));
