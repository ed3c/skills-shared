#!/usr/bin/env python3
"""The only supported network publication path for managed private repositories."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ci_publish_gate
import ci_workflow_policy


GITHUB_SSH_RE = re.compile(r"(?:ssh://git@github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?$")
GITHUB_HTTPS_RE = re.compile(r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?$")
BRANCH_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")


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


def _load_snapshot(path: Path) -> dict[str, Any]:
    return ci_publish_gate.load_snapshot(path)


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


def verify(repo_root: Path, policy_path: Path) -> Path:
    policy = ci_workflow_policy.load_policy(policy_path)
    ci_workflow_policy.check(repo_root, policy_path)
    _require_clean(repo_root)
    head = _git(repo_root, "rev-parse", "HEAD")
    if len(head) != 40:
        raise PublicationError("HEAD must resolve to a full commit SHA")
    result = _run(policy["local_verification"], repo_root, capture=False)
    if result.returncode != 0:
        raise PublicationError(f"local verification failed with exit {result.returncode}")
    _require_clean(repo_root)
    receipt = {
        "schema": "github-local-verification/v1",
        "repository": policy["repository"],
        "head_sha": head,
        "status": "passed",
        "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "argv": policy["local_verification"],
    }
    destination = _receipt_path(repo_root, "local-verification.json")
    _write_json(destination, receipt)
    return destination


def publish(
    repo_root: Path,
    policy_path: Path,
    snapshot_path: Path,
    remote: str,
    branch: str | None,
    execute: bool,
) -> tuple[str, list[str]]:
    policy = ci_workflow_policy.load_policy(policy_path)
    ci_workflow_policy.check(repo_root, policy_path)
    _require_clean(repo_root)
    snapshot = _load_snapshot(snapshot_path)
    allowed, reason = ci_publish_gate.evaluate(snapshot)
    if not allowed:
        raise PublicationError(reason)

    head = _git(repo_root, "rev-parse", "HEAD")
    if snapshot["local_head"] != head:
        raise PublicationError("snapshot-local-head-does-not-match-git-head")
    if snapshot["repository"] != policy["repository"]:
        raise PublicationError("snapshot-repository-does-not-match-policy")

    receipt_path = _receipt_path(repo_root, "local-verification.json")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PublicationError(f"missing local verification receipt: {error}") from error
    # The gate compares the security-relevant projection; the receipt retains
    # additional provenance without requiring it to be copied into snapshots.
    for key in ("head_sha", "status", "completed_at"):
        if receipt.get(key) != snapshot["local_verification"].get(key):
            raise PublicationError(f"snapshot verification differs from receipt field {key}")
    if receipt.get("repository") != policy["repository"]:
        raise PublicationError("verification receipt repository mismatch")

    remote_url = _git(repo_root, "remote", "get-url", "--push", remote)
    if _repository_from_url(remote_url).lower() != policy["repository"].lower():
        raise PublicationError("push remote repository does not match policy")
    target_branch = branch or _git(repo_root, "branch", "--show-current")
    if not target_branch or BRANCH_RE.fullmatch(target_branch) is None or ".." in target_branch:
        raise PublicationError("branch is empty or unsafe")
    refspec = f"{head}:refs/heads/{target_branch}"
    commands = [["git", "push", remote, refspec]]

    intent = snapshot["intent"]
    pull = snapshot.get("pull_request")
    if intent == "ready-for-review":
        commands.append(
            ["gh", "pr", "ready", str(pull["number"]), "--repo", policy["repository"]]
        )
    elif intent == "repair" and policy["pull_request_mode"] == "draft-first":
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

    rendered = [" ".join(command) for command in commands]
    if not execute:
        return reason, rendered

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
    feedback = snapshot.get("actionable_feedback")
    if intent == "repair" and isinstance(feedback, dict):
        publication["feedback_observed_at"] = feedback.get("observed_at")
    _write_json(_receipt_path(repo_root, "last-publication.json"), publication)
    return reason, rendered


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
    publisher.add_argument("--remote", required=True)
    publisher.add_argument("--branch")
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
            args.remote,
            args.branch,
            args.execute,
        )
    except (PublicationError, ci_publish_gate.SnapshotError, ci_workflow_policy.PolicyError) as error:
        print(f"BLOCK ci-publication:{error}", file=sys.stderr)
        return 1
    mode = "EXECUTED" if args.execute else "DRY-RUN"
    print(f"ALLOW {reason} {mode}")
    for command in rendered:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
