from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.render_scorecard_index import build_index, canonical


class ScorecardIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.directory = self.root / "evals" / "scorecards"
        self.directory.mkdir(parents=True)
        self.card = self.directory / "demo.json"
        self.write_card()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def value(self) -> dict:
        return {
            "schema_version": "skill-scorecard/v1",
            "skill": "demo-skill",
            "skill_sha": "a" * 40,
            "ecosystem_quality": {
                "static_valid": True,
                "provenance": True,
                "installability": True,
                "security": True,
                "documentation": False,
                "compatibility": True,
                "drift_free": True,
            },
            "verified_capability": {
                "routing_f1": 0.8,
                "task_pass_rate": 0.75,
                "skill_lift": 0.5,
                "candidate_delta": 0.4,
                "generalization_gap": 0.15,
                "cross_harness_variance": 0.03,
                "recovery_rate": 0.7,
                "safety_pass_rate": 1.0,
                "capability_unlock_count": 1,
            },
        }

    def write_card(self, mutate=None) -> None:
        value = self.value()
        if mutate:
            mutate(value)
        self.card.write_text(json.dumps(value), encoding="utf-8")

    def test_index_keeps_scorecards_separate_and_exposes_gap(self) -> None:
        result = build_index(self.root)
        self.assertEqual(len(result["scorecards"]), 1)
        entry = result["scorecards"][0]
        self.assertIn("ecosystem_quality", entry)
        self.assertIn("verified_capability", entry)
        self.assertEqual(entry["generalization_gap"], 0.15)
        self.assertEqual(entry["cross_harness_variance"], 0.03)
        self.assertNotIn("overall_score", entry)
        # Documentation can be false without being converted into or traded
        # against a capability number. The two axes remain independent facts.
        self.assertFalse(entry["ecosystem_quality"]["documentation"])
        self.assertEqual(entry["verified_capability"]["task_pass_rate"], 0.75)

    def test_overall_score_is_rejected(self) -> None:
        self.write_card(lambda value: value.update({"overall_score": 0.99}))
        with self.assertRaisesRegex(ValueError, "overall_score"):
            build_index(self.root)

    def test_missing_generalization_gap_is_rejected(self) -> None:
        self.write_card(lambda value: value["verified_capability"].update({"generalization_gap": None}))
        with self.assertRaisesRegex(ValueError, "gap and variance"):
            build_index(self.root)

    def test_generated_index_is_deterministic(self) -> None:
        first = canonical(build_index(self.root))
        second = canonical(build_index(self.root))
        self.assertEqual(first, second)

    def test_index_file_is_not_read_as_a_scorecard(self) -> None:
        (self.directory / "index.json").write_text("{not valid json", encoding="utf-8")
        result = build_index(self.root)
        self.assertEqual(len(result["scorecards"]), 1)


if __name__ == "__main__":
    unittest.main()
