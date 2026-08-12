#!/usr/bin/env bash
set -euo pipefail

script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "$script_dir/../..")"
PYTHONPATH="$skill_dir/scripts" python3 - <<'PY'
from reference_causality import classify_reference
from delivery_sync import derive_metrics

issue = {"created_at": "2026-08-12T04:00:00Z"}

# Good: issue exists before PR creation, so created_at is a causal lower bound.
known = classify_reference(issue, {
    "created_at": "2026-08-12T05:00:00Z",
    "merged_at": "2026-08-12T06:00:00Z",
})
assert known["status"] == "known_at_create"
assert known["eligible_for_start"] is True
assert known["eligible_for_acceptance"] is True
assert known["effective_at"] == "2026-08-12T05:00:00Z"

# Regression from issue #38: PR existed first, issue was created later, then the
# current PR body gained a reference. Never backdate start to PR.created_at.
late_ref = classify_reference(issue, {
    "created_at": "2026-08-09T01:00:00Z",
    "merged_at": "2026-08-12T07:00:00Z",
    "updated_at": "2026-08-12T08:00:00Z",
})
assert late_ref["status"] == "unknown_post_create"
assert late_ref["eligible_for_start"] is False
assert late_ref["eligible_for_acceptance"] is False
assert late_ref["effective_at"] is None
assert "no reference-edit timestamp" in late_ref["reason"]

# Stronger impossibility: PR was already merged before the issue existed.
post_merge_edit = classify_reference(issue, {
    "created_at": "2026-08-08T01:00:00Z",
    "merged_at": "2026-08-10T01:00:00Z",
})
assert post_merge_edit["eligible_for_start"] is False
assert post_merge_edit["eligible_for_acceptance"] is False
assert "merged before issue existed" in post_merge_edit["reason"]

# Boundary: exact same timestamp is non-negative and admissible.
boundary = classify_reference(issue, {
    "created_at": "2026-08-12T04:00:00Z",
    "merged_at": None,
})
assert boundary["eligible_for_start"] is True
assert boundary["eligible_for_acceptance"] is False

# Integration: public delivery_sync.derive_metrics must no longer throw a
# negative queue for a PR that predates the issue and only references it now.
snapshot = {
    "fetched_at": "2026-08-12T10:00:00Z",
    "issues": [
        {
            "number": 12,
            "created_at": "2026-08-12T04:00:00Z",
            "closed_at": "2026-08-12T07:00:00Z",
            "state": "CLOSED",
            "title": "Late-linked issue",
            "labels": [],
            "events": [],
        },
        {
            "number": 13,
            "created_at": "2026-08-12T04:00:00Z",
            "closed_at": "2026-08-12T07:00:00Z",
            "state": "CLOSED",
            "title": "Causal issue",
            "labels": [],
            "events": [],
        },
    ],
    "pulls": [
        {
            "number": 5,
            "body": "Closes #12",
            "created_at": "2026-08-09T01:00:00Z",
            "ready_at": "2026-08-09T01:00:00Z",
            "merged_at": "2026-08-12T07:00:00Z",
            "reviews": [],
        },
        {
            "number": 6,
            "body": "Closes #13",
            "created_at": "2026-08-12T05:00:00Z",
            "ready_at": "2026-08-12T05:00:00Z",
            "merged_at": "2026-08-12T07:00:00Z",
            "reviews": [],
        },
    ],
}
metrics = derive_metrics(
    snapshot,
    ["https://github.com/ed3c/example/issues/12", "https://github.com/ed3c/example/issues/13"],
    "https://github.com/ed3c/example/issues/1",
)
by_issue = {item["issue_number"]: item for item in metrics["slices"]}
late = by_issue[12]
causal = by_issue[13]

assert late["started_pr"] is None
assert late["accepted_pr"] is None
assert late["queue_seconds"] is None
assert late["cycle_seconds"] is None
assert late["reference_causality"]["attribution"] == "excluded"
assert late["reference_causality"]["unknown_current_body_refs"][0]["pull_number"] == 5

assert causal["started_pr"] == 6
assert causal["accepted_pr"] == 6
assert causal["queue_seconds"] == 3600
assert causal["cycle_seconds"] == 7200
assert causal["reference_causality"]["attribution"] == "known-or-absent"

assert metrics["summary"]["accepted_slices"] == 1
assert metrics["summary"]["closed_without_merge"] == 1
assert metrics["summary"]["unknown_reference_attributions"] == 1

print("PASS reference causality fixtures and derive_metrics integration")
PY
