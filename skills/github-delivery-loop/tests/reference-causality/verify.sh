#!/usr/bin/env bash
set -euo pipefail

script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "$script_dir/../..")"
PYTHONPATH="$skill_dir/scripts" python3 - <<'PY'
from reference_causality import classify_reference

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

print("PASS reference causality fixtures")
PY
