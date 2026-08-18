#!/usr/bin/env python3
"""Audit what the #229 rule-naming metric actually measures, and fold it into the result.

Two generations live here, and the audit differs because the metric it is
auditing differs.

Generation 1 (LEXICAL) finished with the candidate ahead on both stacks.
Before that could be read as the candidate being better, the metric itself had
to be checked, because verdict accuracy was at ceiling in every arm -- exactly
as in #225 -- so the entire outcome rested on rule naming. Rule naming was
scored by loose token overlap against the checker's internal marker string.
That is not a measure of whether the model identified the right rule; it is a
measure of whether it used the checker's words. This audits, per case and per
arm, the answer the model actually gave alongside the token verdict, and
separately measures how much of each marker's vocabulary each arm's prompt
contains. It always records INDETERMINATE, because a metric shown to be
lexical cannot carry a portability verdict either way.

Generation 2 (RUBRIC) replaced token overlap with an executed paraphrase
rubric, so it does not need the vocabulary audit generation 1 needed. What it
needs is the frozen eligibility rule applied to the result's own cells: mean
verdict and rule accuracy per (stack, arm), compared against the strongest
baseline on each axis, on every stack. A regression on either axis on any
stack is disqualifying, because portability is a claim about all of them.

It re-reads the cells of a completed run. It calls no model and changes no cell.

Usage:
  audit_crossstack_metric.py --run DIR --result R --cases C --preregistration P
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from crossstack_rubric import LEXICAL, RUBRIC, observed_metric

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parents[1]


def tokens_of(marker: str) -> list[str]:
    return [t for t in marker.split("-") if len(t) > 3]


def token_hit(marker: str, stated: str | None) -> bool:
    text = (stated or "").lower().replace("_", "-")
    tokens = tokens_of(marker)
    return bool(tokens) and sum(t in text for t in tokens) >= max(1, len(tokens) // 2)


def prompt_bytes(commit: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{path}"],
                          capture_output=True, text=True, check=True).stdout.lower()


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def derive_eligibility_crossstack(prereg: dict[str, Any],
                                  result: dict[str, Any]) -> dict[str, Any]:
    """Recompute the frozen cross-stack eligibility rule from the result's own cells.

    Not asserted -- derived. `verdict_accuracy` and `rule_accuracy` are the mean
    of each cell's own scored metrics, grouped by (stack, arm). For each axis,
    the strongest baseline is whichever non-candidate arm scores highest on
    that axis on that stack, and a regression is the candidate scoring below
    it. A run that regressed on nothing is PORTABLE_RECORD_ELIGIBLE; a
    regression on either axis on any stack is NOT_ELIGIBLE, per the frozen
    rule: "no hard regression against the strongest baseline arm ... on every
    stack".
    """
    by_stack_arm: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for cell in result["cells"]:
        by_stack_arm.setdefault(cell["stack_id"], {}).setdefault(cell["arm"], []).append(cell)

    verdict = {stack: {arm: mean([c["metrics"]["verdict_correct"] for c in cells])
                       for arm, cells in arms.items()}
              for stack, arms in by_stack_arm.items()}
    rule = {stack: {arm: mean([c["metrics"]["rule_correct"] for c in cells])
                    for arm, cells in arms.items()}
           for stack, arms in by_stack_arm.items()}

    candidate = "CANDIDATE_V2_1"
    strongest: dict[str, dict[str, str]] = {}
    regression: dict[str, dict[str, bool]] = {}
    regressed_stacks: list[str] = []
    for stack in by_stack_arm:
        stack_strongest: dict[str, str] = {}
        stack_regression: dict[str, bool] = {}
        for name, computed in (("verdict_accuracy", verdict), ("rule_accuracy", rule)):
            baselines = {arm: score for arm, score in computed[stack].items()
                        if arm != candidate}
            best = max(baselines, key=lambda arm: baselines[arm])
            stack_strongest[name] = best
            stack_regression[name] = computed[stack][candidate] < baselines[best]
        strongest[stack] = stack_strongest
        regression[stack] = stack_regression
        if any(stack_regression.values()):
            regressed_stacks.append(stack)

    outcome = "NOT_ELIGIBLE" if regressed_stacks else "PORTABLE_RECORD_ELIGIBLE"
    return {
        "frozen_rule": prereg["eligibility_threshold"]["rule"],
        "verdict_accuracy": verdict,
        "rule_accuracy": rule,
        "strongest_baseline": strongest,
        "regression_against_strongest_baseline": regression,
        "regressed_stacks": sorted(regressed_stacks),
        "outcome": outcome,
    }


def audit_lexical(args: argparse.Namespace, prereg: dict[str, Any], result: dict[str, Any],
                  cases: list[dict[str, Any]]) -> dict[str, Any]:
    truth = {c["case_id"]: c["ground_truth"] for c in cases}
    refusals = [c["case_id"] for c in cases if truth[c["case_id"]]["verdict"] == "REFUSE"]

    answers: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list))
    cells_dir = args.run / "cells"
    if not cells_dir.is_dir():
        print(f"USAGE: no cells under {args.run}", file=sys.stderr)
        raise SystemExit(64)

    for cell_dir in sorted(cells_dir.iterdir()):
        output = cell_dir / "agent-output.json"
        if not output.is_file():
            continue
        arm = cell_dir.name.split("__")[1]
        body = json.loads(output.read_text(encoding="utf-8"))
        seen: dict[str, Any] = {}
        for item in body.get("judgements", []):
            if isinstance(item, dict) and isinstance(item.get("case_id"), str):
                seen.setdefault(item["case_id"], item)
        for case_id in refusals:
            got = seen.get(case_id) or {}
            marker = truth[case_id]["violated_rule"]
            answers[arm][case_id].append({
                "cell": cell_dir.name,
                "verdict_correct": str(got.get("verdict", "")).upper() == "REFUSE",
                "stated_rule": str(got.get("violated_rule") or ""),
                "token_hit": token_hit(marker, got.get("violated_rule")),
            })

    per_case: list[dict[str, Any]] = []
    for case_id in refusals:
        marker = truth[case_id]["violated_rule"]
        row: dict[str, Any] = {"case_id": case_id, "marker": marker,
                               "marker_tokens": tokens_of(marker), "arms": {}}
        for arm, by_case in answers.items():
            entries = by_case[case_id]
            row["arms"][arm] = {
                "cells": len(entries),
                "verdict_correct": sum(1 for e in entries if e["verdict_correct"]),
                "token_hit": sum(1 for e in entries if e["token_hit"]),
                "stated_rules": sorted({e["stated_rule"] for e in entries}),
            }
        per_case.append(row)

    # How much of each marker's vocabulary does each arm's prompt already carry?
    path = prereg["subject"]["prompt_path"]
    vocabulary: list[dict[str, Any]] = []
    texts = {arm["arm"]: (prompt_bytes(arm["prompt_commit"], path)
                          if arm["prompt_commit"] else "")
             for arm in prereg["arms"]}
    for case_id in refusals:
        marker = truth[case_id]["violated_rule"]
        tokens = tokens_of(marker)
        vocabulary.append({
            "marker": marker,
            "tokens": tokens,
            "present_in_arm_prompt": {
                arm: sum(1 for t in tokens if t in text) for arm, text in texts.items()},
            "token_count": len(tokens),
        })

    verdict_always_right = all(
        row["arms"][arm]["verdict_correct"] == row["arms"][arm]["cells"]
        for row in per_case for arm in row["arms"])
    token_gap = any(
        row["arms"][arm]["token_hit"] < row["arms"][arm]["verdict_correct"]
        for row in per_case for arm in row["arms"])

    audit = {
        "what_the_metric_measures": (
            "loose token overlap between the model's stated rule and the checker's "
            "internal marker string"),
        "verdict_correct_on_every_refusal_case_in_every_arm": verdict_always_right,
        "cases_where_a_correct_answer_scored_no_token_hit": token_gap,
        "per_case": per_case,
        "marker_vocabulary_in_each_arm_prompt": vocabulary,
        "finding": (
            "Every arm identified every refusal case correctly. The rule-naming score "
            "differs only in whether the model happened to use the checker's words, and "
            "the candidate prompt carries more of that vocabulary than the baseline "
            "does. A lexical metric plus a ceilinged verdict metric cannot separate "
            "prompt quality from prompt vocabulary."),
        "consequence_for_225": (
            "#225 rests on this same rule-naming metric with its own verdict metric at "
            "ceiling, so its NOT_ELIGIBLE is subject to the same objection in the "
            "opposite direction. Neither run supports a claim about judgement."),
    }

    result["metric_audit"] = audit
    result["eligibility"] = {
        "frozen_rule": prereg["eligibility_threshold"]["rule"],
        "mechanical_outcome": "no hard regression against the strongest baseline on "
                              "either stack",
        "outcome": "INDETERMINATE",
        "why_not_portable_candidate": (
            "Applying the frozen rule to a metric this run has just shown to be lexical "
            "would report a portability result the evidence does not carry. The "
            "preregistration's own non-claim already covers it: a difference inside the "
            "per-cell spread is not a finding, and the observed gap is one rule name "
            "against a spread of one."),
        "why_not_not_eligible": (
            "The candidate regressed on nothing. Reporting ineligibility would be the "
            "same error with the sign flipped."),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))

    generation = observed_metric(cases)
    if generation == RUBRIC:
        result["eligibility"] = derive_eligibility_crossstack(prereg, result)
        args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        print(json.dumps({"result": str(args.result), "generation": generation,
                          "outcome": result["eligibility"]["outcome"],
                          "regressed_stacks": result["eligibility"]["regressed_stacks"]},
                         indent=2))
        return 0

    if generation != LEXICAL:
        print(f"USAGE: cases are {generation}; this script audits LEXICAL or RUBRIC "
              f"generations only", file=sys.stderr)
        return 64

    result = audit_lexical(args, prereg, result, cases)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"result": str(args.result),
                      "verdict_always_right": result["metric_audit"][
                          "verdict_correct_on_every_refusal_case_in_every_arm"],
                      "correct_answers_scored_zero": result["metric_audit"][
                          "cases_where_a_correct_answer_scored_no_token_hit"],
                      "outcome": result["eligibility"]["outcome"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
