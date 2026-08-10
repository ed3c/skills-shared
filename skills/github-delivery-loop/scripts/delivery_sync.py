"""GitHub snapshot ingestion, flow metrics, and decision-dashboard projection."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SNAPSHOT_SCHEMA = "github-delivery-snapshot/v1"
METRICS_SCHEMA = "github-delivery-metrics/v1"
BLOCKED_LABELS = {"blocked", "blocked-dependency"}
REFERENCE_RE = re.compile(r"(?im)\b(closes|fixes|resolves|part\s+of)\s+#([1-9][0-9]*)")


class SyncError(ValueError):
    """Raised when GitHub state cannot produce a trustworthy projection."""


def _parse_time(raw: Any, field: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise SyncError(f"{field} must be an ISO-8601 timestamp")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise SyncError(f"{field} must be an ISO-8601 timestamp") from error
    if value.tzinfo is None:
        raise SyncError(f"{field} must include a timezone")
    return value


def _seconds(start: Any, end: Any, field: str) -> int | None:
    if start is None or end is None:
        return None
    delta = int(
        (
            _parse_time(end, f"{field}.end") - _parse_time(start, f"{field}.start")
        ).total_seconds()
    )
    if delta < 0:
        raise SyncError(f"{field} cannot be negative")
    return delta


def _issue_number(url: str) -> int:
    match = re.search(r"/issues/([1-9][0-9]*)$", url)
    if match is None:
        raise SyncError(f"invalid issue URL: {url}")
    return int(match.group(1))


def _references(body: Any) -> tuple[set[int], set[int]]:
    all_refs: set[int] = set()
    closing_refs: set[int] = set()
    for kind, raw_number in REFERENCE_RE.findall(body if isinstance(body, str) else ""):
        number = int(raw_number)
        all_refs.add(number)
        if kind.lower() != "part of":
            closing_refs.add(number)
    return all_refs, closing_refs


def _label_names(issue: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    labels = issue.get("labels", [])
    if not isinstance(labels, list):
        raise SyncError(f"issue #{issue.get('number')}: labels must be a list")
    for label in labels:
        name = label.get("name") if isinstance(label, dict) else label
        if isinstance(name, str):
            names.add(name.lower())
    return names


def _blocked_seconds(issue: dict[str, Any], fetched_at: str) -> int:
    events = issue.get("events", [])
    if not isinstance(events, list):
        raise SyncError(f"issue #{issue.get('number')}: events must be a list")
    started: datetime | None = None
    total = 0
    for event in sorted(events, key=lambda item: str(item.get("created_at", ""))):
        name = str(event.get("label", "")).lower()
        if name not in BLOCKED_LABELS:
            continue
        at = _parse_time(event.get("created_at"), "blocked event")
        if event.get("event") == "labeled" and started is None:
            started = at
        elif event.get("event") == "unlabeled" and started is not None:
            total += int((at - started).total_seconds())
            started = None
    if started is not None:
        stop_raw = issue.get("closed_at") or fetched_at
        stop = _parse_time(stop_raw, "blocked interval end")
        total += max(0, int((stop - started).total_seconds()))
    return total


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def derive_metrics(
    snapshot: dict[str, Any], issue_urls: list[str], prd_issue_url: str
) -> dict[str, Any]:
    """Derive flow-health metrics from GitHub event timestamps."""
    fetched_at = snapshot.get("fetched_at")
    now = _parse_time(fetched_at, "fetched_at")
    issues = snapshot.get("issues")
    pulls = snapshot.get("pulls")
    if not isinstance(issues, list) or not isinstance(pulls, list):
        raise SyncError("snapshot issues and pulls must be lists")
    by_issue = {item.get("number"): item for item in issues if isinstance(item, dict)}
    prd_number = _issue_number(prd_issue_url)
    slice_numbers = [
        _issue_number(url) for url in issue_urls if _issue_number(url) != prd_number
    ]

    pull_refs: list[tuple[dict[str, Any], set[int], set[int]]] = []
    for pull in pulls:
        if not isinstance(pull, dict):
            raise SyncError("snapshot pull must be an object")
        all_refs, closing_refs = _references(pull.get("body"))
        pull_refs.append((pull, all_refs, closing_refs))

    slices: list[dict[str, Any]] = []
    accepted_times: list[datetime] = []
    first_pass_values: list[bool] = []
    reopened_count = 0
    for number in slice_numbers:
        issue = by_issue.get(number)
        if not isinstance(issue, dict):
            raise SyncError(f"snapshot missing registered issue #{number}")
        starts = [pull for pull, all_refs, _closing in pull_refs if number in all_refs]
        starts.sort(key=lambda pull: str(pull.get("created_at", "")))
        accepted = [
            pull
            for pull, _all_refs, closing_refs in pull_refs
            if number in closing_refs and pull.get("merged_at")
        ]
        accepted.sort(key=lambda pull: str(pull.get("merged_at", "")))
        start = starts[0] if starts else None
        merge = accepted[0] if accepted else None
        blocked = _blocked_seconds(issue, str(fetched_at))
        events = issue.get("events", [])
        reopened = any(
            isinstance(event, dict) and event.get("event") == "reopened"
            for event in events
        )
        reopened_count += int(reopened)
        if merge is not None:
            merged_at = _parse_time(
                merge.get("merged_at"), f"PR #{merge.get('number')}.merged_at"
            )
            accepted_times.append(merged_at)
            reviews = merge.get("reviews", [])
            if isinstance(reviews, list):
                actionable = [
                    review
                    for review in reviews
                    if isinstance(review, dict)
                    and review.get("state") in {"APPROVED", "CHANGES_REQUESTED"}
                ]
                actionable.sort(key=lambda review: str(review.get("submitted_at", "")))
                if actionable:
                    first_pass_values.append(actionable[0]["state"] == "APPROVED")

        state = str(issue.get("state", "")).upper()
        labels = _label_names(issue)
        slices.append(
            {
                "accepted_pr": merge.get("number") if merge else None,
                "blocked_seconds": blocked,
                "cycle_seconds": (
                    _seconds(start.get("created_at"), merge.get("merged_at"), "cycle")
                    if start and merge
                    else None
                ),
                "issue_number": number,
                "issue_state": state,
                "lead_seconds": (
                    _seconds(issue.get("created_at"), merge.get("merged_at"), "lead")
                    if merge
                    else None
                ),
                "queue_seconds": (
                    _seconds(issue.get("created_at"), start.get("created_at"), "queue")
                    if start
                    else None
                ),
                "reopened": reopened,
                "review_seconds": (
                    _seconds(
                        merge.get("ready_at") or merge.get("created_at"),
                        merge.get("merged_at"),
                        "review",
                    )
                    if merge
                    else None
                ),
                "started_pr": start.get("number") if start else None,
                "title": issue.get("title"),
                "currently_blocked": bool(labels & BLOCKED_LABELS),
            }
        )

    def values(field: str) -> list[int]:
        return [item[field] for item in slices if isinstance(item[field], int)]

    seven_days = 7 * 24 * 3600
    twenty_eight_days = 28 * 24 * 3600
    accepted_count = len(accepted_times)
    summary = {
        "accepted_slices": accepted_count,
        "blocked_slices": sum(item["currently_blocked"] for item in slices),
        "closed_without_merge": sum(
            item["issue_state"] == "CLOSED" and item["accepted_pr"] is None
            for item in slices
        ),
        "total_slices": len(slices),
        "throughput_7d": sum(
            0 <= (now - item).total_seconds() <= seven_days for item in accepted_times
        ),
        "throughput_28d": sum(
            0 <= (now - item).total_seconds() <= twenty_eight_days
            for item in accepted_times
        ),
        "wip": sum(
            item["issue_state"] == "OPEN" and item["started_pr"] is not None
            for item in slices
        ),
    }
    percentiles = {
        field: {
            "p50": _nearest_rank(values(field), 0.50),
            "p85": _nearest_rank(values(field), 0.85),
        }
        for field in (
            "lead_seconds",
            "queue_seconds",
            "cycle_seconds",
            "review_seconds",
            "blocked_seconds",
        )
    }
    return {
        "fetched_at": fetched_at,
        "percentiles": percentiles,
        "quality": {
            "first_pass_rate": (
                sum(first_pass_values) / len(first_pass_values)
                if first_pass_values
                else None
            ),
            "redaction_leakage_rate": None,
            "reopen_rate": reopened_count / len(slices) if slices else None,
        },
        "schema": METRICS_SCHEMA,
        "slices": slices,
        "summary": summary,
    }


def _gh_json(args: list[str]) -> Any:
    result = subprocess.run(["gh", *args], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "gh command failed"
        raise SyncError(detail)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SyncError(f"gh returned invalid JSON: {error}") from error


def fetch_github_snapshot(repository: str, project_url: str) -> dict[str, Any]:
    """Fetch one normalized snapshot through the authenticated GitHub CLI."""
    repo = _gh_json(["api", f"repos/{repository}"])
    default_branch = repo.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise SyncError("GitHub repository has no default branch")
    head = _gh_json(["api", f"repos/{repository}/commits/{default_branch}"])
    head_sha = head.get("sha")
    tree_sha = head.get("commit", {}).get("tree", {}).get("sha")
    tree = _gh_json(["api", f"repos/{repository}/git/trees/{tree_sha}?recursive=1"])
    commits = _gh_json(
        ["api", f"repos/{repository}/commits?sha={default_branch}&per_page=100"]
    )
    raw_issues = _gh_json(["api", f"repos/{repository}/issues?state=all&per_page=100"])
    raw_pulls = _gh_json(["api", f"repos/{repository}/pulls?state=all&per_page=100"])

    issues: list[dict[str, Any]] = []
    for issue in raw_issues:
        if "pull_request" in issue:
            continue
        number = issue["number"]
        events = _gh_json(
            ["api", f"repos/{repository}/issues/{number}/events?per_page=100"]
        )
        issues.append(
            {
                "closed_at": issue.get("closed_at"),
                "created_at": issue.get("created_at"),
                "events": [
                    {
                        "created_at": event.get("created_at"),
                        "event": event.get("event"),
                        "label": (event.get("label") or {}).get("name"),
                    }
                    for event in events
                    if event.get("event") in {"labeled", "unlabeled", "reopened"}
                ],
                "labels": [label.get("name") for label in issue.get("labels", [])],
                "number": number,
                "state": str(issue.get("state", "")).upper(),
                "title": issue.get("title"),
            }
        )

    pulls: list[dict[str, Any]] = []
    for pull in raw_pulls:
        number = pull["number"]
        reviews = _gh_json(
            ["api", f"repos/{repository}/pulls/{number}/reviews?per_page=100"]
        )
        pulls.append(
            {
                "body": pull.get("body") or "",
                "closed_at": pull.get("closed_at"),
                "created_at": pull.get("created_at"),
                "merged_at": pull.get("merged_at"),
                "number": number,
                "ready_at": pull.get("created_at") if not pull.get("draft") else None,
                "reviews": [
                    {
                        "state": review.get("state"),
                        "submitted_at": review.get("submitted_at"),
                    }
                    for review in reviews
                ],
                "state": "MERGED"
                if pull.get("merged_at")
                else str(pull.get("state", "")).upper(),
                "title": pull.get("title"),
            }
        )

    parsed_project = urlparse(project_url)
    parts = parsed_project.path.strip("/").split("/")
    project: dict[str, Any] = {"url": project_url, "title": "", "status_counts": {}}
    if len(parts) == 4 and parts[0] in {"users", "orgs"} and parts[2] == "projects":
        owner, number = parts[1], parts[3]
        view = _gh_json(
            ["project", "view", number, "--owner", owner, "--format", "json"]
        )
        items = _gh_json(
            [
                "project",
                "item-list",
                number,
                "--owner",
                owner,
                "--format",
                "json",
                "--limit",
                "100",
            ]
        )
        counts: dict[str, int] = {}
        for item in items.get("items", []):
            status = item.get("status") or "No Status"
            counts[status] = counts.get(status, 0) + 1
        project = {
            "url": project_url,
            "title": view.get("title", ""),
            "status_counts": counts,
        }

    license_value = repo.get("license") or {}
    return {
        "fetched_at": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "issues": issues,
        "project": project,
        "pulls": pulls,
        "repository": {
            "default_branch": default_branch,
            "file_count": sum(
                item.get("type") == "blob" for item in tree.get("tree", [])
            ),
            "full_name": repo.get("full_name"),
            "id": repo.get("node_id"),
            "head_sha": head_sha,
            "history_root": any(not item.get("parents") for item in commits),
            "license_spdx": license_value.get("spdx_id"),
            "tree_sha": tree_sha,
            "url": repo.get("html_url"),
            "visibility": str(repo.get("visibility", "")).upper(),
        },
        "schema": SNAPSHOT_SCHEMA,
    }


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()


def render_dashboard(
    line_id: str,
    snapshot: dict[str, Any],
    metrics: dict[str, Any],
    blockers: list[str],
) -> str:
    """Render a compact Markdown decision snapshot from event-derived metrics."""
    summary = metrics["summary"]
    project = snapshot.get("project", {})
    repository = snapshot["repository"]
    lines = [
        f"# {line_id} delivery dashboard",
        "",
        f"> Snapshot: `{snapshot['fetched_at']}`。本頁是 GitHub event truth 的時間點快照，",
        "> 不是 registry 的第二份真相，也不是個人生產力排名。",
        "",
        "## Truth boundary",
        "",
        "```text",
        "┌───────────────┐    ┌──────────────┐    ┌────────────────────────┐",
        "│ GitHub events │ ─→ │ metrics.json │ ─→ │ Markdown decision view │",
        "└───────────────┘    └──────────────┘    └────────────────────────┘",
        "         │",
        "         ├─→ GitHub Project (status projection only)",
        "         └─→ publication attestation ─→ human visibility gate",
        "```",
        "",
        "## Current decision",
        "",
        f"- Repository: `{repository['full_name']}` (`{repository['visibility']}`)",
        f"- Remote tree: `{repository.get('tree_sha')}` "
        f"({repository.get('file_count')} files, orphan root: "
        f"`{'YES' if repository.get('history_root') else 'NO'}`)",
        f"- Public ready: `{'YES' if not blockers else 'NO'}`",
        f"- Blockers: `{', '.join(blockers) if blockers else 'none'}`",
        f"- Project: [{project.get('title') or 'GitHub Project'}]({project.get('url', '')})",
        "",
        "## Flow health",
        "",
        "| Signal | Value |",
        "|---|---:|",
        f"| accepted slices | {summary['accepted_slices']} |",
        f"| WIP | {summary['wip']} |",
        f"| blocked | {summary['blocked_slices']} |",
        f"| throughput 7d / 28d | {summary['throughput_7d']} / {summary['throughput_28d']} |",
        f"| closed_without_merge | {summary['closed_without_merge']} |",
        "",
        "## Project projection",
        "",
        "| Status | Items |",
        "|---|---:|",
        *[
            f"| {status} | {count} |"
            for status, count in sorted(project.get("status_counts", {}).items())
        ],
        "",
        "`closed_without_merge` 是證據缺口，不計入 throughput。"
        "p50/p85 只在有 merge event 樣本時顯示。",
        "",
        "## Slice evidence",
        "",
        "| Issue | State | Started PR | Accepted PR | Lead | Blocked |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for item in metrics["slices"]:
        lines.append(
            (
                "| #{issue_number} | {issue_state} | {started} | "
                "{accepted} | {lead} | {blocked} |"
            ).format(
                issue_number=item["issue_number"],
                issue_state=item["issue_state"],
                started=item["started_pr"] or "—",
                accepted=item["accepted_pr"] or "—",
                lead=item["lead_seconds"]
                if item["lead_seconds"] is not None
                else "UNKNOWN",
                blocked=item["blocked_seconds"],
            )
        )
    lines.extend(
        [
            "",
            "## Human gate",
            "",
            "只有 blockers 清空、publication attestation 與遠端 HEAD 對齊後，"
            "人類才可執行 PR merge 與 PRIVATE→PUBLIC。",
            "",
            "## MVP extraction",
            "",
            "| Step | Direct? | Undecided dependency | Permission | Measurable change | Size |",
            "|---|---|---|---|---|---|",
            "| Clear mechanical blockers | direct | none | repository scope | "
            "blockers count decreases | small |",
            "| Human visibility decision | direct | owner review | owner only | "
            "visibility becomes PUBLIC | human gate |",
            "",
            "Rejected now: custom daemon (extra operational surface); personal ranking "
            "(Goodhart risk); automatic merge/public toggle (violates human gate).",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs(
    *,
    line: dict[str, Any],
    snapshot: dict[str, Any],
    export_source_commit: str,
    export_tree_sha: str,
    repo_root: Path,
    expected_prd_issue_url: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Validate one snapshot and build all synchronized output values in memory."""
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise SyncError(f"snapshot schema must be {SNAPSHOT_SCHEMA}")
    repository = snapshot.get("repository")
    if not isinstance(repository, dict):
        raise SyncError("snapshot repository must be an object")
    # Identity is pinned by repository id, not by name: an id survives a rename,
    # a name does not. The old name comparison is gone rather than kept dormant.
    expected_repository_id = line.get("github_repository_id")
    if not isinstance(expected_repository_id, str) or not expected_repository_id:
        raise SyncError("registry line must pin github_repository_id")
    if repository.get("id") != expected_repository_id:
        raise SyncError(
            "snapshot repository mismatch: "
            f"expected id {expected_repository_id}, got {repository.get('id')} "
            f"({repository.get('full_name')})"
        )
    canonical_repo = repository.get("full_name")
    if not isinstance(canonical_repo, str) or not canonical_repo:
        raise SyncError("snapshot repository full_name missing")
    if re.fullmatch(r"[0-9a-f]{40}", export_source_commit) is None:
        raise SyncError("export source commit must be a full 40-character SHA")
    if re.fullmatch(r"[0-9a-f]{40}", export_tree_sha) is None:
        raise SyncError("export tree sha must be a full 40-character SHA")
    issues = snapshot.get("issues")
    pulls = snapshot.get("pulls")
    if not isinstance(issues, list) or not issues:
        raise SyncError("snapshot issues must be a non-empty list")
    if not isinstance(pulls, list):
        raise SyncError("snapshot pulls must be a list")
    if expected_prd_issue_url is not None:
        expected_prd_number = _issue_number(expected_prd_issue_url)
        prd_candidates = [
            issue
            for issue in issues
            if isinstance(issue, dict) and issue.get("number") == expected_prd_number
        ]
        if len(prd_candidates) != 1:
            raise SyncError(
                f"snapshot missing receipt-pinned PRD issue #{expected_prd_number}"
            )
        if not str(prd_candidates[0].get("title", "")).upper().startswith("PRD"):
            raise SyncError(
                f"receipt-pinned issue #{expected_prd_number} is no longer PRD-titled"
            )
    else:
        prd_candidates = [
            issue
            for issue in issues
            if isinstance(issue, dict)
            and str(issue.get("title", "")).upper().startswith("PRD")
        ]
        if len(prd_candidates) != 1:
            raise SyncError("snapshot must contain exactly one PRD-titled issue")
    prd = prd_candidates[0]
    base_url = f"https://github.com/{canonical_repo}"
    issue_urls = [
        f"{base_url}/issues/{issue['number']}"
        for issue in sorted(issues, key=lambda value: value["number"])
        if issue is not prd
    ]
    pr_urls = [
        f"{base_url}/pull/{pull['number']}"
        for pull in sorted(pulls, key=lambda value: value["number"])
    ]
    project = snapshot.get("project")
    if not isinstance(project, dict) or not isinstance(project.get("url"), str):
        raise SyncError("snapshot project URL missing")
    receipt = {
        "github_repo": canonical_repo,
        "github_repository_id": expected_repository_id,
        "issue_urls": issue_urls,
        "line": line["id"],
        "pr_urls": pr_urls,
        "prd_issue_url": f"{base_url}/issues/{prd['number']}",
        "project_url": project["url"],
        "schema": "github-delivery-receipt/v1",
        "source_commit": export_source_commit,
        "synced_at": snapshot["fetched_at"],
    }
    metrics = derive_metrics(snapshot, issue_urls, receipt["prd_issue_url"])
    metrics.update(
        {
            "github_repo": canonical_repo,
            "github_repository_id": expected_repository_id,
            "line": line["id"],
            "project_url": project["url"],
        }
    )
    open_slices = [
        issue
        for issue in issues
        if issue is not prd and str(issue.get("state", "")).upper() == "OPEN"
    ]
    open_pulls = [
        pull for pull in pulls if str(pull.get("state", "")).upper() == "OPEN"
    ]
    blockers: list[str] = []
    if repository.get("license_spdx") != "MIT":
        blockers.append("license-missing")
    if repository.get("history_root") is not True:
        blockers.append("non-orphan-history")
    if repository.get("tree_sha") != export_tree_sha:
        blockers.append("export-tree-drift")
    if open_slices:
        blockers.append("open-delivery-slices")
    if open_pulls:
        blockers.append("open-delivery-prs")
    if repository.get("visibility") != "PUBLIC":
        blockers.append("human-visibility-gate")
    publication = {
        "blockers": blockers,
        "commit": repository.get("head_sha"),
        "export_source_commit": export_source_commit,
        "export_tree_sha": export_tree_sha,
        "file_count": repository.get("file_count"),
        "github_repo": canonical_repo,
        "github_repository_id": expected_repository_id,
        "history_root": repository.get("history_root"),
        "license_spdx": repository.get("license_spdx"),
        "line": line["id"],
        "public_ready": not blockers,
        "remote_url": repository.get("url"),
        "schema": "github-publication-attestation/v1",
        "verified_at": snapshot["fetched_at"],
        "visibility": repository.get("visibility"),
    }
    dashboard = render_dashboard(line["id"], snapshot, metrics, blockers)
    return receipt, publication, metrics, dashboard


def write_outputs(outputs: dict[Path, bytes]) -> None:
    """Prepare every output before replacing destinations."""
    prepared: list[tuple[Path, Path]] = []
    try:
        for destination, content in outputs.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            descriptor, raw_temp = tempfile.mkstemp(
                prefix=f".{destination.name}.", dir=destination.parent
            )
            temp = Path(raw_temp)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            prepared.append((temp, destination))
        for temp, destination in prepared:
            os.replace(temp, destination)
    finally:
        for temp, _destination in prepared:
            temp.unlink(missing_ok=True)
