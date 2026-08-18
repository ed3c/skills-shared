#!/usr/bin/env python3
"""Validate the #229 cross-stack artifacts against each other. Zero network.

Two generations live here and the checker reads both.

Generation 1 executed. Its own audit showed the discriminating metric to be
lexical: every arm identified every refusal case correctly, and the whole score
difference came from one case where the candidate prompt happens to carry the
checker's vocabulary. So the outcome is recorded as INDETERMINATE, and that
cannot be edited to a portability claim while the audit still says the metric
measures words. That receipt is history; nothing here rewrites it.

Generation 2 is the repaired instrument. It pairs every refusal family with an
admitted near miss so no constant verdict scores well, and scores rule naming
from a paraphrase rubric whose accept and reject phrasings are re-executed
here. Once it carries a result, its eligibility outcome is recomputed from the
cells rather than accepted: mean verdict and rule accuracy per (stack, arm),
compared against the strongest baseline on each axis, on every stack.

The two are told apart by evidence rather than by trust: a refusal case either
carries a rubric or it does not. A set where none do is the lexical generation,
which is exactly what generation 1's files say by carrying no rubric field --
absence is read as its own declared state, never as a rubric the checker then
pretends to have found. A set where only some do is refused outright.

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

from crossstack_rubric import LEXICAL, MIXED, NO_REFUSAL_CASES, RUBRIC, observed_metric, validate_rubric

SKILL = Path(__file__).resolve().parent.parent
PREREG = SKILL / "evals" / "prompt-crossstack-preregistration.json"
CASES = SKILL / "evals" / "prompt-crossstack-cases.json"
RESULT = SKILL / "evals" / "prompt-crossstack-result.json"
PREREG_V2 = SKILL / "evals" / "prompt-crossstack-v2-preregistration.json"
CASES_V2 = SKILL / "evals" / "prompt-crossstack-v2-cases.json"
RESULT_V2 = SKILL / "evals" / "prompt-crossstack-v2-result.json"

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


def metric_generation(prereg: dict[str, Any], cases: dict[str, Any]) -> str:
    """Derive which metric the case set is scored by, from the cases themselves.

    A file cannot be believed about its own metric, so the rubrics decide. The
    absence of every rubric is the lexical generation's declared state and is
    reported as such; a partial set is refused, because a run scored two ways has
    no single metric to compare arms on.
    """
    observed = observed_metric(cases["cases"])
    if observed == NO_REFUSAL_CASES:
        refuse("CASE_SET_DRIFT", "no refusal cases, so no rule can be named or scored")
    if observed == MIXED:
        refuse("METRIC_GENERATION_MIXED",
               "only some refusal cases carry a rubric; a set scored two ways has no "
               "single metric to compare arms on")

    declared = ((prereg.get("metric_design") or {}).get("rule_metric")
                or cases.get("rule_metric"))
    if declared is None and observed == RUBRIC:
        refuse("METRIC_GENERATION_MISDECLARED",
               "every refusal case carries a rubric and nothing declares it; only the "
               "lexical generation may be declared by absence, and only because that is "
               "what its committed files actually say")
    if declared is not None and declared != observed:
        refuse("METRIC_GENERATION_MISDECLARED",
               f"declared {declared} against {observed} observed in the cases")
    return observed


def constant_verdict_share(cases: dict[str, Any]) -> float:
    """What the best one-word answer scores. A high number is a ceiling, not a pass."""
    verdicts = [c["ground_truth"]["verdict"] for c in cases["cases"]]
    return max(verdicts.count("ADMIT"), verdicts.count("REFUSE")) / len(verdicts)


def check_case_design(prereg: dict[str, Any], cases: dict[str, Any],
                      generation: str) -> None:
    """Gate the instrument, not the run: a set nothing can lose on measures nothing."""
    policy = prereg.get("metric_design") or {}
    ceiling = policy.get("max_constant_verdict_share")
    if ceiling is not None:
        share = constant_verdict_share(cases)
        if share > ceiling:
            refuse("METRIC_AT_CEILING",
                   f"a constant verdict scores {share:.3f} against a frozen ceiling of "
                   f"{ceiling}; every arm passing is not a measurement")

    if generation != RUBRIC:
        return

    refusal_families = {c["field_family"] for c in cases["cases"]
                        if c["ground_truth"]["verdict"] == "REFUSE"
                        and "field_family" in c}
    for case in cases["cases"]:
        if case["ground_truth"]["verdict"] != "ADMIT" or "field_family" not in case:
            continue
        if case["field_family"] not in refusal_families:
            refuse("NEAR_MISS_UNPAIRED",
                   f"{case['case_id']} is admitted in field family "
                   f"{case['field_family']}, where no refusal case lives; an admitted "
                   f"case nothing is near is not a near miss")

    problems: list[str] = []
    for case in cases["cases"]:
        marker = case["ground_truth"]["violated_rule"]
        if marker:
            problems.extend(validate_rubric(marker, case.get("rule_rubric")))
    if problems:
        refuse("RUBRIC_UNUSABLE",
               "; ".join(problems[:3]) + (f" (+{len(problems) - 3} more)"
                                          if len(problems) > 3 else ""))


def check_result_metric(result: dict[str, Any], generation: str) -> None:
    if result.get("rule_metric") != generation:
        refuse("METRIC_GENERATION_MISDECLARED",
               f"the result was scored as {result.get('rule_metric')!r} while the case "
               f"set is {generation}")


def check_eligibility_crossstack(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    """Recompute the frozen cross-stack outcome instead of accepting what was written.

    Mirrors #225's check_eligibility, generalised over stacks: mean verdict and
    rule accuracy per (stack, arm) from the cells, the strongest non-candidate
    baseline on each axis per stack, and a regression wherever the candidate
    scores below it. Any regression on any stack is disqualifying, so the
    outcome is derived rather than trusted.
    """
    eligibility = result.get("eligibility")
    if not isinstance(eligibility, dict):
        refuse("ELIGIBILITY_NOT_DERIVED", "result.eligibility must be an object")

    by_stack_arm: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for cell in result["cells"]:
        by_stack_arm.setdefault(cell["stack_id"], {}).setdefault(cell["arm"], []).append(cell)

    def mean(values: list[float]) -> float:
        return sum(values) / len(values)

    verdict = {stack: {arm: mean([c["metrics"]["verdict_correct"] for c in cells])
                       for arm, cells in arms.items()}
              for stack, arms in by_stack_arm.items()}
    rule = {stack: {arm: mean([c["metrics"]["rule_correct"] for c in cells])
                    for arm, cells in arms.items()}
           for stack, arms in by_stack_arm.items()}

    for name, computed in (("verdict_accuracy", verdict), ("rule_accuracy", rule)):
        recorded = eligibility.get(name)
        if not isinstance(recorded, dict):
            refuse("ELIGIBILITY_NOT_DERIVED", f"eligibility.{name} is missing")
        for stack, arms in computed.items():
            for arm, value in arms.items():
                got = (recorded.get(stack) or {}).get(arm)
                if got is None or abs(float(got) - value) > 1e-9:
                    refuse("ELIGIBILITY_NOT_DERIVED",
                           f"eligibility.{name}[{stack}][{arm}] records {got!r}, the "
                           f"cells compute {value}")

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

    if eligibility.get("strongest_baseline") != strongest:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"strongest_baseline records {eligibility.get('strongest_baseline')!r}, "
               f"the cells compute {strongest!r}")
    if eligibility.get("regression_against_strongest_baseline") != regression:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"regression_against_strongest_baseline records "
               f"{eligibility.get('regression_against_strongest_baseline')!r}, the cells "
               f"compute {regression!r}")

    computed_regressed = sorted(regressed_stacks)
    if eligibility.get("regressed_stacks") != computed_regressed:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"regressed_stacks records {eligibility.get('regressed_stacks')!r}, the "
               f"cells compute {computed_regressed!r}")

    outcome = "NOT_ELIGIBLE" if regressed_stacks else "PORTABLE_RECORD_ELIGIBLE"
    if outcome not in prereg["eligibility_threshold"]["outcome_values"]:
        refuse("ELIGIBILITY_NOT_DERIVED", f"{outcome} is not a frozen outcome value")
    if eligibility.get("outcome") != outcome:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"outcome records {eligibility.get('outcome')!r}; the frozen rule applied "
               f"to these cells gives {outcome}")


CHECKS = (check_stacks, check_cells, check_order)


def validate(prereg: dict[str, Any], cases: dict[str, Any],
             result: dict[str, Any] | None) -> None:
    check_lifecycle(prereg, result)
    generation = metric_generation(prereg, cases)
    check_case_design(prereg, cases, generation)
    if result is None:
        return
    check_binding(prereg, cases, result)
    for check in CHECKS:
        check(prereg, result)
    check_summary(result)
    if generation == LEXICAL:
        check_metric_audit(result)
    else:
        check_result_metric(result, generation)
        check_eligibility_crossstack(prereg, result)


Trio = tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]


def mutator(prereg: dict[str, Any], cases: dict[str, Any],
            result: dict[str, Any] | None) -> Any:
    def mutate(target: str, fn: Any) -> Trio:
        trio: dict[str, Any] = {"prereg": copy.deepcopy(prereg),
                                "cases": copy.deepcopy(cases),
                                "result": copy.deepcopy(result)}
        fn(trio[target])
        return trio["prereg"], trio["cases"], trio["result"]
    return mutate


def generation1_controls(prereg: dict[str, Any], cases: dict[str, Any],
                         result: dict[str, Any]) -> list[tuple[str, str, Trio]]:
    mutate = mutator(prereg, cases, result)
    return [
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


def first_refusal(cases: dict[str, Any]) -> dict[str, Any]:
    return next(c for c in cases["cases"] if c["ground_truth"]["violated_rule"])


def drop_near_misses(cases: dict[str, Any]) -> None:
    """Put the generation-1 ceiling back: refusals plus one admitted case."""
    cases["cases"] = [c for c in cases["cases"]
                      if c["ground_truth"]["verdict"] == "REFUSE"
                      or c["case_id"] == "heldout-positive"]


def generation2_controls(prereg: dict[str, Any], cases: dict[str, Any],
                         result: dict[str, Any] | None) -> list[tuple[str, str, Trio]]:
    """The instrument's own controls: properties of the case set, independent of a result.

    `result` is threaded through unmutated so check_lifecycle does not trip on
    its own -- once generation 2 carries a real result, a trio built with
    result=None would be refused as LIFECYCLE_CONTRADICTION before the planted
    case-set defect is ever reached, masking the control this exists to prove.
    """
    mutate = mutator(prereg, cases, result)
    return [
        ("gen2-ceiling-restored", "METRIC_AT_CEILING",
         mutate("cases", drop_near_misses)),
        ("gen2-near-miss-unpaired", "NEAR_MISS_UNPAIRED",
         mutate("cases", lambda d: next(
             c for c in d["cases"] if c["ground_truth"]["verdict"] == "ADMIT"
             and "field_family" in c).update({"field_family": "budget-ledger"}))),
        ("gen2-rubric-marker-echo", "RUBRIC_UNUSABLE",
         mutate("cases", lambda d: first_refusal(d)["rule_rubric"].update(
             {"accept_any": [[["runtime"]]]}))),
        ("gen2-rubric-removed", "METRIC_GENERATION_MIXED",
         mutate("cases", lambda d: first_refusal(d).pop("rule_rubric"))),
        ("gen2-metric-misdeclared", "METRIC_GENERATION_MISDECLARED",
         mutate("prereg", lambda d: d["metric_design"].update(
             {"rule_metric": LEXICAL}))),
    ]


def generation2_result_controls(prereg: dict[str, Any], cases: dict[str, Any],
                                result: dict[str, Any]) -> list[tuple[str, str, Trio]]:
    """Controls for the executed generation-2 result and its recomputed eligibility."""
    mutate = mutator(prereg, cases, result)
    return [
        ("gen2-stale-status", "LIFECYCLE_CONTRADICTION",
         mutate("prereg", lambda d: d.update({"status": "FROZEN_NOT_EXECUTED"}))),
        ("gen2-eligibility-removed", "ELIGIBILITY_NOT_DERIVED",
         mutate("result", lambda d: d.pop("eligibility"))),
        ("gen2-eligibility-hand-flipped", "ELIGIBILITY_NOT_DERIVED",
         mutate("result", lambda d: d["eligibility"].update(
             {"outcome": "PORTABLE_RECORD_ELIGIBLE"
                        if d["eligibility"]["outcome"] == "NOT_ELIGIBLE" else "NOT_ELIGIBLE"}))),
        ("gen2-verdict-accuracy-inflated", "ELIGIBILITY_NOT_DERIVED",
         mutate("result", lambda d: d["eligibility"]["verdict_accuracy"]["codex-cli-gpt"]
                .update({"CANDIDATE_V2_1": 13.0}))),
    ]


def run_controls(controls: list[tuple[str, str, Trio]]) -> int:
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
    return failed


def selftest(generation1: Trio, generation2: Trio) -> int:
    for label, trio in (("generation 1", generation1), ("generation 2", generation2)):
        try:
            validate(*trio)
        except Refused as failure:
            print(f"SELFTEST RED: committed {label} artifacts already refused -- "
                  f"{failure}", file=sys.stderr)
            return 2

    prereg, cases, result = generation1
    assert result is not None
    prereg2, cases2, result2 = generation2
    controls = (generation1_controls(prereg, cases, result)
                + generation2_controls(prereg2, cases2, result2))
    if result2 is not None:
        controls += generation2_result_controls(prereg2, cases2, result2)
    if run_controls(controls):
        return 2
    print(f"SELFTEST GREEN: committed cross-stack artifacts admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def load(prereg_path: Path, cases_path: Path, result_path: Path) -> Trio:
    result = (json.loads(result_path.read_text(encoding="utf-8"))
              if result_path.is_file() else None)
    return (json.loads(prereg_path.read_text(encoding="utf-8")),
            json.loads(cases_path.read_text(encoding="utf-8")),
            result)


def report(trio: Trio) -> None:
    prereg, cases, result = trio
    generation = metric_generation(prereg, cases)
    if result is None:
        print(f"CROSS-STACK GREEN: {prereg['preregistration_id']} frozen, not executed; "
              f"{cases['case_count']} cases, best constant verdict scores "
              f"{constant_verdict_share(cases):.3f}, rule metric {generation}")
        return
    if generation == LEXICAL:
        print(f"CROSS-STACK GREEN: {result['cell_count']} cells over "
              f"{len(result['per_stack'])} stacks; outcome "
              f"{result['eligibility']['outcome']} -- every arm judged every refusal case "
              f"correctly and the score gap is vocabulary ({generation})")
        return
    print(f"CROSS-STACK GREEN: {result['cell_count']} cells over "
          f"{len(result['per_stack'])} stacks; outcome "
          f"{result['eligibility']['outcome']} -- regressed stacks: "
          f"{result['eligibility']['regressed_stacks'] or 'none'} ({generation})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    args = parser.parse_args(argv)

    try:
        generation1 = load(PREREG, CASES, RESULT)
        generation2 = load(PREREG_V2, CASES_V2, RESULT_V2)
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable artifact: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        if generation1[2] is None:
            print("USAGE: selftest needs the committed generation-1 result",
                  file=sys.stderr)
            return 64
        return selftest(generation1, generation2)

    for trio in (generation1, generation2):
        try:
            validate(*trio)
        except Refused as failure:
            print(f"CROSS-STACK REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
            return 2
        except Exception as error:
            print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
            return 70
        report(trio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
