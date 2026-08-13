#!/usr/bin/env bun
import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, readdirSync, realpathSync, writeFileSync } from "node:fs";
import { basename, dirname, isAbsolute, relative, resolve } from "node:path";

export type Failure = { id: string; detail: string };

const PORTABLE_FIELDS = new Set([
  "name",
  "description",
  "license",
  "compatibility",
  "metadata",
  "allowed-tools",
]);
const HOST_ONLY_FIELDS = new Set([
  "argument-hint",
  "context",
  "agent",
  "model",
  "disable-model-invocation",
  "user-invocable",
]);
const REQUIRED_HEADINGS = [
  "Trigger",
  "Non-trigger",
  "Inputs",
  "Outputs",
  "Core laws",
  "State machine",
  "S0 — Scope",
  "S1 — Route",
  "S2 — Discover",
  "S3 — Retrieve",
  "S4 — Verify",
  "S5 — Infer",
  "S6 — Write",
  "S7 — Assert",
  "S8 — Handoff",
  "Module law",
];
const REQUIRED_MODULE_SECTIONS = [
  "Trigger",
  "Non-trigger",
  "Purpose",
  "Assumptions",
  "State machine",
  "Inputs",
  "Outputs and effects",
  "Evidence class and freshness",
  "Fallback",
  "Core laws that remain authoritative",
  "Consumer-owned values",
];
const REQUIRED_TOOL_MODULES = ["grepai.md", "serena.md", "code-graph-rag.md", "mem0.md"];
const REQUIRED_ROUTING_CASES = new Set([
  "MODULE-GREPAI-TRIGGER",
  "MODULE-SERENA-TRIGGER",
  "MODULE-GRAPH-TRIGGER",
  "MODULE-MEM0-TRIGGER",
  "MODULE-CORE-ONLY",
  "MODULE-GREPAI-STALE",
  "MODULE-SERENA-WRONG-PROJECT",
  "MODULE-GRAPH-INCOMPLETE",
  "MODULE-MEMORY-CONFLICT",
  "MODULE-AMBIGUOUS-PRIMARY",
  "MODULE-LAW-OVERRIDE",
]);
const ROUTABLE_MODULES = new Set(["grepai", "serena", "code-graph-rag", "mem0"]);

class UsageError extends Error {}

function sha256(data: string | Buffer): string {
  return createHash("sha256").update(data).digest("hex");
}

function fail(failures: Failure[], id: string, detail: string): void {
  failures.push({ id, detail });
}

function parseFrontmatter(text: string): { fields: Map<string, string>; bodyStart: number } {
  const lines = text.split(/\r?\n/);
  if (lines[0] !== "---") throw new UsageError("SKILL.md must begin with ---");
  const close = lines.indexOf("---", 1);
  if (close < 0) throw new UsageError("SKILL.md frontmatter has no closing ---");
  const fields = new Map<string, string>();
  let index = 1;
  while (index < close) {
    const line = lines[index] ?? "";
    if (!line.trim() || line.trimStart().startsWith("#")) {
      index += 1;
      continue;
    }
    if (/^\s/.test(line)) throw new UsageError(`unexpected indentation at frontmatter line ${index + 1}`);
    const match = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (!match?.[1]) throw new UsageError(`invalid frontmatter line ${index + 1}`);
    const key = match[1];
    if (fields.has(key)) throw new UsageError(`duplicate frontmatter field ${key}`);
    let value = match[2] ?? "";
    const nested: string[] = [];
    let next = index + 1;
    while (next < close && (/^\s/.test(lines[next] ?? "") || !(lines[next] ?? "").trim())) {
      nested.push(lines[next] ?? "");
      next += 1;
    }
    if (/^[|>][-+]?$/.test(value)) {
      const indents = nested.filter((item) => item.trim()).map((item) => item.length - item.trimStart().length);
      const indent = indents.length ? Math.min(...indents) : 0;
      value = nested.map((item) => (item.trim() ? item.slice(indent) : "")).join(value.startsWith(">") ? " " : "\n");
      index = next;
    } else if (key === "metadata" && !value) {
      for (const [nestedIndex, item] of nested.entries()) {
        if (!item.trim()) continue;
        const metadataMatch = /^\s{2,}([A-Za-z0-9_.-]+):\s*(.+)$/.exec(item);
        if (!metadataMatch?.[1] || !metadataMatch[2]?.trim()) {
          throw new UsageError(`metadata must be a string map at frontmatter line ${index + nestedIndex + 2}`);
        }
        const scalar = metadataMatch[2].trim();
        if (/^(?:true|false|null|[-+]?\d+(?:\.\d+)?|\[|\{)/i.test(scalar)) {
          throw new UsageError(`metadata values must be strings at frontmatter line ${index + nestedIndex + 2}`);
        }
      }
      value = nested.join("\n");
      index = next;
    } else {
      if (nested.some((item) => item.trim())) throw new UsageError(`${key} has unsupported nested content`);
      index = next;
    }
    fields.set(key, value.replace(/^['"]|['"]$/g, "").trim());
  }
  return { fields, bodyStart: close + 1 };
}

function inside(root: string, target: string): boolean {
  const rel = relative(root, target);
  return rel === "" || (!rel.startsWith("..") && !isAbsolute(rel));
}

function checkLinks(skillRoot: string, documentPath: string, text: string, failures: Failure[]): void {
  const linkPattern = /\[[^\]]*\]\(([^)]+)\)/g;
  for (const match of text.matchAll(linkPattern)) {
    const raw = (match[1] ?? "").split("#", 1)[0] ?? "";
    if (!raw || /^[a-z]+:/i.test(raw)) continue;
    const target = resolve(dirname(documentPath), raw);
    if (!inside(skillRoot, target)) {
      fail(failures, "BROKEN_RELATIVE_REFERENCE", `link escapes skill root: ${raw}`);
    } else if (!existsSync(target)) {
      fail(failures, "BROKEN_RELATIVE_REFERENCE", `link target absent: ${raw}`);
    }
  }
}

function activeMarkdownFiles(root: string): string[] {
  const files: string[] = [];
  const pending = [root];
  while (pending.length) {
    const directory = pending.pop()!;
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) pending.push(path);
      else if (entry.isFile() && entry.name.endsWith(".md")) files.push(path);
    }
  }
  return files.sort();
}

function checkToolModules(skillRoot: string, failures: Failure[]): void {
  for (const name of REQUIRED_TOOL_MODULES) {
    const path = resolve(skillRoot, "modules", name);
    if (!existsSync(path)) {
      fail(failures, "MODULE_CONTRACT_INCOMPLETE", `missing modules/${name}`);
      continue;
    }
    const text = readFileSync(path, "utf8");
    for (const heading of REQUIRED_MODULE_SECTIONS) {
      if (!text.includes(`## ${heading}`)) {
        fail(failures, "MODULE_CONTRACT_INCOMPLETE", `modules/${name} missing ${heading}`);
      }
    }
    if (!text.includes("Failure states:")) {
      fail(failures, "MODULE_CONTRACT_INCOMPLETE", `modules/${name} missing Failure states`);
    }
    if (/override.{0,30}(core law|source authority)/i.test(text)) {
      fail(failures, "MODULE_LAW_OVERRIDE", `modules/${name} attempts to override core law`);
    }
  }
}

function checkRoutingCases(skillRoot: string, failures: Failure[]): void {
  const path = resolve(skillRoot, "evals/fixtures/module-routing-cases.json");
  if (!existsSync(path)) {
    fail(failures, "MODULE_ROUTING_CASE_INVALID", "missing evals/fixtures/module-routing-cases.json");
    return;
  }
  let value: unknown;
  try {
    value = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    fail(failures, "MODULE_ROUTING_CASE_INVALID", `invalid JSON: ${error instanceof Error ? error.message : path}`);
    return;
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    fail(failures, "MODULE_ROUTING_CASE_INVALID", "routing fixture must be an object");
    return;
  }
  const fixture = value as Record<string, unknown>;
  if (fixture.schema !== "repo-agent-native/module-routing-cases/v1" || !Array.isArray(fixture.cases)) {
    fail(failures, "MODULE_ROUTING_CASE_INVALID", "routing fixture schema/cases are invalid");
    return;
  }
  const ids = new Set<string>();
  const positivelyRouted = new Set<string>();
  for (const [index, raw] of fixture.cases.entries()) {
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
      fail(failures, "MODULE_ROUTING_CASE_INVALID", `case[${index}] must be an object`);
      continue;
    }
    const item = raw as Record<string, unknown>;
    if (typeof item.id !== "string" || !item.id || ids.has(item.id)) {
      fail(failures, "MODULE_ROUTING_CASE_INVALID", `case[${index}] has absent or duplicate id`);
      continue;
    }
    ids.add(item.id);
    if (typeof item.prompt !== "string" || !item.prompt.trim()) {
      fail(failures, "MODULE_ROUTING_CASE_INVALID", `${item.id} has no prompt`);
    }
    if (item.expected_modules !== undefined) {
      if (!Array.isArray(item.expected_modules) || item.expected_modules.some((name) => typeof name !== "string" || !ROUTABLE_MODULES.has(name))) {
        fail(failures, "MODULE_ROUTING_CASE_INVALID", `${item.id} contains an unknown expected module`);
      } else {
        for (const name of item.expected_modules) positivelyRouted.add(name);
      }
    }
    const hasBehavior = Array.isArray(item.required_behavior) && item.required_behavior.length > 0;
    const hasFailure = typeof item.required_failure === "string" && Boolean(item.required_failure);
    if (!hasBehavior && !hasFailure) fail(failures, "MODULE_ROUTING_CASE_INVALID", `${item.id} has no observable expectation`);
  }
  for (const id of REQUIRED_ROUTING_CASES) {
    if (!ids.has(id)) fail(failures, "MODULE_ROUTING_CASE_INVALID", `required routing case absent: ${id}`);
  }
  for (const name of ROUTABLE_MODULES) {
    if (!positivelyRouted.has(name)) fail(failures, "MODULE_ROUTING_CASE_INVALID", `no positive routing case for ${name}`);
  }
}

export function validateSkill(skillRootInput: string): { failures: Failure[]; skillSha256: string } {
  const skillRoot = resolve(skillRootInput);
  if (!existsSync(skillRoot) || !lstatSync(skillRoot).isDirectory()) throw new UsageError(`skill root absent: ${skillRoot}`);
  const realRoot = realpathSync(skillRoot);
  const skillPath = resolve(realRoot, "SKILL.md");
  if (!existsSync(skillPath)) throw new UsageError(`SKILL.md absent: ${skillPath}`);
  const text = readFileSync(skillPath, "utf8");
  const failures: Failure[] = [];
  const { fields } = parseFrontmatter(text);

  for (const key of fields.keys()) {
    if (HOST_ONLY_FIELDS.has(key)) fail(failures, "NON_PORTABLE_FRONTMATTER", `host-only field: ${key}`);
    else if (!PORTABLE_FIELDS.has(key)) fail(failures, "NON_PORTABLE_FRONTMATTER", `unknown canonical field: ${key}`);
  }
  const name = fields.get("name") ?? "";
  const description = fields.get("description") ?? "";
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) || name.length > 64 || name !== basename(realRoot)) {
    fail(failures, "FRONTMATTER_NAME", "name must be 1-64 lower-kebab-case and equal the directory name");
  }
  if (!description || description.length > 1024) fail(failures, "FRONTMATTER_DESCRIPTION", "description must be 1-1024 characters");
  const compatibility = fields.get("compatibility");
  if (fields.has("compatibility") && (!compatibility || compatibility.length > 500)) {
    fail(failures, "FRONTMATTER_COMPATIBILITY", "compatibility must be 1-500 characters when present");
  }
  if (fields.has("allowed-tools") && !fields.get("allowed-tools")) {
    fail(failures, "FRONTMATTER_ALLOWED_TOOLS", "allowed-tools must be a non-empty space-separated string when present");
  }
  if (text.split(/\r?\n/).length > 220) {
    fail(failures, "SKILL_CORE_BUDGET", "portable SKILL.md core must contain at most 220 lines; route details to references, modules, scripts, or evals");
  }

  for (const heading of REQUIRED_HEADINGS) {
    if (!text.includes(`## ${heading}`)) fail(failures, "MISSING_CORE_SECTION", heading);
  }
  const portableLeaks: Array<[RegExp, string]> = [
    [/(?:\/Users\/|\/home\/|[A-Za-z]:\\)/, "machine-local absolute path"],
    [/^\s*!`/m, "Claude dynamic shell injection"],
    [/\bshell\s*:\s*true\b/i, "raw shell execution"],
    [/\b(?:api[_-]?key|password|access[_-]?token)\s*[:=]\s*["'][^"']+["']/i, "secret-shaped value"],
  ];
  for (const [pattern, label] of portableLeaks) if (pattern.test(text)) fail(failures, "NON_PORTABLE_BODY", label);
  if (/\b(?:grepai|serena|code-graph-rag|mem0)\b/i.test(text)) {
    fail(failures, "DOMAIN_INSTANCE_IN_CORE", "provider instances belong in trigger-selected modules, not the portable core");
  }

  for (const path of [
    "scripts/validate-skill.ts",
    "scripts/assert-output.ts",
    "scripts/score-ab-output.ts",
    "scripts/compare-ab.ts",
    "scripts/run-ab.ts",
    "tests/selftest.ts",
    "tests/ab-selftest.ts",
  ]) {
    if (!existsSync(resolve(realRoot, path))) fail(failures, "EXECUTABLE_ASSERTION_ABSENT", path);
  }
  for (const documentPath of activeMarkdownFiles(realRoot)) {
    checkLinks(realRoot, documentPath, readFileSync(documentPath, "utf8"), failures);
  }
  checkToolModules(realRoot, failures);
  checkRoutingCases(realRoot, failures);
  return { failures: failures.sort((a, b) => `${a.id}:${a.detail}`.localeCompare(`${b.id}:${b.detail}`)), skillSha256: sha256(text) };
}

type CliOptions = { skillRoot: string; receipt: string };

function parseArgs(args: string[]): CliOptions {
  let skillRoot: string | undefined;
  let receipt: string | undefined;
  for (let index = 0; index < args.length; index += 1) {
    const value = args[index];
    if (value === "--skill-root") skillRoot = args[++index];
    else if (value === "--json") receipt = args[++index];
    else throw new UsageError(`unknown argument: ${value}`);
  }
  if (!skillRoot || !receipt) throw new UsageError("usage: validate-skill.ts --skill-root <path> --json <receipt>");
  return { skillRoot, receipt };
}

function writeReceipt(path: string, value: unknown): void {
  const parent = dirname(resolve(path));
  if (!existsSync(parent)) throw new UsageError(`receipt parent absent: ${parent}`);
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

export function runValidateCli(args: string[]): number {
  try {
    const options = parseArgs(args);
    const result = validateSkill(options.skillRoot);
    writeReceipt(options.receipt, {
      schema: "repo-agent-native/skill-validation-receipt/v1",
      subject: { skill_root: resolve(options.skillRoot), skill_sha256: result.skillSha256 },
      state: result.failures.length ? "FAIL" : "PASS",
      failures: result.failures,
    });
    return result.failures.length ? 2 : 0;
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(error.message);
      return 64;
    }
    console.error(error instanceof Error ? error.message : "internal validation error");
    return 70;
  }
}

if (import.meta.main) process.exitCode = runValidateCli(Bun.argv.slice(2));
