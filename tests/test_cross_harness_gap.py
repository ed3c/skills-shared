from __future__ import annotations

import unittest

from scripts.summarize_cross_harness_gap import summarize


def row(case_id: str, condition: str, seed: int, passed: bool, model: str, harness: str):
    return {
        "schema_version": "skill-eval-run/v1",
        "case_id": case_id,
        "condition": condition,
        "seed": seed,
        "model": {"name": model},
        "harness": {"name": harness},
        "outcome": {"passed": passed},
    }


class CrossHarnessGapTests(unittest.TestCase):
    def test_gap_and_pairwise_disagreement(self):
        rows = [
            row("a", "candidate_skill", 1, True, "m", "arena"),
            row("b", "candidate_skill", 1, True, "m", "arena"),
            row("a", "candidate_skill", 1, False, "m", "skill-up"),
            row("b", "candidate_skill", 1, True, "m", "skill-up"),
        ]
        result = summarize(rows)
        self.assertEqual(result["stack_count"], 2)
        self.assertEqual(result["generalization_gap_by_condition"]["candidate_skill"], 0.5)
        self.assertEqual(result["paired_agreement"]["shared_identities"], 2)
        self.assertEqual(result["paired_agreement"]["disagreement_rate"], 0.5)

    def test_single_stack_has_no_cross_harness_gap(self):
        result = summarize([row("a", "candidate_skill", 1, True, "m", "arena")])
        self.assertIsNone(result["generalization_gap_by_condition"]["candidate_skill"])
        self.assertIsNone(result["paired_agreement"]["disagreement_rate"])

    def test_duplicate_stack_identity_is_rejected(self):
        rows = [
            row("a", "candidate_skill", 1, True, "m", "arena"),
            row("a", "candidate_skill", 1, False, "m", "arena"),
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize(rows)

    def test_executor_evidence_shape_is_supported_without_promotion(self):
        value = row("a", "candidate_skill", 1, True, "m", "skill-up")
        value["schema_version"] = "skill-eval-executor-evidence/v1"
        result = summarize([value])
        self.assertEqual(result["stack_count"], 1)


if __name__ == "__main__":
    unittest.main()
