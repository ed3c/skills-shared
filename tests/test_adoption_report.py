"""Controls for the generated cross-Skill adoption report.

`--check` is the only thing standing between "a projection of the ledger" and
"a second ledger that drifts". So it gets the same treatment as any other
guard: prove it is green on the committed bytes, and prove it goes red when
the report and the ledger disagree -- in both directions, because a renderer
that ignores its input is as green as one that works.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER = ROOT / "skills" / "skill-refactor-proof-loop" / "scripts" / "render_adoption_report.py"
LEDGER = ROOT / "skills" / "skill-refactor-proof-loop" / "references" / "skill-adoption-ledger.json"
REPORT = ROOT / "docs" / "traceability" / "SKILL_ADOPTION_AUDIT.md"


def check(output: Path, ledger: Path = LEDGER) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDERER), "--check",
         "--ledger", str(ledger), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )


class AdoptionReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="adoption-report.")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def test_committed_report_is_fresh(self) -> None:
        result = check(REPORT)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_edited_report_is_stale(self) -> None:
        copy = self.work / "report.md"
        shutil.copyfile(REPORT, copy)
        copy.write_text(
            copy.read_text(encoding="utf-8").replace("`ABSENT`", "`PASS`", 1),
            encoding="utf-8",
        )
        result = check(copy)
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
        self.assertIn("ADOPTION REPORT STALE", result.stderr)

    def test_changed_ledger_makes_the_report_stale(self) -> None:
        """The other direction: the report must track the ledger, not survive it."""
        ledger = self.work / "ledger.json"
        document = json.loads(LEDGER.read_text(encoding="utf-8"))
        criteria = document["skills"][0]["criteria"]
        criteria[sorted(criteria)[0]]["state"] = "ABSENT"
        ledger.write_text(json.dumps(document, indent=2), encoding="utf-8")
        result = check(REPORT, ledger=ledger)
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)

    def test_absent_report_is_stale_not_green(self) -> None:
        result = check(self.work / "never-written.md")
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
        self.assertIn("is absent", result.stderr)

    def test_render_is_idempotent(self) -> None:
        first = self.work / "a.md"
        second = self.work / "b.md"
        for output in (first, second):
            result = subprocess.run(
                [sys.executable, str(RENDERER),
                 "--ledger", str(LEDGER), "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(
            first.read_bytes(), second.read_bytes(), "the renderer is not deterministic"
        )


if __name__ == "__main__":
    unittest.main()
