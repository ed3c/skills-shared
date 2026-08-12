#!/usr/bin/env python3
"""Admit deliberate GitHub CI publications without performing a push."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA = "github-ci-publish-snapshot/v1"
ALLOWED_INTENTS = {"initial-pr", "ready-for-review", "repair"}
SHA_RE = re.compile(r"[0-9a-f]{40}")
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


class SnapshotError(ValueError):
    """The supplied publication evidence is malformed."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise SnapshotError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SnapshotError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise SnapshotError(f"{field} must include a timezone")
    return parsed


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise SnapshotError(f"{field} must be a 40-character lowercase SHA")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotError(f"{field} must be an object")
    return value


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SnapshotError(f"unreadable snapshot: {error}") from error
    if not isinstance(value, dict):
        raise SnapshotError("snapshot root must be an object")
    return value


def evaluate(snapshot: dict[str, Any]) -> tuple[bool, str]:
    if snapshot.get("schema") != SCHEMA:
        raise SnapshotError(f"schema must be {SCHEMA}")
    repository = snapshot.get("repository")
    if not isinstance(repository, str) or REPOSITORY_RE.fullmatch(repository) is None:
        raise SnapshotError("repository must be OWNER/REPOSITORY")
    owner = snapshot.get("repository_owner")
    if not isinstance(owner, str) or not owner:
        raise SnapshotError("repository_owner must be a non-empty login")
    if repository.split("/", 1)[0].lower() != owner.lower():
        raise SnapshotError("repository_owner must match the repository owner")
    if snapshot.get("private") is not True:
        raise SnapshotError("private must be true for this cost-admission contract")

    intent = snapshot.get("intent")
    if not isinstance(intent, str):
        raise SnapshotError("intent must be a string")
    if intent not in ALLOWED_INTENTS:
        return False, f"unsupported-intent:{intent}"

    local_head = _sha(snapshot.get("local_head"), "local_head")
    verification = _object(snapshot.get("local_verification"), "local_verification")
    if _sha(verification.get("head_sha"), "local_verification.head_sha") != local_head:
        return False, "verification-head-mismatch"
    if verification.get("status") != "passed":
        return False, "local-verification-not-passed"
    verification_at = _timestamp(
        verification.get("completed_at"), "local_verification.completed_at"
    )

    blocker = snapshot.get("billing_blocker")
    if blocker is not None:
        blocker = _object(blocker, "billing_blocker")
        if blocker.get("kind") != "account-billing-no-runner":
            raise SnapshotError("billing_blocker.kind is unsupported")
        blocked_at = _timestamp(blocker.get("observed_at"), "billing_blocker.observed_at")
        recovery = snapshot.get("recovery")
        if recovery is None:
            return False, "billing-circuit-open"
        recovery = _object(recovery, "recovery")
        if recovery.get("author") != owner or recovery.get("status") != "actions-restored":
            return False, "billing-recovery-untrusted"
        if _timestamp(recovery.get("recovered_at"), "recovery.recovered_at") <= blocked_at:
            return False, "billing-recovery-stale"

    pull = snapshot.get("pull_request")
    if intent == "initial-pr":
        if pull is not None:
            return False, "initial-pr-already-exists"
        return True, intent

    pull = _object(pull, "pull_request")
    if not isinstance(pull.get("number"), int) or pull["number"] < 1:
        raise SnapshotError("pull_request.number must be positive")
    remote_head = _sha(pull.get("remote_head"), "pull_request.remote_head")
    if remote_head == local_head:
        return False, "remote-head-already-current"

    if intent == "ready-for-review":
        if pull.get("is_draft") is not True:
            return False, "pull-request-already-ready"
        return True, intent

    feedback = _object(snapshot.get("actionable_feedback"), "actionable_feedback")
    if feedback.get("actionable") is not True:
        return False, "feedback-not-actionable"
    if _sha(feedback.get("head_sha"), "actionable_feedback.head_sha") != remote_head:
        return False, "feedback-head-mismatch"
    feedback_at = _timestamp(feedback.get("observed_at"), "actionable_feedback.observed_at")
    if verification_at <= feedback_at:
        return False, "verification-predates-feedback"
    last_publication = snapshot.get("last_publication")
    if isinstance(last_publication, dict):
        if (
            last_publication.get("intent") == "repair"
            and last_publication.get("feedback_observed_at") == feedback.get("observed_at")
        ):
            return False, "feedback-already-published"
    return True, intent


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()

    try:
        allowed, reason = evaluate(load_snapshot(args.snapshot))
    except SnapshotError as error:
        print(f"BLOCK malformed-snapshot:{error}", file=sys.stderr)
        return 2
    if allowed:
        print(f"ALLOW {reason}")
        return 0
    print(f"BLOCK {reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
