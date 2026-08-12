from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "check_verifier_calibrations.py"


class VerifierCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "evals" / "cases" / "demo").mkdir(parents=True)
        (self.root / "evals" / "verifiers").mkdir(parents=True)
        (self.root / "evals" / "calibration" / "positive").mkdir(parents=True)
        (self.root / "evals" / "calibration" / "negative").mkdir(parents=True)
        shutil.copy2(SOURCE, self.root / "scripts" / "check_verifier_calibrations.py")
        (self.root / "evals" / "calibration" / "positive" / "valid.txt").write_text("yes\n")
        (self.root / "evals" / "verifiers" / "verify.py").write_text(
            "from pathlib import Path\nraise SystemExit(0 if Path('valid.txt').is_file() else 1)\n",
            encoding="utf-8",
        )
        self.case_path = self.root / "evals" / "cases" / "demo" / "gold.json"
        self.write_case()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_case(self, **overrides) -> None:
        value = {
            "schema_version": "skill-eval/v1",
            "id": "gold-case",
            "split": "gold-replay",
            "verifier": {
                "type": "script",
                "command": "python3 evals/verifiers/verify.py",
            },
            "calibration": {
                "positive_fixture": "evals/calibration/positive",
                "negative_fixtures": ["evals/calibration/negative"],
            },
        }
        value.update(overrides)
        self.case_path.write_text(json.dumps(value), encoding="utf-8")

    def run_gate(self):
        return subprocess.run(
            ["python3", str(self.root / "scripts" / "check_verifier_calibrations.py"), "--root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_discriminating_verifier_passes(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS verifier calibration", result.stdout)

    def test_always_pass_shape_is_rejected_by_negative_fixture(self):
        (self.root / "evals" / "calibration" / "negative" / "valid.txt").write_text("yes\n")
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hollow calibration unexpectedly passed", result.stderr)

    def test_positive_fixture_must_really_pass(self):
        (self.root / "evals" / "calibration" / "positive" / "valid.txt").unlink()
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("positive calibration failed", result.stderr)

    def test_gold_replay_without_calibration_fails(self):
        self.write_case(calibration=None)
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires calibration metadata", result.stderr)

    def test_arbitrary_shell_pipeline_is_rejected(self):
        self.write_case(
            verifier={
                "type": "script",
                "command": "python3 evals/verifiers/verify.py && echo forged",
            }
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("calibration permits only direct", result.stderr)

    def test_fixture_escape_is_rejected(self):
        self.write_case(
            calibration={
                "positive_fixture": "../outside",
                "negative_fixtures": ["evals/calibration/negative"],
            }
        )
        result = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escapes repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
