"""Cloud/local execution-domain controls for the commit-role gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_commit_roles.py"
VOCABULARY = ROOT / "evals" / "commit-roles.json"


def load_checker():
    spec = importlib.util.spec_from_file_location("ccr_cloud", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    import os
    full = dict(os.environ)
    full.update(env or {})
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=full)
    return result.stdout


class RepoFixture:
    def __init__(self, tmp: Path) -> None:
        self.path = tmp / "repo"
        self.path.mkdir()
        subprocess.run(["git", "init", "-q", str(self.path)], check=True)
        git(self.path, "config", "user.name", "seed")
        git(self.path, "config", "user.email", "seed@example.invalid")
        (self.path / "seed.txt").write_text("seed\n")
        git(self.path, "add", "-A")
        git(self.path, "commit", "-qm", "seed")
        self.base = git(self.path, "rev-parse", "HEAD").strip()

    def commit(self, message: str, email: str, filename: str = "x.txt") -> None:
        (self.path / filename).write_text(filename + "\n")
        git(self.path, "add", "-A")
        git(self.path, "commit", "-qm", message, env={
            "GIT_AUTHOR_NAME": "ed3c",
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": "ed3c",
            "GIT_COMMITTER_EMAIL": email,
        })


class CloudExecutionDomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.vocabulary = json.loads(VOCABULARY.read_text(encoding="utf-8"))

    def run_gate(self, repo: RepoFixture):
        return self.checker.evaluate(repo.path, f"{repo.base}..HEAD", self.vocabulary)[1]

    def test_cloud_connector_machine_role_accepts_declared_owner_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("feat: cloud write\n\nDriven-By: agent-macro\nDriven-On: chatgpt-github-connector\n", "30064024+ed3c@users.noreply.github.com")
            self.assertEqual(self.run_gate(repo), [])

    def test_same_owner_identity_on_local_host_stays_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("feat: local write\n\nDriven-By: agent-macro\nDriven-On: claude-code\n", "30064024+ed3c@users.noreply.github.com")
            problems = self.run_gate(repo)
            self.assertTrue(any("local host" in p for p in problems), problems)

    def test_cloud_host_with_undeclared_real_identity_stays_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("feat: unknown cloud author\n\nDriven-By: agent-macro\nDriven-On: chatgpt-github-connector\n", "someone@example.com")
            problems = self.run_gate(repo)
            self.assertTrue(any("undeclared endpoint author" in p for p in problems), problems)

    def test_local_synthetic_identity_still_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("feat: local agent\n\nDriven-By: agent-macro\nDriven-On: claude-code\n", "agent-macro@claude-code.invalid")
            self.assertEqual(self.run_gate(repo), [])

    def test_known_nonlocal_host_is_cloud(self) -> None:
        self.assertEqual(self.checker.execution_domain("chatgpt-github-connector", self.vocabulary), "CLOUD")
        self.assertEqual(self.checker.execution_domain("ci", self.vocabulary), "CLOUD")
        self.assertEqual(self.checker.execution_domain("claude-code", self.vocabulary), "LOCAL")

    def test_unknown_host_is_not_silently_cloud(self) -> None:
        with self.assertRaises(self.checker.Unusable):
            self.checker.execution_domain("invented-cloud", self.vocabulary)


if __name__ == "__main__":
    unittest.main()
