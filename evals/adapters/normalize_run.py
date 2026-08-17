#!/usr/bin/env python3
"""Normalize executor-specific results into skill-eval-run/v1.

Translation never grants promotion authority. Sampling identity is explicit:
callers must provide either a controlled model seed or a repetition index; a
harness without seed control must never fabricate one.

Perturbation identity is explicit for the same reason and keeps three states
distinct, matching run-trace.schema.json: passing neither perturbation flag
omits the field (this harness invocation does not record perturbation identity
at all), `--no-perturbation` emits an explicit null (measured undisturbed
baseline), and `--perturbation-id` with `--perturbation-axis` emits the named
object. A perturbation-blind run must never be readable as proven baseline.

Run identity names the world a run happened in, so an applied perturbation
joins the identity string -- without it two runs differing only by which
perturbation was applied would collide onto one run_id. The component is
appended only when a perturbation object is emitted, which keeps every
undisturbed run_id byte-identical to what earlier revisions of this adapter
produced (evals/fixtures/run-identity/baseline-absent.json pins that). The
cost of that stability is that the absent and explicit-null states share a
run_id: they describe the same world and differ only in recording fidelity,
which the trace field, not the id, is responsible for keeping distinct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Both mirror run-trace.schema.json; a value this adapter emits that the schema
# would reject is a trace nothing downstream can read.
PERTURBATION_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
PERTURBATION_AXES = ["context", "tool", "state", "task"]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def int_nonnegative(value, default=0):
    if value is None:
        return default
    value = int(value)
    if value < 0:
        raise ValueError("metrics cannot be negative")
    return value


def normalize_generic(raw: dict) -> dict:
    return {
        "passed": bool(raw.get("passed", False)),
        "verifier": str(raw.get("verifier", "generic")),
        "failure_class": raw.get("failure_class"),
        "selected_skill": raw.get("selected_skill"),
        "did_invoke": bool(raw.get("did_invoke", False)),
        "wall_seconds": float(raw.get("wall_seconds", 0)),
        "tool_calls": int_nonnegative(raw.get("tool_calls")),
        "input_tokens": int_nonnegative(raw.get("input_tokens")),
        "output_tokens": int_nonnegative(raw.get("output_tokens")),
        "retries": int_nonnegative(raw.get("retries")),
        "artifacts": list(raw.get("artifacts", [])),
    }


def normalize_skill_up(raw: dict) -> dict:
    result = raw.get("result", raw)
    if not isinstance(result, dict):
        raise ValueError("skill-up result must be an object")
    status = str(result.get("status", "")).lower()
    passed = bool(result.get("passed", status in {"pass", "passed", "success"}))
    metrics = result.get("metrics", {}) if isinstance(result.get("metrics", {}), dict) else {}
    timing = result.get("timing", {}) if isinstance(result.get("timing", {}), dict) else {}
    return {
        "passed": passed,
        "verifier": str(result.get("judge_type", "skill-up")),
        "failure_class": result.get("failure_class"),
        "selected_skill": result.get("selected_skill"),
        "did_invoke": bool(result.get("did_invoke", result.get("selected_skill"))),
        "wall_seconds": float(timing.get("total_duration_seconds", metrics.get("wall_seconds", 0)) or 0),
        "tool_calls": int_nonnegative(metrics.get("total_tool_calls")),
        "input_tokens": int_nonnegative(metrics.get("input_tokens", metrics.get("prompt_tokens", 0))),
        "output_tokens": int_nonnegative(metrics.get("output_tokens", metrics.get("completion_tokens", 0))),
        "retries": int_nonnegative(result.get("retries")),
        "artifacts": list(result.get("artifacts", [])) if isinstance(result.get("artifacts", []), list) else [],
    }


def sampling_from_args(args) -> dict:
    if args.seed is not None and args.repetition is not None:
        raise ValueError("provide exactly one of --seed or --repetition")
    if args.seed is None and args.repetition is None:
        raise ValueError("provide exactly one of --seed or --repetition")
    if args.seed is not None:
        if args.seed < 0:
            raise ValueError("seed must be >= 0")
        return {"kind": "controlled_seed", "index": 1, "seed": args.seed}
    if args.repetition < 1:
        raise ValueError("repetition must be >= 1")
    return {"kind": "repetition", "index": args.repetition, "seed": None}


def perturbation_from_args(args) -> tuple[bool, dict | None]:
    """Return (recorded, value) so absent stays distinguishable from null."""
    named = args.perturbation_id is not None or args.perturbation_axis is not None
    if args.no_perturbation and named:
        raise ValueError("--no-perturbation cannot be combined with --perturbation-id/--perturbation-axis")
    if args.no_perturbation:
        return True, None
    if not named:
        return False, None
    if args.perturbation_id is None or args.perturbation_axis is None:
        raise ValueError("--perturbation-id and --perturbation-axis must be provided together")
    if not PERTURBATION_ID.fullmatch(args.perturbation_id):
        raise ValueError(f"perturbation id is not a declarable case id: {args.perturbation_id!r}")
    return True, {"id": args.perturbation_id, "axis": args.perturbation_axis}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=["generic", "skill-up"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--condition", required=True, choices=["no_skill", "current_skill", "candidate_skill", "wrong_skill", "composed_skills"])
    parser.add_argument("--skill-sha", default="")
    parser.add_argument("--eval-suite-sha", required=True)
    parser.add_argument("--model-provider", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--harness-name", required=True)
    parser.add_argument("--harness-version", required=True)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--network-policy", required=True)
    parser.add_argument("--fresh-workspace", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--repetition", type=int)
    parser.add_argument("--should-invoke", action="store_true")
    parser.add_argument("--perturbation-id")
    parser.add_argument("--perturbation-axis", choices=PERTURBATION_AXES)
    parser.add_argument(
        "--no-perturbation",
        action="store_true",
        help="record an explicit undisturbed baseline instead of omitting perturbation identity",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        raw = load(Path(args.input))
        normalized = normalize_generic(raw) if args.adapter == "generic" else normalize_skill_up(raw)
        if args.condition != "no_skill" and not args.skill_sha:
            raise ValueError("skill_sha is required except for no_skill runs")
        sampling = sampling_from_args(args)
        records_perturbation, perturbation = perturbation_from_args(args)
        sampling_identity = f"{sampling['kind']}:{sampling['seed'] if sampling['kind'] == 'controlled_seed' else sampling['index']}"
        identity = "|".join([
            args.case_id, args.condition, args.skill_sha or "none", args.model_provider,
            args.model_name, args.harness_name, args.harness_version, args.runtime, sampling_identity,
        ])
        if perturbation is not None:
            identity = f"{identity}|perturbation:{perturbation['id']}"
        run_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
        trace = {
            "schema_version": "skill-eval-run/v1",
            "run_id": run_id,
            "case_id": args.case_id,
            "condition": args.condition,
            "skill_sha": args.skill_sha or None,
            "model": {"provider": args.model_provider, "name": args.model_name},
            "harness": {"name": args.harness_name, "version": args.harness_version},
            "environment": {
                "runtime": args.runtime,
                "fresh_workspace": args.fresh_workspace,
                "network_policy": args.network_policy,
            },
            "sampling": sampling,
            "outcome": {
                "passed": normalized["passed"],
                "verifier": normalized["verifier"],
                "failure_class": normalized["failure_class"],
            },
            "routing": {
                "should_invoke": args.should_invoke,
                "did_invoke": normalized["did_invoke"],
                "selected_skill": normalized["selected_skill"],
            },
            "metrics": {
                "wall_seconds": normalized["wall_seconds"],
                "tool_calls": normalized["tool_calls"],
                "input_tokens": normalized["input_tokens"],
                "output_tokens": normalized["output_tokens"],
                "retries": normalized["retries"],
            },
            "artifacts": normalized["artifacts"],
        }
        if records_perturbation:
            trace["perturbation"] = perturbation
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
