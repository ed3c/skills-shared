#!/usr/bin/env python3
"""Deterministic semantic gate for universal-refactor-controller packets.

This module intentionally does not re-implement the semantic engines owned by the
entropy, refactor-proof, Tech Lead, or Shadow skills. It verifies only identity,
receipt, evidence-lane, and cross-packet invariants declared by those owners.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUBJECT_KEYS = ("repository", "commit", "tree", "dirty")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
OWNER_NAMES = ("entropy", "refactor_proof", "tech_lead", "shadow")
PROTECTED_DIMENSIONS = {
    "sources_of_truth",
    "ownership_edges",
    "synchronization_paths",
    "policy_authorities",
}
PROOF_RANK = {
    "L0_SOURCE_FREEZE": 0,
    "L1_STRUCTURAL_REACHABILITY": 1,
    "L2_EXECUTABLE_CONTRACT": 2,
    "L3_HERMETIC_REAL_TASK": 3,
    "L4_MATCHED_LIVE_RUNTIME": 4,
    "L5_DELIVERY_HUMAN_ADMIT": 5,
}


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str


def _violation(code: str, detail: str) -> Violation:
    return Violation(code=code, detail=detail)


def _subject(obj: Any) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None
    if set(obj) != set(SUBJECT_KEYS):
        return None
    repository = obj.get("repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        return None
    if not isinstance(obj.get("commit"), str) or not HEX40.fullmatch(obj["commit"]):
        return None
    if not isinstance(obj.get("tree"), str) or not HEX40.fullmatch(obj["tree"]):
        return None
    if obj.get("dirty") is not False:
        return None
    return obj


def _same_subject(*subjects: Any) -> bool:
    normalized = [_subject(item) for item in subjects]
    return all(item is not None for item in normalized) and all(
        item == normalized[0] for item in normalized[1:]
    )


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _owner_receipt(packet: dict[str, Any], name: str) -> dict[str, Any] | None:
    receipts = packet.get("receipts")
    if not isinstance(receipts, dict):
        return None
    value = receipts.get(name)
    return value if isinstance(value, dict) else None


def _required_proof_rank(controller: dict[str, Any]) -> int | None:
    requirements = controller.get("proof_requirements")
    if not isinstance(requirements, list) or not requirements:
        return None
    ranks: list[int] = []
    for item in requirements:
        rank = PROOF_RANK.get(item)
        if rank is None:
            return None
        ranks.append(rank)
    return max(ranks)


def validate_gate(packet: Any) -> list[Violation]:
    out: list[Violation] = []
    if not isinstance(packet, dict):
        return [_violation("GATE_INPUT_INVALID", "gate input must be an object")]
    if packet.get("schema_version") != "universal-refactor/controller-gate-input/v1":
        out.append(_violation("GATE_INPUT_INVALID", "unexpected gate input schema_version"))

    controller = packet.get("controller")
    delta = packet.get("complexity_delta")
    if not isinstance(controller, dict):
        out.append(_violation("CONTROLLER_CONTRACT_MISSING", "controller object missing"))
        return out
    if not isinstance(delta, dict):
        out.append(_violation("COMPLEXITY_DELTA_MISSING", "complexity_delta object missing"))
        return out

    subject = _subject(controller.get("subject"))
    if subject is None:
        out.append(_violation("EXACT_SUBJECT_MISSING", "controller subject is not exact/clean/content-bound"))

    if controller.get("schema_version") != "universal-refactor/controller-contract/v1":
        out.append(_violation("CONTROLLER_CONTRACT_INVALID", "controller schema_version mismatch"))
    if delta.get("schema_version") != "universal-refactor/complexity-delta/v1":
        out.append(_violation("COMPLEXITY_DELTA_INVALID", "complexity delta schema_version mismatch"))
    if controller.get("target_kind") != delta.get("target_kind"):
        out.append(_violation("TARGET_KIND_MISMATCH", "controller and delta target_kind differ"))

    receipts = packet.get("receipts")
    owner_ids = controller.get("owner_receipts")
    if not isinstance(receipts, dict) or not isinstance(owner_ids, dict):
        out.append(_violation("OWNER_RECEIPTS_MISSING", "owner receipt map is missing"))
        receipts = {}
        owner_ids = {}
    else:
        for owner in OWNER_NAMES:
            receipt = receipts.get(owner)
            expected = owner_ids.get(owner)
            if not isinstance(receipt, dict) or not isinstance(expected, str) or not expected:
                out.append(_violation("OWNER_RECEIPTS_MISSING", f"missing {owner} receipt"))
                continue
            if receipt.get("id") != expected:
                out.append(_violation("OWNER_RECEIPT_ID_MISMATCH", f"{owner} receipt id mismatch"))

    capabilities = controller.get("capabilities")
    old_strengths = controller.get("old_strengths")
    entropy_findings = controller.get("entropy_findings")
    if not _nonempty_strings(capabilities):
        out.append(_violation("CAPABILITY_NOT_FROZEN", "capabilities must be a non-empty frozen set"))
        capabilities = []
    if not _nonempty_strings(old_strengths):
        out.append(_violation("OLD_STRENGTH_UNBOUND", "old_strengths must be a non-empty frozen set"))
        old_strengths = []
    if not _nonempty_strings(entropy_findings):
        out.append(_violation("ENTROPY_FINDING_NOT_ADMITTED", "entropy_findings must be non-empty"))
        entropy_findings = []

    entropy = _owner_receipt(packet, "entropy")
    refactor = _owner_receipt(packet, "refactor_proof")
    tech_lead = _owner_receipt(packet, "tech_lead")
    shadow = _owner_receipt(packet, "shadow")

    subject_candidates = [controller.get("subject"), delta.get("subject")]
    for receipt in (entropy, refactor, tech_lead, shadow):
        if receipt is not None:
            subject_candidates.append(receipt.get("subject"))
    if not _same_subject(*subject_candidates):
        out.append(_violation("SUBJECT_MISMATCH", "controller, delta, or owner receipts target different immutable subjects"))

    if entropy is not None:
        if entropy.get("admitted") is not True:
            out.append(_violation("ENTROPY_FINDING_NOT_ADMITTED", "entropy receipt is not admitted"))
        if set(entropy.get("finding_ids", [])) != set(entropy_findings):
            out.append(_violation("ENTROPY_FINDING_MISMATCH", "entropy receipt finding ids differ from controller"))
        if entropy.get("consumer_proof") != "PASS":
            out.append(_violation("DYNAMIC_OR_PERSISTED_CONSUMER_UNPROVED", "consumer proof is not PASS"))
        if entropy.get("boundary_proof") != "PASS":
            out.append(_violation("BOUNDARY_PROOF_MISSING", "ownership/boundary proof is not PASS"))

    treatments = controller.get("treatments")
    if not isinstance(treatments, dict) or not all(
        isinstance(treatments.get(key), str) and treatments.get(key) for key in ("A", "B0", "B1")
    ):
        out.append(_violation("TREATMENT_IDENTITY_MISSING", "A/B0/B1 treatment identities are incomplete"))
        treatments = {}

    if refactor is not None:
        if refactor.get("treatments") != treatments:
            out.append(_violation("TREATMENT_IDENTITY_MISMATCH", "refactor receipt treatments differ from controller"))
        if set(refactor.get("capabilities", [])) != set(capabilities):
            out.append(_violation("CAPABILITY_NOT_FROZEN", "refactor receipt does not bind the exact capability set"))
        if set(refactor.get("old_strengths", [])) != set(old_strengths):
            out.append(_violation("OLD_STRENGTH_UNBOUND", "refactor receipt does not bind the exact old-strength set"))
        required_rank = _required_proof_rank(controller)
        actual_rank = PROOF_RANK.get(refactor.get("highest_layer"))
        if required_rank is None or actual_rank is None or actual_rank < required_rank:
            out.append(_violation("LOWER_EVIDENCE_PROMOTED", "refactor proof layer is below the frozen requirement"))
        layer_states = refactor.get("layer_states")
        if not isinstance(layer_states, dict):
            out.append(_violation("LOWER_EVIDENCE_PROMOTED", "proof layer states are missing"))
        else:
            for requirement in controller.get("proof_requirements", []):
                if layer_states.get(requirement) != "PASS":
                    out.append(_violation("LOWER_EVIDENCE_PROMOTED", f"required proof layer {requirement} is not PASS"))
                    break

    if shadow is not None:
        if shadow.get("independent") is not True:
            out.append(_violation("SHADOW_NOT_INDEPENDENT", "Shadow receipt is not independent"))
        if shadow.get("read_only") is not True:
            out.append(_violation("SHADOW_NOT_READ_ONLY", "Shadow receipt is not read-only"))
        if shadow.get("verdict") != "ELIGIBLE_FOR_IMPLEMENTATION":
            out.append(_violation("SHADOW_NOT_ELIGIBLE", "Shadow verdict does not admit implementation"))

    if tech_lead is not None:
        if tech_lead.get("global_objective") != "PASS":
            out.append(_violation("GLOBAL_OBJECTIVE_NOT_EXERCISED", "Tech Lead global objective is not PASS"))
        if tech_lead.get("residue_regression") != "PASS":
            out.append(_violation("RESIDUE_OR_REGRESSION_UNPROVED", "residue/regression receipt is not PASS"))
        if tech_lead.get("relocation_check") != "PASS":
            out.append(_violation("COMPLEXITY_RELOCATED", "obligation relocation check is not PASS"))
        if tech_lead.get("state_recomputation_check") != "PASS":
            out.append(_violation("STATE_RECOMPUTED_IN_MULTIPLE_PLACES", "state recomputation check is not PASS"))
        if tech_lead.get("semantic_blast_radius") != "PASS":
            out.append(_violation("SEMANTIC_BLAST_RADIUS_INCREASED_WITHOUT_ADMISSION", "semantic blast radius is not admitted"))
        forbidden = {"MERGE", "RELEASE"}
        authority = set(tech_lead.get("controller_authority", [])) if isinstance(tech_lead.get("controller_authority"), list) else set()
        if authority & forbidden:
            out.append(_violation("CONTROLLER_AUTHORITY_WIDENED", "controller claims merge/release authority"))

    if treatments:
        baseline = delta.get("baseline")
        candidate = delta.get("candidate")
        if not isinstance(baseline, dict) or baseline.get("treatment_id") != treatments.get("A"):
            out.append(_violation("BASELINE_TREATMENT_MISMATCH", "complexity baseline must bind treatment A"))
        if not isinstance(candidate, dict) or candidate.get("treatment_id") != treatments.get("B1"):
            out.append(_violation("CANDIDATE_TREATMENT_MISMATCH", "complexity candidate must bind treatment B1"))
        if isinstance(candidate, dict) and set(candidate.get("entropy_finding_ids", [])) != set(entropy_findings):
            out.append(_violation("ENTROPY_FINDING_MISMATCH", "complexity candidate findings differ from controller"))

    dimensions = delta.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        out.append(_violation("LOC_ONLY_SIMPLIFICATION", "no non-LOC complexity dimension is bound"))
        dimensions = []
    seen_dimensions: set[str] = set()
    strict_reduction = False
    for item in dimensions:
        if not isinstance(item, dict):
            out.append(_violation("COMPLEXITY_DELTA_INVALID", "dimension entry must be an object"))
            continue
        dimension_id = item.get("id")
        if not isinstance(dimension_id, str):
            out.append(_violation("COMPLEXITY_DELTA_INVALID", "dimension id missing"))
            continue
        if dimension_id in seen_dimensions:
            out.append(_violation("DUPLICATE_COMPLEXITY_DIMENSION", f"duplicate dimension {dimension_id}"))
        seen_dimensions.add(dimension_id)
        before = item.get("before")
        after = item.get("after")
        role = item.get("role")
        if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
            out.append(_violation("COMPLEXITY_DELTA_INVALID", f"dimension {dimension_id} lacks numeric before/after"))
            continue
        if role == "REDUCTION_TARGET" and after < before:
            strict_reduction = True
        if role == "NON_REGRESSION" and after > before:
            out.append(_violation("NON_REGRESSION_DIMENSION_INCREASED", f"{dimension_id} increased"))
        if dimension_id in PROTECTED_DIMENSIONS and after > before:
            code = {
                "sources_of_truth": "SOURCE_OF_TRUTH_ADDED",
                "ownership_edges": "OWNERSHIP_EDGE_HIDDEN",
                "synchronization_paths": "SYNCHRONIZATION_PATH_ADDED",
                "policy_authorities": "POLICY_AUTHORITY_ADDED",
            }[dimension_id]
            out.append(_violation(code, f"protected dimension {dimension_id} increased"))
    if dimensions and not strict_reduction:
        out.append(_violation("NO_STRICT_COMPLEXITY_REDUCTION", "no REDUCTION_TARGET strictly decreases"))

    burden = delta.get("replacement_burden")
    if not isinstance(burden, dict) or not isinstance(burden.get("removed"), (int, float)) or not isinstance(burden.get("added"), (int, float)):
        out.append(_violation("REPLACEMENT_BURDEN_MISSING", "replacement burden is not measurable"))
    elif burden["added"] >= burden["removed"]:
        out.append(_violation("WRAPPER_WITH_EQUAL_OR_GREATER_BURDEN", "replacement burden cancels the claimed reduction"))

    preservation = delta.get("capability_preservation")
    covered: set[str] = set()
    if isinstance(preservation, list):
        for item in preservation:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                covered.add(item["id"])
    required_preservation = set(capabilities) | set(old_strengths)
    if required_preservation - covered:
        out.append(_violation("CAPABILITY_OR_OLD_STRENGTH_NOT_PRESERVED", "complexity delta omits frozen capability/old-strength ids"))

    delta_shadow = delta.get("shadow")
    if not isinstance(delta_shadow, dict) or not all(
        delta_shadow.get(key) is True for key in ("independent", "read_only", "subject_match")
    ):
        out.append(_violation("SHADOW_DELTA_INVALID", "complexity delta Shadow identity is not independently bound"))
    elif delta_shadow.get("verdict") != "ELIGIBLE_FOR_IMPLEMENTATION":
        out.append(_violation("SHADOW_NOT_ELIGIBLE", "complexity delta Shadow verdict is not eligible"))

    objective = delta.get("global_objective")
    if not isinstance(objective, dict) or objective.get("state") != "PASS":
        out.append(_violation("GLOBAL_OBJECTIVE_NOT_EXERCISED", "complexity delta global objective is not PASS"))
    if delta.get("verdict") != "PASS":
        out.append(_violation("DELTA_VERDICT_NOT_PASS", "complexity delta verdict is not PASS"))

    portable_core = packet.get("portable_core")
    if not isinstance(portable_core, dict) or portable_core.get("domain_values") not in ([], None):
        out.append(_violation("DOMAIN_VALUE_IN_PORTABLE_CORE", "portable controller core carries target-domain values"))

    deduped: list[Violation] = []
    seen: set[tuple[str, str]] = set()
    for violation in out:
        key = (violation.code, violation.detail)
        if key not in seen:
            seen.add(key)
            deduped.append(violation)
    return deduped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="controller gate input JSON")
    args = parser.parse_args(argv)
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "FAIL", "violations": [{"code": "INPUT_READ_FAILED", "detail": str(exc)}]}, indent=2))
        return 2
    violations = validate_gate(packet)
    payload = {
        "verdict": "PASS" if not violations else "FAIL",
        "evidence_class": "LOCAL_DETERMINISTIC",
        "violations": [violation.__dict__ for violation in violations],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
