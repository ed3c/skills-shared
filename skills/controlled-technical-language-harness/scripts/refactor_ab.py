#!/usr/bin/env python3
"""Matched hermetic A/B over this Skill's four frozen body treatments.

Deterministic, offline, no model and no provider. It compares the bytes this
Skill's body actually had at each of its four landings, on one criteria matrix
applied identically to every arm, and refuses the three ways that comparison
usually lies: a drifted "frozen" fixture, an old guarantee that quietly left,
and a candidate that gained nothing over its predecessor.

Provenance -- every arm is a real blob from this repository's history, not a
reconstruction. `git cat-file -p <blob>` reproduces each fixture byte for byte:

    A_PRE_LANE_SPLIT              061ff5e  PR #126  blob bced264
    B0_EVALUATOR_LANES_AS_LANDED  edfa292  PR #127  blob d4d3b97
    B1_FORMAT_PRIVACY_REPAIRED    e4f22e8  PR #131  blob a002af7
    B2_AB_VALIDITY_REPAIRED       47cbb25  PR #140  blob 5c19321  (the live SKILL.md)

On the role names, stated plainly because the vocabulary carries weight this
history does not: this Skill's body was never restructured wholesale, so there
is no monolith-to-modules event here to call OLD_CANONICAL and
REFACTOR_AS_LANDED. What the roles are bound to instead is the one landing that
replaced an existing claim rather than appending to it. A declared a single
undifferentiated `deterministic rule evaluation IMPLEMENTED` while its own
ruleset carried `DECLARED_NOT_IMPLEMENTED`; B0 deleted that line and split the
claim into two named evaluator lanes with the boundary between them stated. A
is the body before that split and B0 is the split as it landed. B1 and B2 are
the two later repairs, in the order they landed.

B0 is retained and reported whatever it scores. On this matrix it happens not
to regress against A -- it gains two criteria and loses none -- and that is a
measured result rather than the reason it is here. An arm sequence that keeps
only the arms that came out well is not a denominator, so the intermediate
landing stays in whether or not it flatters the line.

One old strength did leave the body, and that is the finding this comparison
exists to surface rather than to hide. A's `BOUNDED_EXTERNAL` lane was bound to
a "named field set, recorded in the receipt"; B1 replaced that lane with
PRIVATE_ENDPOINT/EXTERNAL_APPROVED and the field-set bound is in no later body.
It was not lost -- it moved into `scripts/check_privacy_routing.py`, which
carries `durable_receipt_fields` and refuses a field whose name looks like a
secret. So the strength is asserted against its executable owner instead of
against the body, and deleting it there turns this red. A relocated guarantee
and a deleted one read identically in the prose; they do not read identically
here.

Exits: 0 green, 2 refused, 64 unusable input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = "tests/refactor-treatments/fixtures"

# (arm id, role, path relative to the skill root, expected git blob sha1)
TREATMENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "A_PRE_LANE_SPLIT",
        "OLD_CANONICAL",
        f"{FIXTURES}/old-canonical-SKILL.txt",
        "bced26459939d78c086139f40513393542b11d89",
    ),
    (
        "B0_EVALUATOR_LANES_AS_LANDED",
        "REFACTOR_AS_LANDED",
        f"{FIXTURES}/refactor-as-landed-SKILL.txt",
        "d4d3b9773c5ec4a640c280d36cc090b8f3f7ba2b",
    ),
    (
        "B1_FORMAT_PRIVACY_REPAIRED",
        "REPAIRED_CANDIDATE",
        f"{FIXTURES}/format-privacy-repaired-SKILL.txt",
        "a002af7079b516836b1167185f3d53572125851a",
    ),
    (
        "B2_AB_VALIDITY_REPAIRED",
        "REPAIRED_CANDIDATE",
        "SKILL.md",
        "5c1932161e9d4164b013f0e2b1f7dc7830021c5d",
    ),
)

# Every criterion is a literal-substring question about the arm's own body, so
# a reader can check any cell by hand against the frozen bytes.
CRITERIA: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # name: (substrings that must all be present, substrings that must all be absent)
    "profile_absent_is_its_own_state": (
        ("`PROFILE_ABSENT`", "it does not silently"),
        (),
    ),
    "named_failure_per_transition": (
        ("Each transition has one named failure", "`SUBJECT_UNBOUND`", "`RECEIPT_SUBJECT_MISMATCH`"),
        (),
    ),
    "deterministic_outranks_model_prose": (
        ("deterministic failure vetoes an advisory pass",),
        (),
    ),
    "privacy_lane_decided_before_evaluators": (
        ("decided before any evaluator runs", "`PRIVACY_LANE_UNDECIDED`, not an implicit"),
        (),
    ),
    "repair_must_strictly_decrease": (
        ("violation count must strictly decrease", "otherwise STOP"),
        (),
    ),
    "repair_may_not_edit_evaluator": (
        ("edit an evaluator so it passes",),
        (),
    ),
    "terminology_admitted_by_a_human": (
        ("never inferred from frequency",),
        (),
    ),
    "compliance_and_safety_are_human_owned": (
        ("compliance / certification claim     HUMAN_ADMIT_REQUIRED",
         "safety-critical acceptance           HUMAN_ADMIT_REQUIRED"),
        (),
    ),
    "receipt_bound_to_exact_subject": (
        ("bound to the exact subject",),
        (),
    ),
    "external_lane_bound_to_named_field_set": (
        ("named field set, recorded in the receipt",),
        (),
    ),
    "evaluator_lanes_separated": (
        ("CALIBRATED_HEURISTIC", "cannot overturn a deterministic failure"),
        (),
    ),
    "no_undifferentiated_deterministic_claim": (
        (),
        ("deterministic rule evaluation        IMPLEMENTED",),
    ),
    "format_declared_never_sniffed": (
        ("never sniffed from content", "stays a **candidate** until source-node readback"),
        (),
    ),
    "privacy_class_routed_by_class_not_by_health": (
        ("`RESTRICTED` always routes `LOCAL_ONLY`", "unhealthy blocks rather than falling back"),
        (),
    ),
    "ab_validity_gate_precedes_any_metric": (
        ("No metric is emitted for a bundle that fails validity",),
        (),
    ),
}

# The guarantees the baseline body carried. Every later arm has to still carry
# each one, or have it named below with the executable owner that took it over.
OLD_STRENGTHS: tuple[str, ...] = (
    "profile_absent_is_its_own_state",
    "named_failure_per_transition",
    "deterministic_outranks_model_prose",
    "privacy_lane_decided_before_evaluators",
    "repair_must_strictly_decrease",
    "repair_may_not_edit_evaluator",
    "terminology_admitted_by_a_human",
    "compliance_and_safety_are_human_owned",
    "receipt_bound_to_exact_subject",
    "external_lane_bound_to_named_field_set",
)

# criterion -> (executable owner relative to the skill root, literals it must carry)
RELOCATED_STRENGTHS: dict[str, tuple[str, tuple[str, ...]]] = {
    "external_lane_bound_to_named_field_set": (
        "scripts/check_privacy_routing.py",
        ("durable_receipt_fields", "looks like a secret"),
    ),
}


class Unusable(Exception):
    """The subjects could not be read. Not the same event as a refusal."""


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def score(body: str) -> dict[str, bool]:
    return {
        name: all(token in body for token in present) and not any(token in body for token in absent)
        for name, (present, absent) in CRITERIA.items()
    }


def read(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        return path.read_bytes()
    except OSError as error:
        raise Unusable(f"unreadable subject: {path}: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=SKILL_ROOT,
        help="Skill directory holding the treatments. Overridden only by the "
             "planted-defect controls in tests/refactor-treatments/verify.sh.",
    )
    args = parser.parse_args(argv)
    root = args.skill_root.resolve()

    refusals: list[str] = []
    try:
        bodies: dict[str, str] = {}
        for arm, _role, relative, expected in TREATMENTS:
            raw = read(root, relative)
            observed = git_blob_sha(raw)
            if observed != expected:
                refusals.append(
                    f"TREATMENT_BLOB_DRIFT {arm}:{relative} expected={expected} observed={observed}"
                )
            bodies[arm] = raw.decode("utf-8")
        owners = {
            criterion: read(root, owner).decode("utf-8")
            for criterion, (owner, _literals) in RELOCATED_STRENGTHS.items()
        }
    except Unusable as error:
        print(f"CTL-REFACTOR-AB-UNUSABLE {error}", file=sys.stderr)
        return 64

    results = {arm: score(bodies[arm]) for arm, _role, _relative, _expected in TREATMENTS}
    order = [arm for arm, _role, _relative, _expected in TREATMENTS]
    baseline = results[order[0]]

    # A criterion the baseline never had cannot be an old strength, and an
    # "old strength" list nobody checks is how a preservation claim goes hollow.
    for criterion in OLD_STRENGTHS:
        if not baseline[criterion]:
            refusals.append(f"OLD_STRENGTH_NOT_IN_BASELINE {order[0]}:{criterion}")

    for arm in order[1:]:
        for criterion in OLD_STRENGTHS:
            if results[arm][criterion]:
                continue
            relocation = RELOCATED_STRENGTHS.get(criterion)
            if relocation is None:
                refusals.append(f"OLD_STRENGTH_LOST {arm}:{criterion}")
                continue
            owner, literals = relocation
            absent = [token for token in literals if token not in owners[criterion]]
            if absent:
                refusals.append(
                    f"OLD_STRENGTH_LOST {arm}:{criterion} relocated to {owner} "
                    f"which no longer carries {absent}"
                )

    # Non-regression and gain are scored over the criteria still owned by the
    # body. A relocated one is excluded here because it is asserted above
    # against the file that now owns it; scoring it twice would report the
    # relocation as a defect.
    comparable = [name for name in CRITERIA if name not in RELOCATED_STRENGTHS]
    for previous, current in zip(order, order[1:]):
        regressed = sorted(
            name for name in comparable if results[previous][name] and not results[current][name]
        )
        if regressed:
            refusals.append(f"TREATMENT_REGRESSION {previous}->{current} {regressed}")
        if not any(results[current][name] and not results[previous][name] for name in comparable):
            refusals.append(f"TREATMENT_GAINED_NOTHING {previous}->{current}")

    if refusals:
        for refusal in refusals:
            print(f"CTL-REFACTOR-AB-RED {refusal}", file=sys.stderr)
        return 2

    report = {
        "schema": "controlled-language/refactor-ab/v1",
        "evidence_scope": "deterministic body-treatment comparison over frozen historical bytes only",
        "physical_model_or_harness_runs": "NOT_EXERCISED",
        "live_provider_or_endpoint": "NOT_EXERCISED",
        "official_asd_ste100_compliance": "NOT_EXERCISED",
        "subjects": {
            arm: {"role": role, "path": relative, "blob_sha": expected}
            for arm, role, relative, expected in TREATMENTS
        },
        "results": results,
        "totals": {arm: sum(values.values()) for arm, values in results.items()},
        "old_strengths_preserved_in_body": [
            name for name in OLD_STRENGTHS if name not in RELOCATED_STRENGTHS
        ],
        "old_strengths_relocated_to_executable_owner": {
            name: RELOCATED_STRENGTHS[name][0]
            for name in OLD_STRENGTHS
            if name in RELOCATED_STRENGTHS
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    totals = " ".join(f"{arm}={sum(results[arm].values())}" for arm in order)
    print(
        f"CTL-REFACTOR-AB-GREEN {len(TREATMENTS)} frozen treatments, "
        f"{len(CRITERIA)} criteria, {totals}; every baseline guarantee still asserted "
        "in the body or against its executable owner; live model/provider A/B NOT_EXERCISED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
