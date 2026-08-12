#!/usr/bin/env bash
set -euo pipefail
script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "$script_dir/../..")"
PYTHONPATH="$skill_dir/scripts" python3 - <<'PY'
from delivery_sync import derive_metrics

snapshot = {
    "fetched_at": "2026-08-12T10:00:00Z",
    "issues": [
        {"number": 12, "created_at": "2026-08-12T04:00:00Z", "closed_at": "2026-08-12T07:00:00Z", "state": "CLOSED", "title": "Late-linked issue", "labels": [], "events": []},
        {"number": 13, "created_at": "2026-08-12T04:00:00Z", "closed_at": "2026-08-12T07:00:00Z", "state": "CLOSED", "title": "Causal issue", "labels": [], "events": []},
    ],
    "pulls": [
        {"number": 5, "body": "Closes #12", "created_at": "2026-08-09T01:00:00Z", "ready_at": "2026-08-09T01:00:00Z", "merged_at": "2026-08-12T07:00:00Z", "reviews": []},
        {"number": 6, "body": "Closes #13", "created_at": "2026-08-12T05:00:00Z", "ready_at": "2026-08-12T05:00:00Z", "merged_at": "2026-08-12T07:00:00Z", "reviews": []},
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

# The issue-38 shape must be surfaced, never backdated to PR creation.
assert late["started_pr"] is None
assert late["accepted_pr"] is None
assert late["queue_seconds"] is None
assert late["cycle_seconds"] is None
assert late["reference_causality"]["attribution"] == "excluded"
assert late["reference_causality"]["unknown_current_body_refs"][0]["pull_number"] == 5

# A genuinely causal reference retains the original metric semantics.
assert causal["started_pr"] == 6
assert causal["accepted_pr"] == 6
assert causal["queue_seconds"] == 3600
assert causal["cycle_seconds"] == 7200
assert causal["reference_causality"]["attribution"] == "known-or-absent"

assert metrics["summary"]["accepted_slices"] == 1
assert metrics["summary"]["closed_without_merge"] == 1
assert metrics["summary"]["unknown_reference_attributions"] == 1
print("PASS causal derive_metrics integration")
PY
