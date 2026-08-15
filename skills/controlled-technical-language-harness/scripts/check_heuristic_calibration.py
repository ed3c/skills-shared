#!/usr/bin/env python3
"""Admission rules for the calibrated-heuristic lane.

A heuristic evaluator -- mood, voice, noun clusters, ambiguous pronouns, action
counts -- guesses. Pinning its model makes it repeatable, not correct, and the
whole point of this lane is that repeatable and correct are different claims. A
pinned parser that is wrong the same way every time is exactly as wrong.

So a heuristic is admitted only with an identity, a corpus it was measured
against, both error rates, and a ceiling it may not exceed. And no matter how
good those numbers are, a heuristic result cannot by itself produce a final
PASS, and can never overturn a deterministic failure.

Exits: 0 admitted, 2 refused, 64 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED = (
    "schema_version",
    "heuristic_id",
    "implementation",
    "corpus",
    "error_rates",
    "failure_ceiling",
    "admission",
)


class Refused(Exception):
    pass


def check_calibration(body: Any) -> None:
    if not isinstance(body, dict):
        raise Refused("calibration receipt must be an object")
    missing = [field for field in REQUIRED if field not in body]
    if missing:
        raise Refused(f"missing required field(s): {', '.join(missing)}")
    if body["schema_version"] != "controlled-language-heuristic-calibration/v1":
        raise Refused(f"unknown schema_version {body['schema_version']!r}")

    implementation = body["implementation"]
    for field in ("id", "version", "digest"):
        if field not in implementation:
            raise Refused(f"implementation.{field} is absent")
    if not DIGEST.fullmatch(str(implementation["digest"])):
        raise Refused("implementation.digest must be a sha256 digest")
    if str(implementation["version"]).strip().lower() in {"latest", "current", "head", ""}:
        raise Refused(
            f"implementation.version {implementation['version']!r} is mutable; a "
            f"calibration measures one build, not a moving one"
        )

    corpus = body["corpus"]
    for field in ("id", "digest", "case_count", "exercised_case_count"):
        if field not in corpus:
            raise Refused(f"corpus.{field} is absent")
    if not DIGEST.fullmatch(str(corpus["digest"])):
        raise Refused("corpus.digest must be a sha256 digest")
    if not isinstance(corpus["case_count"], int) or corpus["case_count"] <= 0:
        raise Refused("corpus.case_count must be a positive integer; an empty corpus calibrates nothing")
    if not isinstance(corpus["exercised_case_count"], int) or corpus["exercised_case_count"] <= 0:
        raise Refused(
            "corpus.exercised_case_count must be positive; zero cases exercised "
            "is an absent measurement, not a calibrated one"
        )
    if corpus["exercised_case_count"] > corpus["case_count"]:
        raise Refused("more cases exercised than the corpus contains")

    rates = body["error_rates"]
    for field in ("false_positive", "false_negative"):
        if field not in rates:
            raise Refused(
                f"error_rates.{field} is absent; a heuristic reporting only one "
                f"direction of error is reporting half its behaviour"
            )
        value = rates[field]
        if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
            raise Refused(f"error_rates.{field} must be a rate between 0 and 1")

    ceiling = body["failure_ceiling"]
    if not isinstance(ceiling, (int, float)) or not 0.0 < float(ceiling) <= 1.0:
        raise Refused("failure_ceiling must be a rate above 0 and at most 1")
    worst = max(float(rates["false_positive"]), float(rates["false_negative"]))
    if worst > float(ceiling):
        raise Refused(
            f"measured error {worst} exceeds the declared ceiling {ceiling}"
        )

    admission = body["admission"]
    if admission.get("human_admit") is not True:
        raise Refused("a calibration threshold is admitted by a human, not by the run that measured it")
    if admission.get("can_produce_final_pass") is not False:
        raise Refused(
            "can_produce_final_pass must be false: a heuristic contributes "
            "evidence and never concludes the run"
        )
    if admission.get("can_override_deterministic") is not False:
        raise Refused(
            "can_override_deterministic must be false: a deterministic failure "
            "is not negotiable by a guess"
        )


def check_composition(receipt: Any) -> None:
    """A completed run may not rest on heuristics alone."""
    if not isinstance(receipt, dict):
        raise Refused("receipt must be an object")
    runs = receipt.get("evaluator_runs")
    if not isinstance(runs, list) or not runs:
        raise Refused("receipt has no evaluator runs")
    decision = receipt.get("decision") or receipt.get("status")
    classes = {run.get("evidence_class") for run in runs if isinstance(run, dict)}

    if decision == "PASS":
        if "DETERMINISTIC" not in classes:
            raise Refused(
                "PASS without any deterministic evaluator run: the decision "
                "rests on heuristics alone"
            )
        for run in runs:
            if not isinstance(run, dict):
                continue
            if run.get("evidence_class") == "DETERMINISTIC" and run.get("status") == "FAIL":
                raise Refused(
                    f"PASS while deterministic evaluator "
                    f"{run.get('evaluator_id')!r} reported FAIL"
                )
            # An evaluator that could not run is not an evaluator that passed.
            if run.get("status") == "ERROR":
                raise Refused(
                    f"PASS while evaluator {run.get('evaluator_id')!r} errored; "
                    f"a checker failure is not a document result"
                )


def _fixture() -> dict[str, Any]:
    return {
        "schema_version": "controlled-language-heuristic-calibration/v1",
        "heuristic_id": "fixture-passive-voice",
        "implementation": {
            "id": "fixture-parser",
            "version": "1.4.2",
            "digest": "sha256:" + "a" * 64,
        },
        "corpus": {
            "id": "fixture-corpus",
            "digest": "sha256:" + "b" * 64,
            "case_count": 200,
            "exercised_case_count": 200,
        },
        "error_rates": {"false_positive": 0.04, "false_negative": 0.07},
        "failure_ceiling": 0.10,
        "admission": {
            "human_admit": True,
            "can_produce_final_pass": False,
            "can_override_deterministic": False,
        },
    }


def _selftest() -> int:
    import copy

    survived: list[str] = []

    try:
        check_calibration(_fixture())
    except Refused as error:
        print(f"SELFTEST RED: canonical calibration refused: {error}", file=sys.stderr)
        return 2

    mutations: list[tuple[str, Any]] = [
        ("mutable implementation version",
         lambda b: b["implementation"].__setitem__("version", "latest")),
        ("implementation digest absent",
         lambda b: b["implementation"].__setitem__("digest", "not-a-digest")),
        ("empty corpus",
         lambda b: b["corpus"].__setitem__("case_count", 0)),
        ("zero cases exercised",
         lambda b: b["corpus"].__setitem__("exercised_case_count", 0)),
        ("more exercised than present",
         lambda b: b["corpus"].__setitem__("exercised_case_count", 999)),
        ("false negative rate omitted",
         lambda b: b["error_rates"].pop("false_negative")),
        ("error exceeds the declared ceiling",
         lambda b: b.__setitem__("failure_ceiling", 0.01)),
        ("ceiling of zero",
         lambda b: b.__setitem__("failure_ceiling", 0)),
        ("calibration self-admitted",
         lambda b: b["admission"].__setitem__("human_admit", False)),
        ("heuristic allowed to conclude the run",
         lambda b: b["admission"].__setitem__("can_produce_final_pass", True)),
        ("heuristic allowed to overturn a deterministic failure",
         lambda b: b["admission"].__setitem__("can_override_deterministic", True)),
    ]
    for name, apply in mutations:
        body = copy.deepcopy(_fixture())
        apply(body)
        try:
            check_calibration(body)
        except Refused:
            continue
        survived.append(name)

    good_receipt = {
        "decision": "PASS",
        "evaluator_runs": [
            {"evaluator_id": "det", "evidence_class": "DETERMINISTIC", "status": "PASS"},
            {"evaluator_id": "heu", "evidence_class": "CALIBRATED_HEURISTIC", "status": "PASS"},
        ],
    }
    try:
        check_composition(good_receipt)
    except Refused as error:
        print(f"SELFTEST RED: canonical composition refused: {error}", file=sys.stderr)
        return 2

    composition_mutations: list[tuple[str, dict[str, Any]]] = [
        ("PASS on heuristics alone", {
            "decision": "PASS",
            "evaluator_runs": [
                {"evaluator_id": "heu", "evidence_class": "CALIBRATED_HEURISTIC", "status": "PASS"},
            ],
        }),
        ("heuristic PASS hiding a deterministic FAIL", {
            "decision": "PASS",
            "evaluator_runs": [
                {"evaluator_id": "det", "evidence_class": "DETERMINISTIC", "status": "FAIL"},
                {"evaluator_id": "heu", "evidence_class": "CALIBRATED_HEURISTIC", "status": "PASS"},
            ],
        }),
        ("checker error read as a document result", {
            "decision": "PASS",
            "evaluator_runs": [
                {"evaluator_id": "det", "evidence_class": "DETERMINISTIC", "status": "PASS"},
                {"evaluator_id": "heu", "evidence_class": "CALIBRATED_HEURISTIC", "status": "ERROR"},
            ],
        }),
    ]
    for name, receipt in composition_mutations:
        try:
            check_composition(receipt)
        except Refused:
            continue
        survived.append(name)

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    total = len(mutations) + len(composition_mutations)
    print(f"SELFTEST GREEN: canonical calibration and composition admitted; {total} mutations refused")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if not args.calibration and not args.receipt:
        parser.error("--calibration, --receipt or --selftest is required")

    try:
        if args.calibration:
            check_calibration(json.loads(args.calibration.read_text(encoding="utf-8")))
        if args.receipt:
            check_composition(json.loads(args.receipt.read_text(encoding="utf-8")))
    except Refused as error:
        print(f"HEURISTIC ADMISSION RED: {error}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as error:
        print(f"FATAL: {error}", file=sys.stderr)
        return 64

    print("HEURISTIC ADMISSION GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
