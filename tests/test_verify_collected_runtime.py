from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_collected_runtime.py"


class VerifyCollectedRuntimeTests(unittest.TestCase):
    def workspace(self, include_guard=True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "evidence").mkdir()
        (root / "artifacts").mkdir()
        contract = {
            "Goal": "improve lint pass rate",
            "Scope": "bounded files",
            "Metric": "lint pass rate",
            "Direction": "maximize",
            "Verify": "run numeric lint verifier",
            "Guard": "preserve invariant" if include_guard else "",
            "Iterations": 3,
        }
        (root / "artifacts" / "iteration-contract.json").write_text(json.dumps(contract))
        (root / "evidence" / "run.json").write_text(json.dumps({
            "case_id": "autoresearch-metric-loop-plan",
            "decision": "invoke",
            "selected_skill": "autoresearch-composer",
            "plan_artifact": "artifacts/iteration-contract.json",
        }))
        return td, root

    def run_verify(self, workspace: Path):
        receipt = workspace / "receipt.json"
        proc = subprocess.run([
            "python3", str(SCRIPT),
            "--case", "autoresearch-metric-loop-plan",
            "--workspace", str(workspace),
            "--run-id", "run-12345678",
            "--output", str(receipt),
        ], text=True, capture_output=True)
        return proc, receipt

    def test_pass_emits_deterministic_receipt(self):
        td, workspace = self.workspace()
        self.addCleanup(td.cleanup)
        proc, receipt = self.run_verify(workspace)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(receipt.read_text())
        self.assertEqual(value["authority"], "deterministic")
        self.assertTrue(value["passed"])
        self.assertEqual(len(value["verifier"]["implementation_sha256"]), 64)
        self.assertEqual(len(value["input_digest"]), 64)
        logs = json.loads(receipt.with_suffix(".json.logs.json").read_text())
        self.assertEqual(logs["exit_code"], 0)

    def test_failed_contract_still_emits_failed_receipt(self):
        td, workspace = self.workspace(include_guard=False)
        self.addCleanup(td.cleanup)
        proc, receipt = self.run_verify(workspace)
        self.assertEqual(proc.returncode, 1)
        value = json.loads(receipt.read_text())
        self.assertFalse(value["passed"])
        self.assertTrue(receipt.with_suffix(".json.logs.json").is_file())

    def test_missing_artifact_fails_closed_without_receipt(self):
        td, workspace = self.workspace()
        self.addCleanup(td.cleanup)
        (workspace / "evidence" / "run.json").unlink()
        proc, receipt = self.run_verify(workspace)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("required verifier input missing", proc.stderr)
        self.assertFalse(receipt.exists())


if __name__ == "__main__":
    unittest.main()
