"""Offline unfinished-issue snapshot normalizer and controller-plan renderer."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from repository_control_plane_consumer import inspect_attachment
from repository_control_plane_profile import (
    EXIT_ABSENT,
    ContractError,
    read_json,
    render,
    sha256_document,
)


def _normalize_labels(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError("issue labels must be an array")
    labels: list[str] = []
    for item in value:
        if isinstance(item, str):
            label = item
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            label = item["name"]
        else:
            raise ContractError("each issue label must be a string or an object with name")
        labels.append(label.strip())
    return sorted(set(label for label in labels if label))


def _normalize_blockers(value: Any) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError("issue blocked_by must be an array")
    blockers: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool) or item <= 0:
            raise ContractError("issue blocked_by values must be positive integers")
        blockers.append(item)
    return sorted(set(blockers))


def issue_records(snapshot: Any) -> list[dict[str, Any]]:
    if isinstance(snapshot, list):
        issues = snapshot
    elif isinstance(snapshot, dict) and isinstance(snapshot.get("issues"), list):
        issues = snapshot["issues"]
    else:
        raise ContractError("issue snapshot must be an array or an object containing issues")

    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            raise ContractError(f"issues[{index}] must be an object")
        number = issue.get("number", issue.get("issue_number"))
        title = issue.get("title")
        state = str(issue.get("state", "open")).lower()
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ContractError(f"issues[{index}].number must be a positive integer")
        if number in seen:
            raise ContractError(f"duplicate issue number: {number}")
        seen.add(number)
        if not isinstance(title, str) or not title.strip():
            raise ContractError(f"issues[{index}].title must be non-empty")
        if state not in {"open", "closed"}:
            raise ContractError(f"issues[{index}].state must be open or closed")
        normalized.append(
            {
                "number": number,
                "title": title.strip(),
                "state": state,
                "labels": _normalize_labels(issue.get("labels")),
                "blocked_by": _normalize_blockers(issue.get("blocked_by")),
            }
        )
    return sorted(normalized, key=lambda item: item["number"])


def _effective_open_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove resolved blockers and reject self/cyclic open dependency graphs."""

    by_number = {issue["number"]: issue for issue in issues}
    open_issues: list[dict[str, Any]] = []
    for issue in issues:
        if issue["state"] != "open":
            continue
        blockers = [
            number
            for number in issue["blocked_by"]
            if by_number.get(number, {"state": "open"})["state"] != "closed"
        ]
        if issue["number"] in blockers:
            raise ContractError(f"issue #{issue['number']} cannot block itself")
        open_issues.append({**issue, "blocked_by": blockers})

    open_numbers = {issue["number"] for issue in open_issues}
    graph = {
        issue["number"]: [number for number in issue["blocked_by"] if number in open_numbers]
        for issue in open_issues
    }
    visiting: list[int] = []
    state: dict[int, int] = {}

    def visit(number: int) -> None:
        marker = state.get(number, 0)
        if marker == 2:
            return
        if marker == 1:
            start = visiting.index(number)
            cycle = visiting[start:] + [number]
            raise ContractError(
                "open issue dependency cycle: " + " -> ".join(f"#{item}" for item in cycle)
            )
        state[number] = 1
        visiting.append(number)
        for blocker in graph[number]:
            visit(blocker)
        visiting.pop()
        state[number] = 2

    for number in sorted(graph):
        visit(number)
    return open_issues


def build_monitor_plan(
    profile: dict[str, Any],
    *,
    control: dict[str, Any],
    snapshot: Any,
) -> dict[str, Any]:
    if control.get("schema") != "repository-control-plane/consumer-binding/v1":
        raise ContractError("consumer control-plane binding schema mismatch")
    issues = issue_records(snapshot)
    open_issues = _effective_open_issues(issues)
    planned: list[dict[str, Any]] = []
    chain = profile["controller_chain"]
    blocked_labels = {"blocked", "status:blocked", "status/blocked"}
    in_progress_labels = {"in-progress", "status:in-progress", "status/in-progress"}
    for issue in open_issues:
        labels = {label.lower() for label in issue["labels"]}
        if issue["blocked_by"] or labels & blocked_labels:
            routing_state = "BLOCKED"
        elif labels & in_progress_labels:
            routing_state = "IN_PROGRESS"
        else:
            routing_state = "READY"
        planned.append(
            {
                "task_id": f"github-issue-{issue['number']}",
                "number": issue["number"],
                "title": issue["title"],
                "routing_state": routing_state,
                "blocked_by": issue["blocked_by"],
                "labels": issue["labels"],
                "controller_chain": chain,
                "required_receipts": [item["receipt"] for item in chain],
                "execution_state": "NOT_EXERCISED",
                "merge_admission": "HUMAN_OR_TRUSTED_REPOSITORY_POLICY",
            }
        )
    return {
        "schema": profile["monitor"]["output_schema"],
        "consumer_repository_id": control["consumer_repository_id"],
        "profile": control["profile"],
        "control_binding_sha256": sha256_document(control),
        "source": {
            "kind": profile["monitor"]["source"],
            "query": profile["monitor"]["query"],
            "snapshot_sha256": sha256_document(snapshot),
            "input_issue_count": len(issues),
            "open_issue_count": len(planned),
        },
        "mode": profile["monitor"]["mode"],
        "issues": planned,
        "authority": control["authority"],
    }


def _atomic_output(path: Path, content: str) -> None:
    destination = path.expanduser()
    if os.path.lexists(destination) and destination.is_symlink():
        raise ContractError(f"monitor output must not be a symlink: {destination}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    except OSError as error:
        try:
            if "temporary" in locals() and temporary.exists():
                temporary.unlink()
        except OSError:
            pass
        raise ContractError(f"cannot atomically write monitor output {destination}: {error}") from error


def monitor_plan(
    profile: dict[str, Any],
    *,
    target_root: Path,
    issues_path: Path,
    output_path: Path | None,
) -> int:
    inspection = inspect_attachment(profile, target_root=target_root)
    if inspection.code != 0:
        for message in inspection.messages:
            print(message, file=sys.stderr)
        return inspection.code
    if inspection.control is None:
        raise ContractError("structurally closed attachment lacks its control binding")
    snapshot = read_json(issues_path, label="issue snapshot")
    plan = build_monitor_plan(profile, control=inspection.control, snapshot=snapshot)
    rendered = render(plan)
    if output_path is None:
        sys.stdout.write(rendered)
    else:
        _atomic_output(output_path, rendered)
        print(f"WROTE {output_path}")
    return 0 if plan["issues"] else EXIT_ABSENT
