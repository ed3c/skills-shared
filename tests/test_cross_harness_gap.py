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


def repetition_row(case_id: str, condition: str, repetition: int, passed: bool, model: str, harness: str):
    return {
        "schema_version": "skill-eval-executor-evidence/v1",
        "case_id": case_id,
        "condition": condition,
        "sampling": {"repetition_index": repetition, "seed_controlled": False, "model_seed": None},
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

    def test_executor_repetitions_pair_without_fabricating_seed(self):
        rows = [
            repetition_row("a", "candidate_skill", 1, True, "m", "arena"),
            repetition_row("a", "candidate_skill", 1, False, "m", "skill-up"),
        ]
        result = summarize(rows)
        self.assertEqual(result["stack_count"], 2)
        self.assertEqual(result["paired_agreement"]["shared_identities"], 1)
        self.assertEqual(result["paired_agreement"]["disagreement_rate"], 1.0)

    def test_uncontrolled_executor_cannot_claim_model_seed(self):
        value = repetition_row("a", "candidate_skill", 1, True, "m", "skill-up")
        value["sampling"]["model_seed"] = 7
        with self.assertRaisesRegex(ValueError, "must not claim"):
            summarize([value])


if __name__ == "__main__":
    unittest.main()
