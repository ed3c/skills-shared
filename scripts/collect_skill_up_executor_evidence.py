#!/usr/bin/env python3
"""Normalize pinned skill-up report.json into non-promotable executor evidence.

This collector intentionally does NOT emit skill-eval-evidence/v1. skill-up's
agent_judge is executor evidence, not deterministic promotion authority. The
pinned skill-up CLI exposes iteration sampling but no model-seed control, so a
repetition index is recorded explicitly and model seed is never fabricated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HARNESS_SHA = "425e3f5a0c23e80f2c7933785d54c53ffe01b40c"
VALID_STATUS = {"pass", "fail", "error", "skip", "skipped"}


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_sha(value: str, name: str) -> str:
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} must be an exact lowercase 40-char commit SHA")
    return value


def select_result(results: list, case_id: str, configuration: str) -> dict:
    matches = [r for r in results if isinstance(r, dict) and r.get("case_id") == case_id and r.get("configuration") == configuration]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {configuration} result for {case_id}, got {len(matches)}")
    status = str(matches[0].get("status", "")).lower()
    if status not in VALID_STATUS:
        raise ValueError(f"unrecognized skill-up status: {status!r}")
    return matches[0]


def build_value(args, report: Path, result: dict, condition: str, skill_sha: str | None) -> dict:
    status = str(result.get("status", "")).lower()
    identity_skill = skill_sha or "none"
    run_identity = "|".join([args.case_id, condition, identity_skill, args.provider, args.model, args.engine, HARNESS_SHA, f"repetition:{args.repetition}"])
    run_id = hashlib.sha256(run_identity.encode()).hexdigest()[:24]
    return {
        "schema_version": "skill-eval-executor-evidence/v1",
        "run_id": run_id,
        "case_id": args.case_id,
        "condition": condition,
        "skill": args.skill,
        "skill_sha": skill_sha,
        "eval_suite_sha": args.eval_suite_sha,
        "sampling": {
            "repetition_index": args.repetition,
            "seed_controlled": False,
            "model_seed": None,
        },
        "model": {"provider": args.provider, "name": args.model},
        "harness": {"name": "skill-up", "version": HARNESS_SHA, "engine": args.engine},
        "outcome": {
            "passed": status == "pass",
            "status": status,
            "verifier": "skill-up/agent_judge",
            "duration_ms": int(result.get("duration_ms", 0) or 0),
            "input_tokens": int(result.get("input_tokens", 0) or 0),
            "output_tokens": int(result.get("output_tokens", 0) or 0),
        },
        "raw_report": {"path": str(report), "sha256": sha256(report)},
        "promotion": {
            "eligible": False,
            "reason": "executor agent_judge is not deterministic promotion authority",
            "required_next_receipt": "skill-eval-verifier-receipt/v1",
        },
    }


def write(path: str, value: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report-dir", required=True)
    p.add_argument("--case-id", required=True)
    p.add_argument("--condition", required=True, choices=["current_skill", "candidate_skill"])
    p.add_argument("--skill-sha", required=True)
    p.add_argument("--eval-suite-sha", required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--engine", required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--repetition", type=int, required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--baseline-output")
    args = p.parse_args()

    try:
        if args.repetition < 1:
            raise ValueError("repetition must be >= 1")
        exact_sha(args.skill_sha, "skill_sha")
        exact_sha(args.eval_suite_sha, "eval_suite_sha")
        report = Path(args.report_dir) / "report.json"
        if not report.is_file():
            raise ValueError(f"missing pinned skill-up fact source: {report}")
        raw = load(report)
        results = raw.get("case_results")
        if not isinstance(results, list):
            raise ValueError("skill-up report case_results must be an array")

        primary = select_result(results, args.case_id, "with_skill")
        primary_value = build_value(args, report, primary, args.condition, args.skill_sha)
        write(args.output, primary_value)

        if args.baseline_output:
            baseline = select_result(results, args.case_id, "without_skill")
            baseline_value = build_value(args, report, baseline, "no_skill", None)
            write(args.baseline_output, baseline_value)

        print(primary_value["run_id"])
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
