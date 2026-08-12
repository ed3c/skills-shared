from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_dead_assertions.py"


class DeadAssertionCompatibilityTests(unittest.TestCase):
    def run_lint(self, body: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        path = root / "tests" / "case" / "verify.sh"
        path.parent.mkdir(parents=True)
        path.write_text("#!/usr/bin/env bash\nset -eEuo pipefail\n" + body, encoding="utf-8")
        proc = subprocess.run(
            ["python3", str(SCRIPT), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        return td, proc

    def test_good_explicit_assertions_pass(self):
        td, proc = self.run_lint(
            "if grep -q Traceback out.err; then echo bad >&2; exit 1; fi\n"
            "test ! -e one\n"
            "test ! -e two\n"
        )
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_leading_bang_is_rejected(self):
        td, proc = self.run_lint('! grep -q "Traceback" out.err\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DEAD-NEGATION", proc.stderr)

    def test_if_bang_is_allowed(self):
        td, proc = self.run_lint('if ! grep -q "PASS" out; then exit 1; fi\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_and_chained_assertions_are_rejected(self):
        td, proc = self.run_lint('test ! -e one && test ! -e two\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DEAD-AND-CHAIN", proc.stderr)

    def test_assertion_swallowed_by_true_is_rejected(self):
        td, proc = self.run_lint('grep -q expected out || true\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DEAD-SWALLOW", proc.stderr)

    def test_best_effort_effect_command_is_allowed(self):
        td, proc = self.run_lint('mkdir -p optional-dir || true\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_redirected_grep_under_errexit_is_live(self):
        td, proc = self.run_lint('grep expected out > /dev/null\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_redirected_grep_in_set_plus_e_is_rejected(self):
        td, proc = self.run_lint('set +e\ngrep expected out > /dev/null\nset -e\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DEAD-DISCARD", proc.stderr)


if __name__ == "__main__":
    unittest.main()
