#!/usr/bin/env bun
import { resolve } from "node:path";

export type PredicateScalar = string | number | boolean | null;
export type ObservedPredicate = {
  id: string;
  value: PredicateScalar;
  source: string;
  mechanism: string;
};

class PredicateEvaluationError extends Error {}

function gitShow(repo: string, path: string): string {
  const result = Bun.spawnSync(["git", "-C", resolve(repo), "show", `HEAD:${path}`], {
    stdout: "pipe",
    stderr: "pipe",
    timeout: 10_000,
  });
  if (result.exitCode !== 0) {
    throw new PredicateEvaluationError(`cannot read exact subject ${path}: ${result.stderr.toString().trim()}`);
  }
  return result.stdout.toString("utf8");
}

function requiredInteger(text: string, pattern: RegExp, label: string): number {
  const value = pattern.exec(text)?.[1];
  if (!value) throw new PredicateEvaluationError(`${label} is not statically observable`);
  return Number(value);
}

function resultContract(source: string): string {
  const declaration = /export\s+type\s+RetryResult<[^>]+>\s*=([\s\S]*?)export\s+const\s+MAX_ATTEMPTS\b/.exec(source)?.[1] ?? "";
  const success = /ok\s*:\s*true/.test(declaration) && /value\s*:/.test(declaration);
  const failure = /ok\s*:\s*false/.test(declaration) && /error\s*:\s*Error/.test(declaration);
  const attempts = (declaration.match(/attempts\s*:/g) ?? []).length >= 2;
  return success && failure && attempts ? "discriminated-success-failure-attempts" : "other";
}

function delayStrategy(source: string): string {
  const argument = /await\s+sleep\s*\(([^\n;]+)\)/.exec(source)?.[1]?.trim();
  if (!argument) return "absent";
  if (argument === "RETRY_DELAY_MS") return "fixed";
  if (/attempt/.test(argument) && (/\*\*/.test(argument) || /Math\.pow/.test(argument))) return "exponential";
  return "variable";
}

function metricsFailureMode(source: string): string {
  const region = /recordRetryFailure\([\s\S]*?\)\s*;\s*}\s*catch\s*(?:\([^)]*\))?\s*\{([\s\S]*?)\}\s*}/.exec(source)?.[1];
  if (region === undefined) return "unhandled";
  if (/\bthrow\b/.test(region)) return "propagated";
  const executable = region.replace(/\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "").trim();
  return executable ? "handled" : "swallowed";
}

function observabilitySink(source: string): string {
  const body = /export\s+async\s+function\s+recordRetryFailure\([^)]*\)\s*:\s*Promise<void>\s*\{([\s\S]*)\}\s*$/.exec(source)?.[1] ?? "";
  const withoutGuard = body
    .replace(/if\s*\([^)]*\)\s*\{[\s\S]*?throw\s+new\s+Error\([^)]*\)\s*;?[\s\S]*?\}/, "")
    .replace(/\/\/.*$/gm, "")
    .trim();
  return withoutGuard ? "present" : "none";
}

export function observeRetryPredicates(repo: string): ObservedPredicate[] {
  const retry = gitShow(repo, "src/retry-policy.ts");
  const api = gitShow(repo, "src/api-client.ts");
  const metrics = gitShow(repo, "src/metrics.ts");
  return [
    {
      id: "retry.result_contract",
      value: resultContract(retry),
      source: "src/retry-policy.ts",
      mechanism: "typed-union-static-query/v1",
    },
    {
      id: "retry.max_attempts",
      value: requiredInteger(retry, /MAX_ATTEMPTS\s*=\s*(\d+)/, "MAX_ATTEMPTS"),
      source: "src/retry-policy.ts",
      mechanism: "constant-static-query/v1",
    },
    {
      id: "retry.delay_ms",
      value: requiredInteger(retry, /RETRY_DELAY_MS\s*=\s*(\d+)/, "RETRY_DELAY_MS"),
      source: "src/retry-policy.ts",
      mechanism: "constant-static-query/v1",
    },
    {
      id: "retry.delay_strategy",
      value: delayStrategy(retry),
      source: "src/retry-policy.ts",
      mechanism: "sleep-argument-static-query/v1",
    },
    {
      id: "metrics.failure_mode",
      value: metricsFailureMode(api),
      source: "src/api-client.ts",
      mechanism: "catch-boundary-static-query/v1",
    },
    {
      id: "metrics.observability_sink",
      value: observabilitySink(metrics),
      source: "src/metrics.ts",
      mechanism: "function-effect-static-query/v1",
    },
  ];
}
