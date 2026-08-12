from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_dead_assertions.py"


class DeadAssertionLinterTests(unittest.TestCase):
    def run_lint(self, body: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        path = root / "tests" / "case" / "verify.sh"
        path.parent.mkdir(parents=True)
        path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8")
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
        self.assertIn("dead-leading-bang", proc.stderr)
        self.assertIn(":3:", proc.stderr)

    def test_if_bang_is_allowed(self):
        td, proc = self.run_lint('if ! grep -q "PASS" out; then exit 1; fi\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_and_chained_tests_are_rejected(self):
        td, proc = self.run_lint('test ! -e one && test ! -e two\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("dead-and-chain", proc.stderr)

    def test_swallowed_status_is_rejected_even_if_next_line_reads_dollar_question(self):
        td, proc = self.run_lint('command_that_may_fail || true\nif test "$?" -ne 0; then exit 1; fi\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("swallowed-status", proc.stderr)

    def test_direct_rc_capture_is_allowed(self):
        td, proc = self.run_lint('rc=0\ncommand_that_may_fail || rc=$?\nif test "$rc" -ne 0; then exit 1; fi\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_discarded_grep_output_is_rejected(self):
        td, proc = self.run_lint('grep Traceback out.err > /dev/null\n')
        self.addCleanup(td.cleanup)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("discarded-grep-status", proc.stderr)


if __name__ == "__main__":
    unittest.main()
