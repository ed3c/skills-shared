from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_intent_bound_constraints.py"
SPEC = importlib.util.spec_from_file_location("check_intent_bound_constraints", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE_ROOT = ROOT / "evals" / "fixtures" / "intent-bound-constraint"


class IntentBoundConstraintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract_path = FIXTURE_ROOT / "valid-contract.json"
        self.contract_raw = self.contract_path.read_bytes()
        self.contract = json.loads(self.contract_raw)
        self.receipt = json.loads((FIXTURE_ROOT / "valid-receipt.json").read_text())

    def test_positive_contract_is_green(self) -> None:
        self.assertEqual(MODULE.validate_contract(self.contract), [])

    def test_positive_receipt_is_green(self) -> None:
        self.assertEqual(MODULE.validate_receipt(self.receipt, self.contract, self.contract_raw), [])

    def test_uncovered_intent_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["meta_intents"].append({
            "id": "MI-TEST-UNUSED",
            "statement": "Detect uncovered intent.",
            "protected_property": "coverage",
            "priority": "task",
            "scope": ["fixture"],
            "forbidden_outcomes": ["silent omission"],
            "proof_obligations": ["PO-TEST-UNUSED"],
            "completion_criteria": ["constraint coverage exists"],
            "human_owned_boundaries": []
        })
        errors = MODULE.validate_contract(mutated)
        self.assertIn("uncovered meta-intent: MI-TEST-UNUSED", errors)
        self.assertIn("undischarged proof obligation: PO-TEST-UNUSED", errors)

    def test_unknown_intent_reference_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][0]["protects_intents"] = ["MI-UNKNOWN"]
        errors = MODULE.validate_contract(mutated)
        self.assertIn("C-KC-UNIQUE references unknown meta-intent MI-UNKNOWN", errors)

    def test_obligation_must_belong_to_protected_intent(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][0]["discharges_obligations"] = ["PO-KC-HUMAN"]
        errors = MODULE.validate_contract(mutated)
        self.assertTrue(any("does not protect that intent" in item for item in errors))

    def test_hard_advisory_constraint_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][0]["evidence_class"] = "advisory"
        errors = MODULE.validate_contract(mutated)
        self.assertIn("C-KC-UNIQUE is hard but relies on advisory evidence", errors)

    def test_missing_mutation_control_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][0]["mutation_controls"] = []
        errors = MODULE.validate_contract(mutated)
        self.assertIn("C-KC-UNIQUE is hard but has no mutation control", errors)

    def test_repair_without_delta_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][0]["expected_delta_metric"] = None
        errors = MODULE.validate_contract(mutated)
        self.assertIn("C-KC-UNIQUE is repairable but has no expected delta metric", errors)

    def test_module_policy_override_turns_red(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["module_policy"]["may_weaken_constraints"] = True
        errors = MODULE.validate_contract(mutated)
        self.assertIn("module_policy must be monotonic and block ambiguous routing", errors)

    def test_human_constraint_cannot_retry(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["constraints"][1]["retry_budget"] = 1
        errors = MODULE.validate_contract(mutated)
        self.assertIn("C-KC-HUMAN is human_owned and must have retry_budget 0", errors)

    def test_receipt_wrong_subject_turns_red(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["subject_identity"]["commit_sha"] = "f" * 40
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("receipt subject_identity does not match the contract subject", errors)

    def test_receipt_wrong_contract_digest_turns_red(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["contract_identity"]["contract_sha256"] = "0" * 64
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("receipt contract_sha256 does not match the exact contract bytes", errors)

    def test_receipt_repair_must_be_allowlisted(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["selected_repair"] = "WEAKEN_TEST"
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("receipt selected_repair is not allowlisted", errors)

    def test_receipt_cannot_retry_at_exhaustion(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["retry_index"] = 2
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("receipt cannot select REPAIR at or beyond retry exhaustion", errors)

    def test_no_improvement_stops_repair(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["actual_delta"] = {"after": 1, "improved": False}
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("receipt cannot continue repair after a measured no-improvement result", errors)

    def test_verified_requires_measured_improvement(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["decision"] = "VERIFIED"
        mutated["selected_repair"] = None
        errors = MODULE.validate_receipt(mutated, self.contract, self.contract_raw)
        self.assertIn("VERIFIED requires an actual_delta with improved=true", errors)

    def test_fixture_digest_is_current(self) -> None:
        expected = hashlib.sha256(self.contract_raw).hexdigest()
        self.assertEqual(self.receipt["contract_identity"]["contract_sha256"], expected)


if __name__ == "__main__":
    unittest.main()
