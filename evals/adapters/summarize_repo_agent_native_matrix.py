#!/usr/bin/env python3
"""Aggregate a complete repo-agent-native 4-arm, repeated, cross-harness matrix."""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

CONDITIONS = {"no_skill", "current_skill", "candidate_skill", "wrong_skill"}


def load_rows(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {number}: row must be object")
        rows.append(value)
    if not rows:
        raise ValueError("no receipts")
    return rows


def summarize(rows: list[dict]) -> dict:
    failures: list[str] = []
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    subject = None
    evaluator = None
    scenario = None
    for row in rows:
        if row.get("schema") != "repo-agent-native/ab-run-receipt/v1":
            failures.append("unsupported receipt schema")
            continue
        carrier = row.get("carrier", {}).get("id")
        condition = row.get("condition")
        if carrier not in {"codex", "claude"} or condition not in CONDITIONS:
            failures.append(f"invalid cell: {carrier}/{condition}")
            continue
        cells[(carrier, condition)].append(row)
        current_subject = (row.get("fixture_commit"), row.get("subject_bundle", {}).get("sha256"))
        current_evaluator = json.dumps(row.get("evaluator"), sort_keys=True)
        subject = current_subject if subject is None else subject
        evaluator = current_evaluator if evaluator is None else evaluator
        scenario = row.get("scenario") if scenario is None else scenario
        if current_subject != subject:
            failures.append(f"{carrier}/{condition}: subject differs")
        if current_evaluator != evaluator:
            failures.append(f"{carrier}/{condition}: evaluator differs")
        if row.get("scenario") != scenario:
            failures.append(f"{carrier}/{condition}: scenario differs")
    by_stack: dict[str, dict] = {}
    for carrier in ("codex", "claude"):
        stack: dict[str, dict] = {}
        for condition in sorted(CONDITIONS):
            items = cells.get((carrier, condition), [])
            repetitions = sorted(item.get("repetition") for item in items)
            if repetitions != [1, 2, 3]:
                failures.append(f"{carrier}/{condition}: repetitions must equal [1, 2, 3]")
            qualities, durations, passed = [], [], []
            for item in items:
                score = item.get("score")
                if not isinstance(score, dict) or not isinstance(score.get("admission_quality"), (int, float)):
                    failures.append(f"{carrier}/{condition}: score absent")
                    continue
                qualities.append(float(score["admission_quality"]))
                durations.append(float(item.get("execution", {}).get("duration_ms", 0)) / 1000)
                passed.append(item.get("state") == "PASS" and score.get("hard_gate") == "PASS")
            stack[condition] = {
                "runs": len(items),
                "pass_rate": sum(passed) / len(passed) if passed else None,
                "median_admission_quality": statistics.median(qualities) if qualities else None,
                "median_wall_seconds": statistics.median(durations) if durations else None,
            }
        candidate = stack["candidate_skill"]["median_admission_quality"]
        current = stack["current_skill"]["median_admission_quality"]
        no_skill = stack["no_skill"]["median_admission_quality"]
        wrong = stack["wrong_skill"]["median_admission_quality"]
        stack["deltas"] = {
            "candidate_minus_current": None if candidate is None or current is None else candidate - current,
            "candidate_minus_no_skill": None if candidate is None or no_skill is None else candidate - no_skill,
            "candidate_minus_wrong_skill": None if candidate is None or wrong is None else candidate - wrong,
        }
        by_stack[carrier] = stack
    candidate_rates = [by_stack[c]["candidate_skill"]["pass_rate"] for c in ("codex", "claude")]
    return {
        "schema_version": "repo-agent-native/physical-matrix/v1",
        "state": "PASS" if not failures else "FAIL",
        "failures": sorted(set(failures)),
        "matrix": {"expected_cells": 24, "observed_cells": len(rows), "conditions": sorted(CONDITIONS), "repetitions": 3, "harnesses": 2},
        "subject": {"fixture_commit": subject[0], "bundle_sha256": subject[1]} if subject else None,
        "evaluator_digest_set": json.loads(evaluator) if evaluator else None,
        "by_stack": by_stack,
        "cross_harness_candidate_pass_rate_gap": None if any(rate is None for rate in candidate_rates) else max(candidate_rates) - min(candidate_rates),
        "admission_rule": "All hard gates pass; candidate medians exceed current/no_skill/wrong_skill on both stacks. Cost is reported separately.",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_repo_agent_native_matrix.py <receipts.jsonl>", file=sys.stderr)
        return 2
    try:
        result = summarize(load_rows(Path(sys.argv[1])))
        for stack in result["by_stack"].values():
            deltas = stack["deltas"]
            if any(value is None or value < 0.01 for value in deltas.values()):
                result["failures"].append("candidate median lift below 0.01")
        if result["failures"]:
            result["state"] = "FAIL"
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["state"] == "PASS" else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
