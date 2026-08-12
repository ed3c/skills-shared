from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "evals" / "adapters" / "build_evidence_bundle.py"


class VerifierAuthorityTests(unittest.TestCase):
    def fixture(self, authority="deterministic", passed=True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        run = root / "run.json"
        receipt = root / "receipt.json"
        out = root / "bundle.json"
        run_value = {
            "schema_version": "skill-eval-run/v1",
            "run_id": "run-12345678",
            "case_id": "holdout-0",
            "skill_sha": "a" * 40,
        }
        run.write_text(json.dumps(run_value))
        receipt.write_text(json.dumps({
            "schema_version": "skill-eval-verifier-receipt/v1",
            "run_id": run_value["run_id"],
            "case_id": run_value["case_id"],
            "authority": authority,
            "verifier": {
                "kind": "script",
                "implementation_sha256": hashlib.sha256(b"verifier").hexdigest(),
            },
            "passed": passed,
            "input_digest": hashlib.sha256(b"inputs").hexdigest(),
        }))
        return td, run, receipt, out

    def run_builder(self, run: Path, receipt: Path, out: Path):
        return subprocess.run([
            "python3", str(BUILDER),
            "--run-trace", str(run),
            "--verifier-receipt", str(receipt),
            "--eval-suite-sha", "b" * 40,
            "--output", str(out),
        ], text=True, capture_output=True)

    def test_deterministic_passing_receipt_builds_promotable_bundle(self):
        td, run, receipt, out = self.fixture()
        self.addCleanup(td.cleanup)
        proc = self.run_builder(run, receipt, out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(out.read_text())
        self.assertTrue(value["promotion_eligible"])
        self.assertEqual(value["verifier_receipt_sha256"], hashlib.sha256(receipt.read_bytes()).hexdigest())

    def test_llm_judge_receipt_is_rejected(self):
        td, run, receipt, out = self.fixture(authority="llm_judge")
        self.addCleanup(td.cleanup)
        proc = self.run_builder(run, receipt, out)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("deterministic verifier authority", proc.stderr)

    def test_failed_deterministic_receipt_is_rejected(self):
        td, run, receipt, out = self.fixture(passed=False)
        self.addCleanup(td.cleanup)
        proc = self.run_builder(run, receipt, out)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("passing verifier receipt", proc.stderr)

    def test_mismatched_run_identity_is_rejected(self):
        td, run, receipt, out = self.fixture()
        self.addCleanup(td.cleanup)
        value = json.loads(receipt.read_text())
        value["run_id"] = "other-run-12345678"
        receipt.write_text(json.dumps(value))
        proc = self.run_builder(run, receipt, out)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("run_id does not match", proc.stderr)


if __name__ == "__main__":
    unittest.main()
