from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[2]


def load(name: str):
    script = SKILL / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICY = load("ci_workflow_policy")
GUARD = load("ci_publish_guard")


WORKFLOW = """name: verify

on:
  pull_request:
    types: [ready_for_review]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: verify-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - run: bash verify.sh
"""


UNIVERSAL_WORKFLOW = WORKFLOW.replace(
    "types: [ready_for_review]",
    "types: [opened, synchronize, reopened, ready_for_review]",
)


def policy(pull_request_mode: str | None = "draft-first") -> dict:
    value = {
        "schema": "github-ci-policy/v1",
        "repository": "ed3c/example",
        "private": True,
        "default_branch": "main",
        "workflow": ".github/workflows/verify.yml",
        "required_jobs": ["verify"],
        "local_verification": ["/usr/bin/true"],
    }
    if pull_request_mode is not None:
        value["pull_request_mode"] = pull_request_mode
    return value


class WorkflowPolicyTests(unittest.TestCase):
    def test_cost_controlled_workflow_is_accepted(self) -> None:
        details = POLICY.evaluate_workflow(policy(), WORKFLOW)
        self.assertIn("required_jobs=verify", details)

    def test_default_pull_request_synchronize_is_rejected(self) -> None:
        hollow = WORKFLOW.replace(
            "pull_request:\n    types: [ready_for_review]", "pull_request:"
        )
        with self.assertRaisesRegex(POLICY.PolicyError, "missing types"):
            POLICY.evaluate_workflow(policy(), hollow)

    def test_universal_pull_request_mode_accepts_exact_event_set(self) -> None:
        details = POLICY.evaluate_workflow(policy("universal"), UNIVERSAL_WORKFLOW)
        self.assertIn("pull_request_mode=universal", details)

    def test_draft_first_mode_rejects_universal_event_set(self) -> None:
        with self.assertRaisesRegex(POLICY.PolicyError, "draft-first"):
            POLICY.evaluate_workflow(policy(), UNIVERSAL_WORKFLOW)

    def test_universal_mode_rejects_missing_event(self) -> None:
        hollow = UNIVERSAL_WORKFLOW.replace("synchronize, ", "")
        with self.assertRaisesRegex(POLICY.PolicyError, "universal"):
            POLICY.evaluate_workflow(policy("universal"), hollow)

    def test_universal_mode_rejects_extra_event(self) -> None:
        hollow = UNIVERSAL_WORKFLOW.replace(
            "ready_for_review]", "ready_for_review, converted_to_draft]"
        )
        with self.assertRaisesRegex(POLICY.PolicyError, "universal"):
            POLICY.evaluate_workflow(policy("universal"), hollow)

    def test_unknown_pull_request_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy("every-event")), encoding="utf-8")
            with self.assertRaisesRegex(POLICY.PolicyError, "pull_request_mode"):
                POLICY.load_policy(path)

    def test_non_string_pull_request_mode_is_rejected_as_policy_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            value = policy()
            value["pull_request_mode"] = ["universal"]
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(POLICY.PolicyError, "pull_request_mode"):
                POLICY.load_policy(path)

    def test_legacy_policy_defaults_to_draft_first(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy(None)), encoding="utf-8")
            loaded = POLICY.load_policy(path)
        self.assertEqual(loaded["pull_request_mode"], "draft-first")

    def test_tagged_action_is_rejected(self) -> None:
        hollow = WORKFLOW.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@v4",
        )
        with self.assertRaisesRegex(POLICY.PolicyError, "immutable SHAs"):
            POLICY.evaluate_workflow(policy(), hollow)


class PublicationGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(
            ["git", "-C", self.root, "remote", "add", "github", "git@github.com:ed3c/example.git"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", self.root, "remote", "add", "forgejo", "http://localhost:3000/neon/example.git"],
            check=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self, command: str) -> dict:
        return {"tool_name": "Bash", "tool_input": {"command": command, "cwd": str(self.root)}}

    def test_unmanaged_repository_is_not_blocked(self) -> None:
        self.assertEqual(GUARD.should_block(self.payload("git push github main"))[0], False)

    def test_managed_repository_blocks_direct_github_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        blocked, reason = GUARD.should_block(self.payload("git push github main"))
        self.assertTrue(blocked)
        self.assertIn("ci_publish.py", reason)

    def test_non_push_command_is_not_blocked(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertEqual(GUARD.should_block(self.payload("git status"))[0], False)

    def test_managed_forgejo_push_remains_available(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertEqual(GUARD.should_block(self.payload("git push forgejo main"))[0], False)

    def test_cd_then_absolute_git_path_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"cd {self.root} && /usr/bin/git push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])


if __name__ == "__main__":
    unittest.main()
