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
SKILL = ROOT / "skills" / "github-delivery-loop" / "scripts"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SKILL / f"{name}.py")
    if spec is None or spec.loader is None:  # pragma: no cover - environment guard
        raise unittest.SkipTest(f"{name} is not available")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SKILL))
    sys.modules[name] = module
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
        self.assertEqual(policy["schema"], "github-ci-policy/v2")
        self.assertEqual(policy["repository"], "ed3c/skills-shared")
        self.assertIs(policy["private"], True)
        self.assertEqual(policy["default_branch"], "main")

    def test_declared_verification_contract_exists_and_matches_repository(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        contract_path = ROOT / policy["local_verification_contract"]
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(
            contract["schema"], "github-delivery-local-verification-contract/v1"
        )
        self.assertEqual(contract["repository_id"], 1326262274)
        module = load_module("local_verification")
        module.validate_contract(contract, 1326262274)

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

    def subject(self, **overrides):
        now = datetime.now(UTC)
        import tempfile
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "fixture"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
            (repo / "subject.txt").write_text("subject\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "subject.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "subject"], check=True)
            contract = {
                "schema": "github-delivery-local-verification-contract/v1",
                "repository_id": 1326262274,
                "inherit_env": ["PATH"],
                "commands": [{
                    "id": "repository-contract",
                    "argv": ["python3", "-c", "print('ok')"],
                    "cwd": ".",
                    "timeout_seconds": 10,
                    "max_output_bytes": 4096,
                }],
            }
            local = load_module("local_verification")
            verification, evidence, code = local.build(repo, contract, 1326262274)
            self.assertEqual(code, 0)
        head = verification["head_sha"]
        tree = evidence["tree_sha"]
        snapshot = {
            "schema": "github-actions-publish-snapshot/v4",
            "repository": {
                "full_name": "ed3c/skills-shared",
                "repository_id": 1326262274,
                "owner_login": "ed3c",
                "private": True,
            },
            "branch": {"name": "agent/fixture", "head_sha": None},
            "initial_boundary": "trusted-initial",
            "pull_request": {
                "number": None,
                "state": "absent",
                "head_sha": None,
                "last_published_sha": None,
                "last_published_at": None,
                "feedback": None,
            },
            "actions": {
                "circuit": "closed",
                "observed_at": None,
                "blocker": None,
                "latest_check": None,
            },
            "captured_at": now.isoformat().replace("+00:00", "Z"),
        }
        snapshot.update(overrides.get("snapshot", {}))
        if (
            snapshot["pull_request"]["state"] != "absent"
            and "initial_boundary" not in overrides.get("snapshot", {})
        ):
            snapshot["initial_boundary"] = "not-initial"
        verification.update(overrides.get("verification", {}))
        if "evidence" in overrides:
            evidence.update(overrides["evidence"])
        return snapshot, verification, evidence, contract, head, tree

    @staticmethod
    def decide(module, subject, intent="initial-pr", recovery=None):
        snapshot, verification, evidence, contract, head, tree = subject
        return module.evaluate(
            snapshot, verification, evidence, contract, intent, head, tree, recovery
        )

    def test_initial_publication_is_admitted(self) -> None:
        module = load_module("ci_publish_gate")
        decision = self.decide(module, self.subject())
        self.assertEqual(decision.decision, "ALLOW")
        self.assertEqual(decision.reason, "allow-initial-pr")

    def test_initial_publication_requires_remote_branch_absence(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject(snapshot={
            "branch": {"name": "agent/fixture", "head_sha": "1" * 40},
            "initial_boundary": "branch-present-without-pr",
        })
        decision = self.decide(module, subject)
        self.assertEqual(decision.reason, "initial-boundary-refused")

    def test_stale_verification_head_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject(verification={"head_sha": "0" * 40})
        with self.assertRaisesRegex(module.InputError, "stale"):
            self.decide(module, subject)

    def test_failed_verification_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject(verification={"status": "FAIL"})
        with self.assertRaisesRegex(module.InputError, "must be PASS"):
            self.decide(module, subject)

    def test_tampered_detailed_evidence_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject(evidence={"status": "FAIL"})
        with self.assertRaisesRegex(module.InputError, "clean PASS"):
            self.decide(module, subject)

    def test_resigned_command_drift_from_contract_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject()
        subject[2]["commands"][0]["argv"] = ["false"]
        content = dict(subject[2])
        content.pop("content_sha256")
        subject[2]["content_sha256"] = module.digest(content)
        subject[1]["evidence_sha256"] = module.digest(subject[2])
        with self.assertRaisesRegex(module.InputError, "differs from contract"):
            self.decide(module, subject)

    def test_noncanonical_inherit_env_order_matches_producer_normalization(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject()
        subject[3]["inherit_env"] = ["TZ", "PATH"]
        normalized = module.LOCAL_VERIFICATION.validate_contract(subject[3], 1326262274)
        subject[2]["contract_sha256"] = module.digest(normalized)
        content = dict(subject[2])
        content.pop("content_sha256")
        subject[2]["content_sha256"] = module.digest(content)
        subject[1]["evidence_sha256"] = module.digest(subject[2])
        decision = self.decide(module, subject)
        self.assertEqual(decision.decision, "ALLOW")

    def test_open_billing_circuit_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        subject = self.subject(snapshot={"actions": {
            "circuit": "billing-open", "observed_at": now,
            "blocker": "billing-or-spending-limit", "latest_check": None,
        }})
        decision = self.decide(module, subject)
        self.assertEqual(decision.reason, "billing-circuit-open")

    def test_stale_billing_recovery_is_refused(self) -> None:
        """A recovery older than the blocker does not clear it."""
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        observed = now.isoformat().replace("+00:00", "Z")
        subject = self.subject(snapshot={"actions": {
            "circuit": "billing-open", "observed_at": observed,
            "blocker": "billing-or-spending-limit", "latest_check": None,
        }})
        recovery = {
            "schema": "github-actions-billing-recovery/v1",
            "repository_id": 1326262274,
            "owner_login": "ed3c",
            "blocker_observed_at": observed,
            "recovered_at": (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "note": "fixture",
        }
        decision = self.decide(module, subject, recovery=recovery)
        self.assertEqual(decision.reason, "billing-recovery-invalid")

    def test_untrusted_billing_recovery_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        now = datetime.now(UTC)
        observed = now.isoformat().replace("+00:00", "Z")
        subject = self.subject(snapshot={"actions": {
            "circuit": "billing-open", "observed_at": observed,
            "blocker": "billing-or-spending-limit", "latest_check": None,
        }})
        recovery = {
            "schema": "github-actions-billing-recovery/v1",
            "repository_id": 1326262274,
            "owner_login": "someone-else",
            "blocker_observed_at": observed,
            "recovered_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            "note": "fixture",
        }
        decision = self.decide(module, subject, recovery=recovery)
        self.assertEqual(decision.reason, "billing-recovery-invalid")

    def test_ready_transition_on_unchanged_head_does_not_push(self) -> None:
        module = load_module("ci_publish_gate")
        base = self.subject()
        head = base[4]
        pull = {
            "number": 1, "state": "draft", "head_sha": head,
            "last_published_sha": head, "last_published_at": "2026-08-12T05:00:00Z",
            "feedback": None,
        }
        subject = self.subject(snapshot={
            "branch": {"name": "agent/fixture", "head_sha": head},
            "pull_request": pull,
        })
        # Bind the pull to this subject's independently produced exact HEAD.
        actual = subject[4]
        subject[0]["branch"]["head_sha"] = actual
        subject[0]["pull_request"]["head_sha"] = actual
        subject[0]["pull_request"]["last_published_sha"] = actual
        decision = self.decide(module, subject, intent="ready-for-review")
        self.assertEqual(decision.operation, "ready-transition-only")

    def test_repeated_feedback_is_refused(self) -> None:
        module = load_module("ci_publish_gate")
        remote = "1" * 40
        subject = self.subject(snapshot={
            "branch": {"name": "agent/fixture", "head_sha": remote},
            "pull_request": {
                "number": 1, "state": "ready", "head_sha": remote,
                "last_published_sha": remote,
                "last_published_at": "2026-08-12T05:00:00Z",
                "feedback": {
                    "id": "review:1", "kind": "review", "head_sha": remote,
                    "observed_at": "2026-08-12T05:01:00Z", "consumed_by_sha": None,
                },
            },
        })
        subject[0]["pull_request"]["feedback"]["consumed_by_sha"] = subject[4]
        decision = self.decide(module, subject, intent="batched-repair")
        self.assertEqual(decision.reason, "repair-feedback-already-consumed")

    def test_checkpoint_intent_is_not_a_publication_reason(self) -> None:
        module = load_module("ci_publish_gate")
        subject = self.subject()
        with self.assertRaisesRegex(module.InputError, "intent must be"):
            self.decide(module, subject, intent="checkpoint")


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
