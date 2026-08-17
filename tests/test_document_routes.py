"""Planted-defect controls for the document-routing gate.

Every assertion `scripts/check_document_routes.py` implements gets one defect
planted into a throwaway copy of the real tree, and the gate must go red on it.
A routing check that runs on a green tree and has never been observed failing
is the same unfalsifiable shape the gate was written to kill -- #322's
"Markdown-only route counted as executable", one layer up.

The subject is a copy of this repository rather than a synthetic fixture,
because a fixture proves the gate can fail on a tree nobody ships. The copy
carries no `.git`, which is also how `check_guard_controls.py` isolates its
mutations, so every command here has to be self-contained.

`check_guard_controls.py` additionally strips `.claude` from its copy, which
means no route in this tree may depend on a `.claude` path: two snapshot links
did, and they made the routing gate report a defect that only exists inside the
isolation harness. They are code spans now. The rule this leaves behind is that
a governed route resolves against repository content, never against host
configuration that a harness is entitled to remove.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = Path("docs/INDEX.md")


class RouteGateTests(unittest.TestCase):
    """Each test mutates the copy and restores it, so order cannot matter."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory(prefix="document-routes.")
        cls.work = Path(cls._temp.name) / "repo"
        shutil.copytree(
            ROOT,
            cls.work,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    def run_gate(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/check_document_routes.py"],
            cwd=self.work,
            capture_output=True,
            text=True,
            check=False,
        )

    def plant(self, relative: str, mutate) -> None:
        """Apply `mutate` to one file and restore it when the test ends."""
        path = self.work / relative
        original = path.read_text(encoding="utf-8") if path.exists() else None
        self.addCleanup(
            lambda: path.write_text(original, encoding="utf-8")
            if original is not None
            else path.unlink(missing_ok=True)
        )
        mutate(path)

    def assert_red(self, marker: str) -> None:
        result = self.run_gate()
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(marker, result.stderr)

    # -- the tree as committed -------------------------------------------

    def test_committed_tree_is_green(self) -> None:
        """Without a baseline pass, a red result proves nothing about the defect."""
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("DOCUMENT ROUTES GREEN", result.stdout)

    # -- DR-01 ------------------------------------------------------------

    def test_missing_standard_route_is_red(self) -> None:
        target = self.work / "ARCHITECTURE.md"
        body = target.read_text(encoding="utf-8")
        self.addCleanup(lambda: target.write_text(body, encoding="utf-8"))
        target.unlink()
        self.assert_red("DR-01")

    def test_removed_route_authority_block_is_unusable_not_green(self) -> None:
        """An absent declaration is a distinct state, never a satisfied one."""
        self.plant(
            "AGENTS.md",
            lambda path: path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "## Document-route authority", "## Document-route notes"
                ),
                encoding="utf-8",
            ),
        )
        result = self.run_gate()
        self.assertEqual(result.returncode, 64, msg=result.stdout + result.stderr)
        self.assertIn("DOCUMENT ROUTES UNUSABLE", result.stderr)

    # -- DR-02 ------------------------------------------------------------

    def test_dead_relative_link_is_red(self) -> None:
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8")
                + "\n- [`gone.md`](architecture/GONE.md) — never existed.\n",
                encoding="utf-8",
            ),
        )
        self.assert_red("DR-02")

    def test_link_into_an_archive_surface_is_not_governed(self) -> None:
        """The archive exclusion comes from the body-neutrality owner, not from here.

        If this gate grew its own list, the two would drift and the repository
        would hold two answers to "is this file a live route".
        """
        archive = self.work / "docs" / "superseded"
        archive.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(archive, ignore_errors=True))
        (archive / "OLD.md").write_text(
            "# Superseded\n\n[gone](./NEVER_EXISTED.md)\n", encoding="utf-8"
        )
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    # -- DR-06 ------------------------------------------------------------

    def test_machine_local_link_target_is_red(self) -> None:
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8")
                + "\n- [local](file:///Users/someone/checkout/AGENTS.md)\n",
                encoding="utf-8",
            ),
        )
        self.assert_red("DR-06")

    # -- DR-03 ------------------------------------------------------------

    def test_skill_directory_with_neither_readme_nor_skill_is_red(self) -> None:
        """`external-verify` has no README; the inheritance covers it only while
        it actually ships the single procedural body the inheritance names."""
        target = self.work / "skills" / "external-verify" / "SKILL.md"
        body = target.read_text(encoding="utf-8")
        self.addCleanup(lambda: target.write_text(body, encoding="utf-8"))
        target.unlink()
        self.assert_red("DR-03")

    # -- DR-13 ------------------------------------------------------------

    def test_dropped_index_row_is_red(self) -> None:
        """Deleting a route row is the omission that looks exactly like completeness."""
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                "\n".join(
                    line
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if "../skills/repo-agent-native/README.md" not in line
                )
                + "\n",
                encoding="utf-8",
            ),
        )
        self.assert_red("DR-13")

    def test_stale_stated_count_is_red(self) -> None:
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "12 of 31 skill directories", "11 of 30 skill directories"
                ),
                encoding="utf-8",
            ),
        )
        self.assert_red("DR-13")

    def test_new_skill_readme_left_unnamed_is_red(self) -> None:
        directory = self.work / "skills" / "invented-for-this-test"
        directory.mkdir()
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        (directory / "README.md").write_text("# Invented\n", encoding="utf-8")
        (directory / "SKILL.md").write_text("# Invented\n", encoding="utf-8")
        self.assert_red("is not named there as a known omission")

    def test_removed_count_sentence_is_unusable_not_green(self) -> None:
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "12 of 31 skill directories ship a", "several skill directories ship a"
                ),
                encoding="utf-8",
            ),
        )
        result = self.run_gate()
        self.assertEqual(result.returncode, 64, msg=result.stdout + result.stderr)
        self.assertIn("no longer states its", result.stderr)

    # -- DR-14 ------------------------------------------------------------

    def test_existing_path_marked_planned_is_red(self) -> None:
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8")
                + "\n| Route | Status |\n|---|---|\n"
                + "| [`architecture/STATE_MACHINES.md`]"
                + "(architecture/STATE_MACHINES.md) | `PLANNED` |\n",
                encoding="utf-8",
            ),
        )
        self.assert_red("DR-14")

    def test_planned_row_for_an_absent_path_stays_green(self) -> None:
        """DR-14 forbids `PLANNED` on a path that exists, not the word itself."""
        self.plant(
            INDEX.as_posix(),
            lambda path: path.write_text(
                path.read_text(encoding="utf-8")
                + "\n| Route | Status |\n|---|---|\n"
                + "| `architecture/NOT_WRITTEN_YET.md` | `PLANNED` |\n",
                encoding="utf-8",
            ),
        )
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
