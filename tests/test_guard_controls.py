"""Contract tests for the guard-control gate.

The gate's own selftest proves it reports each shape distinctly. These prove
the committed manifest is real: every anchor resolves, exactly once, in a file
that exists, and every verify command is self-contained enough to run inside an
isolated copy.

A manifest that drifted would make the gate report "unreachable" or "absent"
forever, which is a green-adjacent state nobody reads.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "evals" / "guard-controls.json"


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.body = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_schema_and_non_empty(self) -> None:
        self.assertEqual(self.body["schema"], "guard-control-manifest/v1")
        self.assertTrue(self.body["guards"])

    def test_every_anchor_resolves_exactly_once(self) -> None:
        for guard in self.body["guards"]:
            with self.subTest(guard=guard["id"]):
                target = ROOT / guard["file"]
                self.assertTrue(target.is_file(), guard["file"])
                text = target.read_text(encoding="utf-8")
                self.assertEqual(
                    text.count(guard["anchor"]), 1,
                    f"{guard['id']}: anchor must appear exactly once",
                )

    def test_guard_ids_are_unique(self) -> None:
        ids = [guard["id"] for guard in self.body["guards"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_guard_states_why_it_matters(self) -> None:
        """An entry with no note becomes unmaintainable the day it drifts."""
        for guard in self.body["guards"]:
            with self.subTest(guard=guard["id"]):
                self.assertTrue(guard.get("note", "").strip(), guard["id"])


class GateBehaviourTests(unittest.TestCase):
    def test_selftest_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_guard_controls.py"),
             "--repo-root", str(ROOT), "--selftest"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SELFTEST GREEN", result.stdout)

    def test_an_unknown_guard_id_is_unusable_not_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_guard_controls.py"),
             "--repo-root", str(ROOT), "--only", "no-such-guard"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 64)


if __name__ == "__main__":
    unittest.main()
