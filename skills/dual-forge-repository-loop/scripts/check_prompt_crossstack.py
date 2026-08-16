#!/usr/bin/env python3
"""Validate the #229 cross-stack artifacts against each other. Zero network.

The rule that matters most here is the last one. This run's own audit showed the
discriminating metric to be lexical: every arm identified every refusal case
correctly, and the whole score difference came from one case where the candidate
prompt happens to carry the checker's vocabulary. So the outcome is recorded as
INDETERMINATE, and that cannot be edited to a portability claim while the audit
still says the metric measures words. Flipping the outcome now requires fixing
the metric, which is the point.

Exit codes: 0 pass, 2 contract failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
PREREG = SKILL / "evals" / "prompt-crossstack-preregistration.json"
CASES = SKILL / "evals" / "prompt-crossstack-cases.json"
RESULT = SKILL / "evals" / "prompt-crossstack-result.json"

EXECUTED = {"EXECUTED", "EXECUTED_INDETERMINATE"}
UNEXECUTED = {"FROZEN_NOT_EXECUTED"}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def check_lifecycle(prereg: dict[str, Any], result: dict[str, Any] | None) -> None:
    status = prereg.get("status")
    if status in UNEXECUTED and result is not None:
        refuse("LIFECYCLE_CONTRADICTION",
               f"preregistration status is {status} beside a committed result")
    if status in EXECUTED and result is None:
        refuse("LIFECYCLE_CONTRADICTION", f"status {status} with no result")
    if status not in EXECUTED | UNEXECUTED:
        refuse("LIFECYCLE_CONTRADICTION", f"unknown status {status!r}")


def check_binding(prereg: dict[str, Any], cases: dict[str, Any],
                  result: dict[str, Any]) -> None:
    if result.get("preregistration_id") != prereg.get("preregistration_id"):
        refuse("PREREGISTRATION_MISBOUND", "result names another preregistration")
    frozen = prereg["case_set"]
    if not cases["set_digest"].startswith(frozen["set_digest"]):
        refuse("CASE_SET_DRIFT",
               f"case file digest {cases['set_digest'][:12]} is not the frozen "
               f"{frozen['set_digest']}")
    if result.get("case_set_id") != cases["case_set_id"]:
        refuse("PREREGISTRATION_MISBOUND", "result names another case set")
    if cases["case_count"] < 6:
        refuse("CASE_SET_DRIFT",
               f"{cases['case_count']} cases; #229 requires at least six held out")
    families = {c["ground_truth"]["violated_rule"] for c in cases["cases"]
                if c["ground_truth"]["violated_rule"]}
    if len(families) < 6:
        refuse("CASE_SET_DRIFT",
               f"{len(families)} distinct rule families; six refusal families were frozen")


def check_stacks(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    stacks = prereg["stacks"]
    if len(stacks) < 2:
        refuse("STACKS_NOT_DISTINCT", "a cross-stack run needs at least two stacks")
    providers = {s["provider"] for s in stacks}
    harnesses = {s["harness"] for s in stacks}
    if len(providers) < 2 or len(harnesses) < 2:
        refuse("STACKS_NOT_DISTINCT",
               f"{len(providers)} provider(s) and {len(harnesses)} harness(es); one model "
               f"behind two aliases is not two stacks")
    if set(result["per_stack"]) != {s["stack_id"] for s in stacks}:
        refuse("STACKS_NOT_DISTINCT", "per_stack does not cover the frozen stacks")


def check_cells(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    stacks = [s["stack_id"] for s in prereg["stacks"]]
    arms = [a["arm"] for a in prereg["arms"]]
    reps = prereg["design"]["repetitions_per_arm"]
    expected = len(stacks) * len(arms) * reps

    cells = result.get("cells")
    if not isinstance(cells, list) or len(cells) != expected:
        refuse("DROPPED_CELL",
               f"{len(cells) if isinstance(cells, list) else '?'} cells against "
               f"{len(stacks)}x{len(arms)}x{reps}={expected}")
    if result.get("cell_count") != expected:
        refuse("DROPPED_CELL", f"cell_count {result.get('cell_count')} is not {expected}")

    seen = {(c["stack_id"], c["arm"], c["repetition"]) for c in cells}
    if len(seen) != expected:
        refuse("DROPPED_CELL", "duplicate or missing (stack, arm, repetition)")

    failures = sum(1 for c in cells if not c.get("scored"))
    if result.get("failed_cells") != failures:
        refuse("DROPPED_CELL",
               f"failed_cells reports {result.get('failed_cells')} while {failures} "
               f"cell(s) carry a failure")


def check_order(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    order: list[tuple[int, str, str, int]] = []
    index = 0
    for stack in prereg["stacks"]:
        for repetition in range(1, prereg["design"]["repetitions_per_arm"] + 1):
            for arm in sorted(prereg["arms"], key=lambda a: hashlib.sha256(
                    f"{stack['stack_id']}|{a['arm']}|{repetition}".encode()).hexdigest()):
                index += 1
                order.append((index, stack["stack_id"], arm["arm"], repetition))
    recorded = sorted((c["arm_order_index"], c["stack_id"], c["arm"], c["repetition"])
                      for c in result["cells"])
    if recorded != order:
        refuse("ARM_ORDER_UNREPRODUCIBLE",
               "recorded order does not re-derive from sha256(stack|arm|repetition)")


def check_summary(result: dict[str, Any]) -> None:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for cell in result["cells"]:
        grouped.setdefault(cell["stack_id"], {}).setdefault(cell["arm"], []).append(cell)
    for stack_id, arms in grouped.items():
        for arm, cells in arms.items():
            recorded = result["per_stack"][stack_id][arm]
            verdict = sum(c["metrics"]["verdict_correct"] for c in cells) / len(cells)
            rule = sum(c["metrics"]["rule_correct"] for c in cells) / len(cells)
            if abs(recorded["verdict_accuracy"] - verdict) > 1e-9:
                refuse("SUMMARY_NOT_DERIVED",
                       f"{stack_id}/{arm} verdict_accuracy {recorded['verdict_accuracy']} "
                       f"against {verdict} computed from cells")
            if abs(recorded["rule_accuracy"] - rule) > 1e-9:
                refuse("SUMMARY_NOT_DERIVED",
                       f"{stack_id}/{arm} rule_accuracy {recorded['rule_accuracy']} "
                       f"against {rule} computed from cells")


def check_metric_audit(result: dict[str, Any]) -> None:
    """An outcome may not out-claim the audit of the metric it rests on."""
    audit = result.get("metric_audit")
    if not isinstance(audit, dict):
        refuse("METRIC_UNAUDITED",
               "a result whose discriminating metric was never audited cannot report an "
               "outcome; verdict accuracy is at ceiling and rule naming is lexical")
    for field in ("verdict_correct_on_every_refusal_case_in_every_arm",
                  "cases_where_a_correct_answer_scored_no_token_hit", "per_case",
                  "marker_vocabulary_in_each_arm_prompt"):
        if field not in audit:
            refuse("METRIC_UNAUDITED", f"metric_audit has no {field}")

    # Recompute the audit's two headline claims from its own per-case table.
    per_case = audit["per_case"]
    always_right = all(arm["verdict_correct"] == arm["cells"]
                       for row in per_case for arm in row["arms"].values())
    gap = any(arm["token_hit"] < arm["verdict_correct"]
              for row in per_case for arm in row["arms"].values())
    if audit["verdict_correct_on_every_refusal_case_in_every_arm"] != always_right:
        refuse("METRIC_UNAUDITED",
               "the audit's verdict claim does not match its own per-case table")
    if audit["cases_where_a_correct_answer_scored_no_token_hit"] != gap:
        refuse("METRIC_UNAUDITED",
               "the audit's token-gap claim does not match its own per-case table")

    eligibility = result.get("eligibility") or {}
    outcome = eligibility.get("outcome")
    if gap and outcome != "INDETERMINATE":
        refuse("OUTCOME_OUTRUNS_THE_METRIC",
               f"outcome {outcome!r} while the audit records correct answers scoring no "
               f"token hit; a lexical metric cannot carry a portability verdict either "
               f"way. Fix the metric, then the outcome may move")


CHECKS = (check_stacks, check_cells, check_order)


def validate(prereg: dict[str, Any], cases: dict[str, Any],
             result: dict[str, Any] | None) -> None:
    check_lifecycle(prereg, result)
    if result is None:
        return
    check_binding(prereg, cases, result)
    for check in CHECKS:
        check(prereg, result)
    check_summary(result)
    check_metric_audit(result)


def selftest(prereg: dict[str, Any], cases: dict[str, Any],
             result: dict[str, Any]) -> int:
    try:
        validate(prereg, cases, result)
    except Refused as failure:
        print(f"SELFTEST RED: committed artifacts already refused -- {failure}",
              file=sys.stderr)
        return 2

    def mutate(target: str, fn: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        trio = {"prereg": copy.deepcopy(prereg), "cases": copy.deepcopy(cases),
                "result": copy.deepcopy(result)}
        fn(trio[target])
        return trio["prereg"], trio["cases"], trio["result"]

    controls = [
        ("stale-status", "LIFECYCLE_CONTRADICTION",
         mutate("prereg", lambda d: d.update({"status": "FROZEN_NOT_EXECUTED"}))),
        ("case-set-drift", "CASE_SET_DRIFT",
         mutate("prereg", lambda d: d["case_set"].update({"set_digest": "0" * 12}))),
        ("one-provider", "STACKS_NOT_DISTINCT",
         mutate("prereg", lambda d: d["stacks"][1].update(
             {"provider": d["stacks"][0]["provider"]}))),
        ("one-harness", "STACKS_NOT_DISTINCT",
         mutate("prereg", lambda d: d["stacks"][1].update(
             {"harness": d["stacks"][0]["harness"]}))),
        ("dropped-cell", "DROPPED_CELL",
         mutate("result", lambda d: d.update({"cells": d["cells"][:-1]}))),
        ("hidden-failure", "DROPPED_CELL",
         mutate("result", lambda d: d["cells"][0].update({"scored": False}))),
        ("order-chosen", "ARM_ORDER_UNREPRODUCIBLE",
         mutate("result", lambda d: d["cells"][0].update({"arm_order_index": 99}))),
        ("summary-inflated", "SUMMARY_NOT_DERIVED",
         mutate("result", lambda d: list(d["per_stack"].values())[0]
                ["CANDIDATE_V2_1"].update({"rule_accuracy": 6.0}))),
        ("audit-removed", "METRIC_UNAUDITED",
         mutate("result", lambda d: d.pop("metric_audit"))),
        ("audit-contradicts-itself", "METRIC_UNAUDITED",
         mutate("result", lambda d: d["metric_audit"].update(
             {"cases_where_a_correct_answer_scored_no_token_hit": False}))),
        ("outcome-upgraded", "OUTCOME_OUTRUNS_THE_METRIC",
         mutate("result", lambda d: d["eligibility"].update(
             {"outcome": "PORTABLE_CANDIDATE"}))),
        ("outcome-downgraded", "OUTCOME_OUTRUNS_THE_METRIC",
         mutate("result", lambda d: d["eligibility"].update({"outcome": "NOT_ELIGIBLE"}))),
    ]

    failed = 0
    for name, code, trio in controls:
        try:
            validate(*trio)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                  file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused",
              file=sys.stderr)
        failed += 1

    if failed:
        return 2
    print(f"SELFTEST GREEN: committed cross-stack artifacts admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    args = parser.parse_args(argv)

    try:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        result = json.loads(RESULT.read_text(encoding="utf-8")) if RESULT.is_file() else None
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable artifact: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        if result is None:
            print("USAGE: selftest needs a committed result", file=sys.stderr)
            return 64
        return selftest(prereg, cases, result)

    try:
        validate(prereg, cases, result)
    except Refused as failure:
        print(f"CROSS-STACK REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    if result is None:
        print(f"CROSS-STACK GREEN: {prereg['preregistration_id']} frozen, not executed")
        return 0
    print(f"CROSS-STACK GREEN: {result['cell_count']} cells over "
          f"{len(result['per_stack'])} stacks; outcome "
          f"{result['eligibility']['outcome']} -- every arm judged every refusal case "
          f"correctly and the score gap is vocabulary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
