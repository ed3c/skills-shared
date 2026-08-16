#!/usr/bin/env python3
"""Controls for the arm-separation analysis.

The gate exists for one sentence: a metric with zero within-arm variance cannot
support a null finding about the treatment. Slice 1 read a null off exactly such
metrics and stopped a six-slice matrix on it, while the one metric that did vary
sat unanalysed in the same file. So the controls that matter are the two that
plant each half of that mistake -- a saturated metric declared primary, and a
varying metric that must not be reported as flat.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CHECKER = SKILL / "scripts" / "analyze_arm_separation.py"


def cell(arm: str, count: int, opportunities: int, **extra) -> dict:
    metrics = {"false_pass_count": count, "false_pass_opportunities": opportunities}
    metrics.update(extra)
    return {"arm": arm, "metrics": metrics}


def run(cells: list[dict] | None, *args: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "result.json"
        if cells is not None:
            path.write_text(json.dumps({"cells": cells}), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CHECKER), "--result", str(path), *args],
            capture_output=True, text=True, check=False,
        )


class ArmSeparation(unittest.TestCase):
    def test_selftest_passes(self):
        done = subprocess.run([sys.executable, str(CHECKER), "--selftest"],
                              capture_output=True, text=True, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_saturated_primary_is_refused(self):
        """The exact mistake slice 1 made: concluding from a flat metric."""
        cells = [cell(a, 5, 20, task_success=True) for a in ("x", "y") for _ in range(3)]
        done = run(cells, "--primary", "task_success")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("SEPARATION-SATURATED", done.stderr)

    def test_varying_primary_is_admitted_and_ranked(self):
        cells = ([cell("low", n, 20) for n in (4, 6, 5)]
                 + [cell("high", n, 20) for n in (9, 11, 10)])
        done = run(cells)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("low < high", done.stdout)

    def test_rate_not_count(self):
        """Equal counts over unequal opportunities are not equal performance."""
        # Same counts in both arms, twice the opportunities in one. Counts also
        # vary within each arm, so this isolates the denominator rather than
        # tripping the saturation guard.
        cells = ([cell("dense", n, 12) for n in (5, 6, 7)]
                 + [cell("sparse", n, 24) for n in (5, 6, 7)])
        done = run(cells)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("sparse < dense", done.stdout)

    def test_absent_result_is_distinct_from_a_refusal(self):
        done = run(None)
        self.assertEqual(done.returncode, 64)
        self.assertIn("SEPARATION-INVALID", done.stderr)

    def test_empty_cells_is_distinct_from_a_refusal(self):
        done = run([])
        self.assertEqual(done.returncode, 64)
        self.assertIn("carries no cells", done.stderr)

    def test_unmeasured_primary_is_invalid_not_null(self):
        """A metric nothing recorded must not read as a metric that was flat."""
        done = run([cell("x", 5, 20)], "--primary", "never_recorded")
        self.assertEqual(done.returncode, 64)
        self.assertIn("not measured", done.stderr)

    def test_committed_slice1_reproduces_the_recorded_ranking(self):
        """The correction written into the slice-1 record is recomputable from it."""
        result = SKILL / "evals" / "matrix-slice1-result.json"
        done = subprocess.run(
            [sys.executable, str(CHECKER), "--result", str(result)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(
            "current_full_composition < no_skill < candidate_trimmed_skill",
            done.stdout,
        )


if __name__ == "__main__":
    unittest.main()
