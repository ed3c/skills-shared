from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]


class DocumentRouteDiagnosticTests(unittest.TestCase):
    def test_repository_document_routes_are_green(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_document_routes.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            0,
            result.returncode,
            msg="document-route diagnostic\nSTDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
