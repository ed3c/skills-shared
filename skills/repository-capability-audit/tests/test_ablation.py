from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryCapabilityAuditAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        output = Path(cls._temp.name) / "out"
        process = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_ablation.py"), "--output", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise AssertionError(process.stderr + process.stdout)
        cls.report = json.loads((output / "effectiveness.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    def test_candidate_outperforms_no_skill_without_losing_full_outcome(self):
        profiles = self.report["profiles"]
        self.assertEqual(profiles["candidate_trimmed_skill"]["metrics"]["score"], 1.0)
        self.assertEqual(
            profiles["candidate_trimmed_skill"]["metrics"],
            profiles["current_full_composition"]["metrics"],
        )
        self.assertLess(
            profiles["no_skill"]["metrics"]["defect_recall"],
            profiles["candidate_trimmed_skill"]["metrics"]["defect_recall"],
        )
        self.assertGreater(profiles["no_skill"]["metrics"]["false_pass_count"], 0)

    def test_every_retained_rule_has_a_deciding_ablation(self):
        self.assertEqual(self.report["core_supported_fraction"], 1.0)
        for rule_id, result in self.report["ablations"].items():
            self.assertTrue(result["effective"], rule_id)
            self.assertLess(result["score_delta"], 0, rule_id)
            self.assertTrue(result["affected_cases"], rule_id)

    def test_dependency_fraction_is_semantic_claim_count_not_token_count(self):
        dependency = self.report["source_effectiveness"]["dependency_aggregate"]
        self.assertEqual(dependency["supported"], 14)
        self.assertEqual(dependency["total"], 25)
        self.assertEqual(dependency["supported_fraction"], 0.56)
        self.assertGreater(self.report["procedure_reduction_fraction"], 0)

    def test_real_runtime_receipt_is_bounded(self):
        contract = json.loads((ROOT / "evals" / "contract.json").read_text(encoding="utf-8"))
        receipt = contract["observed_external_trace"]
        self.assertEqual(receipt["observed_result"]["required_pass"], 16)
        self.assertEqual(receipt["observed_result"]["required_total"], 16)
        self.assertEqual(len(receipt["material_defects_exposed"]), 5)
        self.assertIn("does not isolate", receipt["boundary"])


if __name__ == "__main__":
    unittest.main()
