"""The #235 canary cell's deterministic evaluator, run as part of the suite.

`run_canary_cell.py --selftest` is the cheap verification surface the runner
carries at its own entrypoint. Discovery-based suites cannot see a flag, so this
names it: without this file the evaluator that scores every canary receipt could
rot untouched while the suite stayed green.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_canary_cell.py"


class CanaryCellSelftest(unittest.TestCase):
    def test_selftest_admits_one_and_refuses_each_planted_mutation(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--selftest"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CANARY-CELL-SELFTEST GREEN", result.stdout)

    def test_output_is_required_for_a_real_cell(self) -> None:
        """A cell with nowhere to write its receipt must refuse, not run."""
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--consumer-index", "0"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("--output is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
