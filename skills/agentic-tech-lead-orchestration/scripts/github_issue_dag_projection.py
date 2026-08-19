#!/usr/bin/env python3
"""Project an asserted semantic issue DAG into GitHub Issue Dependencies.

GitHub blockedBy is a durable projection of completion-readiness edges, never
semantic DAG authority. Live application fails closed unless repository identity,
visibility/default branch, issue states, and linked-PR ownership still match the
frozen graph.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

REPO_VISIBILITIES = {"PUBLIC", "PRIVATE", "INTERNAL"}
ISSUE_STATES = {"OPEN", "CLOSED"}

class ContractError(ValueError):
    pass

def canonical_graph_digest(data: dict[str, Any]) -> str:
    subject = {
        "repo": data.get("repo"),
        "repo_visibility": data.get("repo_visibility"),
        "default_branch": data.get("default_branch"),
        "nodes": data.get("nodes"),
        "edges": data.get("edges"),
    }
    encoded = json.dumps(
        subject, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def validate_graph(data: dict[str, Any]) -> None:
    repo = data.get("repo")
    if not isinstance(repo, str) or repo.count("/") != 1:
        raise ContractError("repo must be exact owner/name")
    visibility = data.get("repo_visibility")
    if visibility not in REPO_VISIBILITIES:
        raise ContractError("repo_visibility must be PUBLIC, PRIVATE, or INTERNAL")
    default_branch = data.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise ContractError("default_branch must be a non-empty string")

    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ContractError("nodes/edges must be lists")
    expected_digest = data.get("graph_digest")
    if expected_digest is not None and expected_digest != canonical_graph_digest(data):
        raise ContractError("graph_digest does not match frozen graph bytes")

    issues: list[int] = []
    for node in nodes:
        if not isinstance(node, dict):
            raise ContractError("node must be an object")
        allowed_node_keys = {"issue", "github_state", "state"}
        if set(node) - allowed_node_keys:
            raise ContractError(f"unsupported node fields: {sorted(set(node)-allowed_node_keys)}")
        issue = node.get("issue")
        if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
            raise ContractError("node issue must be positive integer")
        if issue in issues:
            raise ContractError(f"duplicate node: {issue}")
        issues.append(issue)
        if node.get("github_state") not in ISSUE_STATES:
            raise ContractError(f"github_state must be OPEN or CLOSED for issue {issue}")
        state = node.get("state", {})
        if not isinstance(state, dict):
            raise ContractError(f"state must be object for issue {issue}")
        if set(state) - {"start_readable", "completion_admitted"}:
            raise ContractError(f"unsupported state fields for issue {issue}")
        if not all(isinstance(v, bool) for v in state.values()):
            raise ContractError(f"readiness state must be boolean for issue {issue}")

    known = set(issues)
    seen: set[tuple[int, int, str]] = set()
    adjacency: dict[int, list[int]] = defaultdict(list)
    indeg = {i: 0 for i in issues}
    for edge in edges:
        if not isinstance(edge, dict):
            raise ContractError("edge must be an object")
        allowed_edge_keys = {"blocker", "blocked", "readiness", "project_to_github"}
        if set(edge) - allowed_edge_keys:
            raise ContractError(f"unsupported edge fields: {sorted(set(edge)-allowed_edge_keys)}")
        blocker = edge.get("blocker")
        blocked = edge.get("blocked")
        readiness = edge.get("readiness")
        project = edge.get("project_to_github", False)
        if not isinstance(project, bool):
            raise ContractError("project_to_github must be boolean")
        if blocker not in known or blocked not in known:
            raise ContractError("edge references unknown issue")
        if blocker == blocked:
            raise ContractError("self dependency is forbidden")
        if readiness not in {"start", "completion"}:
            raise ContractError("readiness must be start or completion")
        key = (blocker, blocked, readiness)
        if key in seen:
            raise ContractError(f"duplicate semantic edge: {key}")
        seen.add(key)
        if project and readiness != "completion":
            raise ContractError(
                "GitHub blockedBy may project completion-readiness edges only"
            )
        adjacency[blocker].append(blocked)
        indeg[blocked] += 1

    queue = deque(i for i, degree in indeg.items() if degree == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for nxt in adjacency[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if visited != len(issues):
        raise ContractError("semantic dependency graph contains a cycle")

def desired_blocked_by(data: dict[str, Any]) -> dict[int, list[int]]:
    validate_graph(data)
    desired = {node["issue"]: [] for node in data["nodes"]}
    for edge in data["edges"]:
        if edge.get("project_to_github", False):
            desired[edge["blocked"]].append(edge["blocker"])
    return {issue: sorted(values) for issue, values in desired.items()}

def ready_wave(data: dict[str, Any]) -> list[int]:
    validate_graph(data)
    states = {node["issue"]: node.get("state", {}) for node in data["nodes"]}
    incoming: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in data["edges"]:
        incoming[edge["blocked"]].append(edge)
    ready: list[int] = []
    for node in data["nodes"]:
        issue = node["issue"]
        ok = True
        for edge in incoming[issue]:
            source = states[edge["blocker"]]
            field = (
                "start_readable"
                if edge["readiness"] == "start"
                else "completion_admitted"
            )
            if source.get(field) is not True:
                ok = False
                break
        if ok:
            ready.append(issue)
    return sorted(ready)

def compare_readback(
    data: dict[str, Any], readback: dict[str, Any]
) -> dict[str, Any]:
    desired = desired_blocked_by(data)
    missing: dict[str, list[int]] = {}
    extra: dict[str, list[int]] = {}
    for issue, wanted in desired.items():
        row = readback.get(str(issue))
        if not isinstance(row, dict) or not isinstance(row.get("blockedBy"), list):
            raise ContractError(
                f"missing complete blockedBy readback for issue {issue}"
            )
        got = row["blockedBy"]
        if not all(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in got
        ):
            raise ContractError(f"malformed blockedBy readback for issue {issue}")
        got = sorted(got)
        missing_values = sorted(set(wanted) - set(got))
        extra_values = sorted(set(got) - set(wanted))
        if missing_values:
            missing[str(issue)] = missing_values
        if extra_values:
            extra[str(issue)] = extra_values
    return {
        "match": not missing and not extra,
        "missing": missing,
        "extra": extra,
    }

def _run(args: list[str]) -> str:
    process = subprocess.run(args, text=True, capture_output=True)
    if process.returncode:
        raise ContractError(
            f"command failed ({process.returncode}): {' '.join(args)}: "
            f"{process.stderr.strip()}"
        )
    return process.stdout

def _linked_pr_rows(repo: str, issue: int, refs: Any) -> list[dict[str, Any]]:
    if refs is None:
        refs = []
    if not isinstance(refs, list):
        raise ContractError(f"malformed linked PR readback for issue {issue}")
    rows: list[dict[str, Any]] = []
    for item in refs:
        if not isinstance(item, dict):
            raise ContractError(f"malformed linked PR item for issue {issue}")
        number = item.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ContractError(f"malformed linked PR number for issue {issue}")
        state = item.get("state")
        if state is None:
            raw = _run(
                ["gh", "pr", "view", str(number), "--repo", repo, "--json", "number,state"]
            )
            observed = json.loads(raw)
            state = observed.get("state")
            if observed.get("number") != number:
                raise ContractError(
                    f"linked PR identity mismatch for issue {issue}: expected {number}"
                )
        state = str(state).upper()
        if state not in {"OPEN", "CLOSED", "MERGED"}:
            raise ContractError(
                f"malformed linked PR state for issue {issue}: {state}"
            )
        rows.append({"number": number, "state": state})
    return sorted(rows, key=lambda row: row["number"])

def live_preflight(data: dict[str, Any]) -> dict[str, Any]:
    validate_graph(data)
    repo = data["repo"]
    raw_repo = _run(
        [
            "gh", "repo", "view", repo,
            "--json", "nameWithOwner,visibility,defaultBranchRef",
        ]
    )
    observed_repo = json.loads(raw_repo)
    default_ref = observed_repo.get("defaultBranchRef")
    observed_branch = (
        default_ref.get("name") if isinstance(default_ref, dict) else None
    )
    if observed_repo.get("nameWithOwner") != repo:
        raise ContractError(
            f"repository identity mismatch: expected {repo}, "
            f"got {observed_repo.get('nameWithOwner')}"
        )
    if str(observed_repo.get("visibility", "")).upper() != data["repo_visibility"]:
        raise ContractError(
            f"repository visibility drift: expected {data['repo_visibility']}"
        )
    if observed_branch != data["default_branch"]:
        raise ContractError(
            f"default branch drift: expected {data['default_branch']}, "
            f"got {observed_branch}"
        )

    expected_nodes = {node["issue"]: node for node in data["nodes"]}
    issues: dict[str, Any] = {}
    for issue in sorted(expected_nodes):
        raw_issue = _run(
            [
                "gh", "issue", "view", str(issue), "--repo", repo,
                "--json", "number,state,closedByPullRequestsReferences",
            ]
        )
        observed_issue = json.loads(raw_issue)
        if observed_issue.get("number") != issue:
            raise ContractError(
                f"issue identity mismatch: expected {issue}, "
                f"got {observed_issue.get('number')}"
            )
        observed_state = str(observed_issue.get("state", "")).upper()
        expected_state = expected_nodes[issue]["github_state"]
        if observed_state != expected_state:
            raise ContractError(
                f"stale issue state for {issue}: expected {expected_state}, "
                f"got {observed_state}"
            )
        linked = _linked_pr_rows(
            repo, issue, observed_issue.get("closedByPullRequestsReferences")
        )
        open_linked = [row["number"] for row in linked if row["state"] == "OPEN"]
        if len(open_linked) > 1:
            raise ContractError(
                f"duplicate open linked PR ownership for issue {issue}: {open_linked}"
            )
        issues[str(issue)] = {
            "state": observed_state,
            "linked_prs": linked,
        }

    return {
        "repository": {
            "nameWithOwner": repo,
            "visibility": data["repo_visibility"],
            "default_branch": data["default_branch"],
        },
        "issues": issues,
    }

def _linked_issue_numbers(value: Any, repo: str) -> list[int]:
    # gh issue view --json blockedBy returns a LinkedIssueConnection
    # ({"nodes": [...], "totalCount": N}), never a bare list (#497).
    if not isinstance(value, dict) or set(value) != {"nodes", "totalCount"}:
        raise ContractError("blockedBy connection malformed")
    nodes = value["nodes"]
    total = value["totalCount"]
    if not isinstance(nodes, list):
        raise ContractError("blockedBy nodes malformed")
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise ContractError("blockedBy totalCount malformed")
    if total != len(nodes):
        raise ContractError("blockedBy totalCount mismatch")
    numbers: list[int] = []
    for node in nodes:
        if not isinstance(node, dict):
            raise ContractError("blockedBy node malformed")
        number = node.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ContractError("blockedBy number malformed")
        repository = node.get("repository")
        if (
            not isinstance(repository, dict)
            or repository.get("nameWithOwner") != repo
        ):
            raise ContractError("blockedBy repository drift")
        numbers.append(number)
    if len(set(numbers)) != len(numbers):
        raise ContractError("blockedBy duplicate")
    return sorted(numbers)

def live_readback(repo: str, issues: list[int]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for issue in issues:
        raw = _run(
            ["gh", "issue", "view", str(issue), "--repo", repo, "--json", "blockedBy"]
        )
        obj = json.loads(raw)
        if not isinstance(obj, dict) or set(obj) != {"blockedBy"}:
            raise ContractError(
                f"malformed GitHub blockedBy response for issue {issue}"
            )
        result[str(issue)] = {
            "blockedBy": _linked_issue_numbers(obj["blockedBy"], repo)
        }
    return result

def apply_projection(data: dict[str, Any]) -> dict[str, Any]:
    desired = desired_blocked_by(data)
    preflight_before = live_preflight(data)
    before = live_readback(data["repo"], sorted(desired))
    diff = compare_readback(data, before)
    if diff["extra"]:
        raise ContractError(
            "remote contains extra blockedBy edges not owned by this projection; "
            f"refusing destructive reconciliation: {diff['extra']}"
        )
    for issue, values in diff["missing"].items():
        for blocker in values:
            _run(
                [
                    "gh", "issue", "edit", issue, "--repo", data["repo"],
                    "--add-blocked-by", str(blocker),
                ]
            )
    after = live_readback(data["repo"], sorted(desired))
    check = compare_readback(data, after)
    if not check["match"]:
        raise ContractError(f"remote readback drift remains: {check}")
    preflight_after = live_preflight(data)
    if preflight_after != preflight_before:
        raise ContractError(
            "repository/issue/linked-PR preflight changed during projection; "
            "refusing stable admission"
        )
    return {
        "repo": data["repo"],
        "graph_digest": canonical_graph_digest(data),
        "desired": desired,
        "preflight": preflight_after,
        "before": before,
        "after": after,
        "ready_wave": ready_wave(data),
        "evidence_ceiling": "REMOTE_PROJECTION_READBACK_ONLY",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph")
    parser.add_argument("--readback")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path(args.graph).read_text())
    output: dict[str, Any] = {
        "repo": data["repo"],
        "graph_digest": canonical_graph_digest(data),
        "desired": desired_blocked_by(data),
        "ready_wave": ready_wave(data),
        "evidence_ceiling": "STATIC_PROJECTION_ONLY",
    }
    if args.readback:
        readback = json.loads(Path(args.readback).read_text())
        output["readback"] = compare_readback(data, readback)
    if args.apply:
        output = apply_projection(data)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
