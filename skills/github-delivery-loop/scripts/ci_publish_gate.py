#!/usr/bin/env python3
"""Fail-closed publication gate for private-repository GitHub Actions.

The gate is intentionally zero-network. A trusted sync step captures GitHub PR,
check, and billing state in a versioned snapshot. A repository-local verifier
produces a receipt for the exact local HEAD. This command decides whether one
remote publication is admitted without turning every local commit into a billed
GitHub Actions run.

Exit codes:
  0  ALLOW
  2  BLOCK by publication policy
  64 malformed input, missing evidence, or local Git failure
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA = "github-actions-publish-snapshot/v1"
VERIFICATION_SCHEMA = "github-delivery-local-verification/v1"
RECOVERY_SCHEMA = "github-actions-billing-recovery/v1"
DECISION_SCHEMA = "github-actions-publish-decision/v1"
INTENTS = {"initial-pr", "ready-for-review", "batched-repair"}
PR_STATES = {"absent", "draft", "ready"}
CIRCUITS = {"closed", "billing-open", "unknown"}
CHECK_CONCLUSIONS = {
    "success",
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "neutral",
    "skipped",
}
ACTIONABLE_CI_CONCLUSIONS = {"failure", "timed_out", "action_required"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class InputError(ValueError):
    """The supplied snapshot or receipt is not a trustworthy policy input."""


@dataclass(frozen=True)
class Decision:
    decision: str
    reason: str
    intent: str
    head_sha: str | None
    operation: str | None = None
    detail: str | None = None

    def as_json(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": DECISION_SCHEMA,
            "decision": self.decision,
            "reason": self.reason,
            "intent": self.intent,
            "head_sha": self.head_sha,
            "operation": self.operation,
        }
        if self.detail is not None:
            value["detail"] = self.detail
        return value


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"missing {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"unreadable {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} root must be an object")
    return value


def exact_fields(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise InputError(f"{label} fields drifted: missing={missing} extra={extra}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{label} must be a non-empty string")
    return value


def require_sha(value: Any, label: str) -> str:
    text = require_string(value, label)
    if SHA_RE.fullmatch(text) is None:
        raise InputError(f"{label} must be an exact lowercase 40-character SHA")
    return text


def optional_sha(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return require_sha(value, label)


def require_digest(value: Any, label: str) -> str:
    text = require_string(value, label)
    if DIGEST_RE.fullmatch(text) is None:
        raise InputError(f"{label} must be a lowercase SHA-256")
    return text


def parse_time(value: Any, label: str) -> datetime:
    text = require_string(value, label)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InputError(f"{label} must be ISO-8601 with timezone") from exc
    if parsed.tzinfo is None:
        raise InputError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def optional_time(value: Any, label: str) -> datetime | None:
    if value is None:
        return None
    return parse_time(value, label)


def git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise InputError(
            f"cannot resolve local Git HEAD at {repo_root}: {result.stderr.strip()}"
        )
    return require_sha(result.stdout.strip(), "local Git HEAD")


def validate_repository(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("snapshot.repository must be an object")
    exact_fields(
        value,
        {"full_name", "repository_id", "owner_login", "private"},
        "snapshot.repository",
    )
    full_name = require_string(value["full_name"], "repository.full_name")
    if REPO_RE.fullmatch(full_name) is None:
        raise InputError("repository.full_name must be owner/name")
    if not isinstance(value["repository_id"], int) or value["repository_id"] <= 0:
        raise InputError("repository.repository_id must be a positive integer")
    owner = require_string(value["owner_login"], "repository.owner_login")
    if full_name.split("/", 1)[0].casefold() != owner.casefold():
        raise InputError("repository owner does not match full_name")
    if value["private"] is not True:
        raise InputError("this gate is for private repositories and requires private=true")
    return value


def validate_feedback(value: Any, remote_head: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise InputError("pull_request.feedback must be an object or null")
    exact_fields(
        value,
        {"id", "kind", "head_sha", "observed_at", "consumed_by_sha"},
        "pull_request.feedback",
    )
    require_string(value["id"], "feedback.id")
    if value["kind"] not in {"ci", "review"}:
        raise InputError("feedback.kind must be ci or review")
    feedback_head = require_sha(value["head_sha"], "feedback.head_sha")
    if remote_head is not None and feedback_head != remote_head:
        raise InputError("feedback.head_sha must match the observed PR head")
    parse_time(value["observed_at"], "feedback.observed_at")
    optional_sha(value["consumed_by_sha"], "feedback.consumed_by_sha")
    return value


def validate_pull_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("snapshot.pull_request must be an object")
    exact_fields(
        value,
        {
            "number",
            "state",
            "head_sha",
            "last_published_sha",
            "last_published_at",
            "feedback",
        },
        "snapshot.pull_request",
    )
    state = value["state"]
    if state not in PR_STATES:
        raise InputError(f"pull_request.state must be one of {sorted(PR_STATES)}")
    number = value["number"]
    head = optional_sha(value["head_sha"], "pull_request.head_sha")
    last_sha = optional_sha(
        value["last_published_sha"], "pull_request.last_published_sha"
    )
    last_at = optional_time(
        value["last_published_at"], "pull_request.last_published_at"
    )

    if state == "absent":
        if any(item is not None for item in (number, head, last_sha, last_at)):
            raise InputError("absent PR may not carry number/head/publication state")
    else:
        if not isinstance(number, int) or number <= 0:
            raise InputError("draft/ready PR requires a positive number")
        if head is None or last_sha is None or last_at is None:
            raise InputError("draft/ready PR requires exact head and last publication")
        if head != last_sha:
            raise InputError("observed PR head must equal last_published_sha")

    validate_feedback(value["feedback"], head)
    return value


def validate_latest_check(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise InputError("actions.latest_check must be an object or null")
    exact_fields(
        value,
        {"head_sha", "conclusion", "completed_at"},
        "actions.latest_check",
    )
    require_sha(value["head_sha"], "latest_check.head_sha")
    if value["conclusion"] not in CHECK_CONCLUSIONS:
        raise InputError("latest_check.conclusion is unsupported")
    parse_time(value["completed_at"], "latest_check.completed_at")
    return value


def validate_actions(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError("snapshot.actions must be an object")
    exact_fields(
        value,
        {"circuit", "observed_at", "blocker", "latest_check"},
        "snapshot.actions",
    )
    circuit = value["circuit"]
    if circuit not in CIRCUITS:
        raise InputError(f"actions.circuit must be one of {sorted(CIRCUITS)}")
    observed = optional_time(value["observed_at"], "actions.observed_at")
    blocker = value["blocker"]
    if blocker not in {None, "billing-or-spending-limit", "runner-unavailable", "other"}:
        raise InputError("actions.blocker is unsupported")
    validate_latest_check(value["latest_check"])
    if circuit == "closed" and blocker is not None:
        raise InputError("closed Actions circuit may not carry a blocker")
    if circuit == "billing-open":
        if observed is None or blocker != "billing-or-spending-limit":
            raise InputError(
                "billing-open circuit requires observed_at and billing-or-spending-limit"
            )
    if circuit == "unknown" and blocker is None:
        raise InputError("unknown Actions circuit must name the observation problem")
    return value


def validate_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    exact_fields(
        value,
        {"schema", "repository", "pull_request", "actions"},
        "snapshot",
    )
    if value["schema"] != SNAPSHOT_SCHEMA:
        raise InputError(f"snapshot.schema must be {SNAPSHOT_SCHEMA}")
    validate_repository(value["repository"])
    validate_pull_request(value["pull_request"])
    validate_actions(value["actions"])
    return value


def validate_verification(
    value: dict[str, Any], repository_id: int, actual_head: str
) -> dict[str, Any]:
    exact_fields(
        value,
        {
            "schema",
            "repository_id",
            "head_sha",
            "status",
            "verified_at",
            "evidence_sha256",
            "commands",
        },
        "local verification",
    )
    if value["schema"] != VERIFICATION_SCHEMA:
        raise InputError(f"verification.schema must be {VERIFICATION_SCHEMA}")
    if value["repository_id"] != repository_id:
        raise InputError("verification repository identity does not match snapshot")
    receipt_head = require_sha(value["head_sha"], "verification.head_sha")
    if receipt_head != actual_head:
        raise InputError("verification is stale for the local Git HEAD")
    if value["status"] != "PASS":
        raise InputError("local verification status must be PASS")
    parse_time(value["verified_at"], "verification.verified_at")
    require_digest(value["evidence_sha256"], "verification.evidence_sha256")
    commands = value["commands"]
    if (
        not isinstance(commands, list)
        or not commands
        or any(not isinstance(command, str) or not command.strip() for command in commands)
    ):
        raise InputError("verification.commands must contain executed commands")
    return value


def validate_recovery(
    value: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any]:
    exact_fields(
        value,
        {
            "schema",
            "repository_id",
            "owner_login",
            "blocker_observed_at",
            "recovered_at",
            "note",
        },
        "billing recovery",
    )
    if value["schema"] != RECOVERY_SCHEMA:
        raise InputError(f"recovery.schema must be {RECOVERY_SCHEMA}")
    repository = snapshot["repository"]
    actions = snapshot["actions"]
    if value["repository_id"] != repository["repository_id"]:
        raise InputError("recovery repository identity does not match snapshot")
    if value["owner_login"].casefold() != repository["owner_login"].casefold():
        raise InputError("recovery must be authored by the repository owner")
    blocked_at = parse_time(
        value["blocker_observed_at"], "recovery.blocker_observed_at"
    )
    observed_at = parse_time(actions["observed_at"], "actions.observed_at")
    if blocked_at != observed_at:
        raise InputError("recovery does not name the current billing blocker")
    recovered_at = parse_time(value["recovered_at"], "recovery.recovered_at")
    if recovered_at <= observed_at:
        raise InputError("recovery timestamp must be later than the blocker")
    require_string(value["note"], "recovery.note")
    return value


def block(reason: str, intent: str, head: str, detail: str | None = None) -> Decision:
    return Decision("BLOCK", reason, intent, head, detail=detail)


def evaluate(
    snapshot: dict[str, Any],
    verification: dict[str, Any],
    intent: str,
    actual_head: str,
    recovery: dict[str, Any] | None,
) -> Decision:
    if intent not in INTENTS:
        raise InputError(f"intent must be one of {sorted(INTENTS)}")
    validate_snapshot(snapshot)
    repository = snapshot["repository"]
    validate_verification(verification, repository["repository_id"], actual_head)
    actions = snapshot["actions"]
    pr = snapshot["pull_request"]

    if actions["circuit"] == "unknown":
        return block("actions-state-unknown", intent, actual_head)
    if actions["circuit"] == "billing-open":
        if recovery is None:
            return block("billing-circuit-open", intent, actual_head)
        try:
            validate_recovery(recovery, snapshot)
        except InputError as exc:
            return block("billing-recovery-invalid", intent, actual_head, str(exc))

    if intent == "initial-pr":
        if pr["state"] != "absent":
            return block("initial-pr-already-exists", intent, actual_head)
        return Decision(
            "ALLOW",
            "allow-initial-pr",
            intent,
            actual_head,
            operation="push-and-create-draft-pr",
        )

    if intent == "ready-for-review":
        if pr["state"] != "draft":
            return block("ready-requires-draft-pr", intent, actual_head)
        operation = (
            "ready-transition-only"
            if actual_head == pr["head_sha"]
            else "push-and-ready-transition"
        )
        return Decision(
            "ALLOW",
            "allow-ready-for-review",
            intent,
            actual_head,
            operation=operation,
        )

    if pr["state"] != "ready":
        return block("repair-requires-ready-pr", intent, actual_head)
    if actual_head == pr["head_sha"]:
        return block("repair-has-no-new-head", intent, actual_head)
    feedback = pr["feedback"]
    if feedback is None:
        return block("repair-no-actionable-feedback", intent, actual_head)
    if feedback["consumed_by_sha"] is not None:
        return block("repair-feedback-already-consumed", intent, actual_head)
    observed = parse_time(feedback["observed_at"], "feedback.observed_at")
    last_published = parse_time(
        pr["last_published_at"], "pull_request.last_published_at"
    )
    if observed <= last_published:
        return block("repair-feedback-not-newer-than-publication", intent, actual_head)

    if feedback["kind"] == "ci":
        check = actions["latest_check"]
        if check is None:
            return block("repair-ci-check-missing", intent, actual_head)
        if check["head_sha"] != pr["head_sha"]:
            return block("repair-ci-check-stale", intent, actual_head)
        if check["conclusion"] not in ACTIONABLE_CI_CONCLUSIONS:
            return block("repair-ci-check-not-actionable", intent, actual_head)

    return Decision(
        "ALLOW",
        "allow-batched-repair",
        intent,
        actual_head,
        operation="single-batched-repair-push",
    )


def emit(decision: Decision, json_output: bool, stream: Any = sys.stdout) -> None:
    if json_output:
        print(json.dumps(decision.as_json(), sort_keys=True), file=stream)
        return
    suffix = f" operation={decision.operation}" if decision.operation else ""
    if decision.detail:
        suffix += f" detail={decision.detail}"
    print(f"{decision.decision} {decision.reason}{suffix}", file=stream)


def fixture_snapshot(head: str) -> dict[str, Any]:
    return {
        "schema": SNAPSHOT_SCHEMA,
        "repository": {
            "full_name": "ed3c/skills-shared",
            "repository_id": 1326262274,
            "owner_login": "ed3c",
            "private": True,
        },
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
    }


def fixture_verification(head: str) -> dict[str, Any]:
    return {
        "schema": VERIFICATION_SCHEMA,
        "repository_id": 1326262274,
        "head_sha": head,
        "status": "PASS",
        "verified_at": "2026-08-12T05:00:00Z",
        "evidence_sha256": "a" * 64,
        "commands": ["bash skills/github-delivery-loop/tests/run-all.sh"],
    }


def expect(
    name: str,
    expected_decision: str,
    expected_reason: str,
    snapshot: dict[str, Any],
    verification: dict[str, Any],
    intent: str,
    head: str,
    recovery: dict[str, Any] | None = None,
) -> None:
    result = evaluate(snapshot, verification, intent, head, recovery)
    if result.decision != expected_decision or result.reason != expected_reason:
        raise InputError(
            f"selftest {name}: got {result.decision}/{result.reason}, "
            f"want {expected_decision}/{expected_reason}"
        )


def selftest() -> None:
    head = "1" * 40
    new_head = "2" * 40
    base = fixture_snapshot(head)
    verification = fixture_verification(head)
    expect(
        "initial",
        "ALLOW",
        "allow-initial-pr",
        base,
        verification,
        "initial-pr",
        head,
    )

    stale = json.loads(json.dumps(verification))
    stale["head_sha"] = "0" * 40
    try:
        evaluate(base, stale, "initial-pr", head, None)
    except InputError:
        pass
    else:
        raise InputError("selftest stale-local-verification unexpectedly passed")

    draft = json.loads(json.dumps(base))
    draft["pull_request"].update(
        {
            "number": 42,
            "state": "draft",
            "head_sha": head,
            "last_published_sha": head,
            "last_published_at": "2026-08-12T05:01:00Z",
        }
    )
    expect(
        "repeat-initial",
        "BLOCK",
        "initial-pr-already-exists",
        draft,
        verification,
        "initial-pr",
        head,
    )
    expect(
        "ready",
        "ALLOW",
        "allow-ready-for-review",
        draft,
        verification,
        "ready-for-review",
        head,
    )

    ready = json.loads(json.dumps(draft))
    ready["pull_request"]["state"] = "ready"
    ready["pull_request"]["feedback"] = {
        "id": "review:9001",
        "kind": "review",
        "head_sha": head,
        "observed_at": "2026-08-12T05:02:00Z",
        "consumed_by_sha": None,
    }
    new_verification = fixture_verification(new_head)
    expect(
        "review-repair",
        "ALLOW",
        "allow-batched-repair",
        ready,
        new_verification,
        "batched-repair",
        new_head,
    )

    consumed = json.loads(json.dumps(ready))
    consumed["pull_request"]["feedback"]["consumed_by_sha"] = new_head
    expect(
        "consumed-feedback",
        "BLOCK",
        "repair-feedback-already-consumed",
        consumed,
        new_verification,
        "batched-repair",
        new_head,
    )

    ci = json.loads(json.dumps(ready))
    ci["pull_request"]["feedback"]["kind"] = "ci"
    ci["actions"]["latest_check"] = {
        "head_sha": "3" * 40,
        "conclusion": "failure",
        "completed_at": "2026-08-12T05:02:00Z",
    }
    expect(
        "older-ci-head",
        "BLOCK",
        "repair-ci-check-stale",
        ci,
        new_verification,
        "batched-repair",
        new_head,
    )

    billing = json.loads(json.dumps(base))
    billing["actions"] = {
        "circuit": "billing-open",
        "observed_at": "2026-08-12T05:03:00Z",
        "blocker": "billing-or-spending-limit",
        "latest_check": None,
    }
    expect(
        "billing-open",
        "BLOCK",
        "billing-circuit-open",
        billing,
        verification,
        "initial-pr",
        head,
    )

    stale_recovery = {
        "schema": RECOVERY_SCHEMA,
        "repository_id": 1326262274,
        "owner_login": "ed3c",
        "blocker_observed_at": "2026-08-12T05:03:00Z",
        "recovered_at": "2026-08-12T05:02:59Z",
        "note": "billing reviewed",
    }
    expect(
        "stale-recovery",
        "BLOCK",
        "billing-recovery-invalid",
        billing,
        verification,
        "initial-pr",
        head,
        stale_recovery,
    )

    recovery = dict(stale_recovery)
    recovery["recovered_at"] = "2026-08-12T05:04:00Z"
    expect(
        "recovered",
        "ALLOW",
        "allow-initial-pr",
        billing,
        verification,
        "initial-pr",
        head,
        recovery,
    )
    print("SELFTEST GREEN: GitHub Actions publication gate (10 policy cases)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ci_publish_gate.py")
    parser.add_argument("--selftest", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--snapshot", type=Path, required=True)
    evaluate_parser.add_argument("--verification", type=Path, required=True)
    evaluate_parser.add_argument("--recovery", type=Path)
    evaluate_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    evaluate_parser.add_argument("--intent", choices=sorted(INTENTS), required=True)
    evaluate_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        if args.command is not None:
            parser.error("--selftest cannot be combined with a command")
        try:
            selftest()
            return 0
        except (InputError, OSError) as exc:
            print(f"SELFTEST RED: {exc}", file=sys.stderr)
            return 1

    if args.command != "evaluate":
        parser.error("evaluate or --selftest is required")

    try:
        snapshot = load_object(args.snapshot, "publish snapshot")
        verification = load_object(args.verification, "local verification receipt")
        recovery = (
            load_object(args.recovery, "billing recovery receipt")
            if args.recovery is not None
            else None
        )
        actual_head = git_head(args.repo_root.resolve())
        decision = evaluate(
            snapshot,
            verification,
            args.intent,
            actual_head,
            recovery,
        )
        emit(decision, args.json)
        return 0 if decision.decision == "ALLOW" else 2
    except InputError as exc:
        decision = Decision(
            "BLOCK",
            "invalid-policy-input",
            args.intent,
            None,
            detail=str(exc),
        )
        emit(decision, args.json, stream=sys.stderr)
        return 64
    except OSError as exc:
        print(f"BLOCK local-io-failure detail={exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
