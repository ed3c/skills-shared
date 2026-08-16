#!/usr/bin/env python3
"""The only supported network publication path for managed private repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ci_publish_gate
import ci_workflow_policy
import github_actions_snapshot
import local_verification


GITHUB_SSH_RE = re.compile(r"(?:ssh://git@github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?$")
GITHUB_HTTPS_RE = re.compile(r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?$")
BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
DECISION_MANIFEST_SCHEMA = "github-actions-publish-decision-manifest/v1"


class PublicationError(ValueError):
    """Publication preconditions are absent or inconsistent."""


def _run(argv: list[str], cwd: Path, *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        capture_output=capture,
        text=True,
        check=False,
    )


def _git(repo_root: Path, *args: str) -> str:
    result = _run(["git", *args], repo_root)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise PublicationError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def _repository_from_url(url: str) -> str:
    for pattern in (GITHUB_SSH_RE, GITHUB_HTTPS_RE):
        match = pattern.fullmatch(url)
        if match:
            return match.group(1)
    raise PublicationError("push remote must be an exact github.com SSH or HTTPS URL")


def _receipt_path(repo_root: Path, name: str) -> Path:
    relative = _git(repo_root, "rev-parse", "--git-path", f"github-delivery/{name}")
    value = Path(relative)
    return value if value.is_absolute() else repo_root / value


def _require_clean(repo_root: Path) -> None:
    status = _git(repo_root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise PublicationError("working tree must be clean before verification or publication")


def _require_canonical_policy(repo_root: Path, policy_path: Path) -> Path:
    canonical = (repo_root / ".github-delivery" / "ci-policy.json").resolve()
    if policy_path.resolve() != canonical:
        raise PublicationError("policy must be the canonical repository-owned ci-policy.json")
    _git(repo_root, "ls-files", "--error-unmatch", "--", ".github-delivery/ci-policy.json")
    return canonical


def _require_tracked(repo_root: Path, path: Path, label: str) -> None:
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError as error:
        raise PublicationError(f"{label} resolves outside repository") from error
    _git(repo_root, "ls-files", "--error-unmatch", "--", relative.as_posix())


def _write_json(path: Path, value: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(path)
    except OSError as error:
        raise PublicationError(f"cannot persist receipt {path}: {error}") from error


def _sha256_file(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise PublicationError(f"cannot hash {label} {path}: {error}") from error


def verify(repo_root: Path, policy_path: Path) -> Path:
    policy_path = _require_canonical_policy(repo_root, policy_path)
    policy = ci_workflow_policy.load_policy(policy_path)
    ci_workflow_policy.check(repo_root, policy_path)
    _require_clean(repo_root)
    contract_path = repo_root / policy["local_verification_contract"]
    _require_tracked(repo_root, contract_path, "local verification contract")
    contract = local_verification.load(contract_path, "local verification contract")
    repository_id = contract.get("repository_id")
    if not isinstance(repository_id, int) or isinstance(repository_id, bool):
        raise PublicationError("local verification contract repository_id is invalid")
    receipt = _receipt_path(repo_root, "local-verification.json")
    evidence = _receipt_path(repo_root, "local-verification-evidence.json")
    result = local_verification.verify(
        repo_root, contract_path, repository_id, receipt, evidence
    )
    if result != 0:
        raise PublicationError(f"local verification failed with exit {result}")
    _require_clean(repo_root)
    return receipt


def _capture_live_state(
    repository: str, branch: str, feedback_checks: list[dict[str, str]]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Capture every policy-bound repair feedback check and derive one snapshot."""
    transport = github_actions_snapshot.capture_transport(
        repository, branch, feedback_checks, 30
    )
    observation = github_actions_snapshot.observation_from_transport(transport)
    snapshot = github_actions_snapshot.build(
        observation, feedback_checks, strict=True
    )
    return transport, observation, snapshot


def _require_snapshot_feedback_checks(
    snapshot: dict[str, Any], declared: list[dict[str, str]]
) -> None:
    actions = snapshot.get("actions")
    if not isinstance(actions, dict) or actions.get("circuit") != "closed":
        return
    checks = actions.get("checks")
    if not checks:
        return
    actual = [
        {key: item.get(key) for key in ("workflow", "job", "role")}
        for item in checks
        if isinstance(item, dict)
    ] if isinstance(checks, list) else []
    if actual != declared:
        raise PublicationError(
            "snapshot repair-feedback checks do not match policy declarations"
        )


def publish(
    repo_root: Path,
    policy_path: Path,
    snapshot_path: Path,
    intent: str,
    recovery_path: Path | None,
    remote: str,
    branch: str | None,
    pr_title: str | None,
    pr_body: str | None,
    execute: bool,
) -> tuple[str, list[str]]:
    policy_path = _require_canonical_policy(repo_root, policy_path)
    policy = ci_workflow_policy.load_policy(policy_path)
    ci_workflow_policy.check(repo_root, policy_path)
    _require_clean(repo_root)
    head = _git(repo_root, "rev-parse", "HEAD")
    tree = _git(repo_root, "rev-parse", "HEAD^{tree}")
    current_branch = _git(repo_root, "branch", "--show-current")
    target_branch = branch or current_branch
    if not target_branch or BRANCH_RE.fullmatch(target_branch) is None or ".." in target_branch:
        raise PublicationError("branch is empty or unsafe")
    if current_branch != target_branch:
        raise PublicationError("publication branch must equal the current worktree branch")
    remote_url = _git(repo_root, "remote", "get-url", "--push", remote)
    if _repository_from_url(remote_url).lower() != policy["repository"].lower():
        raise PublicationError("push remote repository does not match policy")
    repair_feedback_checks = ci_workflow_policy.feedback_checks(policy)
    if execute:
        transport, observation, snapshot = _capture_live_state(
            policy["repository"], target_branch, repair_feedback_checks
        )
        _write_json(_receipt_path(repo_root, "live-transport.json"), transport)
        _write_json(_receipt_path(repo_root, "live-observation.json"), observation)
        effective_snapshot_path = _receipt_path(repo_root, "live-snapshot.json")
        _write_json(effective_snapshot_path, snapshot)
    else:
        snapshot = ci_publish_gate.load_object(snapshot_path, "publish snapshot")
        effective_snapshot_path = snapshot_path
    if snapshot.get("repository", {}).get("full_name") != policy["repository"]:
        raise PublicationError("snapshot-repository-does-not-match-policy")
    _require_snapshot_feedback_checks(snapshot, repair_feedback_checks)
    receipt_path = _receipt_path(repo_root, "local-verification.json")
    receipt = ci_publish_gate.load_object(receipt_path, "local verification receipt")
    evidence = ci_publish_gate.load_object(
        _receipt_path(repo_root, "local-verification-evidence.json"),
        "local verification evidence",
    )
    contract_path = repo_root / policy["local_verification_contract"]
    _require_tracked(repo_root, contract_path, "local verification contract")
    contract = ci_publish_gate.load_object(contract_path, "local verification contract")
    recovery = (
        ci_publish_gate.load_object(recovery_path, "billing recovery receipt")
        if recovery_path is not None
        else None
    )
    evaluated_at = datetime.now(UTC)
    decision = ci_publish_gate.evaluate(
        snapshot, receipt, evidence, contract, intent, head, tree, recovery,
        evaluated_at,
    )
    if decision.decision != "ALLOW":
        raise PublicationError(decision.reason)
    decision_manifest = {
        "schema": DECISION_MANIFEST_SCHEMA,
        "evaluated_at": evaluated_at.isoformat().replace("+00:00", "Z"),
        "required_check_name": policy["required_jobs"][0],
        "decision": decision.as_json(),
        "inputs": {
            "policy_sha256": _sha256_file(policy_path, "publication policy"),
            "snapshot_sha256": _sha256_file(effective_snapshot_path, "snapshot"),
            "verification_sha256": _sha256_file(receipt_path, "verification receipt"),
            "evidence_sha256": _sha256_file(
                _receipt_path(repo_root, "local-verification-evidence.json"),
                "verification evidence",
            ),
            "contract_sha256": _sha256_file(contract_path, "verification contract"),
            "recovery_sha256": (
                _sha256_file(recovery_path, "billing recovery receipt")
                if recovery_path is not None
                else None
            ),
        },
    }
    if snapshot["branch"]["name"] != target_branch:
        raise PublicationError(
            "publication target branch must match the exact observed pull request head ref"
        )
    pull = snapshot["pull_request"]
    if intent == "batched-repair" and isinstance(pull.get("feedback"), dict):
        previous_path = _receipt_path(repo_root, "last-publication.json")
        if previous_path.is_file():
            previous = ci_publish_gate.load_object(previous_path, "last publication receipt")
            if previous.get("feedback_id") == pull["feedback"].get("id"):
                raise PublicationError("repair-feedback-already-published")
    if policy["pull_request_mode"] == "universal" and intent != "initial-pr":
        if pull["state"] == "absent":
            raise PublicationError("universal publication requires an open pull request")
    refspec = f"{head}:refs/heads/{target_branch}"
    commands: list[list[str]] = []
    if decision.operation != "ready-transition-only":
        commands.append(["git", "push", remote, refspec])

    if intent == "initial-pr":
        if not pr_title or not pr_body:
            raise PublicationError("initial-pr requires --pr-title and --pr-body")
        commands.append(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                policy["repository"],
                "--head",
                target_branch,
                "--base",
                policy["default_branch"],
                "--draft",
                "--title",
                pr_title,
                "--body",
                pr_body,
            ]
        )
    elif intent == "ready-for-review":
        commands.append(
            ["gh", "pr", "ready", str(pull["number"]), "--repo", policy["repository"]]
        )
    elif intent == "batched-repair" and policy["pull_request_mode"] == "draft-first":
        commands.append(
            [
                "gh",
                "workflow",
                "run",
                policy["workflow"],
                "--repo",
                policy["repository"],
                "--ref",
                target_branch,
            ]
        )

    # Persist admission only after every zero-network publication precondition
    # has passed.  A branch/PR/idempotence refusal must not leave an ALLOW
    # manifest that a later proof bundle could mistake for a complete decision.
    _write_json(_receipt_path(repo_root, "publication-decision.json"), decision_manifest)

    rendered = [" ".join(command) for command in commands]
    if not execute:
        return decision.reason, rendered

    for command in commands:
        result = _run(command, repo_root, capture=False)
        if result.returncode != 0:
            raise PublicationError(f"command failed with exit {result.returncode}: {' '.join(command)}")
    publication = {
        "schema": "github-ci-publication/v1",
        "repository": policy["repository"],
        "head_sha": head,
        "branch": target_branch,
        "intent": intent,
        "published_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    feedback = pull.get("feedback")
    if intent == "batched-repair" and isinstance(feedback, dict):
        publication["feedback_id"] = feedback.get("id")
    _write_json(_receipt_path(repo_root, "last-publication.json"), publication)
    return decision.reason, rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    verifier = commands.add_parser("verify")
    verifier.add_argument("--repo-root", type=Path, required=True)
    verifier.add_argument("--policy", type=Path)

    publisher = commands.add_parser("publish")
    publisher.add_argument("--repo-root", type=Path, required=True)
    publisher.add_argument("--policy", type=Path)
    publisher.add_argument("--snapshot", type=Path, required=True)
    publisher.add_argument("--intent", choices=sorted(ci_publish_gate.INTENTS), required=True)
    publisher.add_argument("--recovery", type=Path)
    publisher.add_argument("--remote", required=True)
    publisher.add_argument("--branch")
    publisher.add_argument("--pr-title")
    publisher.add_argument("--pr-body")
    publisher.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    policy_path = args.policy or repo_root / ".github-delivery" / "ci-policy.json"
    try:
        if args.command == "verify":
            receipt = verify(repo_root, policy_path)
            print(f"PASS local-verification receipt={receipt}")
            return 0
        reason, rendered = publish(
            repo_root,
            policy_path,
            args.snapshot,
            args.intent,
            args.recovery,
            args.remote,
            args.branch,
            args.pr_title,
            args.pr_body,
            args.execute,
        )
    except (
        PublicationError,
        ci_publish_gate.InputError,
        ci_workflow_policy.PolicyError,
        github_actions_snapshot.CaptureError,
        github_actions_snapshot.SnapshotError,
        local_verification.VerificationError,
    ) as error:
        print(f"BLOCK ci-publication:{error}", file=sys.stderr)
        return 1
    mode = "EXECUTED" if args.execute else "DRY-RUN"
    print(f"ALLOW {reason} {mode}")
    for command in rendered:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
