"""Regression controls for PR-scoped commit-role subject selection.

These tests exercise the exact distinction introduced by Shadow issue #310:
a pull request owns only commits after its merge-base, while push/manual/local
execution retains the repository's enforced historical range.  The tests use
real temporary Git repositories so branch and merge-base semantics are not
mocked.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_commit_roles.py"
VOCABULARY = ROOT / "evals" / "commit-roles.json"

GOOD_MESSAGE = """feat: compliant feature commit

Driven-By: agent-macro
Driven-On: claude-code
"""


def load_checker():
    spec = importlib.util.spec_from_file_location("commit_roles_subject", CHECKER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    merged_env = dict(os.environ)
    merged_env.update(env or {})
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
        env=merged_env,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr}"
        )
    return result.stdout.strip()


class RepositoryFixture:
    def __init__(self, root: Path) -> None:
        self.path = root / "repo"
        self.path.mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.path)], check=True
        )
        git(self.path, "config", "user.name", "fixture")
        git(self.path, "config", "user.email", "fixture@example.invalid")
        self.seed = self.commit(
            "seed without trailers",
            filename="seed.txt",
            name="fixture",
            email="fixture@example.invalid",
        )

    def commit(
        self,
        message: str,
        *,
        filename: str,
        name: str,
        email: str,
    ) -> str:
        target = self.path / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{filename}\n", encoding="utf-8")
        git(self.path, "add", "-A")
        git(
            self.path,
            "commit",
            "-qm",
            message,
            env={
                "GIT_AUTHOR_NAME": name,
                "GIT_AUTHOR_EMAIL": email,
                "GIT_COMMITTER_NAME": name,
                "GIT_COMMITTER_EMAIL": email,
            },
        )
        return git(self.path, "rev-parse", "HEAD")


class SubjectSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.vocabulary = json.loads(VOCABULARY.read_text(encoding="utf-8"))

    def test_pr_scope_excludes_unclassified_upstream_debt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            upstream = repo.commit(
                "main debt without trailers",
                filename="upstream.txt",
                name="ed3c",
                email="mcnum01@gmail.com",
            )
            git(repo.path, "switch", "-c", "feature")
            repo.commit(
                GOOD_MESSAGE,
                filename="feature.txt",
                name="agent-macro",
                email="agent-macro@claude-code.invalid",
            )

            selected = self.checker.select_rev_range(
                repo.path, self.vocabulary, base_ref="main"
            )
            self.assertEqual(selected, f"{upstream}..HEAD")
            total, problems = self.checker.evaluate(
                repo.path, selected, self.vocabulary
            )
            self.assertEqual(total, 1)
            self.assertEqual(problems, [])

    def test_pr_scope_still_catches_a_feature_violation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            repo.commit(
                "main debt without trailers",
                filename="upstream.txt",
                name="ed3c",
                email="mcnum01@gmail.com",
            )
            git(repo.path, "switch", "-c", "feature")
            feature = repo.commit(
                "feature without trailers",
                filename="feature.txt",
                name="ed3c",
                email="mcnum01@gmail.com",
            )

            selected = self.checker.select_rev_range(
                repo.path, self.vocabulary, base_ref="main"
            )
            total, problems = self.checker.evaluate(
                repo.path, selected, self.vocabulary
            )
            self.assertEqual(total, 1)
            self.assertTrue(any(feature[:12] in item for item in problems), problems)
            self.assertTrue(any("no Driven-By" in item for item in problems), problems)

    def test_explicit_range_has_precedence_over_an_invalid_pr_base(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            explicit = f"{repo.seed}..HEAD"
            selected = self.checker.select_rev_range(
                repo.path,
                self.vocabulary,
                explicit_range=explicit,
                base_ref="does-not-exist",
            )
            self.assertEqual(selected, explicit)

    def test_non_pr_execution_retains_enforced_history(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            vocabulary = copy.deepcopy(self.vocabulary)
            vocabulary["enforced_from"] = {"commit_sha": repo.seed}
            repo.commit(
                GOOD_MESSAGE,
                filename="feature.txt",
                name="agent-macro",
                email="agent-macro@claude-code.invalid",
            )

            selected = self.checker.select_rev_range(
                repo.path, vocabulary, base_ref=""
            )
            self.assertEqual(selected, f"{repo.seed}..HEAD")

    def test_environment_pr_base_is_honoured(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            upstream = repo.commit(
                "main debt without trailers",
                filename="upstream.txt",
                name="ed3c",
                email="mcnum01@gmail.com",
            )
            git(repo.path, "switch", "-c", "feature")
            repo.commit(
                GOOD_MESSAGE,
                filename="feature.txt",
                name="agent-macro",
                email="agent-macro@claude-code.invalid",
            )
            with patch.dict(os.environ, {"GITHUB_BASE_REF": "main"}, clear=False):
                selected = self.checker.select_rev_range(
                    repo.path, self.vocabulary
                )
            self.assertEqual(selected, f"{upstream}..HEAD")

    def test_unresolvable_advertised_base_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepositoryFixture(Path(raw))
            with self.assertRaisesRegex(
                self.checker.Unusable, "advertised PR base"
            ):
                self.checker.select_rev_range(
                    repo.path, self.vocabulary, base_ref="missing-base"
                )


if __name__ == "__main__":
    unittest.main()
