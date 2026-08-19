from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "assert_entropy_audit.py"
SPEC = importlib.util.spec_from_file_location("assert_entropy_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EntropyAuditGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = MODULE.load_validator()
        cls.base = json.loads(
            (SKILL_ROOT / "references" / "example-audit.json").read_text(encoding="utf-8")
        )

    def errors(self, document: dict) -> list[str]:
        return MODULE.validate_document(document, validator=self.validator)

    def mutated(self) -> dict:
        return copy.deepcopy(self.base)

    def assert_rejected(self, document: dict, fragment: str) -> None:
        errors = self.errors(document)
        self.assertTrue(errors, "planted defect survived")
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected {fragment!r} in {errors!r}",
        )

    def test_positive_example(self) -> None:
        self.assertEqual([], self.errors(self.base))

    def test_dirty_subject_is_rejected(self) -> None:
        doc = self.mutated()
        doc["subject"]["dirty"] = True
        self.assert_rejected(doc, "subject.dirty")

    def test_absolute_target_is_rejected(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["targets"] = ["/tmp/outside"]
        self.assert_rejected(doc, "safe repository-relative path")

    def test_unknown_boundary_is_rejected(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["boundary_ids"] = ["BOUNDARY_UNKNOWN"]
        self.assert_rejected(doc, "unknown boundaries")

    def test_production_consumer_blocks_change(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["consumers"]["production"] = copy.deepcopy(
            doc["candidates"][0]["consumers"]["non_production"]
        )
        self.assert_rejected(doc, "production consumers")

    def test_ambiguous_consumer_blocks_change(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["consumers"]["ambiguous"] = copy.deepcopy(
            doc["candidates"][0]["consumers"]["non_production"]
        )
        self.assert_rejected(doc, "ambiguous consumers")

    def test_unexercised_dynamic_check_blocks_change(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["checks"]["dynamic_reachability"] = "NOT_EXERCISED"
        self.assert_rejected(doc, "dynamic_reachability")

    def test_protected_boundary_blocks_automatic_change(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["boundary_ids"] = ["BOUNDARY_RESOURCE_STOP"]
        self.assert_rejected(doc, "protected/Human boundaries")

    def test_unknown_capability_effect_blocks_change(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["capability_effect"] = "UNKNOWN"
        self.assert_rejected(doc, "capability_effect=NONE_OBSERVABLE")

    def test_zero_conceptual_reduction_is_rejected(self) -> None:
        doc = self.mutated()
        reduction = doc["candidates"][0]["reduction"]
        reduction["concepts_removed"] = []
        reduction["states_removed"] = []
        self.assert_rejected(doc, "removes no concept")

    def test_replacement_complexity_cannot_equal_reduction(self) -> None:
        doc = self.mutated()
        doc["candidates"][0]["reduction"]["concepts_added"] = [
            "wrapper A",
            "wrapper B",
        ]
        self.assert_rejected(doc, "not conceptually net-negative")

    def test_shadow_must_be_independent(self) -> None:
        doc = self.mutated()
        doc["shadow_review"]["independent"] = False
        self.assert_rejected(doc, "independent must be true")

    def test_shadow_cannot_write_target(self) -> None:
        doc = self.mutated()
        doc["shadow_review"]["writes_target"] = True
        self.assert_rejected(doc, "not a second writer")

    def test_shadow_subject_must_match(self) -> None:
        doc = self.mutated()
        doc["shadow_review"]["subject_commit"] = "f" * 40
        self.assert_rejected(doc, "must match subject.commit")

    def test_apply_promotion_requires_asserted_delivery(self) -> None:
        doc = self.mutated()
        doc["delivery"]["state"] = "BLOCKED"
        self.assert_rejected(doc, "ASSERTED delivery")

    def test_verified_verdict_requires_decisive_pass(self) -> None:
        doc = self.mutated()
        doc["verification"]["decisive"] = "NOT_EXERCISED"
        self.assert_rejected(doc, "verification.decisive=PASS")

    def test_audit_mode_cannot_select_mutation(self) -> None:
        doc = self.mutated()
        doc["mode"] = "AUDIT"
        doc["verdict"] = "AUDIT_COMPLETE"
        self.assert_rejected(doc, "AUDIT mode cannot select")

    def test_handoff_requires_queue_subject(self) -> None:
        doc = self.mutated()
        doc["local_handoff"]["required"] = True
        doc["local_handoff"]["queue_subject"] = None
        self.assert_rejected(doc, "requires queue_subject")


if __name__ == "__main__":
    unittest.main()
