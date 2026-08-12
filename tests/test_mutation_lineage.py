from __future__ import annotations

import unittest

from scripts.check_mutation_lineage import validate


class MutationLineageTests(unittest.TestCase):
    def good(self):
        return {
            "schema_version": "skill-mutation/v1",
            "skill": "autoresearch-composer",
            "parent_sha": "abcdef0123456789",
            "candidate_sha": "1234567abcdef890",
            "hypothesis": "Explicit recovery before generation reduces context-loss failures.",
            "mutation_class": "recovery",
            "target_failures": ["context-loss"],
            "changed_sections": ["S5 recover"],
            "expected_effect": {"metric": "recovery_rate", "minimum_delta": 0.2, "case_ids": ["autoresearch-recover-compressed-context"]},
            "regression_budget": 0.0,
            "status": "proposed",
            "evidence_bundle": None,
            "rollback_sha": "abcdef0123456789"
        }

    def test_good_record_passes(self):
        validate(self.good())

    def test_candidate_must_differ_from_parent(self):
        value = self.good(); value["candidate_sha"] = value["parent_sha"]
        with self.assertRaisesRegex(ValueError, "differ"):
            validate(value)

    def test_rollback_must_pin_parent(self):
        value = self.good(); value["rollback_sha"] = "fedcba0987654321"
        with self.assertRaisesRegex(ValueError, "rollback"):
            validate(value)

    def test_terminal_status_requires_evidence(self):
        value = self.good(); value["status"] = "won"
        with self.assertRaisesRegex(ValueError, "evidence_bundle"):
            validate(value)

    def test_mutation_class_is_controlled(self):
        value = self.good(); value["mutation_class"] = "rewrite-everything"
        with self.assertRaisesRegex(ValueError, "mutation_class"):
            validate(value)


if __name__ == "__main__":
    unittest.main()
