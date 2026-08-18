#!/usr/bin/env python3
"""Score four frozen treatments of this Skill's entrypoint on named criteria.

The refactor that landed as 4283b48 ("make spatial-loop Constraint-First
universal entry") rewrote 684 of 389 lines and nothing measured whether the
behaviours the old body guaranteed survived. This scorer answers that question
mechanically instead of by reading the new body and finding it cleaner.

Four arms, all real bytes out of this repository's history:

    A  4f21a487  the body ea48423 left behind, immediately before the refactor
    B0 388be0ff  the refactor exactly as it landed, regressions included
    B1 c190932d  the body after #189 restored the escalation law
    B2 live      the current body, after the remaining named laws were rebound

A criterion is not a unique sentence to grep. Each one anchors on a token and
then requires several independent tokens inside a bounded window, so a word that
survived the rewrite without its decidable rule ("qualifying", with the
exclusion list deleted) scores as the loss it is. Emphasis marks and line wraps
are normalized away first: A is hard-wrapped at 80 columns and B is not, and a
criterion that only matched one wrap style would be measuring dialect.

The expected matrix is pinned cell by cell, not just as per-arm totals. Retuning
a predicate until the current body agrees changes some other arm's cell and the
run goes red, so the scorer cannot be quietly fitted to whatever exists now.

Exit: 0 every assertion held, 2 a named assertion failed, 64 unusable input.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = "tests/refactor-proof/fixtures"

# id, role, path relative to the Skill root, pinned blob (None = live body,
# whose identity is owned by the golden proof registry, not duplicated here)
TREATMENTS = [
    (
        "A_OLD_CANONICAL",
        "OLD_CANONICAL",
        f"{FIXTURES}/pre-refactor-SKILL.txt",
        "4f21a487e85360b36dfd524d1d20f7b1010b08d3",
    ),
    (
        "B0_REFACTOR_AS_LANDED",
        "REFACTOR_AS_LANDED",
        f"{FIXTURES}/refactor-as-landed-SKILL.txt",
        "388be0ff697e015968209b028fd04c5de0c5664a",
    ),
    (
        "B1_ESCALATION_LAW_RESTORED",
        "REPAIRED_CANDIDATE",
        f"{FIXTURES}/escalation-restored-SKILL.txt",
        "c190932dc0043ef975da3e34bc22c7a466e61edc",
    ),
    (
        "B2_HARD_LAWS_REBOUND",
        "REPAIRED_CANDIDATE",
        "SKILL.md",
        None,
    ),
]

OLD_STRENGTH = "OLD_STRENGTH"
REFACTOR_PROPERTY = "REFACTOR_PROPERTY"
SHARED = "SHARED"

# name, kind, anchors (empty = whole body), groups (all must match; a group is
# satisfied by any one of its alternatives), window in characters after anchor
CRITERIA = [
    (
        "qualifying_failure_decidable",
        OLD_STRENGTH,
        ["qualifying"],
        [["absent"], ["not_exercised"], ["skipped_by_policy"], ["oracle"]],
        700,
    ),
    (
        "forge_authority_non_substitution",
        OLD_STRENGTH,
        ["github"],
        [["forgejo"], ["not be replaced"], ["workflow"]],
        500,
    ),
    (
        "fresh_diagnosis_not_claimable",
        OLD_STRENGTH,
        ["chatgpt desktop"],
        [["not claim that", "must not claim"], ["handoff"]],
        600,
    ),
    (
        "repair_anti_weakening_enumerated",
        OLD_STRENGTH,
        ["weaken", "weakening"],
        [["negative control"], ["privilege"], ["model judgment"], ["counter"]],
        500,
    ),
    (
        "oracle_outranks_prose",
        OLD_STRENGTH,
        ["outrank"],
        [["oracle"], ["documentation"]],
        400,
    ),
    (
        "no_silent_fallback",
        OLD_STRENGTH,
        ["evidence state"],
        [["never a weaker"], ["privilege"], ["substrate"]],
        400,
    ),
    (
        "capability_evidence_not_transitive",
        OLD_STRENGTH,
        ["package presence"],
        [["documentation"], ["another machine"], ["current-runtime"]],
        400,
    ),
    (
        "non_certification_boundary",
        OLD_STRENGTH,
        ["certif"],
        [["security"], ["production readiness"], ["legal compliance"]],
        400,
    ),
    (
        "complexity_classes_explicit",
        REFACTOR_PROPERTY,
        [],
        [["level a —"], ["level b —"], ["level c —"], ["level d —"]],
        0,
    ),
    (
        "anti_degradation_law",
        REFACTOR_PROPERTY,
        [],
        [["may never silently degrade into level a"]],
        0,
    ),
    (
        "source_claim_classification",
        REFACTOR_PROPERTY,
        [],
        [["design_proposal"], ["measured_fact"], ["external_claim"]],
        0,
    ),
    (
        "evidence_ladder_levels",
        REFACTOR_PROPERTY,
        [],
        [["l0 source_claim"], ["l4 real_substrate_evidence"], ["l6 production_observation"]],
        0,
    ),
    (
        "monitor_default_mode",
        REFACTOR_PROPERTY,
        [],
        [['default_mode: "monitor"'], ["l3 block"], ["shadow architect"]],
        0,
    ),
    (
        "first_green_meta_review",
        REFACTOR_PROPERTY,
        [],
        [["first_green is mandatory"], ["what did these tests not prove?"]],
        0,
    ),
    (
        "contract_checker_route",
        SHARED,
        ["check_system_contract.py"],
        [["check "], ["64"]],
        900,
    ),
    (
        "evidence_state_vocabulary",
        SHARED,
        [],
        [["absent"], ["not_implemented"], ["not_exercised"], ["skipped_by_policy"]],
        0,
    ),
]

EXPECTED = {
    "A_OLD_CANONICAL": {
        "qualifying_failure_decidable": True,
        "forge_authority_non_substitution": True,
        "fresh_diagnosis_not_claimable": True,
        "repair_anti_weakening_enumerated": True,
        "oracle_outranks_prose": True,
        "no_silent_fallback": True,
        "capability_evidence_not_transitive": True,
        "non_certification_boundary": True,
        "complexity_classes_explicit": False,
        "anti_degradation_law": False,
        "source_claim_classification": False,
        "evidence_ladder_levels": False,
        "monitor_default_mode": False,
        "first_green_meta_review": False,
        "contract_checker_route": True,
        "evidence_state_vocabulary": True,
    },
    "B0_REFACTOR_AS_LANDED": {
        "qualifying_failure_decidable": False,
        "forge_authority_non_substitution": False,
        "fresh_diagnosis_not_claimable": False,
        "repair_anti_weakening_enumerated": False,
        "oracle_outranks_prose": False,
        "no_silent_fallback": False,
        "capability_evidence_not_transitive": False,
        "non_certification_boundary": False,
        "complexity_classes_explicit": True,
        "anti_degradation_law": True,
        "source_claim_classification": True,
        "evidence_ladder_levels": True,
        "monitor_default_mode": False,
        "first_green_meta_review": False,
        "contract_checker_route": True,
        "evidence_state_vocabulary": True,
    },
    "B1_ESCALATION_LAW_RESTORED": {
        "qualifying_failure_decidable": True,
        "forge_authority_non_substitution": True,
        "fresh_diagnosis_not_claimable": True,
        "repair_anti_weakening_enumerated": True,
        "oracle_outranks_prose": False,
        "no_silent_fallback": False,
        "capability_evidence_not_transitive": False,
        "non_certification_boundary": False,
        "complexity_classes_explicit": True,
        "anti_degradation_law": True,
        "source_claim_classification": True,
        "evidence_ladder_levels": True,
        "monitor_default_mode": True,
        "first_green_meta_review": True,
        "contract_checker_route": True,
        "evidence_state_vocabulary": True,
    },
    "B2_HARD_LAWS_REBOUND": {name: True for name, *_ in CRITERIA},
}

# The five behaviours the refactor deleted outright and #189 later restored are
# a subset of these; every one of them must read as an A strength and a B0 loss.
EXPECTED_B0_REGRESSIONS = [name for name, kind, *_ in CRITERIA if kind == OLD_STRENGTH]


class ProofError(Exception):
    """Input could not be read at all. Not a scoring result."""


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def normalize(text: str) -> str:
    """Emphasis and line wrapping are dialect, not behaviour."""
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "")).lower()


def windows(body: str, anchors: list[str], span: int) -> list[str]:
    if not anchors:
        return [body]
    found: list[str] = []
    for anchor in anchors:
        start = body.find(anchor)
        while start != -1:
            found.append(body[max(0, start - 100) : start + span])
            start = body.find(anchor, start + 1)
    return found


def holds(body: str, anchors: list[str], groups: list[list[str]], span: int) -> bool:
    for window in windows(body, anchors, span):
        if all(any(alt in window for alt in group) for group in groups):
            return True
    return False


def score(root: Path) -> tuple[dict[str, dict[str, bool]], list[str]]:
    errors: list[str] = []
    matrix: dict[str, dict[str, bool]] = {}
    for arm, _role, rel, pinned in TREATMENTS:
        path = root / rel
        if not path.is_file():
            raise ProofError(f"treatment absent: {rel}")
        if pinned is not None:
            actual = blob_sha(path)
            if actual != pinned:
                errors.append(f"FROZEN_TREATMENT_DRIFT {arm} {actual} != {pinned}")
        body = normalize(path.read_text(encoding="utf-8"))
        matrix[arm] = {
            name: holds(body, anchors, groups, span)
            for name, _kind, anchors, groups, span in CRITERIA
        }
    return matrix, errors


def assertions(matrix: dict[str, dict[str, bool]]) -> list[str]:
    errors: list[str] = []
    for arm, expected in EXPECTED.items():
        for name, want in expected.items():
            got = matrix[arm][name]
            if got != want:
                errors.append(f"CELL_MISMATCH {arm}:{name} expected={want} got={got}")

    for name in EXPECTED_B0_REGRESSIONS:
        if not matrix["A_OLD_CANONICAL"][name]:
            errors.append(f"OLD_STRENGTH_NOT_IN_A {name}")
        if matrix["B0_REFACTOR_AS_LANDED"][name]:
            errors.append(f"REGRESSION_NOT_OBSERVED {name}")

    for name, kind, *_ in CRITERIA:
        if kind == REFACTOR_PROPERTY and matrix["A_OLD_CANONICAL"][name]:
            errors.append(f"OLD_BODY_CREDITED_WITH_NEW_PROPERTY {name}")

    b1 = matrix["B1_ESCALATION_LAW_RESTORED"]
    b2 = matrix["B2_HARD_LAWS_REBOUND"]
    lost = [name for name in b1 if b1[name] and not b2[name]]
    if lost:
        errors.append(f"REPAIR_LOST_EARLIER_STRENGTH {','.join(sorted(lost))}")
    if sum(b2.values()) <= sum(b1.values()):
        errors.append("REPAIR_DID_NOT_DOMINATE_ITS_PREDECESSOR")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    args = parser.parse_args(argv)
    try:
        matrix, errors = score(args.skill_root.resolve())
    except (ProofError, OSError) as exc:
        print(f"REFACTOR-AB-MECHANISM-RED {exc}", file=sys.stderr)
        return 64
    errors.extend(assertions(matrix))
    for arm, _role, _rel, _pin in TREATMENTS:
        held = sorted(name for name, value in matrix[arm].items() if value)
        print(f"{arm} score={len(held)}/{len(CRITERIA)}")
        for name, kind, *_ in CRITERIA:
            state = "HELD" if matrix[arm][name] else "LOST"
            print(f"    {state} {kind} {name}")
    if errors:
        for error in errors:
            print(f"REFACTOR-AB-RED {error}", file=sys.stderr)
        return 2
    print(
        "REFACTOR-AB-GREEN arms=4 criteria=16 "
        "A=10 B0=6 B1=12 B2=16; "
        f"{len(EXPECTED_B0_REGRESSIONS)} old strengths asserted as B0 regressions; "
        "no live model or runtime claim is made here"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
