#!/usr/bin/env python3
"""Bind every prompt-baseline preregistration, case set and result together.

The #225 artifacts were committed with nothing checking them against each
other, and they drifted the way ungated artifacts do: the preregistration still
said `FROZEN_NOT_EXECUTED` and "Nothing here has been executed" while the
result file beside it recorded fifteen executed cells. Read alone, either file
told a confident and wrong story.

Every `evals/prompt-baseline*-preregistration.json` is checked, each against the
case set it names and the `-result.json` beside it when one exists. A design
this checker does not discover is a design nothing gates, so discovery is a
glob rather than a list that has to be remembered.

The preregistrations list required controls that must turn red. Listing a
control is not running it, so the ones that can be decided from the committed
artifacts are decided here:

    dropped-arm          a failure removed from the denominator
    cross-runtime-copy   a cell that cannot have come from the bound runtime
    model-as-verifier    an outcome asserted rather than derived from the metrics
    fixture-as-physical  a cell with no physical usage record
    prompt-pin-drift     a pinned prompt whose bytes at HEAD no longer hash to it
    marker-leak          a candidate prompt carrying the scorer's own marker string

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
ROOT = HERE.parents[1]
EVALS = HERE / "evals"
PREREG_GLOB = "prompt-baseline*-preregistration.json"

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


def candidate_arm(prereg: dict[str, Any]) -> str:
    """The eligibility rule compares one candidate against its baselines.

    Reading the name off the design rather than hard-coding it is what lets a
    second candidate be measured at all; requiring exactly one keeps the
    comparison from silently choosing which arm it is about.
    """
    names = [arm["arm"] for arm in prereg["arms"] if arm["arm"].startswith("CANDIDATE")]
    if len(names) != 1:
        refuse("CANDIDATE_ARM_AMBIGUOUS",
               f"{len(names)} arm(s) named CANDIDATE*: {names}; the eligibility rule "
               f"compares exactly one candidate against the remaining arms")
    return names[0]


def check_prompt_pins(prereg: dict[str, Any], cases: dict[str, Any]) -> None:
    """Rehash the prompts whose bytes are present at HEAD.

    A digest written into a frozen design and never recomputed is decoration:
    the file can be edited afterwards and the freeze still reads as intact. Arms
    whose bytes are historical carry no `pin_verified_at_head` -- they are not
    at that path any more, and the runner verifies them against the same digest
    when git resolves them.

    The same pass refuses a candidate that carries the scorer's marker strings.
    The case set stopped being held out when it was committed, so a prompt
    written afterwards can score by echoing the marker instead of by judging the
    document, and that is indistinguishable from judgement in the aggregate.
    """
    markers = sorted({case["ground_truth"]["violated_rule"]
                      for case in cases["cases"]
                      if case["ground_truth"].get("violated_rule")})
    for arm in prereg["arms"]:
        if not arm.get("pin_verified_at_head"):
            continue
        path = ROOT / arm["prompt_path"]
        if not path.is_file():
            refuse("PROMPT_PIN_DRIFT",
                   f"{arm['arm']} pins {arm['prompt_path']}, which is absent at HEAD")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != arm["prompt_sha256"]:
            refuse("PROMPT_PIN_DRIFT",
                   f"{arm['arm']} pins {arm['prompt_sha256'][:12]} and {arm['prompt_path']} "
                   f"now hashes {digest[:12]}; the frozen subject moved after the freeze")
        if len(raw) != arm["prompt_bytes"]:
            refuse("PROMPT_PIN_DRIFT",
                   f"{arm['arm']} pins {arm['prompt_bytes']} bytes and {arm['prompt_path']} "
                   f"is {len(raw)}")
        text = raw.decode("utf-8", "replace").lower()
        leaked = [marker for marker in markers if marker in text]
        if leaked:
            refuse("MARKER_LEAK",
                   f"{arm['arm']} prompt contains case marker(s) {leaked}; a prompt that "
                   f"carries the scorer's own strings can score by echo rather than by "
                   f"judgement, and the case set is no longer held out")


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

    candidate = candidate_arm(prereg)
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
    candidate_arm(prereg)
    check_prompt_pins(prereg, cases)
    if result is None:
        return
    check_binding(prereg, cases, result)
    check_cells(prereg, result)
    check_order(prereg, result)
    check_physical(prereg, result)
    check_eligibility(prereg, result)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def designs() -> list[tuple[Path, Path, Path]]:
    """Every frozen design in the evals directory, with its case set and result.

    The result path is a naming convention rather than a field: a result whose
    name does not pair with its preregistration is a result no lifecycle check
    can find, which is the exact drift this checker exists for.
    """
    found: list[tuple[Path, Path, Path]] = []
    for prereg_path in sorted(EVALS.glob(PREREG_GLOB)):
        prereg = load(prereg_path)
        cases_path = ROOT / prereg["case_set"]["path"]
        result_path = prereg_path.with_name(
            prereg_path.name.replace("-preregistration.json", "-result.json"))
        found.append((prereg_path, cases_path, result_path))
    return found


def selftest() -> int:
    """Plant one defect at a time and require the matching refusal.

    A checker that has never been shown to go red is a checker whose green is
    a claim about nothing.

    The record mutations are planted on the executed design, which is the only
    one with cells to corrupt. The freeze mutations are planted on a design that
    is frozen and not executed, because a pinned prompt and a held case set are
    exactly what that state has instead of cells.
    """
    executed: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None
    pinned_executed: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None
    frozen: tuple[dict[str, Any], dict[str, Any]] | None = None
    for prereg_path, cases_path, result_path in designs():
        prereg = load(prereg_path)
        cases = load(cases_path)
        result = load(result_path) if result_path.is_file() else None
        try:
            validate(prereg, cases, result)
        except Refused as failure:
            print(f"SELFTEST RED: {prereg_path.name} already refused -- {failure}",
                  file=sys.stderr)
            return 2
        if result is not None and executed is None:
            executed = (prereg, cases, result)
        if (result is not None and pinned_executed is None
                and any(arm.get("pin_verified_at_head") for arm in prereg["arms"])):
            pinned_executed = (prereg, cases, result)
        if result is None and frozen is None:
            frozen = (prereg, cases)

    if executed is None:
        print("SELFTEST RED: no executed design to plant record defects in", file=sys.stderr)
        return 2
    if frozen is None:
        # Every committed design has executed, which is a legitimate repository
        # state, not a selftest failure. The freeze controls still need a
        # frozen subject, so synthesize one from an executed design: same
        # pins, same case set, status back to FROZEN_NOT_EXECUTED and no
        # result beside it. The synthesized base is validated before any
        # mutation, so a control that goes red is red about its planted
        # defect and not about the synthesis.
        # Prefer an executed design whose arms still verify their pins at
        # HEAD: the freeze controls plant pin and marker defects, and a
        # design without pin_verified_at_head arms skips those checks
        # entirely, leaving the controls with nothing to trip.
        source = pinned_executed or executed
        if not any(arm.get("pin_verified_at_head") for arm in source[0]["arms"]):
            print("SELFTEST RED: no executed design carries a HEAD-verified pin "
                  "to synthesize freeze controls from", file=sys.stderr)
            return 2
        synthetic = copy.deepcopy(source[0])
        synthetic["status"] = "FROZEN_NOT_EXECUTED"
        try:
            validate(synthetic, source[1], None)
        except Refused as failure:
            print(f"SELFTEST RED: synthesized frozen base refused -- {failure}",
                  file=sys.stderr)
            return 2
        frozen = (synthetic, copy.deepcopy(source[1]))
    prereg, cases, result = executed
    frozen_prereg, frozen_cases = frozen

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
        doc["eligibility"]["rule_naming_accuracy"][candidate_arm(prereg)] = 6

    def drift_cases(doc: dict[str, Any]) -> None:
        doc["case_set"]["set_digest"] = "0" * 12

    def mutate_frozen_prereg(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(frozen_prereg)
        fn(copied)
        return copied

    def mutate_frozen_cases(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(frozen_cases)
        fn(copied)
        return copied

    def repin_prompt(doc: dict[str, Any]) -> None:
        for arm in doc["arms"]:
            if arm.get("pin_verified_at_head"):
                arm["prompt_sha256"] = "0" * 64

    def second_candidate(doc: dict[str, Any]) -> None:
        twin = copy.deepcopy(doc["arms"][-1])
        twin["arm"] = "CANDIDATE_TWIN"
        twin["pin_verified_at_head"] = False
        doc["arms"].append(twin)

    def marker_the_prompt(doc: dict[str, Any]) -> None:
        # The candidate prompt is pinned on disk and cannot be edited without
        # tripping the digest first, so the leak is planted from the other side:
        # a case whose marker is a word the prompt does demonstrably carry.
        doc["cases"][0]["ground_truth"]["violated_rule"] = "publication"

    controls: list[tuple[str, str, dict[str, Any], dict[str, Any], dict[str, Any] | None]] = [
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
        ("prompt-pin-drift", "PROMPT_PIN_DRIFT", mutate_frozen_prereg(repin_prompt),
         frozen_cases, None),
        ("two-candidates", "CANDIDATE_ARM_AMBIGUOUS",
         mutate_frozen_prereg(second_candidate), frozen_cases, None),
        ("marker-leak", "MARKER_LEAK", frozen_prereg,
         mutate_frozen_cases(marker_the_prompt), None),
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
    print(f"SELFTEST GREEN: every committed design admitted; {len(controls)} "
          f"mutations refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    args = parser.parse_args(argv)

    try:
        found = designs()
        loaded = [(path, load(path), load(cases_path),
                   load(result_path) if result_path.is_file() else None)
                  for path, cases_path, result_path in found]
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except (KeyError, json.JSONDecodeError) as error:
        print(f"USAGE: unparseable baseline artifact: {error}", file=sys.stderr)
        return 64
    if not loaded:
        print(f"USAGE: no {PREREG_GLOB} under {EVALS}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest()

    for path, prereg, cases, result in loaded:
        try:
            validate(prereg, cases, result)
        except Refused as failure:
            print(f"PROMPT BASELINE REFUSED {failure.code} in {path.name}: {failure.detail}",
                  file=sys.stderr)
            return 2
        except Exception as error:
            print(f"EVALUATOR FAILURE in {path.name}: {error!r}", file=sys.stderr)
            return 70

        if result is None:
            print(f"PROMPT BASELINE GREEN: {prereg['preregistration_id']} frozen and "
                  f"not executed; no result claimed")
            continue
        print(f"PROMPT BASELINE GREEN: {result['cell_count']} cell(s) on "
              f"{result['runtime']}/{result['model']}; outcome "
              f"{result['eligibility']['outcome']} recomputed from the cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
