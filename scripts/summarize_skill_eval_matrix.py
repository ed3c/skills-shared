#!/usr/bin/env python3
"""Summarize paired skill-eval JSONL results without external dependencies.

Input rows:
{"case_id":"...","condition":"candidate_skill","should_invoke":true,"did_invoke":true,"passed":true}

Outputs per-condition routing precision/recall/F1 and pass rate, plus candidate
skill lift over no_skill and candidate delta over current_skill.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

VALID = {"no_skill", "current_skill", "candidate_skill", "wrong_skill", "composed_skills"}


def safe_div(num: int, den: int) -> float:
    return num / den if den else 0.0


def summarize(rows: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        condition = row.get("condition")
        if condition not in VALID:
            raise ValueError(f"invalid condition: {condition!r}")
        if not isinstance(row.get("case_id"), str):
            raise ValueError("case_id must be a string")
        for key in ("should_invoke", "did_invoke", "passed"):
            if not isinstance(row.get(key), bool):
                raise ValueError(f"{key} must be boolean")
        buckets[condition].append(row)

    by_condition = {}
    for condition, items in sorted(buckets.items()):
        tp = sum(r["should_invoke"] and r["did_invoke"] for r in items)
        fp = sum((not r["should_invoke"]) and r["did_invoke"] for r in items)
        fn = sum(r["should_invoke"] and (not r["did_invoke"]) for r in items)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        by_condition[condition] = {
            "runs": len(items),
            "pass_rate": safe_div(sum(r["passed"] for r in items), len(items)),
            "routing": {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1},
        }

    candidate = by_condition.get("candidate_skill", {}).get("pass_rate")
    current = by_condition.get("current_skill", {}).get("pass_rate")
    baseline = by_condition.get("no_skill", {}).get("pass_rate")
    return {
        "by_condition": by_condition,
        "candidate_vs_no_skill_lift": None if candidate is None or baseline is None else candidate - baseline,
        "candidate_vs_current_delta": None if candidate is None or current is None else candidate - current,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_skill_eval_matrix.py <results.jsonl>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    rows = []
    try:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {number}: result must be object")
            rows.append(value)
        if not rows:
            raise ValueError("no results")
        result = summarize(rows)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
