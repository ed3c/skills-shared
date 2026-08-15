from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_controlled_language_contracts.py"
SPEC = importlib.util.spec_from_file_location("check_controlled_language_contracts", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE_ROOT = ROOT / "evals" / "fixtures" / "controlled-language"


def load(name: str):
    path = FIXTURE_ROOT / name
    raw = path.read_bytes()
    return json.loads(raw), raw


class ControlledLanguageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack, self.pack_raw = load("valid-standard-pack.json")
        self.tn, self.tn_raw = load("valid-termbase-tn.json")
        self.tv, self.tv_raw = load("valid-termbase-tv.json")
        self.request, self.request_raw = load("valid-request.json")
        self.violation, _ = load("valid-violation.json")
        self.receipt, _ = load("valid-receipt.json")
        self.terms = {
            self.tn["term_id"]: (self.tn, self.tn_raw),
            self.tv["term_id"]: (self.tv, self.tv_raw),
        }

    def validate_receipt(self, receipt=None, request=None, violations=None):
        return MODULE.validate_receipt(
            receipt or self.receipt,
            request or self.request,
            self.request_raw,
            self.pack,
            self.pack_raw,
            self.terms,
            violations=[self.violation] if violations is None else violations,
        )

    def test_positive_bundle_is_green(self) -> None:
        self.assertEqual(MODULE.validate_standard_pack(self.pack), [])
        self.assertEqual(MODULE.validate_termbase_entry(self.tn), [])
        self.assertEqual(MODULE.validate_termbase_entry(self.tv), [])
        self.assertEqual(MODULE.validate_request(self.request, self.pack, self.pack_raw, self.terms), [])
        self.assertEqual(MODULE.validate_violation(self.violation, self.request), [])
        self.assertEqual(self.validate_receipt(), [])

    def test_cli_violation_subcommand_is_executable(self) -> None:
        code = MODULE.main([
            "violation",
            str(FIXTURE_ROOT / "valid-violation.json"),
            "--request",
            str(FIXTURE_ROOT / "valid-request.json"),
        ])
        self.assertEqual(code, 0)

    def test_cli_bundle_reconciles_loaded_violation(self) -> None:
        code = MODULE.main([
            "bundle",
            "--request", str(FIXTURE_ROOT / "valid-request.json"),
            "--standard-pack", str(FIXTURE_ROOT / "valid-standard-pack.json"),
            "--termbase",
            str(FIXTURE_ROOT / "valid-termbase-tn.json"),
            str(FIXTURE_ROOT / "valid-termbase-tv.json"),
            "--violation", str(FIXTURE_ROOT / "valid-violation.json"),
            "--receipt", str(FIXTURE_ROOT / "valid-receipt.json"),
        ])
        self.assertEqual(code, 0)

    def test_nonredistributable_pack_cannot_be_vendored(self) -> None:
        mutated = copy.deepcopy(self.pack)
        mutated["content_mode"] = "VENDORED"
        errors = MODULE.validate_standard_pack(mutated)
        self.assertIn("non-redistributable standard pack cannot use VENDORED content_mode", errors)

    def test_official_claim_policy_cannot_be_weakened(self) -> None:
        mutated = copy.deepcopy(self.pack)
        mutated["compliance_claim_policy"] = "AUTOMATIC"
        errors = MODULE.validate_standard_pack(mutated)
        self.assertIn("official compliance claims must remain HUMAN_ADMIT_REQUIRED", errors)

    def test_missing_term_id_turns_red(self) -> None:
        mutated = copy.deepcopy(self.tn)
        mutated.pop("term_id")
        errors = MODULE.validate_termbase_entry(mutated)
        self.assertIn("termbase term_id must start with TERM-", errors)

    def test_admitted_term_requires_human_receipt(self) -> None:
        mutated = copy.deepcopy(self.tn)
        mutated["human_review"] = {
            "state": "REQUIRED",
            "approval_receipt_ref": None,
            "approval_receipt_digest": None,
        }
        errors = MODULE.validate_termbase_entry(mutated)
        self.assertIn("ADMITTED term requires Human review state ADMITTED", errors)

    def test_admitted_technical_verb_rejects_available_general_replacement(self) -> None:
        mutated = copy.deepcopy(self.tv)
        mutated["replacement_assessment"] = "REPLACEMENT_AVAILABLE"
        errors = MODULE.validate_termbase_entry(mutated)
        self.assertIn("ADMITTED technical verb requires NO_APPROVED_GENERAL_VERB assessment", errors)

    def test_unsafe_profile_path_turns_red(self) -> None:
        mutated = copy.deepcopy(self.request)
        mutated["profile_reference"]["path"] = "/Users/neon/private-pack.json"
        errors = MODULE.validate_request(mutated, self.pack, self.pack_raw, self.terms)
        self.assertIn("request profile path must be repository-relative", errors)

    def test_invalid_repair_code_turns_red(self) -> None:
        mutated = copy.deepcopy(self.request)
        mutated["repair_policy"]["allowed_repair_codes"].append("WEAKEN_CONSTRAINT")
        errors = MODULE.validate_request(mutated, self.pack, self.pack_raw, self.terms)
        self.assertIn("repair allowed_repair_codes are invalid or duplicated", errors)

    def test_restricted_text_cannot_leave_local_lane(self) -> None:
        mutated = copy.deepcopy(self.request)
        mutated["privacy"] = {
            "classification": "RESTRICTED",
            "execution_lane": "EXTERNAL_APPROVED",
            "allow_network": True,
            "human_external_processing_approval": "ADMITTED",
        }
        errors = MODULE.validate_request(mutated, self.pack, self.pack_raw, self.terms)
        self.assertIn("RESTRICTED text must remain LOCAL_ONLY with network disabled", errors)

    def test_warning_requires_human_evidence(self) -> None:
        mutated = copy.deepcopy(self.request)
        mutated["document_class"] = "WARNING"
        mutated["requested_evidence_classes"] = ["DETERMINISTIC", "SEMANTIC"]
        errors = MODULE.validate_request(mutated, self.pack, self.pack_raw, self.terms)
        self.assertIn("WARNING and CAUTION requests must include HUMAN evidence", errors)

    def test_violation_span_digest_must_match_inline_bytes(self) -> None:
        mutated = copy.deepcopy(self.violation)
        mutated["source_span"]["found_text_digest"] = "sha256:" + "0" * 64
        errors = MODULE.validate_violation(mutated, self.request)
        self.assertIn("violation found_text_digest does not match exact INLINE span", errors)

    def test_receipt_wrong_request_digest_turns_red(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["request_identity"]["artifact_digest"] = "sha256:" + "0" * 64
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("receipt request artifact_digest does not match exact request bytes", errors)

    def test_receipt_wrong_subject_turns_red(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["subject_identity"]["artifact_digest"] = "sha256:" + "0" * 64
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("receipt subject_identity does not match request subject", errors)

    def test_evaluator_input_digest_must_match_subject(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["evaluator_runs"][0]["input_digest"] = "sha256:" + "0" * 64
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("evaluator fixture-deterministic-linter input_digest does not match exact subject", errors)

    def test_evaluator_output_digest_must_be_exact(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["evaluator_runs"][0]["output_digest"] = "not-a-digest"
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("evaluator fixture-deterministic-linter output_digest is invalid", errors)

    def test_deterministic_failure_vetoes_semantic_pass(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        deterministic = next(
            run for run in mutated["evaluator_runs"] if run["evidence_class"] == "DETERMINISTIC"
        )
        deterministic["status"] = "FAIL"
        deterministic["exit_code"] = 2
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("deterministic failure or nonzero exit vetoes final PASS", errors)

    def test_not_exercised_requested_lane_vetoes_pass(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        semantic = next(
            run for run in mutated["evaluator_runs"] if run["evidence_class"] == "SEMANTIC"
        )
        semantic["status"] = "NOT_EXERCISED"
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("requested evidence class SEMANTIC is not fully PASS", errors)

    def test_stale_subject_vetoes_pass(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["exact_subject_fresh"] = False
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("stale or unproven subject cannot receive final PASS", errors)

    def test_receipt_must_account_for_loaded_violation(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["violations"] = {
            "open_count": 0,
            "repaired_count": 0,
            "blocked_count": 0,
            "waived_count": 0,
            "violation_ids": [],
        }
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("receipt violation identity set mismatch", errors)
        self.assertIn("receipt REPAIRED violation count mismatch", errors)

    def test_open_loaded_violation_vetoes_pass(self) -> None:
        open_violation = copy.deepcopy(self.violation)
        open_violation["status"] = "OPEN"
        open_violation["candidate_rewrite"] = None
        mutated = copy.deepcopy(self.receipt)
        mutated["violations"] = {
            "open_count": 1,
            "repaired_count": 0,
            "blocked_count": 0,
            "waived_count": 0,
            "violation_ids": [open_violation["violation_id"]],
        }
        errors = self.validate_receipt(receipt=mutated, violations=[open_violation])
        self.assertIn("open or blocked violations veto final PASS", errors)

    def test_warning_cannot_pass_without_human_admit(self) -> None:
        request = copy.deepcopy(self.request)
        request["document_class"] = "WARNING"
        receipt = copy.deepcopy(self.receipt)
        receipt["human_review"] = {"state": "REQUIRED", "receipt_ref": None, "receipt_digest": None}
        receipt["claim_level"] = "PROFILE_CONFORMANCE_CANDIDATE"
        human = next(run for run in receipt["evaluator_runs"] if run["evidence_class"] == "HUMAN")
        human["status"] = "NOT_EXERCISED"
        human["human_receipt_ref"] = None
        errors = self.validate_receipt(receipt=receipt, request=request)
        self.assertIn("WARNING or CAUTION cannot PASS without admitted Human review", errors)

    def test_official_compliance_requires_exact_human_receipt(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["claim_level"] = "OFFICIAL_COMPLIANCE"
        mutated["official_compliance_receipt"] = None
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("OFFICIAL_COMPLIANCE requires official_compliance_receipt", errors)

    def test_no_improvement_stops_repair(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["repair_history"] = [
            {
                "attempt_index": 1,
                "failed_constraint_ids": ["C-CTL-WORD-LIMIT"],
                "selected_repair": "SPLIT_ACTION",
                "expected_delta": {"metric": "violation_count", "before": 1, "target": 0},
                "actual_delta": {"metric": "violation_count", "after": 1, "improved": False},
                "decision": "REPAIR",
            }
        ]
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("measured no improvement requires STOP", errors)

    def test_final_pass_after_repair_requires_verified_terminal(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["repair_history"] = [
            {
                "attempt_index": 1,
                "failed_constraint_ids": ["C-CTL-WORD-LIMIT"],
                "selected_repair": "SPLIT_ACTION",
                "expected_delta": {"metric": "violation_count", "before": 1, "target": 0},
                "actual_delta": {"metric": "violation_count", "after": 0, "improved": True},
                "decision": "REPAIR",
            }
        ]
        errors = self.validate_receipt(receipt=mutated)
        self.assertIn("final PASS after repair requires terminal VERIFIED decision", errors)

    def test_private_reasoning_field_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.receipt)
        mutated["reasoning_trace"] = "hidden internal reasoning"
        errors = self.validate_receipt(receipt=mutated)
        self.assertTrue(any("must not persist private reasoning" in error for error in errors))

    def test_fixture_digests_are_exact(self) -> None:
        self.assertEqual(
            self.request["profile_reference"]["artifact_digest"],
            "sha256:" + hashlib.sha256(self.pack_raw).hexdigest(),
        )
        expected_terms = {
            self.tn["term_id"]: "sha256:" + hashlib.sha256(self.tn_raw).hexdigest(),
            self.tv["term_id"]: "sha256:" + hashlib.sha256(self.tv_raw).hexdigest(),
        }
        self.assertEqual(
            {item["term_id"]: item["artifact_digest"] for item in self.request["termbase_references"]},
            expected_terms,
        )
        self.assertEqual(
            self.receipt["request_identity"]["artifact_digest"],
            "sha256:" + hashlib.sha256(self.request_raw).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
