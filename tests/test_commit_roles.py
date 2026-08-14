"""Controls for the commit-role gate.

Each case builds a disposable repository and makes real commits, because the
subject is what `git log` reports for a commit that actually exists. A fixture
constructed in memory would not exercise trailer parsing, identity resolution,
or the range boundary.

#19 asks for a mutation proof: every rule is neutralised in turn and the suite
must go red. That is `test_every_rule_has_a_control`, and it is the test that
would notice this file becoming decorative.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_commit_roles.py"
VOCABULARY = ROOT / "evals" / "commit-roles.json"


def load_checker():
    spec = importlib.util.spec_from_file_location("ccr", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    import os
    full = dict(os.environ)
    full.update(env or {})
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True, env=full,
    )
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

    def commit(self, message: str, *, name: str, email: str, filename: str) -> str:
        (self.path / filename).write_text(filename + "\n")
        git(self.path, "add", "-A")
        git(self.path, "commit", "-qm", message, env={
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        })
        return git(self.path, "rev-parse", "HEAD").strip()


GOOD_MESSAGE = """feat: a compliant machine commit

Driven-By: agent-macro
Driven-On: claude-code
"""

HUMAN_MESSAGE = """docs: a human commit with a real address

Driven-By: human
Driven-On: shell
"""


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.vocabulary = json.loads(VOCABULARY.read_text(encoding="utf-8"))

    def run_gate(self, repo: RepoFixture, vocabulary=None):
        return self.checker.evaluate(
            repo.path, f"{repo.base}..HEAD", vocabulary or self.vocabulary
        )

    def test_good_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(GOOD_MESSAGE, name="agent-macro",
                        email="agent-macro@claude-code.invalid", filename="a.txt")
            total, problems = self.run_gate(repo)
            self.assertEqual(problems, [])
            self.assertEqual(total, 1)

    def test_human_role_with_a_real_address_is_not_refused(self) -> None:
        """The reverse control #19 asks for: the rule targets machines only."""
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(HUMAN_MESSAGE, name="ed3c",
                        email="mcnum01@gmail.com", filename="h.txt")
            _, problems = self.run_gate(repo)
            self.assertEqual(problems, [])

    def test_missing_driven_by_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            sha = repo.commit("chore: no trailers\n", name="agent-macro",
                              email="agent-macro@claude-code.invalid", filename="b.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("no Driven-By" in p for p in problems), problems)
            self.assertTrue(any(sha[:12] in p for p in problems), problems)

    def test_unknown_driven_by_value_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("chore: bad value\n\nDriven-By: forge-something\n"
                        "Driven-On: claude-code\n",
                        name="agent", email="agent@claude-code.invalid", filename="c.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("not in the vocabulary" in p for p in problems), problems)

    def test_unknown_driven_on_value_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("chore: bad host\n\nDriven-By: agent-macro\n"
                        "Driven-On: some-other-harness\n",
                        name="agent", email="agent-macro@claude-code.invalid",
                        filename="k.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(
                any("Driven-On" in p and "not in the vocabulary" in p for p in problems),
                problems)

    def test_machine_role_with_a_real_address_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(GOOD_MESSAGE, name="ed3c", email="mcnum01@gmail.com",
                        filename="d.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(
                any("contribution graph" in p for p in problems), problems)

    def test_unset_identity_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(GOOD_MESSAGE, name="t", email="t@t.t", filename="e.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("unset default identity" in p for p in problems), problems)

    def test_address_role_must_match_the_trailer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(GOOD_MESSAGE, name="loop",
                        email="loop-iterate@claude-code.invalid", filename="f.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("names role" in p for p in problems), problems)

    def test_address_host_must_match_the_trailer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit(GOOD_MESSAGE, name="agent",
                        email="agent-macro@codex-cli.invalid", filename="g.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("names host" in p for p in problems), problems)

    def test_missing_driven_on_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("chore: one trailer\n\nDriven-By: agent-macro\n",
                        name="agent", email="agent-macro@claude-code.invalid",
                        filename="i.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("no Driven-On" in p for p in problems), problems)

    def test_duplicate_trailers_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            repo.commit("chore: two drivers\n\nDriven-By: agent-macro\n"
                        "Driven-By: human\nDriven-On: claude-code\n",
                        name="agent", email="agent-macro@claude-code.invalid",
                        filename="j.txt")
            _, problems = self.run_gate(repo)
            self.assertTrue(any("one driver" in p for p in problems), problems)

    def test_history_before_the_start_point_is_not_scanned(self) -> None:
        """The honest cost #19 records: old commits cannot be recovered."""
        with tempfile.TemporaryDirectory() as raw:
            repo = RepoFixture(Path(raw))
            # The seed commit has no trailers at all and sits before the range.
            total, problems = self.checker.evaluate(
                repo.path, f"{repo.base}..HEAD", self.vocabulary)
            self.assertEqual(total, 0)
            self.assertEqual(problems, [])


class MutationTests(unittest.TestCase):
    """#19's acceptance: neutralise each rule and the suite must go red."""

    RULES = (
        ('if not by:', "missing Driven-By"),
        ('elif by[0] not in vocabulary["driven_by"]:', "unknown Driven-By value"),
        ('if not on:', "missing Driven-On"),
        ('elif on[0] not in vocabulary["driven_on"]:', "unknown Driven-On value"),
        ('if match is None:', "machine role with a real address"),
        ('elif match.group("role") != by[0]:', "address role mismatch"),
        ('elif len(on) == 1 and match.group("host") != on[0]:', "address host mismatch"),
        ('elif len(by) > 1:', "duplicate Driven-By"),
    )

    def test_every_rule_has_a_control(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        for anchor, label in self.RULES:
            with self.subTest(rule=label):
                self.assertIn(anchor, source, f"anchor drifted: {label}")
                mutated = source.replace(anchor, self._neutralise(anchor), 1)
                self.assertNotEqual(mutated, source, f"mutation changed nothing: {label}")
                self._assert_suite_red(mutated, label)

    def test_unset_identity_rule_has_a_control(self) -> None:
        """Separate: it is a loop body rather than a single condition."""
        source = CHECKER.read_text(encoding="utf-8")
        anchor = 'if record[field].lower() in {item.lower() for item in rules["unset_identities"]}:'
        self.assertIn(anchor, source)
        mutated = source.replace(anchor, "if False:", 1)
        self._assert_suite_red(mutated, "unset identity", only="test_unset_identity_is_refused")

    @staticmethod
    def _neutralise(anchor: str) -> str:
        # `if False and X` would be rewritten by and/or precedence on a compound
        # condition, so the whole condition is replaced instead.
        keyword = "elif" if anchor.strip().startswith("elif") else "if"
        indent = anchor[: len(anchor) - len(anchor.lstrip())]
        return f"{indent}{keyword} False:"

    def _assert_suite_red(self, mutated_source: str, label: str,
                          only: str | None = None) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            target = work / "check_commit_roles.py"
            target.write_text(mutated_source, encoding="utf-8")
            script = work / "run.py"
            script.write_text(
                "import sys, unittest\n"
                f"sys.path.insert(0, {str(work)!r})\n"
                f"sys.argv = ['x']\n"
                f"import importlib.util\n"
                f"spec = importlib.util.spec_from_file_location('ccr', {str(target)!r})\n"
                f"m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                f"sys.modules['patched'] = m\n"
                f"loader = unittest.TestLoader()\n"
                f"import {Path(__file__).stem} as t\n"
                f"t.load_checker = lambda: m\n"
                f"suite = loader.loadTestsFromTestCase(t.GateTests)\n"
                + (f"suite = loader.loadTestsFromName('GateTests.{only}', t)\n" if only else "")
                + "result = unittest.TextTestRunner(verbosity=0).run(suite)\n"
                "raise SystemExit(0 if result.wasSuccessful() else 1)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(ROOT / "tests"), capture_output=True, text=True, check=False,
                env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "tests")},
            )
            self.assertNotEqual(
                result.returncode, 0,
                f"removing the rule for {label!r} left the suite green:\n{result.stdout}\n{result.stderr}",
            )


class VocabularyTests(unittest.TestCase):
    def test_forge_values_stay_separate(self) -> None:
        body = json.loads(VOCABULARY.read_text(encoding="utf-8"))
        for value in ("forge-github", "forge-gitlab", "forge-forgejo"):
            self.assertIn(value, body["driven_by"])
        self.assertNotIn("forge", body["driven_by"])

    def test_human_is_the_only_non_machine_role(self) -> None:
        body = json.loads(VOCABULARY.read_text(encoding="utf-8"))
        non_machine = [k for k, v in body["driven_by"].items() if not v["machine"]]
        self.assertEqual(non_machine, ["human"])

    def test_machine_pattern_rejects_a_deliverable_domain(self) -> None:
        body = json.loads(VOCABULARY.read_text(encoding="utf-8"))
        pattern = re.compile(body["identity_rules"]["machine_author_email_pattern"])
        self.assertIsNone(pattern.match("agent-macro@claude-code.com"))
        self.assertIsNotNone(pattern.match("agent-macro@claude-code.invalid"))

    def test_enforced_from_is_a_real_commit_in_this_repository(self) -> None:
        """A start point nobody can resolve makes the range meaningless."""
        body = json.loads(VOCABULARY.read_text(encoding="utf-8"))
        sha = body["enforced_from"]["commit_sha"]
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        result = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, f"{sha} is not a commit here")


if __name__ == "__main__":
    unittest.main()
