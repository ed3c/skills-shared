#!/usr/bin/env bun
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

type JsonObject = Record<string, unknown>;
type Options = { candidate: string; current: string; noSkill: string; wrongSkill: string; evals: string; output: string };

class UsageError extends Error {}

function object(value: unknown, label: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new UsageError(`${label} must be an object`);
  return value as JsonObject;
}

function readJson(path: string, label: string): JsonObject {
  if (!existsSync(path)) throw new UsageError(`${label} absent: ${path}`);
  try {
    return object(JSON.parse(readFileSync(path, "utf8")), label);
  } catch (error) {
    if (error instanceof UsageError) throw error;
    throw new UsageError(`${label} invalid JSON: ${error instanceof Error ? error.message : path}`);
  }
}

function numberAt(root: JsonObject, path: string[], label: string): number {
  let value: unknown = root;
  for (const key of path) value = object(value, label)[key];
  if (typeof value !== "number" || !Number.isFinite(value)) throw new UsageError(`${label} must be a finite number`);
  return value;
}

function stringAt(root: JsonObject, path: string[], label: string): string {
  let value: unknown = root;
  for (const key of path) value = object(value, label)[key];
  if (typeof value !== "string" || !value) throw new UsageError(`${label} must be a non-empty string`);
  return value;
}

function optionalScore(receipt: JsonObject): { hard_gate: string; procedure_hard_gate: string; admission_quality: number } | null {
  if (typeof receipt.score !== "object" || receipt.score === null || Array.isArray(receipt.score)) return null;
  const score = receipt.score as JsonObject;
  if (typeof score.hard_gate !== "string" || typeof score.procedure_hard_gate !== "string"
    || typeof score.admission_quality !== "number" || !Number.isFinite(score.admission_quality)) return null;
  return { hard_gate: score.hard_gate, procedure_hard_gate: score.procedure_hard_gate, admission_quality: score.admission_quality };
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (typeof value === "object" && value !== null) {
    return `{${Object.entries(value as JsonObject).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => `${JSON.stringify(key)}:${stable(item)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function parseArgs(args: string[]): Options {
  const options: Partial<Options> = {};
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    const value = args[index + 1];
    if (!value) throw new UsageError(`missing value for ${key}`);
    if (key === "--candidate") options.candidate = value;
    else if (key === "--current") options.current = value;
    else if (key === "--no-skill") options.noSkill = value;
    else if (key === "--wrong-skill") options.wrongSkill = value;
    else if (key === "--evals") options.evals = value;
    else if (key === "--output") options.output = value;
    else throw new UsageError(`unknown argument: ${key}`);
  }
  if (!options.candidate || !options.current || !options.noSkill || !options.wrongSkill || !options.evals || !options.output) {
    throw new UsageError("usage: compare-ab.ts --candidate <receipt> --current <receipt> --no-skill <receipt> --wrong-skill <receipt> --evals <evals.json> --output <comparison.json>");
  }
  return options as Options;
}

export function compareAb(receipts: Record<string, JsonObject>, evals: JsonObject): JsonObject {
  const failures: string[] = [];
  const named = ["candidate", "current", "no_skill", "wrong_skill"] as const;
  for (const name of named) {
    const receipt = receipts[name];
    const score = optionalScore(receipt);
    if (receipt.state !== "PASS") failures.push(`${name}: receipt state is not PASS`);
    if (!score) failures.push(`${name}: evaluable score is absent`);
    else if (score.hard_gate !== "PASS") failures.push(`${name}: hard gate is not PASS`);
    else if (score.procedure_hard_gate !== "PASS") failures.push(`${name}: procedure hard gate is not PASS`);
  }
  const candidate = receipts.candidate;
  const current = receipts.current;
  for (const name of ["current", "no_skill", "wrong_skill"] as const) {
    const other = receipts[name];
    for (const field of ["fixture_commit", "scenario"] as const) {
      if (candidate[field] !== other[field]) failures.push(`${name}: ${field} differs from candidate`);
    }
    if (stable(candidate.carrier) !== stable(other.carrier)) failures.push(`${name}: carrier identity differs from candidate`);
    if (stable(candidate.evaluator) !== stable(other.evaluator)) failures.push(`${name}: evaluator digest set differs from candidate`);
    if (stable(candidate.subject_bundle) !== stable(other.subject_bundle)) failures.push(`${name}: subject bundle differs from candidate`);
  }
  const candidateQuality = optionalScore(candidate)?.admission_quality ?? null;
  const currentQuality = optionalScore(current)?.admission_quality ?? null;
  const admission = object(evals.admission, "evals.admission");
  const qualityMinimum = Number(admission.admission_quality_delta_min);
  const controlMinimum = Number(admission.control_quality_delta_min);
  const contextMaximum = Number(admission.median_instruction_context_cost_delta_max);
  const candidateBytes = numberAt(candidate, ["skill", "entrypoint_bytes"], "candidate entrypoint bytes");
  const currentBytes = numberAt(current, ["skill", "entrypoint_bytes"], "current entrypoint bytes");
  const qualityDelta = candidateQuality === null || currentQuality === null ? null : candidateQuality - currentQuality;
  const contextDelta = candidateBytes / currentBytes - 1;
  if (qualityDelta !== null && qualityDelta < qualityMinimum) failures.push(`quality delta ${qualityDelta.toFixed(6)} is below ${qualityMinimum}`);
  for (const name of ["no_skill", "wrong_skill"] as const) {
    const controlQuality = optionalScore(receipts[name])?.admission_quality ?? null;
    if (candidateQuality !== null && controlQuality !== null && candidateQuality - controlQuality < controlMinimum) {
      failures.push(`candidate minus ${name} quality ${(candidateQuality - controlQuality).toFixed(6)} is below ${controlMinimum}`);
    }
  }
  if (contextDelta > contextMaximum) failures.push(`entrypoint context delta ${contextDelta.toFixed(6)} exceeds ${contextMaximum}`);
  if (stringAt(candidate, ["skill", "instruction_digest"], "candidate instruction digest") === stringAt(current, ["skill", "instruction_digest"], "current instruction digest")) {
    failures.push("candidate and current instruction digests are identical");
  }
  if (object(receipts.no_skill.skill, "no_skill.skill").name !== null) failures.push("no_skill condition installed a named Skill");
  if (object(receipts.wrong_skill.skill, "wrong_skill.skill").name === object(candidate.skill, "candidate.skill").name) failures.push("wrong_skill condition installed candidate Skill");
  return {
    schema: "repo-agent-native/ab-comparison/v1",
    state: failures.length ? "FAIL" : "PASS",
    failures,
    subject: { fixture_commit: candidate.fixture_commit, subject_bundle: candidate.subject_bundle },
    carrier: candidate.carrier,
    evaluator: candidate.evaluator,
    quality: {
      candidate: candidateQuality,
      current: currentQuality,
      no_skill: optionalScore(receipts.no_skill)?.admission_quality ?? null,
      wrong_skill: optionalScore(receipts.wrong_skill)?.admission_quality ?? null,
      candidate_minus_current: qualityDelta === null ? null : Number(qualityDelta.toFixed(6)),
      control_delta_min: controlMinimum,
    },
    entrypoint_context_proxy: {
      candidate_bytes: candidateBytes,
      current_bytes: currentBytes,
      relative_delta: Number(contextDelta.toFixed(6)),
    },
    limitations: [
      "One run per condition is a stochastic sample when the carrier exposes no seed.",
      "Entrypoint bytes are a deterministic progressive-disclosure context proxy, not observed model input tokens.",
      "Structured predicates cover only the preregistered fixture claims; they are not exhaustive repository fact precision.",
      "Lexical alias matching is advisory and cannot alter admission or rescue a failed hard assertion.",
    ],
  };
}

export function runCompareCli(args: string[]): number {
  try {
    const options = parseArgs(args);
    const comparison = compareAb({
      candidate: readJson(options.candidate, "candidate receipt"),
      current: readJson(options.current, "current receipt"),
      no_skill: readJson(options.noSkill, "no-skill receipt"),
      wrong_skill: readJson(options.wrongSkill, "wrong-skill receipt"),
    }, readJson(options.evals, "evals"));
    const parent = dirname(resolve(options.output));
    if (!existsSync(parent)) throw new UsageError(`output parent absent: ${parent}`);
    writeFileSync(options.output, `${JSON.stringify(comparison, null, 2)}\n`);
    return comparison.state === "PASS" ? 0 : 2;
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(error.message);
      return 64;
    }
    console.error(error instanceof Error ? error.message : "internal comparison error");
    return 70;
  }
}

if (import.meta.main) process.exitCode = runCompareCli(Bun.argv.slice(2));
