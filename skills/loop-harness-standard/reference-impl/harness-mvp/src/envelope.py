"""Unified cross-layer envelope construction and validation."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any


REQUIRED_FIELDS = (
    "id",
    "parentId",
    "loop_layer",
    "task_ref",
    "event",
    "exec",
    "handoff",
    "budget",
    "freshness",
)

EXEC_FIELDS = ("command", "exit_code", "result_snapshot", "error_snapshot")
HANDOFF_FIELDS = ("verified_hypotheses", "ruled_out", "current_diff", "next_action")
BUDGET_FIELDS = ("tokens_used", "usd")
FRESHNESS_FIELDS = ("git_commit_sha", "fact_stale")
MAX_INLINE_SNAPSHOT_BYTES = 512
POINTER_KEYS = ("uri", "hash", "sha256")


class EnvelopeError(ValueError):
    """Raised when an envelope violates the MVP schema."""


def make_envelope(
    *,
    id: str,
    parentId: str | None,
    loop_layer: str,
    task_ref: dict[str, Any],
    event: dict[str, Any],
    exec: dict[str, Any],
    handoff: dict[str, Any] | None = None,
    budget: dict[str, Any] | None = None,
    freshness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and validate the unified envelope as a plain dictionary."""

    record = {
        "id": id,
        "parentId": parentId,
        "loop_layer": loop_layer,
        "task_ref": deepcopy(task_ref),
        "event": deepcopy(event),
        "exec": {
            "command": exec.get("command"),
            "exit_code": exec.get("exit_code"),
            "result_snapshot": exec.get("result_snapshot"),
            "error_snapshot": exec.get("error_snapshot"),
        },
        "handoff": _handoff_defaults(handoff),
        "budget": _budget_defaults(budget),
        "freshness": _freshness_defaults(freshness),
    }
    validate_envelope(record)
    return record


def validate_envelope(record: dict[str, Any]) -> None:
    """Fail fast if a record is not the nine-field unified envelope."""

    if not isinstance(record, dict):
        raise EnvelopeError("envelope must be a dict")

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    extra = [field for field in record if field not in REQUIRED_FIELDS]
    if missing or extra:
        raise EnvelopeError(f"envelope fields mismatch missing={missing} extra={extra}")

    if not isinstance(record["id"], str) or not record["id"]:
        raise EnvelopeError("id must be a non-empty string")
    if record["parentId"] is not None and not isinstance(record["parentId"], str):
        raise EnvelopeError("parentId must be a string or None")
    if not isinstance(record["loop_layer"], str) or not record["loop_layer"].startswith("L"):
        raise EnvelopeError("loop_layer must be an L0-L7 style string")

    _require_dict(record, "task_ref")
    _require_dict(record, "event")
    _require_keys(record, "exec", EXEC_FIELDS)
    _require_keys(record, "handoff", HANDOFF_FIELDS)
    _require_keys(record, "budget", BUDGET_FIELDS)
    _require_keys(record, "freshness", FRESHNESS_FIELDS)

    exit_code = record["exec"]["exit_code"]
    if not isinstance(exit_code, int):
        raise EnvelopeError("exec.exit_code must be an int")

    tokens_used = record["budget"]["tokens_used"]
    usd = record["budget"]["usd"]
    if not isinstance(tokens_used, int) or tokens_used < 0:
        raise EnvelopeError("budget.tokens_used must be a non-negative int")
    if not isinstance(usd, (int, float)) or usd < 0:
        raise EnvelopeError("budget.usd must be a non-negative number")
    if not isinstance(record["freshness"]["fact_stale"], bool):
        raise EnvelopeError("freshness.fact_stale must be a bool")

    _validate_snapshot("exec.result_snapshot", record["exec"]["result_snapshot"])
    _validate_snapshot("exec.error_snapshot", record["exec"]["error_snapshot"])


def _handoff_defaults(value: dict[str, Any] | None) -> dict[str, Any]:
    source = value or {}
    return {
        "verified_hypotheses": list(source.get("verified_hypotheses", [])),
        "ruled_out": list(source.get("ruled_out", [])),
        "current_diff": source.get("current_diff"),
        "next_action": source.get("next_action"),
    }


def _budget_defaults(value: dict[str, Any] | None) -> dict[str, Any]:
    source = value or {}
    return {
        "tokens_used": int(source.get("tokens_used", 0)),
        "usd": float(source.get("usd", 0.0)),
    }


def _freshness_defaults(value: dict[str, Any] | None) -> dict[str, Any]:
    source = value or {}
    return {
        "git_commit_sha": source.get("git_commit_sha"),
        "fact_stale": bool(source.get("fact_stale", False)),
    }


def _require_dict(record: dict[str, Any], field: str) -> None:
    if not isinstance(record[field], dict):
        raise EnvelopeError(f"{field} must be a dict")


def _require_keys(record: dict[str, Any], field: str, keys: tuple[str, ...]) -> None:
    _require_dict(record, field)
    missing = [key for key in keys if key not in record[field]]
    if missing:
        raise EnvelopeError(f"{field} missing keys {missing}")


def _validate_snapshot(field: str, value: Any) -> None:
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except TypeError as exc:
        raise EnvelopeError(f"{field} must be JSON-serializable") from exc

    if len(payload) > MAX_INLINE_SNAPSHOT_BYTES and not _is_pointer_snapshot(value):
        raise EnvelopeError(f"{field} too large for ledger; store URI/hash pointer instead")


def _is_pointer_snapshot(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return any(isinstance(value.get(key), str) and value.get(key) for key in POINTER_KEYS)
