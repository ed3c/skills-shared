"""Controls for this repository's private CI publication enrollment.

The canonical gate logic lives in the `github-delivery-loop` skill and has its
own tests. What this repository owns, and therefore what is tested here, is that
*its* policy is real: the workflow it names stays sealed, the verification argv
it declares actually exists and runs, and the gate reaches the decisions this
repository expects on its own policy rather than on a fixture.

The failure this guards against is an enrollment that parses and decides
nothing — a policy file present, and every gate in it satisfiable by accident.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / ".github-delivery" / "ci-policy.json"
SKILL = Path.home() / ".claude" / "skills" / "github-delivery-loop" / "scripts"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SKILL / f"{name}.py")
    if spec is None or spec.loader is None:  # pragma: no cover - environment guard
        raise unittest.SkipTest(f"{name} is not available")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SKILL))
    spec.loader.exec_module(module)
    return module


def head_sha() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


class PolicyShapeTests(unittest.TestCase):
    def test_policy_exists_and_declares_this_repository(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(policy["schema"], "github-ci-policy/v1")
        self.assertEqual(policy["repository"], "ed3c/skills-shared")
        self.assertIs(policy["private"], True)
        self.assertEqual(policy["default_branch"], "main")

    def test_declared_verification_argv_exists_and_is_executable(self) -> None:
        """A verification command that is not there would fail only at publish."""
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        argv = policy["local_verification"]
        self.assertEqual(argv[0], "bash")
        script = ROOT / argv[1]
        self.assertTrue(script.is_file(), argv[1])
        self.assertTrue(script.stat().st_mode & 0o111, f"{argv[1]} is not executable")

    def test_named_workflow_exists(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertTrue((ROOT / policy["workflow"]).is_file(), policy["workflow"])


class SealedWorkflowTests(unittest.TestCase):
    def test_owning_workflow_passes_the_canonical_policy_gate(self) -> None:
        module = load_module("ci_workflow_policy")
        module.check(ROOT, POLICY_PATH)

    def test_pull_request_stays_sealed_to_ready_for_review(self) -> None:
        """The whole point of enrollment: a push to an open PR spends no job."""
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        text = (ROOT / policy["workflow"]).read_text(encoding="utf-8")
        module = load_module("ci_workflow_policy")
        lines = text.splitlines()
        on_lines = module._section(lines, "on")
        pull_lines = module._section(on_lines, "pull_request", 2)
        types = module._list_values(pull_lines, "types", 4)
        self.assertEqual(types, ["ready_for_review"])

    def test_unsealing_the_workflow_is_refused(self) -> None:
        """Prove the gate decides, rather than accepting whatever is there."""
        module = load_module("ci_workflow_policy")
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        text = (ROOT / policy["workflow"]).read_text(encoding="utf-8")
        unsealed = text.replace(
            "    types:\n      - ready_for_review\n",
            "    types:\n      - ready_for_review\n      - synchronize\n",
            1,
        )
        self.assertNotEqual(unsealed, text, "workflow anchor not found")
        with self.assertRaises(module.PolicyError):
            module.evaluate_workflow(policy, unsealed)


class GateDecisionTests(unittest.TestCase):
    """Exercise the gate on this repository's own identity, not a fixture."""

    def snapshot(self, **overrides):
        now = datetime.now(UTC)
        head = head_sha()
        body = {
            "schema": "github-ci-publish-snapshot/v1",
            "repository": "ed3c/skills-shared",
            "repository_owner": "ed3c",
            "private": True,
            "intent": "initial-pr",
            "local_head": head,
            "local_verification": {
                "head_sha": head,
                "status": "passed",
                "completed_at": now.isoformat().replace("+00:00", "Z"),
            },
            "pull_request": None,
        }
        body.update(overrides)
        return body

    def test_initial_publication_is_admitted(self) -> None:
        module = load_module("ci_publish_gate")
        allowed, reason = module.evaluate(self.snapshot())
        self.assertTrue(allowed, reason)
        self.assertEqual(reason, "initial-pr")

    def test_stale_verification_head_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        snapshot = self.snapshot()
        snapshot["local_verification"]["head_sha"] = "0" * 40
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "verification-head-mismatch")

    def test_failed_verification_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        snapshot = self.snapshot()
        snapshot["local_verification"]["status"] = "failed"
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "local-verification-not-passed")

    def test_open_billing_circuit_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        snapshot = self.snapshot(billing_blocker={
            "kind": "account-billing-no-runner",
            "observed_at": now.isoformat().replace("+00:00", "Z"),
        })
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "billing-circuit-open")

    def test_stale_billing_recovery_is_refused(self) -> None:
        """A recovery older than the blocker does not clear it."""
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        snapshot = self.snapshot(
            billing_blocker={
                "kind": "account-billing-no-runner",
                "observed_at": now.isoformat().replace("+00:00", "Z"),
            },
            recovery={
                "author": "ed3c",
                "status": "actions-restored",
                "recovered_at": (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            },
        )
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "billing-recovery-stale")

    def test_untrusted_billing_recovery_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        snapshot = self.snapshot(
            billing_blocker={
                "kind": "account-billing-no-runner",
                "observed_at": now.isoformat().replace("+00:00", "Z"),
            },
            recovery={
                "author": "someone-else",
                "status": "actions-restored",
                "recovered_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            },
        )
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "billing-recovery-untrusted")

    def test_republishing_an_unchanged_head_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        head = head_sha()
        snapshot = self.snapshot(intent="ready-for-review", pull_request={
            "number": 1, "remote_head": head, "is_draft": True,
        })
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "remote-head-already-current")

    def test_repeated_feedback_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        observed = (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        snapshot = self.snapshot(
            intent="repair",
            pull_request={"number": 1, "remote_head": "1" * 40, "is_draft": False},
            actionable_feedback={
                "actionable": True, "head_sha": "1" * 40, "observed_at": observed,
            },
            last_publication={"intent": "repair", "feedback_observed_at": observed},
        )
        allowed, reason = module.evaluate(snapshot)
        self.assertFalse(allowed)
        self.assertEqual(reason, "feedback-already-published")

    def test_checkpoint_intent_is_not_a_publication_reason(self) -> None:
        module = load_module("ci_publish_gate")
        allowed, reason = module.evaluate(self.snapshot(intent="checkpoint"))
        self.assertFalse(allowed)
        self.assertEqual(reason, "unsupported-intent:checkpoint")


class PushGuardTests(unittest.TestCase):
    """Disposable repositories, so the result does not depend on whichever
    remotes this checkout happens to have configured."""

    def make_repo(self, tmp: Path, *, enrolled: bool, remotes: dict[str, str]) -> Path:
        repo = tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        for name, url in remotes.items():
            subprocess.run(["git", "-C", str(repo), "remote", "add", name, url], check=True)
        if enrolled:
            policy_dir = repo / ".github-delivery"
            policy_dir.mkdir()
            (policy_dir / "ci-policy.json").write_text(
                POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return repo

    def block(self, repo: Path, command: str):
        module = load_module("ci_publish_guard")
        return module.should_block({
            "tool_name": "Bash",
            "tool_input": {"command": command, "cwd": str(repo)},
        })

    def test_github_push_is_not_blocked_before_enrollment(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw), enrolled=False, remotes={
                "origin": "git@github.com:ed3c/skills-shared.git"})
            blocked, reason = self.block(repo, "git push origin HEAD")
            self.assertFalse(blocked, reason)

    def test_github_push_is_blocked_once_enrolled(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw), enrolled=True, remotes={
                "origin": "git@github.com:ed3c/skills-shared.git"})
            blocked, _ = self.block(repo, "git push origin HEAD")
            self.assertTrue(blocked, "an enrolled repository must route GitHub pushes")

    def test_a_forgejo_remote_stays_open_when_enrolled(self) -> None:
        """Enrollment must not close the Forgejo path a dual-remote repo uses."""
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw), enrolled=True, remotes={
                "origin": "git@github.com:ed3c/skills-shared.git",
                "forgejo": "http://localhost:3000/ed3c/skills-shared.git"})
            blocked, reason = self.block(repo, "git push forgejo HEAD")
            self.assertFalse(blocked, reason)

    def test_an_unresolvable_remote_fails_closed(self) -> None:
        """An enrolled repository with no such remote blocks rather than guessing."""
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            repo = self.make_repo(Path(raw), enrolled=True, remotes={
                "origin": "git@github.com:ed3c/skills-shared.git"})
            blocked, _ = self.block(repo, "git push nowhere HEAD")
            self.assertTrue(blocked)

    def test_this_repository_is_actually_enrolled(self) -> None:
        """The disposable cases prove the mechanism; this proves it applies here."""
        self.assertTrue(POLICY_PATH.is_file())
        blocked, _ = self.block(ROOT, "git push origin HEAD")
        self.assertTrue(blocked)


if __name__ == "__main__":
    unittest.main()
