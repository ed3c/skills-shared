"""Conservative causality rules for PR-body issue references.

GitHub's ordinary pull-request snapshot exposes the current body but not the
historical instant when a closing/reference phrase first appeared. A PR that
predates an issue therefore cannot safely use PR.created_at as the issue-start
time merely because its *current* body mentions that issue.

This module intentionally refuses to guess from updated_at: many unrelated
GitHub events update that timestamp. Callers should exclude unknown references
from queue/cycle/throughput attribution while still surfacing them for humans.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


class ReferenceCausalityError(ValueError):
    pass


def parse_time(raw: Any, field: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise ReferenceCausalityError(f"{field} must be an ISO-8601 timestamp")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReferenceCausalityError(f"{field} must be an ISO-8601 timestamp") from exc
    if value.tzinfo is None:
        raise ReferenceCausalityError(f"{field} must include a timezone")
    return value


def classify_reference(issue: dict[str, Any], pull: dict[str, Any]) -> dict[str, Any]:
    """Return whether a current-body reference has a trustworthy causal start.

    known_at_create means the issue already existed when the PR was created, so
    PR.created_at is a conservative lower-resolution start timestamp.

    unknown_post_create means the PR predates the issue. The current body proves
    a reference exists *now*, but not when it became effective. It must not be
    used for queue/cycle/accepted attribution without stronger history.
    """
    issue_created = parse_time(issue.get("created_at"), "issue.created_at")
    pull_created = parse_time(pull.get("created_at"), "pull.created_at")
    merged_raw = pull.get("merged_at")
    merged = parse_time(merged_raw, "pull.merged_at") if merged_raw else None

    if pull_created >= issue_created:
        return {
            "status": "known_at_create",
            "effective_at": pull.get("created_at"),
            "eligible_for_start": True,
            "eligible_for_acceptance": merged is not None and merged >= issue_created,
            "reason": None,
        }

    # A current-body reference on a PR that existed before the issue cannot be
    # assigned a historical effective timestamp from the normal REST snapshot.
    # Even if merged after issue creation, the body could have been edited after
    # merge, so acceptance attribution is also unknown.
    reason = "pull predates issue; current body has no reference-edit timestamp"
    if merged is not None and merged < issue_created:
        reason = "pull merged before issue existed; current reference is necessarily post-merge"
    return {
        "status": "unknown_post_create",
        "effective_at": None,
        "eligible_for_start": False,
        "eligible_for_acceptance": False,
        "reason": reason,
    }
