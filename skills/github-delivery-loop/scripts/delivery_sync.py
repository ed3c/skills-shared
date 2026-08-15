"""Causality-safe compatibility facade for delivery_sync.

The historical implementation is preserved byte-for-byte in delivery_sync_impl.py.
This facade filters PR-body references whose effective time cannot be established
from the ordinary GitHub snapshot, then delegates every other behavior unchanged.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

# This facade is intentionally loadable by absolute path from any caller CWD.
# Python only adds the caller's import root to sys.path when importlib loads a
# file directly, so bind this script's own directory before importing siblings.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import delivery_sync_impl as _impl
from reference_causality import classify_reference

SyncError = _impl.SyncError
SNAPSHOT_SCHEMA = _impl.SNAPSHOT_SCHEMA
METRICS_SCHEMA = _impl.METRICS_SCHEMA
BLOCKED_LABELS = _impl.BLOCKED_LABELS
REFERENCE_RE = _impl.REFERENCE_RE
_json_bytes = _impl._json_bytes
fetch_github_snapshot = _impl.fetch_github_snapshot
write_outputs = _impl.write_outputs
_ORIGINAL_DERIVE_METRICS = _impl.derive_metrics


def _causal_snapshot(snapshot: dict[str, Any]) -> tuple[dict[str, Any], dict[int, list[dict[str, Any]]]]:
    """Remove only references that cannot be causally placed in time."""
    value = copy.deepcopy(snapshot)
    issues = value.get("issues", [])
    pulls = value.get("pulls", [])
    by_issue = {
        issue.get("number"): issue
        for issue in issues
        if isinstance(issue, dict) and isinstance(issue.get("number"), int)
    }
    unknown: dict[int, list[dict[str, Any]]] = {}

    for pull in pulls:
        if not isinstance(pull, dict):
            continue
        body = pull.get("body")
        if not isinstance(body, str) or not body:
            continue

        def replace(match):
            number = int(match.group(2))
            issue = by_issue.get(number)
            if issue is None:
                return match.group(0)
            causality = classify_reference(issue, pull)
            if causality["eligible_for_start"]:
                return match.group(0)
            unknown.setdefault(number, []).append({
                "pull_number": pull.get("number"),
                "status": causality["status"],
                "reason": causality["reason"],
            })
            return ""

        pull["body"] = _impl.REFERENCE_RE.sub(replace, body)
    return value, unknown


def derive_metrics(
    snapshot: dict[str, Any], issue_urls: list[str], prd_issue_url: str
) -> dict[str, Any]:
    causal, unknown = _causal_snapshot(snapshot)
    metrics = _ORIGINAL_DERIVE_METRICS(causal, issue_urls, prd_issue_url)
    unknown_count = 0
    for item in metrics.get("slices", []):
        if not isinstance(item, dict):
            continue
        refs = unknown.get(item.get("issue_number"), [])
        unknown_count += len(refs)
        item["reference_causality"] = {
            "unknown_current_body_refs": refs,
            "attribution": "excluded" if refs else "known-or-absent",
        }
    summary = metrics.get("summary")
    if isinstance(summary, dict):
        summary["unknown_reference_attributions"] = unknown_count
    return metrics


def build_outputs(
    *,
    line,
    snapshot,
    export_source_commit,
    export_tree_sha,
    repo_root,
    expected_prd_issue_url=None,
):
    # build_outputs lives in the preserved implementation and resolves its
    # module-global derive_metrics at runtime. Patch only for this call.
    previous = _impl.derive_metrics
    _impl.derive_metrics = derive_metrics
    try:
        return _impl.build_outputs(
            line=line,
            snapshot=snapshot,
            export_source_commit=export_source_commit,
            export_tree_sha=export_tree_sha,
            repo_root=repo_root,
            expected_prd_issue_url=expected_prd_issue_url,
        )
    finally:
        _impl.derive_metrics = previous
