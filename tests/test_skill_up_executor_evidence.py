from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "collect_skill_up_executor_evidence.py"
SHA = "a" * 40


class SkillUpExecutorEvidenceTests(unittest.TestCase):
    def run_collector(self, report: dict, baseline=False):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        report_dir = root / "reports"
        report_dir.mkdir()
        (report_dir / "report.json").write_text(json.dumps(report))
        out = root / "evidence.json"
        baseline_out = root / "baseline.json"
        argv = [
            "python3", str(SCRIPT),
            "--report-dir", str(report_dir),
            "--case-id", "case-a",
            "--condition", "candidate_skill",
            "--skill-sha", SHA,
            "--eval-suite-sha", SHA,
            "--skill", "demo-skill",
            "--engine", "codex",
            "--provider", "openai",
            "--model", "model-a",
            "--seed", "1",
            "--output", str(out),
        ]
        if baseline:
            argv += ["--baseline-output", str(baseline_out)]
        proc = subprocess.run(argv, text=True, capture_output=True)
        return td, proc, out, baseline_out

    def test_emits_non_promotable_executor_evidence(self):
        td, proc, out, _ = self.run_collector({"case_results": [{
            "case_id": "case-a", "configuration": "with_skill", "status": "pass",
            "duration_ms": 12, "input_tokens": 10, "output_tokens": 4,
        }]})
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(out.read_text())
        self.assertEqual(value["schema_version"], "skill-eval-executor-evidence/v1")
        self.assertTrue(value["outcome"]["passed"])
        self.assertFalse(value["promotion"]["eligible"])
        self.assertEqual(value["promotion"]["required_next_receipt"], "skill-eval-verifier-receipt/v1")

    def test_preserves_without_skill_denominator(self):
        td, proc, out, baseline_out = self.run_collector({"case_results": [
            {"case_id": "case-a", "configuration": "with_skill", "status": "pass"},
            {"case_id": "case-a", "configuration": "without_skill", "status": "fail"},
        ]}, baseline=True)
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        candidate = json.loads(out.read_text())
        baseline = json.loads(baseline_out.read_text())
        self.assertEqual(candidate["condition"], "candidate_skill")
        self.assertEqual(candidate["skill_sha"], SHA)
        self.assertEqual(baseline["condition"], "no_skill")
        self.assertIsNone(baseline["skill_sha"])
        self.assertFalse(baseline["outcome"]["passed"])
        self.assertNotEqual(candidate["run_id"], baseline["run_id"])

    def test_rejects_ambiguous_with_skill_results(self):
        row = {"case_id": "case-a", "configuration": "with_skill", "status": "pass"}
        td, proc, _, _ = self.run_collector({"case_results": [row, dict(row)]})
        self.addCleanup(td.cleanup)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("exactly one", proc.stderr)

    def test_rejects_unknown_status(self):
        td, proc, _, _ = self.run_collector({"case_results": [{
            "case_id": "case-a", "configuration": "with_skill", "status": "maybe"
        }]})
        self.addCleanup(td.cleanup)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unrecognized", proc.stderr)


if __name__ == "__main__":
    unittest.main()
