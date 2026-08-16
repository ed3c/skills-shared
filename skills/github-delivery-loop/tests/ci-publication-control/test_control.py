from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import UTC, datetime
from pathlib import Path


SKILL = Path(__file__).resolve().parents[2]
PUBLISH_SCRIPT = SKILL / "scripts" / "ci_publish.py"


def load(name: str):
    script = SKILL / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICY = load("ci_workflow_policy")
GUARD = load("ci_publish_guard")
SNAPSHOT = load("github_actions_snapshot")


class LiveCaptureSeamTests(unittest.TestCase):
    def test_live_capture_binds_every_policy_declared_feedback_check(self) -> None:
        scripts = str(SKILL / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        publish = load("ci_publish")
        transport = {"schema": "github-actions-provider-transport/v4"}
        observation = {"schema": "github-actions-observation/v6"}
        snapshot = {"schema": "github-actions-publish-snapshot/v5"}
        with (
            mock.patch.object(
                publish.github_actions_snapshot,
                "capture_transport",
                return_value=transport,
            ) as capture_transport,
            mock.patch.object(
                publish.github_actions_snapshot,
                "observation_from_transport",
                return_value=observation,
            ) as derive,
            mock.patch.object(
                publish.github_actions_snapshot,
                "build",
                return_value=snapshot,
            ) as build,
        ):
            checks = [
                {"workflow": ".github/workflows/verify.yml", "job": "verify"},
                {"workflow": ".github/workflows/binding.yml", "job": "binding"},
            ]
            actual_transport, actual_observation, actual_snapshot = publish._capture_live_state(
                "ed3c/example", "agent/example", checks
            )
        capture_transport.assert_called_once_with(
            "ed3c/example", "agent/example", checks, 30
        )
        derive.assert_called_once_with(transport)
        build.assert_called_once_with(observation, checks, strict=True)
        self.assertIs(actual_transport, transport)
        self.assertIs(actual_observation, observation)
        self.assertIs(actual_snapshot, snapshot)

    def test_snapshot_cannot_omit_a_policy_declared_auxiliary_check(self) -> None:
        scripts = str(SKILL / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        publish = load("ci_publish")
        declared = [
            {"workflow": ".github/workflows/verify.yml", "job": "verify", "role": "primary"},
            {"workflow": ".github/workflows/binding.yml", "job": "binding", "role": "auxiliary"},
        ]
        snapshot = {
            "actions": {
                "circuit": "closed",
                "checks": [{
                    "workflow": ".github/workflows/verify.yml",
                    "job": "verify",
                    "role": "primary",
                }],
            }
        }
        with self.assertRaisesRegex(
            publish.PublicationError, "do not match policy"
        ):
            publish._require_snapshot_feedback_checks(snapshot, declared)


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
    "types: [opened, synchronize, reopened]",
)


AUXILIARY_WORKFLOW = """name: binding

on:
  pull_request:

permissions:
  contents: read

jobs:
  binding:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - run: bash verify-binding.sh
"""


def policy(pull_request_mode: str | None = "draft-first") -> dict:
    value = {
        "schema": "github-ci-policy/v2",
        "repository": "ed3c/example",
        "private": True,
        "default_branch": "main",
        "workflow": ".github/workflows/verify.yml",
        "required_jobs": ["verify"],
        "local_verification_contract": ".github-delivery/local-verification-contract.json",
    }
    if pull_request_mode is not None:
        value["pull_request_mode"] = pull_request_mode
    return value


def multi_workflow_policy() -> dict:
    value = policy("universal")
    value["repair_feedback_checks"] = [
        {"workflow": ".github/workflows/binding.yml", "job": "binding"}
    ]
    return value


class WorkflowPolicyTests(unittest.TestCase):
    def test_auxiliary_feedback_workflow_is_normalized_after_primary(self) -> None:
        checks = POLICY.feedback_checks(multi_workflow_policy())
        self.assertEqual(checks, [
            {"workflow": ".github/workflows/verify.yml", "job": "verify", "role": "primary"},
            {"workflow": ".github/workflows/binding.yml", "job": "binding", "role": "auxiliary"},
        ])

    def test_duplicate_primary_feedback_pair_is_rejected(self) -> None:
        value = policy()
        value["repair_feedback_checks"] = [
            {"workflow": value["workflow"], "job": value["required_jobs"][0]}
        ]
        with self.assertRaisesRegex(POLICY.PolicyError, "duplicate"):
            POLICY.feedback_checks(value)

    def test_auxiliary_feedback_workflow_must_own_declared_job(self) -> None:
        with self.assertRaisesRegex(POLICY.PolicyError, "missing repair-feedback job"):
            POLICY.evaluate_feedback_workflow(
                {"workflow": ".github/workflows/binding.yml", "job": "missing"},
                AUXILIARY_WORKFLOW,
            )

    def test_auxiliary_feedback_workflow_requires_pinned_actions(self) -> None:
        hollow = AUXILIARY_WORKFLOW.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@v4",
        )
        with self.assertRaisesRegex(POLICY.PolicyError, "immutable SHAs"):
            POLICY.evaluate_feedback_workflow(
                {"workflow": ".github/workflows/binding.yml", "job": "binding"},
                hollow,
            )

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
            "reopened]", "reopened, ready_for_review]"
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

    def test_evaluator_rejects_non_string_pull_request_mode_as_policy_error(self) -> None:
        malformed = policy()
        malformed["pull_request_mode"] = ["universal"]

        with self.assertRaisesRegex(POLICY.PolicyError, "pull_request_mode"):
            POLICY.evaluate_workflow(malformed, WORKFLOW)

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


class MultiWorkflowSnapshotTests(unittest.TestCase):
    CHECKS = [
        {"workflow": ".github/workflows/verify.yml", "job": "verify", "role": "primary"},
        {"workflow": ".github/workflows/binding.yml", "job": "binding", "role": "auxiliary"},
    ]

    @staticmethod
    def observation() -> dict:
        value = SNAPSHOT.fixture()
        primary = value["check_runs"][0]
        primary.update({
            "name": "verify",
            "workflow_path": ".github/workflows/verify.yml",
            "conclusion": "success",
            "step_count": 2,
        })
        auxiliary = dict(primary)
        auxiliary.update({
            "id": 9002,
            "name": "binding",
            "workflow_path": ".github/workflows/binding.yml",
            "conclusion": "failure",
            "workflow_id": 6002,
            "workflow_run_id": 7002,
            "check_suite_id": 8002,
            "job_id": 5002,
            "completed_at": "2026-08-12T05:01:01Z",
        })
        value["check_runs"].append(auxiliary)
        return value

    @staticmethod
    def transport_with_skipped_draft_job() -> dict:
        resolved = "/opt/homebrew/Cellar/gh/2.82.0/bin/gh"
        repo = "ed3c/example"
        head = "1" * 40

        def entry(argv: list[str], payload: object) -> dict:
            stdout = json.dumps(payload, separators=(",", ":"))
            return {
                "argv": argv,
                "exit": 0,
                "stdout": stdout,
                "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                "stderr": "",
                "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            }

        captures = [
            entry([resolved, "api", f"repos/{repo}"], {
                "full_name": repo,
                "id": 123,
                "owner": {"login": "ed3c"},
                "private": True,
            }),
            entry([resolved, "api", f"repos/{repo}/actions/workflows/.github%2Fworkflows%2Fverify.yml"], {
                "id": 6001,
                "path": ".github/workflows/verify.yml",
            }),
            entry([resolved, "api", f"repos/{repo}/actions/workflows/.github%2Fworkflows%2Fbinding.yml"], {
                "id": 6002,
                "path": ".github/workflows/binding.yml",
            }),
            entry([resolved, "api", "--paginate", "--slurp", f"repos/{repo}/pulls?state=open&head=ed3c:feature&per_page=100"], [[{
                "number": 42,
                "draft": False,
                "head": {"sha": head},
                "updated_at": "2026-08-12T05:00:00Z",
            }]]),
        ]

        checks = [
            (9001, "verify", 7001, 8001, 5001, 6001, "success", [
                {"name": "Set up job", "conclusion": "success"},
            ]),
            (9003, "binding", 7003, 8003, 5003, 6002, "skipped", []),
            (9002, "binding", 7002, 8002, 5002, 6002, "failure", [
                {"name": "Set up job", "conclusion": "success"},
                {"name": "Validate binding", "conclusion": "failure"},
            ]),
        ]
        check_runs = [{
            "id": check_id,
            "name": name,
            "head_sha": head,
            "status": "completed",
            "conclusion": conclusion,
            "completed_at": f"2026-08-12T05:01:0{index}Z",
            "details_url": f"https://github.com/{repo}/actions/runs/{run_id}/job/{job_id}",
            "app": {"id": 15368, "slug": "github-actions"},
            "check_suite": {"id": suite_id},
        } for index, (check_id, name, run_id, suite_id, job_id, _, conclusion, _) in enumerate(checks, 1)]
        captures.append(entry(
            [resolved, "api", "--paginate", "--slurp", f"repos/{repo}/commits/{head}/check-runs?per_page=100"],
            [{"check_runs": check_runs}],
        ))
        for check_id, _, run_id, _, job_id, workflow_id, _, steps in checks:
            captures.extend([
                entry([resolved, "api", f"repos/{repo}/actions/runs/{run_id}"], {
                    "id": run_id,
                    "head_sha": head,
                    "workflow_id": workflow_id,
                }),
                entry([resolved, "api", f"repos/{repo}/actions/jobs/{job_id}"], {
                    "id": job_id,
                    "run_id": run_id,
                    "head_sha": head,
                    "status": "completed",
                    "conclusion": "skipped" if not steps else (
                        "failure" if any(step["conclusion"] == "failure" for step in steps) else "success"
                    ),
                    "steps": steps,
                }),
                entry([resolved, "api", "--paginate", "--slurp", f"repos/{repo}/check-runs/{check_id}/annotations?per_page=100"], [[]]),
            ])
        captures.append(entry([resolved, "api", "repos/ed3c/example/git/ref/heads/feature"], {
            "object": {"sha": head},
        }))
        return {
            "schema": "github-actions-publish-transport/v6",
            "producer": "github_actions_snapshot.py",
            "gh_executable": {
                "invoked_path": "/opt/homebrew/bin/gh",
                "resolved_path": resolved,
                "sha256": "3" * 64,
                "version": "gh version 2.82.0",
            },
            "repository": repo,
            "branch": "feature",
            "feedback_checks": MultiWorkflowSnapshotTests.CHECKS,
            "captured_at": "2026-08-12T05:02:00Z",
            "captures": captures,
        }

    def test_declared_auxiliary_failure_becomes_exact_batched_feedback(self) -> None:
        result = SNAPSHOT.build(self.observation(), self.CHECKS)
        self.assertEqual(result["schema"], "github-actions-publish-snapshot/v5")
        self.assertEqual(result["pull_request"]["feedback"]["id"], "check-runs:9002")
        self.assertEqual(
            [(item["workflow"], item["job"], item["conclusion"]) for item in result["actions"]["checks"]],
            [
                (".github/workflows/verify.yml", "verify", "success"),
                (".github/workflows/binding.yml", "binding", "failure"),
            ],
        )

    def test_multiple_declared_failures_have_one_deterministic_feedback_id(self) -> None:
        value = self.observation()
        value["check_runs"][0]["conclusion"] = "failure"
        result = SNAPSHOT.build(value, self.CHECKS)
        self.assertEqual(
            result["pull_request"]["feedback"]["id"],
            "check-runs:9001,9002",
        )

    def test_missing_declared_auxiliary_check_fails_closed(self) -> None:
        value = self.observation()
        value["check_runs"] = value["check_runs"][:1]
        with self.assertRaisesRegex(SNAPSHOT.SnapshotError, "declared repair-feedback check.*missing"):
            SNAPSHOT.build(value, self.CHECKS)

    def test_auxiliary_rerun_for_exact_head_is_ambiguous(self) -> None:
        value = self.observation()
        duplicate = dict(value["check_runs"][1], id=9003, job_id=5003)
        value["check_runs"].append(duplicate)
        with self.assertRaisesRegex(SNAPSHOT.SnapshotError, "ran more than once"):
            SNAPSHOT.build(value, self.CHECKS)

    def test_skipped_draft_observation_does_not_make_one_execution_ambiguous(self) -> None:
        value = self.observation()
        skipped = dict(
            value["check_runs"][1],
            id=9003,
            job_id=5003,
            conclusion="skipped",
            completed_at="2026-08-12T05:00:30Z",
            step_count=0,
        )
        value["check_runs"].append(skipped)

        result = SNAPSHOT.build(value, self.CHECKS)

        self.assertEqual(result["pull_request"]["feedback"]["id"], "check-runs:9002")
        self.assertEqual(result["actions"]["checks"][1]["check_run_id"], 9002)

    def test_transport_binds_job_steps_before_skipped_observation_is_ignored(self) -> None:
        observation = SNAPSHOT.observation_from_transport(
            self.transport_with_skipped_draft_job()
        )
        result = SNAPSHOT.build(observation, self.CHECKS, strict=True)

        self.assertEqual([item["step_count"] for item in observation["check_runs"]], [1, 0, 2])
        self.assertEqual(result["pull_request"]["feedback"]["id"], "check-runs:9002")

    def test_transport_rejects_job_conclusion_that_disagrees_with_check_run(self) -> None:
        transport = self.transport_with_skipped_draft_job()
        job_entry = next(
            item for item in transport["captures"]
            if item["argv"][-1] == "repos/ed3c/example/actions/jobs/5003"
        )
        payload = json.loads(job_entry["stdout"])
        payload["conclusion"] = "success"
        job_entry["stdout"] = json.dumps(payload, separators=(",", ":"))
        job_entry["stdout_sha256"] = hashlib.sha256(job_entry["stdout"].encode()).hexdigest()

        with self.assertRaisesRegex(SNAPSHOT.SnapshotError, "Actions job.*mismatch"):
            SNAPSHOT.observation_from_transport(transport)

    def test_skipped_only_auxiliary_does_not_satisfy_declared_check(self) -> None:
        value = self.observation()
        value["check_runs"][1].update({"conclusion": "skipped", "step_count": 0})

        with self.assertRaisesRegex(SNAPSHOT.SnapshotError, "declared repair-feedback check.*missing"):
            SNAPSHOT.build(value, self.CHECKS)

    def test_skipped_draft_plus_one_success_has_no_repair_feedback(self) -> None:
        value = self.observation()
        value["check_runs"][1]["conclusion"] = "success"
        skipped = dict(
            value["check_runs"][1],
            id=9003,
            job_id=5003,
            conclusion="skipped",
            step_count=0,
        )
        value["check_runs"].append(skipped)

        result = SNAPSHOT.build(value, self.CHECKS)

        self.assertIsNone(result["pull_request"]["feedback"])
        self.assertEqual(result["actions"]["checks"][1]["check_run_id"], 9002)

    def test_previous_observation_without_step_provenance_stays_ambiguous(self) -> None:
        value = self.observation()
        value["schema"] = "github-actions-publish-observation/v3"
        skipped = dict(
            value["check_runs"][1],
            id=9003,
            job_id=5003,
            conclusion="skipped",
        )
        value["check_runs"].append(skipped)
        for check_run in value["check_runs"]:
            check_run.pop("step_count")

        with self.assertRaisesRegex(SNAPSHOT.SnapshotError, "ran more than once"):
            SNAPSHOT.build(value, self.CHECKS)

    def test_auxiliary_no_runner_billing_is_not_actionable_feedback(self) -> None:
        value = self.observation()
        value["check_runs"][1]["annotations"] = [{
            "message": "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"
        }]
        result = SNAPSHOT.build(value, self.CHECKS)
        self.assertEqual(result["actions"]["circuit"], "billing-open")
        self.assertEqual(result["actions"]["checks"], [])
        self.assertIsNone(result["pull_request"]["feedback"])

    def test_zero_step_skipped_billing_observation_still_opens_circuit(self) -> None:
        value = self.observation()
        auxiliary = value["check_runs"][1]
        auxiliary.update({"conclusion": "skipped", "step_count": 0})
        auxiliary["annotations"] = [{
            "message": "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"
        }]

        result = SNAPSHOT.build(value, self.CHECKS)

        self.assertEqual(result["actions"]["circuit"], "billing-open")
        self.assertEqual(result["actions"]["checks"], [])

    def test_billing_observation_blocks_before_same_pair_execution_ambiguity(self) -> None:
        value = self.observation()
        billing_skip = dict(
            value["check_runs"][1],
            id=9003,
            job_id=5003,
            conclusion="skipped",
            step_count=0,
        )
        billing_skip["annotations"] = [{
            "message": "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"
        }]
        value["check_runs"].append(billing_skip)

        result = SNAPSHOT.build(value, self.CHECKS)

        self.assertEqual(result["actions"]["circuit"], "billing-open")
        self.assertIsNone(result["pull_request"]["feedback"])


class PublicationCommandTests(unittest.TestCase):
    def render_publication(
        self,
        pull_request_mode: str,
        *,
        intent: str = "batched-repair",
        pull_request_is_open: bool = True,
        pull_request_head_ref: str = "agent/example",
        target_branch: str = "agent/example",
        current_branch: str | None = None,
        external_policy: bool = False,
        inspect_manifest: bool = False,
        multiple_required_jobs: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            subprocess.run(
                ["git", "init", "-q", "-b", current_branch or target_branch, root], check=True
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    root,
                    "remote",
                    "add",
                    "github",
                    "git@github.com:ed3c/example.git",
                ],
                check=True,
            )
            workflow = WORKFLOW if pull_request_mode == "draft-first" else UNIVERSAL_WORKFLOW
            policy_value = policy(pull_request_mode)
            if multiple_required_jobs:
                workflow += """
  second:
    runs-on: ubuntu-latest
    steps:
      - run: echo second
"""
                policy_value["required_jobs"] = ["verify", "second"]
            workflow_path = root / ".github" / "workflows" / "verify.yml"
            workflow_path.parent.mkdir(parents=True)
            workflow_path.write_text(workflow, encoding="utf-8")
            policy_path = root / ".github-delivery" / "ci-policy.json"
            policy_path.parent.mkdir()
            policy_path.write_text(
                json.dumps(policy_value), encoding="utf-8"
            )
            contract_path = root / ".github-delivery" / "local-verification-contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema": "github-delivery-local-verification-contract/v1",
                        "repository_id": 123,
                        "inherit_env": ["PATH"],
                        "commands": [
                            {
                                "id": "fixture",
                                "argv": ["python3", "-c", "print('ok')"],
                                "cwd": ".",
                                "timeout_seconds": 10,
                                "max_output_bytes": 4096,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "README.md").write_text("fixture\n", encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    root,
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            head = subprocess.run(
                ["git", "-C", root, "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            verification = subprocess.run(
                [
                    sys.executable,
                    str(PUBLISH_SCRIPT),
                    "verify",
                    "--repo-root",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verification.returncode, 0, verification.stderr)
            remote_head = "a" * 40
            state = "absent" if not pull_request_is_open else (
                "draft" if intent == "ready-for-review" else "ready"
            )
            snapshot = {
                "schema": "github-actions-publish-snapshot/v5",
                "repository": {
                    "full_name": "ed3c/example",
                    "repository_id": 123,
                    "owner_login": "ed3c",
                    "private": True,
                },
                "branch": {
                    "name": pull_request_head_ref,
                    "head_sha": None if state == "absent" else remote_head,
                },
                "initial_boundary": (
                    "trusted-initial" if state == "absent" else "not-initial"
                ),
                "pull_request": {
                    "number": None if state == "absent" else 7,
                    "state": state,
                    "head_sha": None if state == "absent" else remote_head,
                    "last_published_sha": None if state == "absent" else remote_head,
                    "last_published_at": None if state == "absent" else "2026-08-12T06:00:00Z",
                    "feedback": (
                        {
                            "id": "check-runs:9001",
                            "kind": "ci",
                            "head_sha": remote_head,
                            "observed_at": "2026-08-12T06:01:00Z",
                            "consumed_by_sha": None,
                        }
                        if intent == "batched-repair" and state != "absent"
                        else None
                    ),
                },
                "actions": {
                    "circuit": "closed",
                    "observed_at": None,
                    "blocker": None,
                    "checks": (
                        [
                        {
                            "workflow": ".github/workflows/verify.yml",
                            "job": "verify",
                            "role": "primary",
                            "head_sha": remote_head,
                            "conclusion": "failure",
                            "completed_at": "2026-08-12T06:01:00Z",
                            "check_run_id": 9001,
                            "check_suite_id": 8001,
                            "workflow_run_id": 7001,
                            "workflow_id": 6001,
                            "job_id": 5001,
                            "app_id": 15368,
                        }
                        ]
                        if intent == "batched-repair" and state != "absent"
                        else []
                    ),
                },
                "captured_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            snapshot_path = Path(directory) / "snapshot.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            argv = [
                    sys.executable,
                    str(PUBLISH_SCRIPT),
                    "publish",
                    "--repo-root",
                    str(root),
                    "--snapshot",
                    str(snapshot_path),
                    "--intent",
                    intent,
                    "--remote",
                    "github",
                    "--branch",
                    target_branch,
                ]
            if external_policy:
                copied_policy = Path(directory) / "external-policy.json"
                copied_policy.write_text(
                    policy_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
                argv.extend(["--policy", str(copied_policy)])
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
            )
            if inspect_manifest:
                self.assertEqual(completed.returncode, 0, completed.stderr)
                relative = subprocess.run(
                    ["git", "-C", root, "rev-parse", "--git-path", "github-delivery/publication-decision.json"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                manifest_path = Path(relative)
                if not manifest_path.is_absolute():
                    manifest_path = root / manifest_path
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                receipt_dir = manifest_path.parent
                digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(
                    manifest["schema"], "github-actions-publish-decision-manifest/v1"
                )
                self.assertEqual(manifest["required_check_name"], "verify")
                self.assertEqual(manifest["decision"]["decision"], "ALLOW")
                self.assertEqual(manifest["decision"]["head_sha"], head)
                self.assertEqual(manifest["inputs"], {
                    "policy_sha256": digest(policy_path),
                    "snapshot_sha256": digest(snapshot_path),
                    "verification_sha256": digest(receipt_dir / "local-verification.json"),
                    "evidence_sha256": digest(receipt_dir / "local-verification-evidence.json"),
                    "contract_sha256": digest(contract_path),
                    "recovery_sha256": None,
                })
            return completed

    def test_draft_first_repair_dispatches_verifier(self) -> None:
        completed = self.render_publication("draft-first")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("gh workflow run", completed.stdout)

    def test_wrapper_persists_content_addressed_decision_manifest(self) -> None:
        completed = self.render_publication("draft-first", inspect_manifest=True)

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_dry_run_refuses_multiple_required_check_names(self) -> None:
        completed = self.render_publication(
            "draft-first", multiple_required_jobs=True
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("exactly one stable check name", completed.stderr)

    def test_universal_repair_relies_on_synchronize_without_duplicate_dispatch(self) -> None:
        completed = self.render_publication("universal")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("git push github", completed.stdout)
        self.assertNotIn("gh workflow run", completed.stdout)

    def test_universal_repair_requires_an_open_pull_request(self) -> None:
        completed = self.render_publication("universal", pull_request_is_open=False)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("repair-requires-ready-pr", completed.stderr)

    def test_universal_repair_requires_the_exact_pull_request_head_ref(self) -> None:
        completed = self.render_publication(
            "universal",
            pull_request_head_ref="agent/expected",
            target_branch="agent/wrong",
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("head ref", completed.stderr)

    def test_publication_requires_the_current_worktree_branch(self) -> None:
        completed = self.render_publication(
            "universal",
            current_branch="agent/current",
            target_branch="agent/example",
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("current worktree branch", completed.stderr)

    def test_external_policy_copy_is_rejected(self) -> None:
        completed = self.render_publication("universal", external_policy=True)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("canonical repository-owned", completed.stderr)

    def test_universal_ready_publication_does_not_dispatch_a_second_run(self) -> None:
        completed = self.render_publication("universal", intent="ready-for-review")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("git push github", completed.stdout)
        self.assertIn("gh pr ready", completed.stdout)
        self.assertNotIn("gh workflow run", completed.stdout)


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

    def test_env_assignment_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(self.payload("env FOO=bar git push github main"))[0]
        )

    def test_absolute_env_wrapper_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(self.payload("/usr/bin/env git push github main"))[0]
        )

    def test_git_config_option_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(
                self.payload("git -c core.askPass=true push github main")
            )[0]
        )

    def test_git_dir_option_from_outside_repo_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        git_dir = self.root / ".git"
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"git --git-dir={git_dir} push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_git_dir_assignment_from_outside_repo_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        git_dir = self.root / ".git"
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"env GIT_DIR={git_dir} git push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_command_local_remote_override_cannot_redirect_forgejo_to_github(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = (
            "git -c remote.forgejo.pushurl=git@github.com:ed3c/example.git "
            "push forgejo main"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_environment_remote_override_cannot_redirect_forgejo_to_github(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = (
            "env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.forgejo.pushurl "
            "GIT_CONFIG_VALUE_0=git@github.com:ed3c/example.git git push forgejo main"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_push_remote_precedence_cannot_hide_bare_github_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        subprocess.run(
            ["git", "-C", self.root, "config", "branch.master.remote", "forgejo"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", self.root, "config", "branch.master.pushRemote", "github"],
            check=True,
        )
        self.assertTrue(GUARD.should_block(self.payload("git push"))[0])

    def test_env_split_string_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(
                self.payload("/usr/bin/env -S 'git push github main'")
            )[0]
        )

    def test_env_split_string_equals_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(
                self.payload("env --split-string='git push github main'")
            )[0]
        )

    def test_env_attached_split_string_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(self.payload("env -Sgit\\ push\\ github\\ main"))[0]
        )

    def test_env_chdir_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"env -C {self.root} git push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_env_long_chdir_equals_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"env --chdir={self.root} git push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_env_search_path_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = f"/usr/bin/env -P /usr/bin git -C {self.root} push github HEAD"
        payload = self.payload(command)
        payload["tool_input"]["cwd"] = str(self.root.parent)
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_cd_double_dash_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": f"cd -- {self.root} && git push github main",
                "cwd": str(self.root.parent),
            },
        }
        self.assertTrue(GUARD.should_block(payload)[0])

    def test_command_local_push_alias_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(
                self.payload("git -c alias.ship=push ship github main")
            )[0]
        )

    def test_command_local_shell_alias_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = (
            f"git -c \"alias.ship=!git -C {self.root} push github\" ship HEAD"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_command_local_dynamic_shell_alias_is_unsupported_in_managed_repo(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = "git -c 'alias.ship=!p=push; git \"$p\" github HEAD' ship"
        blocked, reason = GUARD.should_block(self.payload(command))
        self.assertTrue(blocked)
        self.assertIn("unsupported", reason)

    def test_environment_push_alias_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = (
            "env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=alias.ship "
            "GIT_CONFIG_VALUE_0=push git ship github HEAD"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_repository_push_alias_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        subprocess.run(
            ["git", "-C", self.root, "config", "alias.ship", "push"], check=True
        )
        self.assertTrue(GUARD.should_block(self.payload("git ship github HEAD"))[0])

    def test_config_env_push_alias_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = (
            "env ALIAS_VALUE=push git --config-env=alias.ship=ALIAS_VALUE "
            "ship github HEAD"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_git_dir_identity_wins_over_unrelated_work_tree(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        other = self.root / "unrelated-work-tree"
        other.mkdir()
        command = (
            f"git --git-dir={self.root / '.git'} --work-tree={other} "
            "push github HEAD"
        )
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_second_push_url_cannot_hide_github_destination(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        subprocess.run(
            [
                "git", "-C", self.root, "config", "--add",
                "remote.forgejo.pushurl", "http://localhost:3000/neon/example.git",
            ],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", self.root, "config", "--add",
                "remote.forgejo.pushurl", "git@github.com:ed3c/example.git",
            ],
            check=True,
        )
        self.assertTrue(GUARD.should_block(self.payload("git push forgejo HEAD"))[0])

    def test_shell_command_string_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = f"sh -c 'git -C {self.root} push github HEAD'"
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_login_shell_command_string_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = f"bash -lc 'git -C {self.root} push github HEAD'"
        self.assertTrue(GUARD.should_block(self.payload(command))[0])

    def test_static_shell_forgejo_push_remains_available(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = f"sh -c 'git -C {self.root} push forgejo HEAD'"
        blocked, reason = GUARD.should_block(self.payload(command))
        self.assertFalse(blocked)
        self.assertEqual(reason, "no-managed-github-push")

    def test_dynamic_shell_evaluation_is_unsupported_in_managed_repo(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        command = f"sh -c 'p=push; git -C {self.root} \"$p\" github HEAD'"
        payload = self.payload(command)
        payload["tool_input"]["cwd"] = str(self.root.parent)
        blocked, reason = GUARD.should_block(payload)
        self.assertTrue(blocked)
        self.assertIn("unsupported", reason)

    def test_exec_wrapper_cannot_hide_push(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        self.assertTrue(
            GUARD.should_block(self.payload("exec git push github HEAD"))[0]
        )

    def test_direct_git_push_executable_cannot_bypass_guard(self) -> None:
        path = self.root / ".github-delivery" / "ci-policy.json"
        path.parent.mkdir()
        path.write_text(json.dumps(policy()), encoding="utf-8")
        git_exec_path = subprocess.run(
            ["git", "--exec-path"], check=True, capture_output=True, text=True
        ).stdout.strip()
        command = f"{git_exec_path}/git-push github HEAD"
        self.assertTrue(GUARD.should_block(self.payload(command))[0])


if __name__ == "__main__":
    unittest.main()
