from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_skill_eval_runtime.py"
CASE = "autoresearch-metric-loop-plan"
SHA = "1" * 40


class RuntimeExportTests(unittest.TestCase):
    def test_public_case_exports_skill_up_inputs_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: autoresearch-composer\n---\n", encoding="utf-8")
            manifest = root / "manifest.json"
            subprocess.run(
                [
                    "python3", str(SCRIPT), "--case", CASE,
                    "--condition", "candidate_skill", "--skill-sha", SHA,
                    "--engine", "codex", "--provider", "openai", "--model", "test-model",
                    "--skill-root", str(skill), "--out", str(manifest),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            value = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(value["case_id"], CASE)
            self.assertEqual(value["skill_sha"], SHA)
            self.assertEqual(value["executor"], "skill-up")
            self.assertFalse(value["promotion_authority"])
            eval_config = json.loads((skill / ".runtime-eval" / "eval.yaml").read_text(encoding="utf-8"))
            self.assertTrue(eval_config["benchmark"]["enabled"])
            self.assertEqual(eval_config["cases"]["retry_policy"]["max_retries"], 0)

    def test_commit_sha_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / "skill"; skill.mkdir()
            (skill / "SKILL.md").write_text("x", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--case", CASE, "--condition", "candidate_skill",
                 "--skill-sha", "main", "--engine", "codex", "--provider", "openai",
                 "--model", "test-model", "--skill-root", str(skill), "--out", str(root / "x.json")],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("40-character commit SHA", result.stderr)

    def test_holdout_cannot_be_exported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / "skill"; skill.mkdir()
            (skill / "SKILL.md").write_text("x", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--case", "autoresearch-holdout-no-verifier",
                 "--condition", "candidate_skill", "--skill-sha", SHA, "--engine", "codex",
                 "--provider", "openai", "--model", "test-model", "--skill-root", str(skill),
                 "--out", str(root / "x.json")], cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
