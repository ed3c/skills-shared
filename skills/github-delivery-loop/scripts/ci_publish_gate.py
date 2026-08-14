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
import hashlib
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


def canonical(value: Any) -> bytes:
    """The producer's canonical form. Any other encoding computes a different
    digest and would reject every honest receipt."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest_of(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def git_tree(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise InputError(
            f"cannot resolve local Git tree at {repo_root}: {result.stderr.strip()}"
        )
    return require_sha(result.stdout.strip(), "local Git tree")


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


EVIDENCE_SCHEMA = "github-delivery-local-verification-evidence/v1"

COMMAND_FIELDS = {
    "id", "argv", "cwd", "timeout_seconds", "max_output_bytes", "started_at",
    "duration_ms", "exit", "timed_out", "spawn_error", "stdout_bytes",
    "stderr_bytes", "stdout_sha256", "stderr_sha256", "stdout_truncated",
    "stderr_truncated",
}


def require_relative(value: Any, label: str) -> str:
    """A repository-relative path, never one that names this machine.

    An absolute path in a receipt is either a machine-local path that will not
    exist for the next reader, or an escape from the subject the receipt claims
    to describe. Both make the evidence unverifiable rather than merely untidy.
    """
    text = require_string(value, label)
    if text.startswith("/") or text.startswith("~") or ":\\" in text:
        raise InputError(f"{label} must be repository-relative, not {text!r}")
    if ".." in Path(text).parts:
        raise InputError(f"{label} must not traverse out of the repository: {text!r}")
    return text


def validate_command_evidence(value: Any, index: int) -> str:
    label = f"evidence.commands[{index}]"
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    exact_fields(value, COMMAND_FIELDS, label)
    command_id = require_string(value["id"], f"{label}.id")
    argv = value["argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or not item.strip() for item in argv)
    ):
        raise InputError(f"{label}.argv must be a non-empty array of arguments")
    # An argv that is one string is a shell string, which is the thing the
    # producer's fixed-command contract exists to forbid.
    if len(argv) == 1 and any(ch in argv[0] for ch in ";|&$`\n"):
        raise InputError(f"{label}.argv looks like a shell string, not an argument vector")
    require_relative(value["cwd"], f"{label}.cwd")
    for field in ("timeout_seconds", "max_output_bytes", "duration_ms",
                  "stdout_bytes", "stderr_bytes"):
        number = value[field]
        if not isinstance(number, int) or isinstance(number, bool) or number < 0:
            raise InputError(f"{label}.{field} must be a non-negative integer")
    parse_time(value["started_at"], f"{label}.started_at")
    for field in ("timed_out", "stdout_truncated", "stderr_truncated"):
        if not isinstance(value[field], bool):
            raise InputError(f"{label}.{field} must be a boolean")
    require_digest(value["stdout_sha256"], f"{label}.stdout_sha256")
    require_digest(value["stderr_sha256"], f"{label}.stderr_sha256")

    # A receipt says PASS; these say whether anything actually ran to completion.
    if value["spawn_error"] is not None:
        raise InputError(f"{label} never started: {value['spawn_error']}")
    if value["timed_out"]:
        raise InputError(f"{label} timed out, so its result is not a result")
    if value["stdout_truncated"] or value["stderr_truncated"]:
        raise InputError(
            f"{label} output was truncated, so its digests describe a prefix and "
            "cannot be compared against anything"
        )
    if value["exit"] != 0:
        raise InputError(f"{label} exited {value['exit']!r}")
    return command_id


def validate_verification_evidence(
    evidence: dict[str, Any],
    receipt: dict[str, Any],
    repository_id: int,
    actual_head: str,
    actual_tree: str,
) -> dict[str, Any]:
    """Read the bytes the receipt's digest names.

    The compact receipt carries `evidence_sha256`, and until this existed the
    gate checked that the field looked like a digest and never read what it
    pointed at. A digest nobody recomputes is a claim, not a binding: any
    detailed evidence at all -- a failing run, a different repository, a
    different commit -- authorized publication as long as the compact receipt
    said PASS.
    """
    if not isinstance(evidence, dict):
        raise InputError("verification evidence root must be an object")
    exact_fields(
        evidence,
        {
            "schema", "repository_id", "head_sha", "tree_sha", "contract_sha256",
            "verified_at", "clean_subject", "commands", "status", "content_sha256",
        },
        "verification evidence",
    )
    if evidence["schema"] != EVIDENCE_SCHEMA:
        raise InputError(f"evidence.schema must be {EVIDENCE_SCHEMA}")
    if evidence["repository_id"] != repository_id:
        raise InputError("evidence repository identity does not match snapshot")
    if require_sha(evidence["head_sha"], "evidence.head_sha") != actual_head:
        raise InputError("evidence is stale for the local Git HEAD")
    if require_sha(evidence["tree_sha"], "evidence.tree_sha") != actual_tree:
        raise InputError("evidence describes a different tree than the local HEAD")
    require_digest(evidence["contract_sha256"], "evidence.contract_sha256")
    parse_time(evidence["verified_at"], "evidence.verified_at")
    if evidence["clean_subject"] is not True:
        raise InputError("evidence was produced from a dirty subject")
    if evidence["status"] != "PASS":
        raise InputError("evidence status must be PASS")
    if evidence["verified_at"] != receipt["verified_at"]:
        raise InputError("evidence and receipt describe different verification runs")

    commands = evidence["commands"]
    if not isinstance(commands, list) or not commands:
        raise InputError("evidence.commands must record every executed command")
    ids = [validate_command_evidence(item, index) for index, item in enumerate(commands)]
    if len(set(ids)) != len(ids):
        raise InputError("evidence.commands repeats a command id")
    # Ordered, not merely equal as sets: the receipt lists what the contract ran
    # in the order it ran, and a reordering is a different execution.
    if ids != receipt["commands"]:
        raise InputError(
            f"evidence commands do not match the receipt in order: "
            f"evidence={ids} receipt={receipt['commands']}"
        )

    # Two digests, computed the way the producer computes them. `content_sha256`
    # covers the evidence without itself; the receipt's `evidence_sha256` covers
    # the evidence including it. Checking one and not the other leaves the other
    # free to disagree.
    body = {key: value for key, value in evidence.items() if key != "content_sha256"}
    if digest_of(body) != evidence["content_sha256"]:
        raise InputError("evidence content digest does not match its own bytes")
    if digest_of(evidence) != receipt["evidence_sha256"]:
        raise InputError(
            "the receipt's evidence_sha256 does not name these evidence bytes"
        )
    return evidence


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
    evidence: dict[str, Any],
    intent: str,
    actual_head: str,
    actual_tree: str,
    recovery: dict[str, Any] | None,
) -> Decision:
    if intent not in INTENTS:
        raise InputError(f"intent must be one of {sorted(INTENTS)}")
    validate_snapshot(snapshot)
    repository = snapshot["repository"]
    validate_verification(verification, repository["repository_id"], actual_head)
    validate_verification_evidence(
        evidence, verification, repository["repository_id"], actual_head, actual_tree
    )
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


FIXTURE_TREE = "e" * 40


def fixture_command(command_id: str) -> dict[str, Any]:
    return {
        "id": command_id,
        "argv": ["bash", "skills/github-delivery-loop/tests/run-all.sh"],
        "cwd": ".",
        "timeout_seconds": 600,
        "max_output_bytes": 1048576,
        "started_at": "2026-08-12T05:00:00Z",
        "duration_ms": 1200,
        "exit": 0,
        "timed_out": False,
        "spawn_error": None,
        "stdout_bytes": 12,
        "stderr_bytes": 0,
        "stdout_sha256": "b" * 64,
        "stderr_sha256": "c" * 64,
        "stdout_truncated": False,
        "stderr_truncated": False,
    }


def fixture_pair(head: str, tree: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """A receipt and the evidence its digest names, built the way the producer
    builds them: `content_sha256` over the body, `evidence_sha256` over the
    whole. Hand-written digests would make every negative control pass for the
    wrong reason."""
    command_id = "bash skills/github-delivery-loop/tests/run-all.sh"
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "repository_id": 1326262274,
        "head_sha": head,
        "tree_sha": tree,
        "contract_sha256": "d" * 64,
        "verified_at": "2026-08-12T05:00:00Z",
        "clean_subject": True,
        "commands": [fixture_command(command_id)],
        "status": "PASS",
    }
    evidence["content_sha256"] = digest_of(evidence)
    receipt = {
        "schema": VERIFICATION_SCHEMA,
        "repository_id": 1326262274,
        "head_sha": head,
        "status": "PASS",
        "verified_at": "2026-08-12T05:00:00Z",
        "evidence_sha256": digest_of(evidence),
        "commands": [command_id],
    }
    return receipt, evidence


def reseal(receipt: dict[str, Any], evidence: dict[str, Any]) -> None:
    """Re-derive both digests after a mutation.

    Without this a mutation is caught by the digest check rather than by the
    rule under test, and every negative control would pass while proving
    nothing about the rule it names."""
    body = {key: value for key, value in evidence.items() if key != "content_sha256"}
    evidence["content_sha256"] = digest_of(body)
    receipt["evidence_sha256"] = digest_of(evidence)


def expect(
    name: str,
    expected_decision: str,
    expected_reason: str,
    snapshot: dict[str, Any],
    pair: tuple[dict[str, Any], dict[str, Any]],
    intent: str,
    head: str,
    recovery: dict[str, Any] | None = None,
) -> None:
    receipt, evidence = pair
    result = evaluate(
        snapshot, receipt, evidence, intent, head, FIXTURE_TREE, recovery
    )
    if result.decision != expected_decision or result.reason != expected_reason:
        raise InputError(
            f"selftest {name}: got {result.decision}/{result.reason}, "
            f"want {expected_decision}/{expected_reason}"
        )


def refuse(name: str, snapshot: dict[str, Any],
           pair: tuple[dict[str, Any], dict[str, Any]], head: str,
           mutate, *, reseal_after: bool = False) -> None:
    """Plant one defect and require the gate to refuse it.

    `reseal_after` re-derives both digests, so a mutation is caught by the rule
    it names rather than by the digest check standing in front of every rule.
    """
    receipt = json.loads(json.dumps(pair[0]))
    evidence = json.loads(json.dumps(pair[1]))
    mutate(receipt, evidence)
    if reseal_after:
        reseal(receipt, evidence)
    try:
        evaluate(snapshot, receipt, evidence, "initial-pr", head, FIXTURE_TREE, None)
    except InputError:
        return
    raise InputError(f"selftest {name} unexpectedly passed")


def selftest() -> None:
    head = "1" * 40
    new_head = "2" * 40
    base = fixture_snapshot(head)
    verification = fixture_pair(head, FIXTURE_TREE)
    expect(
        "initial",
        "ALLOW",
        "allow-initial-pr",
        base,
        verification,
        "initial-pr",
        head,
    )

    refuse("stale-local-verification", base, verification, head,
           lambda receipt, evidence: receipt.__setitem__("head_sha", "0" * 40))

    # The receipt says PASS; these decide whether the bytes it names say the
    # same thing. Every one of them authorized publication before the gate read
    # the sidecar at all.
    def set_evidence(field: str, value: Any):
        return lambda receipt, evidence: evidence.__setitem__(field, value)

    def set_command(field: str, value: Any):
        return lambda receipt, evidence: evidence["commands"][0].__setitem__(field, value)

    sealed = {"reseal_after": True}
    refuse("evidence-wrong-repository", base, verification, head,
           set_evidence("repository_id", 999), **sealed)
    refuse("evidence-stale-head", base, verification, head,
           set_evidence("head_sha", "0" * 40), **sealed)
    refuse("evidence-other-tree", base, verification, head,
           set_evidence("tree_sha", "f" * 40), **sealed)
    refuse("evidence-dirty-subject", base, verification, head,
           set_evidence("clean_subject", False), **sealed)
    refuse("evidence-not-pass", base, verification, head,
           set_evidence("status", "FAIL"), **sealed)
    refuse("evidence-different-run", base, verification, head,
           set_evidence("verified_at", "2026-08-12T06:00:00Z"), **sealed)
    refuse("evidence-no-commands", base, verification, head,
           set_evidence("commands", []), **sealed)

    refuse("command-nonzero-exit", base, verification, head,
           set_command("exit", 1), **sealed)
    refuse("command-timed-out", base, verification, head,
           set_command("timed_out", True), **sealed)
    refuse("command-stdout-truncated", base, verification, head,
           set_command("stdout_truncated", True), **sealed)
    refuse("command-stderr-truncated", base, verification, head,
           set_command("stderr_truncated", True), **sealed)
    refuse("command-spawn-error", base, verification, head,
           set_command("spawn_error", "No such file or directory"), **sealed)
    refuse("command-absolute-cwd", base, verification, head,
           set_command("cwd", "/Users/someone/checkout"), **sealed)
    refuse("command-escaping-cwd", base, verification, head,
           set_command("cwd", "../elsewhere"), **sealed)
    refuse("command-shell-string", base, verification, head,
           set_command("argv", ["bash tests/run-all.sh | tee log"]), **sealed)
    refuse("command-malformed-stream-hash", base, verification, head,
           set_command("stdout_sha256", "not-a-digest"), **sealed)
    refuse("command-negative-duration", base, verification, head,
           set_command("duration_ms", -1), **sealed)

    def duplicate_ids(receipt, evidence):
        evidence["commands"].append(json.loads(json.dumps(evidence["commands"][0])))
        receipt["commands"].append(receipt["commands"][0])

    refuse("duplicate-command-ids", base, verification, head, duplicate_ids, **sealed)

    def reordered(receipt, evidence):
        second = json.loads(json.dumps(evidence["commands"][0]))
        second["id"] = "second command"
        evidence["commands"].append(second)
        receipt["commands"] = [second["id"], receipt["commands"][0]]

    refuse("reordered-command-ids", base, verification, head, reordered, **sealed)

    # The two digests, each on its own. Checking one and not the other leaves
    # the other free to disagree, which is the compact-only path this closes.
    def stale_content_digest(receipt, evidence):
        # Change the body and leave `content_sha256` describing the old bytes,
        # then re-derive only the receipt's digest. A first attempt simply
        # corrupted `content_sha256`, and that was caught by the receipt digest
        # check standing in front of it -- the control passed while proving
        # nothing about the check it named.
        evidence["contract_sha256"] = "9" * 64
        receipt["evidence_sha256"] = digest_of(evidence)

    refuse("content-digest-disagrees", base, verification, head, stale_content_digest)
    refuse("receipt-names-other-bytes", base, verification, head,
           lambda receipt, evidence: receipt.__setitem__("evidence_sha256", "0" * 64))

    # The old compact-only path: a receipt that is internally perfect paired
    # with evidence from a different verification run.
    def foreign_evidence(receipt, evidence):
        other = fixture_pair("3" * 40, FIXTURE_TREE)[1]
        evidence.clear()
        evidence.update(other)

    refuse("compact-receipt-with-foreign-evidence", base, verification, head,
           foreign_evidence)

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
    new_verification = fixture_pair(new_head, FIXTURE_TREE)
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
    print("SELFTEST GREEN: GitHub Actions publication gate "
        "(10 policy cases, 23 evidence-binding controls)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ci_publish_gate.py")
    parser.add_argument("--selftest", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--snapshot", type=Path, required=True)
    evaluate_parser.add_argument("--verification", type=Path, required=True)
    evaluate_parser.add_argument("--verification-evidence", type=Path, required=True)
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
        evidence = load_object(args.verification_evidence, "local verification evidence")
        recovery = (
            load_object(args.recovery, "billing recovery receipt")
            if args.recovery is not None
            else None
        )
        repo_root = args.repo_root.resolve()
        actual_head = git_head(repo_root)
        actual_tree = git_tree(repo_root)
        decision = evaluate(
            snapshot,
            verification,
            evidence,
            args.intent,
            actual_head,
            actual_tree,
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
