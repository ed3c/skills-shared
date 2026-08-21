#!/usr/bin/env python3
"""Execute the synthesis and problem-closure compilers as deciding gates.

Four things are checked, and each is checked by running the compiler as a
subprocess and reading its own exit code, never by importing it and trusting a
return value:

    stability   every committed projection is what its request compiles to, and
                two runs of the same request produce identical bytes. A planted
                byte in a copy of a projection has to turn the --check red, or
                --check is comparing something it made up.
    composition every compiled artifact validates against the schema that types
                it, so the compiler and the contract cannot drift apart while
                both stay green on their own.
    absence     the NOT_APPLICABLE semantic lane produces a card whose retrieval
                section is typed absent, carries no rows, states why, and adds
                the missing lane to claims-not-proven. An absent lane that
                merely looks empty is the failure this case exists for.
    refusal     every named refusal code fires from a single-field delta against
                a request that compiles green, so the refusal is attributable to
                the field and not to the fixture being broken in general.

Exit 0 green, 2 a case failed, 70 the validator is absent.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "DTCR-SYNTHESIS-UNUSABLE: jsonschema is required. This suite executes the "
        "committed schemas against compiled output; skipping them would report the "
        "same green as running them.",
        file=sys.stderr,
    )
    raise SystemExit(70)

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
COMPILER = HERE / "compile_synthesis.py"
FIXTURES = HERE / "fixtures"
SCHEMAS = SKILL / "references" / "schemas"

PROJECTIONS = (
    ("review", "synthesis-request.json"),
    ("review", "synthesis-request-no-semantic.json"),
    ("closure", "closure-request.json"),
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COMPILER), *args], capture_output=True, text=True
    )


def compiled_name(fixture: str) -> Path:
    return FIXTURES / fixture.replace(".json", ".compiled.json")


def validator(identity: str) -> Draft202012Validator:
    for path in sorted(SCHEMAS.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("properties", {}).get("schema", {}).get("const") == identity:
            return Draft202012Validator(document)
    raise KeyError(f"no committed schema declares the identity {identity}")


# --------------------------------------------------------------------------
# the mutations. Each is a single field away from a request that compiles.
# --------------------------------------------------------------------------

def mutate(request: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    copied = copy.deepcopy(request)
    edit(copied)
    return copied


def review_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def stale(row: dict) -> None:
        row["fact_bundle"]["subject_commit"] = "main"

    def two_writers(row: dict) -> None:
        row["task"]["task_state_writers"].append("a second worker")

    def no_ceiling(row: dict) -> None:
        del row["fact_bundle"]["coverage_ceiling"]

    def suppressed(row: dict) -> None:
        row["fact_bundle"]["observations"][0]["suppressed_by_context"] = True

    def unadmitted(row: dict) -> None:
        row["invariants"][0]["admission"] = "PROPOSED"

    def orphan_row(row: dict) -> None:
        del row["semantic_bundle"]["rows"][0]["back_reference_ref"]

    def incident(row: dict) -> None:
        row["semantic_bundle"]["rows"][0]["influence"] = "DETERMINED_OUTCOME"

    def fabricated(row: dict) -> None:
        row["claims"][1]["claimed_improvement"] = "40% faster"

    def decided(row: dict) -> None:
        row["task"]["decision"] = "approved"

    def wrong_schema(row: dict) -> None:
        row["schema"] = "dtcr/synthesis-request/v2"

    return [
        ("STALE_SUBJECT", mutate(base, stale)),
        ("SECOND_TASK_STATE_WRITER", mutate(base, two_writers)),
        ("COVERAGE_CEILING_OMITTED", mutate(base, no_ceiling)),
        ("DETERMINISTIC_FACT_OMITTED", mutate(base, suppressed)),
        ("UNADMITTED_INVARIANT", mutate(base, unadmitted)),
        ("SEMANTIC_ROW_WITHOUT_BACK_REFERENCE", mutate(base, orphan_row)),
        ("RETRIEVED_INCIDENT_AS_CURRENT_FAILURE", mutate(base, incident)),
        ("FABRICATED_MEASUREMENT", mutate(base, fabricated)),
        ("RECOMMENDATION_PROMOTED_TO_DECISION", mutate(base, decided)),
        ("UNREADABLE_INPUT", mutate(base, wrong_schema)),
    ]


def closure_mutations(base: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def closed_unverified(row: dict) -> None:
        problem = next(p for p in row["problems"] if p["problem_id"] == "GS-01")
        problem["closed"] = True

    def shrunk(row: dict) -> None:
        problem = next(p for p in row["problems"] if p["problem_id"] == "GS-04")
        problem["denominators"]["negative"] = 1

    def two_writers(row: dict) -> None:
        row["ledger_writers"].append("a second ledger writer")

    def stale(row: dict) -> None:
        row["subject"]["subject_commit"] = "refs/heads/main"

    def no_negative(row: dict) -> None:
        problem = next(p for p in row["problems"] if p["problem_id"] == "GS-08")
        problem["denominators"]["negative"] = 0

    return [
        ("SOURCE_OVERCLAIM_CLOSED_WITHOUT_MECHANISM", mutate(base, closed_unverified)),
        ("DENOMINATOR_SHRINKAGE", mutate(base, shrunk)),
        ("DENOMINATOR_SHRINKAGE", mutate(base, no_negative)),
        ("SECOND_TASK_STATE_WRITER", mutate(base, two_writers)),
        ("STALE_SUBJECT", mutate(base, stale)),
    ]


# --------------------------------------------------------------------------

def main() -> int:
    failures: list[str] = []
    stability = composition = refusals = 0

    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)

        # 1. stability. --check reads the committed bytes, so a stale projection
        #    is caught by the same code path a caller would use.
        for stage, fixture in PROJECTIONS:
            request = FIXTURES / fixture
            projection = compiled_name(fixture)
            result = run(stage, "--input", str(request), "--out", str(projection), "--check")
            stability += 1
            if result.returncode != 0:
                failures.append(
                    f"{fixture}: committed projection is not what it compiles to "
                    f"(exit {result.returncode}) {result.stderr.strip()}"
                )
                continue
            first = run(stage, "--input", str(request))
            second = run(stage, "--input", str(request))
            stability += 1
            if first.stdout != second.stdout:
                failures.append(f"{fixture}: two runs of one request produced different bytes")

            # and the --check has to be able to go red, or it compares nothing.
            planted = work / f"planted-{fixture}"
            planted.write_text(
                projection.read_text(encoding="utf-8").replace(
                    '"packet_id": "DTCR-SP-001"', '"packet_id": "DTCR-SP-009"', 1
                ).replace(
                    '"row_id": "DTCR-PC-001"', '"row_id": "DTCR-PC-009"', 1
                ),
                encoding="utf-8",
            )
            stability += 1
            planted_result = run(stage, "--input", str(request), "--out", str(planted), "--check")
            if planted_result.returncode != 2:
                failures.append(
                    f"{fixture}: --check accepted a projection with a planted byte "
                    f"(exit {planted_result.returncode}), so it proves nothing about the "
                    f"committed one"
                )

        # 2. composition against the committed schemas.
        for stage, fixture in PROJECTIONS:
            document = json.loads(compiled_name(fixture).read_text(encoding="utf-8"))
            artifacts = (
                [document["synthesis_packet"], document["review_card"]]
                if stage == "review"
                else document["rows"]
            )
            for artifact in artifacts:
                composition += 1
                errors = sorted(validator(artifact["schema"]).iter_errors(artifact), key=str)
                if errors:
                    failures.append(
                        f"{fixture}: emitted {artifact['schema']} does not validate "
                        f"against its committed schema: {errors[0].message}"
                    )

        # 3. the absent semantic lane, typed rather than empty.
        absent = json.loads(
            compiled_name("synthesis-request-no-semantic.json").read_text(encoding="utf-8")
        )
        lane = absent["review_card"]["retrieved_context"]
        if lane["state"] != "NOT_APPLICABLE":
            failures.append("the NOT_APPLICABLE run produced a card whose lane is not typed absent")
        if lane["rows"]:
            failures.append("the NOT_APPLICABLE run produced a card carrying retrieval rows")
        if len(lane["rationale"]) < 12:
            failures.append("the NOT_APPLICABLE lane states no rationale, so absent reads as quiet")
        if not any(
            row["lane"] == "SEMANTIC" for row in absent["review_card"]["claims_not_proven"]
        ):
            failures.append(
                "the NOT_APPLICABLE run did not add the unconsulted semantic lane to "
                "claims-not-proven, which is where a reader would look for it"
            )
        if absent["synthesis_packet"]["semantic_lane"].get("result_ref"):
            failures.append("an inapplicable semantic lane still points at a retrieval result")

        # 4. every named refusal, from a single-field delta.
        cases = [
            ("review", "synthesis-request.json", review_mutations),
            ("closure", "closure-request.json", closure_mutations),
        ]
        for stage, fixture, builder in cases:
            base = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
            for index, (code, mutated) in enumerate(builder(base)):
                path = work / f"{stage}-{index:02d}.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                result = run(stage, "--input", str(path))
                refusals += 1
                if result.returncode != 2:
                    failures.append(
                        f"{code}: the mutation compiled with exit {result.returncode} "
                        f"instead of being refused"
                    )
                elif code not in result.stderr:
                    failures.append(
                        f"{code}: refused, but the message names something else: "
                        f"{result.stderr.strip()}"
                    )

        # an input the compiler cannot read at all is 64, not 2: a malformed
        # request and a refused one are different facts about the caller.
        broken = work / "broken.json"
        malformed = json.loads((FIXTURES / "synthesis-request.json").read_text(encoding="utf-8"))
        malformed["fact_bundle"]["observations"] = [42]
        broken.write_text(json.dumps(malformed), encoding="utf-8")
        unusable = run("review", "--input", str(broken))
        refusals += 1
        if unusable.returncode != 64:
            failures.append(
                f"a structurally unusable request exited {unusable.returncode} rather than 64, "
                f"so a broken caller reads as a refused one"
            )

    print(
        f"stability_checks={stability} schema_compositions={composition} "
        f"refusal_codes={refusals} projections={len(PROJECTIONS)}"
    )
    if failures:
        for failure in failures:
            print(f"DTCR-SYNTHESIS-RED {failure}", file=sys.stderr)
        return 2
    print(
        f"DTCR-SYNTHESIS-GREEN {len(PROJECTIONS)} projections byte-stable and current, "
        f"{composition} emitted artifacts validate against their committed schemas, "
        f"{refusals} named refusals fired from single-field deltas"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
