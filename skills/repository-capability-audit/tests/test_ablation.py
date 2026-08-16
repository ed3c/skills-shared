from __future__ import annotations

import hashlib
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

    def test_receipts_do_not_silently_claim_stale_repository_state(self):
        # A receipt that names a repository file by digest is asserting something
        # about this tree, not only about the run that produced it. When the file
        # moves on, that assertion becomes false in place -- the receipt still reads
        # as green and nothing recomputes it. Regenerating the receipt is not the
        # fix either: it was produced on a different runtime, and this repository
        # does not accept one host's evidence as another's. So a receipt whose claim
        # no longer matches must say so explicitly.
        receipts = sorted((ROOT / "evals" / "receipts").glob("*.json"))
        self.assertTrue(receipts, "no runtime receipts found to check")
        report = ROOT / "evals" / "expected" / "effectiveness.json"
        current = hashlib.sha256(report.read_bytes()).hexdigest()

        for path in receipts:
            data = json.loads(path.read_text(encoding="utf-8"))
            # This directory holds more than one receipt shape: an ablation receipt
            # keys `artifacts` by name, while an agent-cell receipt uses it for a
            # file manifest list. Assuming one shape is how this guard broke the
            # first time an agent-cell receipt landed beside it -- the same
            # unverified-shape assumption it exists to catch elsewhere.
            artifacts = data.get("artifacts")
            if not isinstance(artifacts, dict):
                continue
            claimed = artifacts.get("committed_expected_report_sha256")
            if claimed is None or claimed == current:
                continue
            superseded = data.get("superseded")
            self.assertIsNotNone(
                superseded,
                f"{path.name} claims committed_expected_report_sha256={claimed} but "
                f"evals/expected/effectiveness.json is now {current}. Mark the receipt "
                f"superseded (with the observed digest and a reason) or replay it on a "
                f"qualifying runtime -- do not leave a false green claim in the tree.",
            )
            self.assertEqual(
                superseded.get("observed_expected_report_sha256"),
                claimed,
                f"{path.name}: superseded block must record the digest the receipt "
                f"actually observed, so the historical claim stays auditable",
            )
            self.assertTrue(
                str(superseded.get("reason", "")).strip(),
                f"{path.name}: superseded block needs a reason",
            )


if __name__ == "__main__":
    unittest.main()
