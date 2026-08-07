"""GitLab snapshot ingestion, flow metrics, and decision-dashboard projection.

This is the GitLab half of the delivery mechanism. It shares no code with the
GitHub skill on purpose: every schema name, every field name and every URL shape
here is `gitlab-*`, so feeding GitHub state into these functions fails loudly
instead of half-working. See modules/github-vs-gitlab.md.
"""

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
from urllib.parse import quote, urlparse


FORGE = "gitlab"
SNAPSHOT_SCHEMA = "gitlab-delivery-snapshot/v1"
METRICS_SCHEMA = "gitlab-delivery-metrics/v1"
RECEIPT_SCHEMA = "gitlab-delivery-receipt/v1"
PUBLICATION_SCHEMA = "gitlab-publication-attestation/v1"
BLOCKED_LABELS = {"blocked", "blocked-dependency"}

# GitLab's documented closing keywords, plus `Part of #N`, which is *our*
# start-marker convention rather than a GitLab keyword: it establishes queue and
# start relationships without ever claiming acceptance.
REFERENCE_RE = re.compile(
    r"(?im)\b(close[sd]?|closing|fix(?:e[sd])?|fixing|resolve[sd]?|resolving"
    r"|implement(?:s|ed)?|implementing|part\s+of)\s+#([1-9][0-9]*)"
)
NON_CLOSING = "part of"
FIRST_PASS_ABSENT = "gitlab-approvals-carry-no-timestamp-and-no-changes-requested-state"

SHA_RE = re.compile(r"[0-9a-f]{40}")
HOST_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?")
# GitLab projects live under nested groups, so a path has two *or more*
# segments. Assuming a single slash is the most common way a GitHub-shaped
# assumption silently breaks on GitLab.
PROJECT_RE = re.compile(r"[A-Za-z0-9_.][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.][A-Za-z0-9_.-]*)+")


class SyncError(ValueError):
    """Raised when GitLab state cannot produce a trustworthy projection."""


# --------------------------------------------------------------------------
# cross-forge guard: GitHub state must never validate here
# --------------------------------------------------------------------------


GITHUB_KEYS = ("github_repo", "github_repository_id")


def reject_github_shape(value: Any, where: str) -> None:
    """Refuse GitHub-shaped state instead of silently ignoring it.

    An unknown key is normally harmless, but `github_repo` in a GitLab registry
    means someone pointed the wrong skill at their work. Ignoring it would let
    the run continue against whatever `gitlab_project` happened to be there --
    the two forges must not be interchangeable by accident.
    """
    if isinstance(value, dict):
        for key in GITHUB_KEYS:
            if key in value:
                raise SyncError(
                    f"{where}: found GitHub field '{key}' -- this is the GitLab skill; "
                    "use github-delivery-loop for GitHub state"
                )
    text = value if isinstance(value, str) else ""
    if "github.com" in text:
        raise SyncError(
            f"{where}: GitHub URL in GitLab state: {text} -- "
            "use github-delivery-loop for GitHub state"
        )


# --------------------------------------------------------------------------
# time helpers
# --------------------------------------------------------------------------


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
        (_parse_time(end, f"{field}.end") - _parse_time(start, f"{field}.start")).total_seconds()
    )
    if delta < 0:
        raise SyncError(f"{field} cannot be negative")
    return delta


def _issue_iid(url: str) -> int:
    """GitLab serves issues at both /-/issues/N and /-/work_items/N.

    The work-item path is not a rewrite we invented: the live API returns it in
    `web_url` for migrated issues, so a validator that only knows /-/issues/
    rejects real GitLab URLs.
    """
    match = re.search(r"/-/(?:issues|work_items)/([1-9][0-9]*)$", url)
    if match is None:
        raise SyncError(f"invalid GitLab issue URL: {url}")
    return int(match.group(1))


def _references(body: Any) -> tuple[set[int], set[int]]:
    all_refs: set[int] = set()
    closing_refs: set[int] = set()
    for kind, raw_iid in REFERENCE_RE.findall(body if isinstance(body, str) else ""):
        iid = int(raw_iid)
        all_refs.add(iid)
        if " ".join(kind.lower().split()) != NON_CLOSING:
            closing_refs.add(iid)
    return all_refs, closing_refs


def _label_names(issue: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    labels = issue.get("labels", [])
    if not isinstance(labels, list):
        raise SyncError(f"issue !{issue.get('iid')}: labels must be a list")
    for label in labels:
        name = label.get("name") if isinstance(label, dict) else label
        if isinstance(name, str):
            names.add(name.lower())
    return names


def _blocked_seconds(issue: dict[str, Any], fetched_at: str) -> int:
    """Sum the blocked intervals from GitLab resource label events.

    GitLab splits what GitHub calls issue events: label transitions live in
    `resource_label_events` with action add/remove, state transitions live in
    `resource_state_events`. Both are normalized into `label_events` /
    `state_events` at fetch time.
    """
    events = issue.get("label_events", [])
    if not isinstance(events, list):
        raise SyncError(f"issue !{issue.get('iid')}: label_events must be a list")
    started: datetime | None = None
    total = 0
    for event in sorted(events, key=lambda item: str(item.get("created_at", ""))):
        name = str(event.get("label", "")).lower()
        if name not in BLOCKED_LABELS:
            continue
        at = _parse_time(event.get("created_at"), "blocked event")
        action = event.get("action")
        if action == "add" and started is None:
            started = at
        elif action == "remove" and started is not None:
            total += int((at - started).total_seconds())
            started = None
    if started is not None:
        stop = _parse_time(issue.get("closed_at") or fetched_at, "blocked interval end")
        total += max(0, int((stop - started).total_seconds()))
    return total


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------


def derive_metrics(
    snapshot: dict[str, Any], issue_urls: list[str], prd_issue_url: str
) -> dict[str, Any]:
    """Derive flow-health metrics from GitLab event timestamps."""
    fetched_at = snapshot.get("fetched_at")
    now = _parse_time(fetched_at, "fetched_at")
    issues = snapshot.get("issues")
    merge_requests = snapshot.get("merge_requests")
    if not isinstance(issues, list) or not isinstance(merge_requests, list):
        raise SyncError("snapshot issues and merge_requests must be lists")
    by_issue = {item.get("iid"): item for item in issues if isinstance(item, dict)}
    prd_iid = _issue_iid(prd_issue_url)
    slice_iids = [_issue_iid(url) for url in issue_urls if _issue_iid(url) != prd_iid]

    mr_refs: list[tuple[dict[str, Any], set[int], set[int]]] = []
    for merge_request in merge_requests:
        if not isinstance(merge_request, dict):
            raise SyncError("snapshot merge_request must be an object")
        all_refs, closing_refs = _references(merge_request.get("description"))
        mr_refs.append((merge_request, all_refs, closing_refs))

    slices: list[dict[str, Any]] = []
    accepted_times: list[datetime] = []
    reopened_count = 0
    for iid in slice_iids:
        issue = by_issue.get(iid)
        if not isinstance(issue, dict):
            raise SyncError(f"snapshot missing registered issue !{iid}")
        starts = [item for item, all_refs, _closing in mr_refs if iid in all_refs]
        starts.sort(key=lambda item: str(item.get("created_at", "")))
        accepted = [
            item
            for item, _all_refs, closing_refs in mr_refs
            if iid in closing_refs and item.get("merged_at")
        ]
        accepted.sort(key=lambda item: str(item.get("merged_at", "")))
        start = starts[0] if starts else None
        merge = accepted[0] if accepted else None
        blocked = _blocked_seconds(issue, str(fetched_at))
        reopened = any(
            isinstance(event, dict) and event.get("state") == "reopened"
            for event in issue.get("state_events", [])
        )
        reopened_count += int(reopened)
        if merge is not None:
            accepted_times.append(
                _parse_time(merge.get("merged_at"), f"MR !{merge.get('iid')}.merged_at")
            )

        labels = _label_names(issue)
        slices.append(
            {
                "accepted_mr": merge.get("iid") if merge else None,
                "blocked_seconds": blocked,
                "currently_blocked": bool(labels & BLOCKED_LABELS),
                "cycle_seconds": (
                    _seconds(start.get("created_at"), merge.get("merged_at"), "cycle")
                    if start and merge
                    else None
                ),
                "issue_iid": iid,
                "issue_state": str(issue.get("state", "")).lower(),
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
                "started_mr": start.get("iid") if start else None,
                "title": issue.get("title"),
            }
        )

    def values(field: str) -> list[int]:
        return [item[field] for item in slices if isinstance(item[field], int)]

    seven_days = 7 * 24 * 3600
    twenty_eight_days = 28 * 24 * 3600
    summary = {
        "accepted_slices": len(accepted_times),
        "blocked_slices": sum(item["currently_blocked"] for item in slices),
        # GitLab issue state is "opened"/"closed" (not "open"/"OPEN"): a state
        # comparison copied from the GitHub skill silently matches nothing.
        "closed_without_merge": sum(
            item["issue_state"] == "closed" and item["accepted_mr"] is None for item in slices
        ),
        "total_slices": len(slices),
        "throughput_7d": sum(
            0 <= (now - item).total_seconds() <= seven_days for item in accepted_times
        ),
        "throughput_28d": sum(
            0 <= (now - item).total_seconds() <= twenty_eight_days for item in accepted_times
        ),
        "wip": sum(
            item["issue_state"] == "opened" and item["started_mr"] is not None for item in slices
        ),
    }
    percentiles = {
        field: {"p50": _nearest_rank(values(field), 0.50), "p85": _nearest_rank(values(field), 0.85)}
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
        "forge": FORGE,
        "percentiles": percentiles,
        "quality": {
            # GitHub derives first-pass rate from review events, which carry a
            # submitted_at and an APPROVED / CHANGES_REQUESTED state. GitLab has
            # neither: approvals are a current-state list with no timestamps
            # (probed live) and there is no changes-requested state at all. The
            # honest output is an explicit absence with its reason, not a number
            # reconstructed from system-note text.
            "first_pass_rate": None,
            "first_pass_rate_absent": FIRST_PASS_ABSENT,
            "redaction_leakage_rate": None,
            "reopen_rate": reopened_count / len(slices) if slices else None,
        },
        "schema": METRICS_SCHEMA,
        "slices": slices,
        "summary": summary,
    }


# --------------------------------------------------------------------------
# live fetch
# --------------------------------------------------------------------------


def _glab_json(host: str, path: str, paginate: bool = False) -> Any:
    args = ["glab", "api", "--hostname", host]
    if paginate:
        args.append("--paginate")
    args.append(path)
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "glab command failed"
        raise SyncError(f"glab api {path}: {detail}")
    raw = result.stdout.strip()
    if not raw:
        return []
    try:
        # `--paginate` concatenates one JSON document per page, so the combined
        # output is not a single document. Decode the stream and splice arrays.
        decoder = json.JSONDecoder()
        documents: list[Any] = []
        index = 0
        while index < len(raw):
            value, offset = decoder.raw_decode(raw, index)
            documents.append(value)
            index = offset
            while index < len(raw) and raw[index] in " \r\n\t":
                index += 1
    except json.JSONDecodeError as error:
        raise SyncError(f"glab api {path} returned invalid JSON: {error}") from error
    if len(documents) == 1:
        return documents[0]
    merged: list[Any] = []
    for document in documents:
        if isinstance(document, list):
            merged.extend(document)
        else:
            merged.append(document)
    return merged


def _encoded(project: str) -> str:
    return quote(project, safe="")


def fetch_gitlab_snapshot(host: str, project: str, board_url: str) -> dict[str, Any]:
    """Fetch one normalized snapshot through the authenticated GitLab CLI."""
    if PROJECT_RE.fullmatch(project) is None:
        raise SyncError(f"gitlab_project must be a namespaced path: {project}")
    encoded = _encoded(project)
    # `license=true` is required: the project payload omits `license` otherwise,
    # which would read as "no license" and raise a false publication blocker.
    meta = _glab_json(host, f"projects/{encoded}?license=true")
    default_branch = meta.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise SyncError("GitLab project has no default branch")
    head = _glab_json(host, f"projects/{encoded}/repository/commits/{default_branch}")
    commits = _glab_json(host, f"projects/{encoded}/repository/commits?per_page=100")
    tree = _glab_json(
        host,
        f"projects/{encoded}/repository/tree?recursive=true&per_page=100&ref={default_branch}",
        paginate=True,
    )

    raw_issues = _glab_json(host, f"projects/{encoded}/issues?state=all&per_page=100", paginate=True)
    issues: list[dict[str, Any]] = []
    for issue in raw_issues:
        iid = issue["iid"]
        label_events = _glab_json(
            host, f"projects/{encoded}/issues/{iid}/resource_label_events?per_page=100", True
        )
        state_events = _glab_json(
            host, f"projects/{encoded}/issues/{iid}/resource_state_events?per_page=100", True
        )
        issues.append(
            {
                "closed_at": issue.get("closed_at"),
                "created_at": issue.get("created_at"),
                "iid": iid,
                "label_events": [
                    {
                        "action": event.get("action"),
                        "created_at": event.get("created_at"),
                        "label": (event.get("label") or {}).get("name"),
                    }
                    for event in label_events
                ],
                "labels": issue.get("labels", []),
                "state": str(issue.get("state", "")).lower(),
                "state_events": [
                    {"created_at": event.get("created_at"), "state": event.get("state")}
                    for event in state_events
                ],
                "title": issue.get("title"),
            }
        )

    raw_mrs = _glab_json(
        host, f"projects/{encoded}/merge_requests?state=all&per_page=100", paginate=True
    )
    merge_requests: list[dict[str, Any]] = []
    for merge_request in raw_mrs:
        iid = merge_request["iid"]
        merge_requests.append(
            {
                "closed_at": merge_request.get("closed_at"),
                "created_at": merge_request.get("created_at"),
                "description": merge_request.get("description") or "",
                "iid": iid,
                "merged_at": merge_request.get("merged_at"),
                "ready_at": (
                    merge_request.get("prepared_at") or merge_request.get("created_at")
                    if not merge_request.get("draft")
                    else None
                ),
                "state": str(merge_request.get("state", "")).lower(),
                "title": merge_request.get("title"),
            }
        )

    boards = _glab_json(host, f"projects/{encoded}/boards?per_page=100", paginate=True)
    board = resolve_board(host, meta.get("path_with_namespace") or project,
                          board_url, boards, issues)

    license_value = meta.get("license") or {}
    namespace = meta.get("namespace") or {}
    return {
        "board": board,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "forge": FORGE,
        "host": host,
        "issues": issues,
        "merge_requests": merge_requests,
        "project": {
            "default_branch": default_branch,
            "file_count": sum(item.get("type") == "blob" for item in tree),
            "head_sha": head.get("id"),
            "history_root": any(not item.get("parent_ids") for item in commits),
            "id": meta.get("id"),
            "license_key": license_value.get("key"),
            "namespace_kind": namespace.get("kind"),
            "namespace_path": namespace.get("full_path") or namespace.get("path"),
            "path_with_namespace": meta.get("path_with_namespace"),
            "visibility": str(meta.get("visibility", "")).lower(),
            "web_url": meta.get("web_url"),
        },
        "schema": SNAPSHOT_SCHEMA,
    }


def resolve_board(
    host: str,
    project: str,
    board_url: str,
    boards: list[Any],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve the board URL against the boards the project actually has.

    Falling back to a nameless placeholder when the URL does not resolve would
    write a receipt pointing at a board that does not exist -- a green receipt
    for an absent artifact, which is the one thing this skill exists to refuse.
    So every way of not finding the board is an explicit exit.
    """
    parsed = urlparse(board_url)
    match = re.fullmatch(r"/(.+)/-/boards/([1-9][0-9]*)", parsed.path)
    if parsed.scheme != "https" or parsed.netloc != host or match is None:
        raise SyncError(
            f"board_url must be https://{host}/{project}/-/boards/N, got: {board_url}"
        )
    if match.group(1) != project:
        raise SyncError(
            f"board_url points at project {match.group(1)!r}, not {project!r}"
        )
    wanted = match.group(2)
    for candidate in boards:
        if isinstance(candidate, dict) and str(candidate.get("id")) == wanted:
            return {
                "url": board_url,
                "name": candidate.get("name", ""),
                # A GitLab board list is a label column; counting open issues
                # per label is the same projection GitHub Projects gives.
                "list_counts": _board_counts(candidate, issues),
            }
    available = ", ".join(
        str(candidate.get("id")) for candidate in boards if isinstance(candidate, dict)
    )
    raise SyncError(
        f"no board {wanted} on {project}; available board ids: {available or 'none'}"
    )


def _board_counts(board: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    lists = board.get("lists")
    if not isinstance(lists, list):
        return counts
    for entry in lists:
        label = (entry.get("label") or {}).get("name")
        if not isinstance(label, str):
            continue
        counts[label] = sum(
            1
            for issue in issues
            if issue.get("state") == "opened" and label in (issue.get("labels") or [])
        )
    return counts


# --------------------------------------------------------------------------
# export tree binding (GitLab exposes no root tree sha -- bind locally)
# --------------------------------------------------------------------------


def remote_head_tree(export_repo: Path, head_sha: str) -> tuple[str | None, str | None]:
    """Resolve the tree of the remote head commit using the local export clone.

    GitHub hands out the head commit's tree sha in its API, so that skill can
    compare "the tree I verified" against "the tree that is published" over the
    wire. GitLab publishes no root tree id at all: the REST commit object has no
    tree field and the GraphQL `Tree` type has no `sha`. Both were probed live
    rather than assumed.

    So the binding is done locally instead: the export clone is the repository
    we pushed, so it already contains the commit GitLab reports as head. If it
    does not, somebody else pushed and nothing local can attest to that tree --
    that is `remote-head-unverifiable`, an explicit exit, not a silent pass.
    """
    if SHA_RE.fullmatch(head_sha or "") is None:
        return None, "remote head is not a full 40-character SHA"
    if not (export_repo / ".git").exists() and not (export_repo / "HEAD").exists():
        return None, f"export repo is not a git repository: {export_repo}"
    done = subprocess.run(
        ["git", "-C", str(export_repo), "rev-parse", "--verify", "--quiet", f"{head_sha}^{{tree}}"],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        return None, f"commit {head_sha[:12]} is not present in {export_repo}"
    tree = done.stdout.strip()
    if SHA_RE.fullmatch(tree) is None:
        return None, f"git returned a non-SHA tree for {head_sha[:12]}"
    return tree, None


# --------------------------------------------------------------------------
# outputs
# --------------------------------------------------------------------------


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def render_dashboard(
    line_id: str, snapshot: dict[str, Any], metrics: dict[str, Any], blockers: list[str]
) -> str:
    """Render a compact Markdown decision snapshot from event-derived metrics."""
    summary = metrics["summary"]
    board = snapshot.get("board", {})
    project = snapshot["project"]
    lines = [
        f"# {line_id} delivery dashboard (GitLab)",
        "",
        f"> Snapshot: `{snapshot['fetched_at']}` @ `{snapshot['host']}`。本頁是 GitLab event truth",
        "> 的時間點快照，不是 registry 的第二份真相，也不是個人生產力排名。",
        "",
        "## Truth boundary",
        "",
        "```text",
        "┌───────────────┐    ┌──────────────┐    ┌────────────────────────┐",
        "│ GitLab events │ ─→ │ metrics.json │ ─→ │ Markdown decision view │",
        "└───────────────┘    └──────────────┘    └────────────────────────┘",
        "         │",
        "         ├─→ GitLab issue board (status projection only)",
        "         └─→ publication attestation ─→ human visibility gate",
        "```",
        "",
        "## Current decision",
        "",
        f"- Project: `{project['path_with_namespace']}` (`{project['visibility']}`, id "
        f"`{project['id']}`)",
        f"- Remote head: `{project.get('head_sha')}` "
        f"({project.get('file_count')} files, orphan root: "
        f"`{'YES' if project.get('history_root') else 'NO'}`)",
        f"- Public ready: `{'YES' if not blockers else 'NO'}`",
        f"- Blockers: `{', '.join(blockers) if blockers else 'none'}`",
        f"- Board: [{board.get('name') or 'GitLab issue board'}]({board.get('url', '')})",
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
        "## Board projection",
        "",
        "| List | Open issues |",
        "|---|---:|",
        *[
            f"| {name} | {count} |"
            for name, count in sorted(board.get("list_counts", {}).items())
        ],
        "",
        "`closed_without_merge` 是證據缺口，不計入 throughput。"
        "p50/p85 只在有 merge event 樣本時顯示。",
        "",
        "## Slice evidence",
        "",
        "| Issue | State | Started MR | Accepted MR | Lead | Blocked |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for item in metrics["slices"]:
        lines.append(
            "| !{issue_iid} | {issue_state} | {started} | {accepted} | {lead} | {blocked} |".format(
                issue_iid=item["issue_iid"],
                issue_state=item["issue_state"],
                started=f"!{item['started_mr']}" if item["started_mr"] else "—",
                accepted=f"!{item['accepted_mr']}" if item["accepted_mr"] else "—",
                lead=item["lead_seconds"] if item["lead_seconds"] is not None else "UNKNOWN",
                blocked=item["blocked_seconds"],
            )
        )
    lines.extend(
        [
            "",
            "## Human gate",
            "",
            "只有 blockers 清空、publication attestation 與遠端 HEAD 對齊後，"
            "人類才可執行 MR merge 與 private→public。",
            "",
            "GitLab 的 `internal` visibility 沒有 GitHub 對應物：它對登入使用者可見，"
            "**不等於 private**，所以它有自己的 blocker，不與 private 併攏。",
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
    export_repo: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Validate one snapshot and build all synchronized output values in memory."""
    reject_github_shape(line, "registry line")
    reject_github_shape(snapshot, "snapshot")
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise SyncError(f"snapshot schema must be {SNAPSHOT_SCHEMA}")
    if snapshot.get("forge") != FORGE:
        raise SyncError(f"snapshot forge must be {FORGE!r}, got {snapshot.get('forge')!r}")
    project = snapshot.get("project")
    if not isinstance(project, dict):
        raise SyncError("snapshot project must be an object")
    host = snapshot.get("host")
    if not isinstance(host, str) or HOST_RE.fullmatch(host) is None:
        raise SyncError("snapshot host must be a hostname")
    if host != line.get("gitlab_host"):
        raise SyncError(
            f"snapshot host {host!r} != registry gitlab_host {line.get('gitlab_host')!r}"
        )

    # Identity is the numeric project id, which survives renames and transfers.
    # The path is only a transferable alias.
    expected_id = line.get("gitlab_project_id")
    if not isinstance(expected_id, int) or isinstance(expected_id, bool) or expected_id < 1:
        raise SyncError("registry line must pin gitlab_project_id (a positive integer)")
    if project.get("id") != expected_id:
        raise SyncError(
            "snapshot project mismatch: expected id "
            f"{expected_id}, got {project.get('id')} ({project.get('path_with_namespace')})"
        )
    canonical = project.get("path_with_namespace")
    if not isinstance(canonical, str) or PROJECT_RE.fullmatch(canonical) is None:
        raise SyncError("snapshot project path_with_namespace missing or malformed")
    if SHA_RE.fullmatch(export_source_commit) is None:
        raise SyncError("export source commit must be a full 40-character SHA")
    if SHA_RE.fullmatch(export_tree_sha) is None:
        raise SyncError("export tree sha must be a full 40-character SHA")

    issues = snapshot.get("issues")
    merge_requests = snapshot.get("merge_requests")
    if not isinstance(issues, list) or not issues:
        raise SyncError("snapshot issues must be a non-empty list")
    if not isinstance(merge_requests, list):
        raise SyncError("snapshot merge_requests must be a list")
    prd_candidates = [
        issue
        for issue in issues
        if isinstance(issue, dict) and str(issue.get("title", "")).upper().startswith("PRD")
    ]
    if len(prd_candidates) != 1:
        raise SyncError("snapshot must contain exactly one PRD-titled issue")
    prd = prd_candidates[0]

    base_url = f"https://{host}/{canonical}"
    issue_urls = [
        f"{base_url}/-/issues/{issue['iid']}"
        for issue in sorted(issues, key=lambda value: value["iid"])
        if issue is not prd
    ]
    mr_urls = [
        f"{base_url}/-/merge_requests/{item['iid']}"
        for item in sorted(merge_requests, key=lambda value: value["iid"])
    ]
    board = snapshot.get("board")
    if not isinstance(board, dict) or not isinstance(board.get("url"), str):
        raise SyncError("snapshot board URL missing")

    receipt = {
        "board_url": board["url"],
        "forge": FORGE,
        "gitlab_host": host,
        "gitlab_project": canonical,
        "gitlab_project_id": expected_id,
        "issue_urls": issue_urls,
        "line": line["id"],
        "mr_urls": mr_urls,
        "prd_issue_url": f"{base_url}/-/issues/{prd['iid']}",
        "schema": RECEIPT_SCHEMA,
        "source_commit": export_source_commit,
        "synced_at": snapshot["fetched_at"],
    }
    metrics = derive_metrics(snapshot, issue_urls, receipt["prd_issue_url"])
    metrics.update(
        {
            "board_url": board["url"],
            "gitlab_host": host,
            "gitlab_project": canonical,
            "gitlab_project_id": expected_id,
            "line": line["id"],
        }
    )

    open_slices = [
        issue for issue in issues if issue is not prd and str(issue.get("state", "")) == "opened"
    ]
    open_mrs = [item for item in merge_requests if str(item.get("state", "")) == "opened"]
    remote_tree, tree_error = remote_head_tree(export_repo, str(project.get("head_sha") or ""))

    blockers: list[str] = []
    if project.get("license_key") != "mit":
        blockers.append("license-missing")
    if project.get("history_root") is not True:
        blockers.append("non-orphan-history")
    if remote_tree is None:
        blockers.append("remote-head-unverifiable")
    elif remote_tree != export_tree_sha:
        blockers.append("export-tree-drift")
    if open_slices:
        blockers.append("open-delivery-slices")
    if open_mrs:
        blockers.append("open-delivery-mrs")
    visibility = project.get("visibility")
    if visibility == "internal":
        blockers.append("internal-visibility")
    elif visibility != "public":
        blockers.append("human-visibility-gate")

    publication = {
        "blockers": blockers,
        "commit": project.get("head_sha"),
        "export_source_commit": export_source_commit,
        "export_tree_sha": export_tree_sha,
        "file_count": project.get("file_count"),
        "forge": FORGE,
        "gitlab_host": host,
        "gitlab_project": canonical,
        "gitlab_project_id": expected_id,
        "history_root": project.get("history_root"),
        "license_key": project.get("license_key"),
        "line": line["id"],
        "public_ready": not blockers,
        "remote_head_tree_sha": remote_tree,
        "remote_head_tree_error": tree_error,
        "remote_url": project.get("web_url"),
        "schema": PUBLICATION_SCHEMA,
        "verified_at": snapshot["fetched_at"],
        "visibility": visibility,
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
