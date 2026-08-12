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


def policy() -> dict:
    return {
        "schema": "github-ci-policy/v1",
        "repository": "ed3c/example",
        "private": True,
        "default_branch": "main",
        "workflow": ".github/workflows/verify.yml",
        "required_jobs": ["verify"],
        "local_verification": ["/usr/bin/true"],
    }


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
