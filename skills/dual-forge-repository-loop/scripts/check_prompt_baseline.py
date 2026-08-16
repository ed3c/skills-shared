#!/usr/bin/env python3
"""Bind the #225 prompt-baseline preregistration, case set and result together.

The three artifacts were committed with nothing checking them against each
other, and they drifted the way ungated artifacts do: the preregistration still
said `FROZEN_NOT_EXECUTED` and "Nothing here has been executed" while the
result file beside it recorded fifteen executed cells. Read alone, either file
told a confident and wrong story.

The preregistration lists eight required controls that must turn red. Listing a
control is not running it, so the ones that can be decided from the committed
artifacts are decided here:

    dropped-arm          a failure removed from the denominator
    cross-runtime-copy   a cell that cannot have come from the bound runtime
    model-as-verifier    an outcome asserted rather than derived from the metrics
    fixture-as-physical  a cell with no physical usage record

The rest -- contaminated context, divergent subject, asymmetric tools, baseline
leakage -- are properties of the run, not of its record, and stay with the
runner.

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

HERE = Path(__file__).resolve().parent.parent
PREREG = HERE / "evals" / "prompt-baseline-preregistration.json"
CASES = HERE / "evals" / "prompt-baseline-cases.json"
RESULT = HERE / "evals" / "prompt-baseline-result.json"

EXECUTED_STATES = {"EXECUTED", "EXECUTED_NOT_ELIGIBLE", "EXECUTED_ELIGIBLE"}
UNEXECUTED_STATES = {"FROZEN_NOT_EXECUTED"}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def check_lifecycle(prereg: dict[str, Any], result: dict[str, Any] | None) -> None:
    status = prereg.get("status")
    if status in UNEXECUTED_STATES and result is not None:
        refuse("LIFECYCLE_CONTRADICTION",
               f"preregistration status is {status} while a result for "
               f"{result.get('preregistration_id')} is committed beside it")
    if status in EXECUTED_STATES and result is None:
        refuse("LIFECYCLE_CONTRADICTION",
               f"preregistration status is {status} with no committed result")
    if status not in EXECUTED_STATES | UNEXECUTED_STATES:
        refuse("LIFECYCLE_CONTRADICTION", f"unknown preregistration status {status!r}")


def check_binding(prereg: dict[str, Any], cases: dict[str, Any],
                  result: dict[str, Any]) -> None:
    if result.get("preregistration_id") != prereg.get("preregistration_id"):
        refuse("PREREGISTRATION_MISBOUND",
               f"result names preregistration {result.get('preregistration_id')!r}, "
               f"file is {prereg.get('preregistration_id')!r}")
    frozen = prereg["case_set"]
    if result.get("case_set_id") != frozen["case_set_id"]:
        refuse("PREREGISTRATION_MISBOUND",
               f"result names case set {result.get('case_set_id')!r}, "
               f"preregistration froze {frozen['case_set_id']!r}")
    if result.get("runtime") != prereg["runtime"]["identity"]:
        refuse("PREREGISTRATION_MISBOUND",
               f"result runtime {result.get('runtime')!r} is not the frozen "
               f"{prereg['runtime']['identity']!r}; #225 forbids combining runtimes")
    if result.get("model") != prereg["runtime"]["model"]:
        refuse("PREREGISTRATION_MISBOUND",
               f"result model {result.get('model')!r} is not the frozen "
               f"{prereg['runtime']['model']!r}")


def check_case_set(prereg: dict[str, Any], cases: dict[str, Any]) -> None:
    frozen = prereg["case_set"]
    declared = cases.get("set_digest", "")
    if not declared.startswith(frozen["set_digest"]):
        refuse("CASE_SET_DRIFT",
               f"case file digest {declared[:12]} is not the frozen "
               f"{frozen['set_digest']}")
    ids = [case["case_id"] for case in cases["cases"]]
    if ids != frozen["case_ids"]:
        refuse("CASE_SET_DRIFT", f"case ids {ids} are not the frozen {frozen['case_ids']}")
    if len(ids) != frozen["case_count"]:
        refuse("CASE_SET_DRIFT",
               f"{len(ids)} cases against the frozen count {frozen['case_count']}")


def expected_order(prereg: dict[str, Any]) -> list[tuple[int, str, int]]:
    """Reproduce the frozen arm order: sha256(arm|repetition), per repetition."""
    order: list[tuple[int, str, int]] = []
    index = 0
    for repetition in range(1, prereg["design"]["repetitions_per_arm"] + 1):
        for arm in sorted(prereg["arms"], key=lambda a: hashlib.sha256(
                f"{a['arm']}|{repetition}".encode()).hexdigest()):
            index += 1
            order.append((index, arm["arm"], repetition))
    return order


def check_cells(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    arms = [arm["arm"] for arm in prereg["arms"]]
    repetitions = prereg["design"]["repetitions_per_arm"]
    expected_count = len(arms) * repetitions

    cells = result.get("cells")
    if not isinstance(cells, list):
        refuse("CELL_INVENTORY_INCOMPLETE", "result.cells must be a list")
    if result.get("cell_count") != expected_count:
        refuse("CELL_INVENTORY_INCOMPLETE",
               f"cell_count {result.get('cell_count')} against the frozen "
               f"{len(arms)} arms x {repetitions} repetitions = {expected_count}")
    if len(cells) != expected_count:
        refuse("DROPPED_ARM",
               f"{len(cells)} cells recorded where the design requires "
               f"{expected_count}; a run that failed stays in the denominator")

    seen: set[tuple[str, int]] = set()
    for cell in cells:
        key = (cell.get("arm"), cell.get("repetition"))
        if key in seen:
            refuse("CELL_INVENTORY_INCOMPLETE", f"duplicate cell {key}")
        seen.add(key)
        if cell.get("arm") not in arms:
            refuse("CELL_INVENTORY_INCOMPLETE", f"cell names unfrozen arm {cell.get('arm')!r}")
    missing = sorted({(arm, rep) for arm in arms for rep in range(1, repetitions + 1)} - seen)
    if missing:
        refuse("DROPPED_ARM", f"no cell for {missing}")

    recorded_failures = sum(1 for cell in cells if not cell.get("scored", False)
                            or cell.get("exit_code") != 0)
    if result.get("failed_cells") != recorded_failures:
        refuse("DROPPED_ARM",
               f"failed_cells reports {result.get('failed_cells')} while {recorded_failures} "
               f"cell(s) carry a failure; a failure edited out of the summary is the "
               f"denominator moving")


def check_order(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    recorded = sorted((cell["arm_order_index"], cell["arm"], cell["repetition"])
                      for cell in result["cells"])
    if recorded != expected_order(prereg):
        refuse("ARM_ORDER_UNREPRODUCIBLE",
               "recorded arm order does not reproduce from sha256(arm|repetition); "
               "an order chosen at run time is an order that can be chosen after "
               "seeing a result")


def check_physical(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    """Every cell must carry the usage its bound carrier actually reports.

    The preregistration chose this host partly because it reports tokens,
    duration and cost, and noted that Codex CLI reports no cost. A cell with no
    cost under this runtime therefore cannot have come from the bound host --
    it is either a foreign cell or a fixture wearing a physical run's shape.
    """
    for cell in result["cells"]:
        usage = cell.get("usage")
        if not isinstance(usage, dict):
            refuse("FIXTURE_AS_PHYSICAL", f"{cell.get('cell_id')} records no usage")
        for field in ("cost_usd", "duration_ms", "input_tokens", "output_tokens"):
            value = usage.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                refuse("CROSS_RUNTIME_COPY",
                       f"{cell.get('cell_id')} reports {field}={value!r}; the frozen "
                       f"runtime {prereg['runtime']['identity']} reports it on every cell")

    prompt_bytes = {arm["arm"]: arm["prompt_bytes"] for arm in prereg["arms"]}
    for cell in result["cells"]:
        expected = prompt_bytes.get(cell["arm"])
        if cell.get("prompt_bytes") != expected:
            refuse("CROSS_RUNTIME_COPY",
                   f"{cell['cell_id']} carried {cell.get('prompt_bytes')} prompt bytes, "
                   f"the frozen arm carries {expected}")


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def check_eligibility(prereg: dict[str, Any], result: dict[str, Any]) -> None:
    """Recompute the outcome instead of accepting the one that was written down."""
    eligibility = result.get("eligibility")
    if not isinstance(eligibility, dict):
        refuse("ELIGIBILITY_NOT_DERIVED", "result.eligibility must be an object")

    by_arm: dict[str, list[dict[str, Any]]] = {}
    for cell in result["cells"]:
        by_arm.setdefault(cell["arm"], []).append(cell)

    rule = {arm: mean([c["metrics"]["rule_correct"] for c in cells])
            for arm, cells in by_arm.items()}
    verdict = {arm: mean([c["metrics"]["verdict_correct"] for c in cells])
               for arm, cells in by_arm.items()}

    for name, computed in (("rule_naming_accuracy", rule), ("verdict_accuracy", verdict)):
        recorded = eligibility.get(name)
        if not isinstance(recorded, dict):
            refuse("ELIGIBILITY_NOT_DERIVED", f"eligibility.{name} is missing")
        for arm, value in computed.items():
            if abs(float(recorded.get(arm, -1)) - value) > 1e-9:
                refuse("ELIGIBILITY_NOT_DERIVED",
                       f"eligibility.{name}[{arm}] records {recorded.get(arm)!r}, "
                       f"the cells compute {value}")

    candidate = "CANDIDATE_V2_1"
    baselines = {arm: score for arm, score in rule.items() if arm != candidate}
    strongest = max(baselines, key=lambda arm: baselines[arm])
    if eligibility.get("strongest_baseline") != strongest:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"strongest_baseline records {eligibility.get('strongest_baseline')!r}, "
               f"the cells compute {strongest!r}")

    regressed = rule[candidate] < baselines[strongest]
    if eligibility.get("regression_against_strongest_baseline") is not regressed:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"regression_against_strongest_baseline records "
               f"{eligibility.get('regression_against_strongest_baseline')!r}, the cells "
               f"compute {regressed}")

    outcome = "NOT_ELIGIBLE" if regressed else "LOCAL_RECORD_ELIGIBLE"
    if outcome not in prereg["eligibility_threshold"]["outcome_values"]:
        refuse("ELIGIBILITY_NOT_DERIVED", f"{outcome} is not a frozen outcome value")
    if eligibility.get("outcome") != outcome:
        refuse("ELIGIBILITY_NOT_DERIVED",
               f"outcome records {eligibility.get('outcome')!r}; the frozen rule applied "
               f"to these cells gives {outcome}")


def validate(prereg: dict[str, Any], cases: dict[str, Any],
             result: dict[str, Any] | None) -> None:
    check_lifecycle(prereg, result)
    check_case_set(prereg, cases)
    if result is None:
        return
    check_binding(prereg, cases, result)
    check_cells(prereg, result)
    check_order(prereg, result)
    check_physical(prereg, result)
    check_eligibility(prereg, result)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def selftest() -> int:
    """Plant one defect at a time and require the matching refusal.

    A checker that has never been shown to go red is a checker whose green is
    a claim about nothing.
    """
    prereg = load(PREREG)
    cases = load(CASES)
    result = load(RESULT)

    try:
        validate(prereg, cases, result)
    except Refused as failure:
        print(f"SELFTEST RED: committed artifacts already refused -- {failure}", file=sys.stderr)
        return 2

    def mutate_prereg(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(prereg)
        fn(copied)
        return copied

    def mutate_result(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(result)
        fn(copied)
        return copied

    def set_status(doc: dict[str, Any]) -> None:
        doc["status"] = "FROZEN_NOT_EXECUTED"

    def drop_cell(doc: dict[str, Any]) -> None:
        doc["cells"] = doc["cells"][:-1]

    def hide_failure(doc: dict[str, Any]) -> None:
        doc["cells"][0]["exit_code"] = 1
        doc["cells"][0]["scored"] = False

    def foreign_runtime(doc: dict[str, Any]) -> None:
        doc["runtime"] = "CODEX_CLI_LOCAL"

    def no_cost(doc: dict[str, Any]) -> None:
        doc["cells"][0]["usage"]["cost_usd"] = 0

    def no_usage(doc: dict[str, Any]) -> None:
        doc["cells"][2].pop("usage")

    def shuffle_order(doc: dict[str, Any]) -> None:
        doc["cells"][0]["arm_order_index"], doc["cells"][1]["arm_order_index"] = (
            doc["cells"][1]["arm_order_index"], doc["cells"][0]["arm_order_index"])

    def assert_eligible(doc: dict[str, Any]) -> None:
        doc["eligibility"]["outcome"] = "LOCAL_RECORD_ELIGIBLE"

    def inflate_metric(doc: dict[str, Any]) -> None:
        doc["eligibility"]["rule_naming_accuracy"]["CANDIDATE_V2_1"] = 6

    def drift_cases(doc: dict[str, Any]) -> None:
        doc["case_set"]["set_digest"] = "0" * 12

    controls: list[tuple[str, str, dict[str, Any], dict[str, Any], dict[str, Any]]] = [
        ("stale-status", "LIFECYCLE_CONTRADICTION", mutate_prereg(set_status), cases, result),
        ("case-set-drift", "CASE_SET_DRIFT", mutate_prereg(drift_cases), cases, result),
        ("dropped-arm", "DROPPED_ARM", prereg, cases, mutate_result(drop_cell)),
        ("failure-hidden", "DROPPED_ARM", prereg, cases, mutate_result(hide_failure)),
        ("cross-runtime-copy", "PREREGISTRATION_MISBOUND", prereg, cases,
         mutate_result(foreign_runtime)),
        ("costless-cell", "CROSS_RUNTIME_COPY", prereg, cases, mutate_result(no_cost)),
        ("fixture-as-physical", "FIXTURE_AS_PHYSICAL", prereg, cases, mutate_result(no_usage)),
        ("order-chosen", "ARM_ORDER_UNREPRODUCIBLE", prereg, cases,
         mutate_result(shuffle_order)),
        ("model-as-verifier", "ELIGIBILITY_NOT_DERIVED", prereg, cases,
         mutate_result(assert_eligible)),
        ("metric-inflated", "ELIGIBILITY_NOT_DERIVED", prereg, cases,
         mutate_result(inflate_metric)),
    ]

    failed = 0
    for name, code, p, c, r in controls:
        try:
            validate(p, c, r)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                  file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused", file=sys.stderr)
        failed += 1

    if failed:
        return 2
    print(f"SELFTEST GREEN: committed baseline admitted; {len(controls)} record "
          f"mutations refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    args = parser.parse_args(argv)

    try:
        prereg = load(PREREG)
        cases = load(CASES)
        result = load(RESULT) if RESULT.is_file() else None
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable baseline artifact: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest()

    try:
        validate(prereg, cases, result)
    except Refused as failure:
        print(f"PROMPT BASELINE REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    if result is None:
        print(f"PROMPT BASELINE GREEN: {prereg['preregistration_id']} frozen and "
              f"not executed; no result claimed")
        return 0
    print(f"PROMPT BASELINE GREEN: {result['cell_count']} cell(s) on "
          f"{result['runtime']}/{result['model']}; outcome "
          f"{result['eligibility']['outcome']} recomputed from the cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
