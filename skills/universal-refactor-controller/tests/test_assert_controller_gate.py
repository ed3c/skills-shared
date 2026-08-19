from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "assert_controller_gate.py"
spec = importlib.util.spec_from_file_location("assert_controller_gate", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
validate_gate = module.validate_gate

SUBJECT = {
    "repository": "ed3c/skills-shared",
    "commit": "a" * 40,
    "tree": "b" * 40,
    "dirty": False,
}
CAPS = ["capability:route", "capability:behavior"]
STRENGTHS = ["strength:old-proof"]
FINDINGS = ["entropy:E-001"]
TREATMENTS = {"A": "treatment:A", "B0": "treatment:B0", "B1": "treatment:B1"}


def packet() -> dict:
    controller = {
        "schema_version": "universal-refactor/controller-contract/v1",
        "subject": copy.deepcopy(SUBJECT),
        "target_kind": "SKILL",
        "owner_receipts": {
            "entropy": "receipt:entropy",
            "refactor_proof": "receipt:refactor",
            "tech_lead": "receipt:tech-lead",
            "shadow": "receipt:shadow",
        },
        "capabilities": list(CAPS),
        "old_strengths": list(STRENGTHS),
        "entropy_findings": list(FINDINGS),
        "root_cause_edges": [
            {"from": "truth:a", "to": "truth:b", "relation": "DUPLICATES", "evidence": "scan:1"}
        ],
        "treatments": dict(TREATMENTS),
        "proof_requirements": [
            "L0_SOURCE_FREEZE",
            "L1_STRUCTURAL_REACHABILITY",
            "L2_EXECUTABLE_CONTRACT",
            "L3_HERMETIC_REAL_TASK",
        ],
        "complexity_delta_ref": "delta:1",
        "human_owned_operations": ["MERGE", "RELEASE"],
    }
    delta = {
        "schema_version": "universal-refactor/complexity-delta/v1",
        "subject": copy.deepcopy(SUBJECT),
        "target_kind": "SKILL",
        "baseline": {"treatment_id": "treatment:A", "content_digest": "c" * 64},
        "candidate": {"treatment_id": "treatment:B1", "content_digest": "d" * 64, "entropy_finding_ids": list(FINDINGS)},
        "dimensions": [
            {"id": "concepts", "role": "REDUCTION_TARGET", "before": 7, "after": 5, "measurement": "typed concept inventory", "evidence_class": "HERMETIC"},
            {"id": "states", "role": "NON_REGRESSION", "before": 4, "after": 4, "measurement": "state graph", "evidence_class": "HERMETIC"},
            {"id": "sources_of_truth", "role": "NON_REGRESSION", "before": 2, "after": 1, "measurement": "owner graph", "evidence_class": "HERMETIC"},
            {"id": "ownership_edges", "role": "NON_REGRESSION", "before": 4, "after": 3, "measurement": "owner graph", "evidence_class": "HERMETIC"},
            {"id": "synchronization_paths", "role": "NON_REGRESSION", "before": 1, "after": 0, "measurement": "sync path inventory", "evidence_class": "HERMETIC"},
            {"id": "policy_authorities", "role": "NON_REGRESSION", "before": 2, "after": 2, "measurement": "authority inventory", "evidence_class": "HERMETIC"},
        ],
        "replacement_burden": {"removed": 10, "added": 3, "measurement": "typed obligations"},
        "capability_preservation": [
            {"id": CAPS[0], "state": "PRESERVED_WITH_EXACT_EVIDENCE", "evidence": "test:route"},
            {"id": CAPS[1], "state": "PRESERVED_WITH_EXACT_EVIDENCE", "evidence": "test:behavior"},
            {"id": STRENGTHS[0], "state": "PRESERVED_WITH_EXACT_EVIDENCE", "evidence": "test:old-strength"},
        ],
        "shadow": {"independent": True, "read_only": True, "subject_match": True, "verdict": "ELIGIBLE_FOR_IMPLEMENTATION", "evidence": "shadow:1"},
        "global_objective": {"state": "PASS", "evidence": "matched-task:1"},
        "verdict": "PASS",
    }
    receipts = {
        "entropy": {
            "id": "receipt:entropy",
            "subject": copy.deepcopy(SUBJECT),
            "finding_ids": list(FINDINGS),
            "admitted": True,
            "consumer_proof": "PASS",
            "boundary_proof": "PASS",
        },
        "refactor_proof": {
            "id": "receipt:refactor",
            "subject": copy.deepcopy(SUBJECT),
            "treatments": dict(TREATMENTS),
            "capabilities": list(CAPS),
            "old_strengths": list(STRENGTHS),
            "highest_layer": "L3_HERMETIC_REAL_TASK",
            "layer_states": {
                "L0_SOURCE_FREEZE": "PASS",
                "L1_STRUCTURAL_REACHABILITY": "PASS",
                "L2_EXECUTABLE_CONTRACT": "PASS",
                "L3_HERMETIC_REAL_TASK": "PASS",
            },
        },
        "tech_lead": {
            "id": "receipt:tech-lead",
            "subject": copy.deepcopy(SUBJECT),
            "global_objective": "PASS",
            "residue_regression": "PASS",
            "relocation_check": "PASS",
            "state_recomputation_check": "PASS",
            "semantic_blast_radius": "PASS",
            "controller_authority": [],
        },
        "shadow": {
            "id": "receipt:shadow",
            "subject": copy.deepcopy(SUBJECT),
            "independent": True,
            "read_only": True,
            "verdict": "ELIGIBLE_FOR_IMPLEMENTATION",
        },
    }
    return {
        "schema_version": "universal-refactor/controller-gate-input/v1",
        "controller": controller,
        "complexity_delta": delta,
        "receipts": receipts,
        "portable_core": {"domain_values": []},
    }


def codes(value: dict) -> set[str]:
    return {item.code for item in validate_gate(value)}


class ControllerGateTest(unittest.TestCase):
    def test_positive_control_passes(self) -> None:
        self.assertEqual([], validate_gate(packet()))

    def assertMutation(self, mutate, expected: str) -> None:
        value = packet()
        mutate(value)
        self.assertIn(expected, codes(value))

    def test_missing_exact_subject(self) -> None:
        self.assertMutation(lambda p: p["controller"]["subject"].__setitem__("dirty", True), "EXACT_SUBJECT_MISSING")

    def test_subject_mismatch(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["shadow"]["subject"].__setitem__("tree", "e" * 40), "SUBJECT_MISMATCH")

    def test_missing_capability_freeze(self) -> None:
        self.assertMutation(lambda p: p["controller"].__setitem__("capabilities", []), "CAPABILITY_NOT_FROZEN")

    def test_missing_old_strength_freeze(self) -> None:
        self.assertMutation(lambda p: p["controller"].__setitem__("old_strengths", []), "OLD_STRENGTH_UNBOUND")

    def test_entropy_not_admitted(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["entropy"].__setitem__("admitted", False), "ENTROPY_FINDING_NOT_ADMITTED")

    def test_consumer_proof_missing(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["entropy"].__setitem__("consumer_proof", "NOT_EXERCISED"), "DYNAMIC_OR_PERSISTED_CONSUMER_UNPROVED")

    def test_boundary_proof_missing(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["entropy"].__setitem__("boundary_proof", "NOT_EXERCISED"), "BOUNDARY_PROOF_MISSING")

    def test_shadow_not_independent(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["shadow"].__setitem__("independent", False), "SHADOW_NOT_INDEPENDENT")

    def test_shadow_not_read_only(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["shadow"].__setitem__("read_only", False), "SHADOW_NOT_READ_ONLY")

    def test_shadow_not_eligible(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["shadow"].__setitem__("verdict", "HOLD"), "SHADOW_NOT_ELIGIBLE")

    def test_treatment_identity_mismatch(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["refactor_proof"]["treatments"].__setitem__("B1", "other"), "TREATMENT_IDENTITY_MISMATCH")

    def test_lower_evidence_promoted(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["refactor_proof"].__setitem__("highest_layer", "L2_EXECUTABLE_CONTRACT"), "LOWER_EVIDENCE_PROMOTED")

    def test_no_strict_reduction(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["dimensions"][0].__setitem__("after", 7), "NO_STRICT_COMPLEXITY_REDUCTION")

    def test_source_of_truth_growth(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["dimensions"][2].__setitem__("after", 3), "SOURCE_OF_TRUTH_ADDED")

    def test_ownership_edge_growth(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["dimensions"][3].__setitem__("after", 5), "OWNERSHIP_EDGE_HIDDEN")

    def test_sync_path_growth(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["dimensions"][4].__setitem__("after", 2), "SYNCHRONIZATION_PATH_ADDED")

    def test_policy_authority_growth(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["dimensions"][5].__setitem__("after", 3), "POLICY_AUTHORITY_ADDED")

    def test_replacement_burden_cancels_reduction(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["replacement_burden"].__setitem__("added", 10), "WRAPPER_WITH_EQUAL_OR_GREATER_BURDEN")

    def test_global_objective_not_exercised(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("global_objective", "NOT_EXERCISED"), "GLOBAL_OBJECTIVE_NOT_EXERCISED")

    def test_residue_regression_absent(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("residue_regression", "NOT_EXERCISED"), "RESIDUE_OR_REGRESSION_UNPROVED")

    def test_complexity_relocated(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("relocation_check", "COMPLEXITY_RELOCATED"), "COMPLEXITY_RELOCATED")

    def test_state_recomputed_elsewhere(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("state_recomputation_check", "FAIL"), "STATE_RECOMPUTED_IN_MULTIPLE_PLACES")

    def test_semantic_blast_radius_growth(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("semantic_blast_radius", "FAIL"), "SEMANTIC_BLAST_RADIUS_INCREASED_WITHOUT_ADMISSION")

    def test_controller_claims_merge_authority(self) -> None:
        self.assertMutation(lambda p: p["receipts"]["tech_lead"].__setitem__("controller_authority", ["MERGE"]), "CONTROLLER_AUTHORITY_WIDENED")

    def test_preservation_gap(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["capability_preservation"].pop(), "CAPABILITY_OR_OLD_STRENGTH_NOT_PRESERVED")

    def test_duplicate_dimension(self) -> None:
        def mutate(p):
            p["complexity_delta"]["dimensions"].append(copy.deepcopy(p["complexity_delta"]["dimensions"][0]))
        self.assertMutation(mutate, "DUPLICATE_COMPLEXITY_DIMENSION")

    def test_domain_value_leaks_into_portable_core(self) -> None:
        self.assertMutation(lambda p: p["portable_core"].__setitem__("domain_values", ["android"]), "DOMAIN_VALUE_IN_PORTABLE_CORE")

    def test_delta_shadow_must_match_independent_claim(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["shadow"].__setitem__("subject_match", False), "SHADOW_DELTA_INVALID")

    def test_delta_global_objective_must_pass(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"]["global_objective"].__setitem__("state", "NOT_EXERCISED"), "GLOBAL_OBJECTIVE_NOT_EXERCISED")

    def test_delta_verdict_must_pass(self) -> None:
        self.assertMutation(lambda p: p["complexity_delta"].__setitem__("verdict", "HOLD"), "DELTA_VERDICT_NOT_PASS")


if __name__ == "__main__":
    unittest.main()
