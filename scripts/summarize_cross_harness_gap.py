#!/usr/bin/env python3
"""Compute stack-specific pass rates and cross-harness generalization gaps.

Accepts JSONL rows in skill-eval-run/v1 or skill-eval-executor-evidence/v1 shape.
The tool never promotes evidence; it only compares explicit observed outcomes.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

VALID_SCHEMAS = {"skill-eval-run/v1", "skill-eval-executor-evidence/v1"}


def parse_row(row: dict) -> dict:
    schema = row.get("schema_version")
    if schema not in VALID_SCHEMAS:
        raise ValueError(f"unsupported schema: {schema!r}")
    case_id = row.get("case_id")
    condition = row.get("condition")
    seed = row.get("seed")
    model = row.get("model")
    harness = row.get("harness")
    outcome = row.get("outcome")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case_id must be non-empty string")
    if not isinstance(condition, str) or not condition:
        raise ValueError("condition must be non-empty string")
    if not isinstance(seed, int):
        raise ValueError("seed must be integer")
    if not isinstance(model, dict) or not isinstance(model.get("name"), str):
        raise ValueError("model.name must be string")
    if not isinstance(harness, dict) or not isinstance(harness.get("name"), str):
        raise ValueError("harness.name must be string")
    if not isinstance(outcome, dict) or not isinstance(outcome.get("passed"), bool):
        raise ValueError("outcome.passed must be boolean")
    return {
        "case_id": case_id,
        "condition": condition,
        "seed": seed,
        "passed": outcome["passed"],
        "stack": (model["name"], harness["name"]),
    }


def summarize(rows: list[dict]) -> dict:
    parsed = [parse_row(r) for r in rows]
    by_stack_condition: dict[tuple[tuple[str, str], str], list[bool]] = defaultdict(list)
    paired: dict[tuple[str, str, int], dict[tuple[str, str], bool]] = defaultdict(dict)
    for row in parsed:
        key = (row["stack"], row["condition"])
        by_stack_condition[key].append(row["passed"])
        pair_key = (row["case_id"], row["condition"], row["seed"])
        if row["stack"] in paired[pair_key]:
            raise ValueError(f"duplicate stack observation for identity {pair_key}: {row['stack']}")
        paired[pair_key][row["stack"]] = row["passed"]

    stack_results: dict[str, dict] = {}
    condition_rates: dict[str, list[float]] = defaultdict(list)
    for (stack, condition), outcomes in sorted(by_stack_condition.items()):
        stack_id = f"{stack[0]}@{stack[1]}"
        rate = sum(outcomes) / len(outcomes)
        stack_results.setdefault(stack_id, {})[condition] = {"runs": len(outcomes), "pass_rate": rate}
        condition_rates[condition].append(rate)

    gaps = {}
    for condition, rates in sorted(condition_rates.items()):
        gaps[condition] = None if len(rates) < 2 else max(rates) - min(rates)

    disagreements = 0
    comparisons = 0
    shared_identities = 0
    for observations in paired.values():
        if len(observations) < 2:
            continue
        shared_identities += 1
        for a, b in itertools.combinations(observations.values(), 2):
            comparisons += 1
            disagreements += a != b

    return {
        "schema_version": "cross-harness-gap/v1",
        "stack_count": len({p["stack"] for p in parsed}),
        "by_stack": stack_results,
        "generalization_gap_by_condition": gaps,
        "paired_agreement": {
            "shared_identities": shared_identities,
            "comparisons": comparisons,
            "disagreements": disagreements,
            "disagreement_rate": None if comparisons == 0 else disagreements / comparisons,
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_cross_harness_gap.py <runs.jsonl>", file=sys.stderr)
        return 2
    try:
        rows = []
        for number, line in enumerate(Path(sys.argv[1]).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {number}: row must be object")
            rows.append(value)
        if not rows:
            raise ValueError("no observations")
        print(json.dumps(summarize(rows), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
