#!/usr/bin/env python3
"""Shared deterministic helpers for repository-portfolio control packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

TERMINAL_AGENT_STATES = {
    "PASS",
    "FAIL",
    "BLOCKED",
    "CANCELLED",
    "STALE",
    "ABSENT",
    "TIMEOUT",
}


def canonical_bytes(value: Any, *, omit_digest: bool = False) -> bytes:
    if omit_digest and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key != "digest"}
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value, omit_digest=True)).hexdigest()


def bind_digest(value: dict[str, Any]) -> dict[str, Any]:
    bound = dict(value)
    bound["digest"] = content_digest(bound)
    return bound


def assert_digest(value: dict[str, Any], *, label: str) -> None:
    observed = value.get("digest")
    expected = content_digest(value)
    if observed != expected:
        raise ValueError(f"{label}: digest mismatch: expected {expected}, observed {observed}")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def duplicate_values(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def assert_acyclic(node_ids: set[str], edges: list[dict[str, Any]], *, graph: str) -> None:
    adjacency: dict[str, list[str]] = {node: [] for node in node_ids}
    indegree: dict[str, int] = {node: 0 for node in node_ids}
    for edge in edges:
        source = edge["from"]
        target = edge["to"]
        if source not in node_ids or target not in node_ids:
            raise ValueError(f"{graph}: edge references unknown node {source!r}->{target!r}")
        if source == target:
            raise ValueError(f"{graph}: self-edge {source!r}")
        adjacency[source].append(target)
        indegree[target] += 1
    queue = sorted(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        node = queue.pop(0)
        visited += 1
        for target in sorted(adjacency[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    if visited != len(node_ids):
        raise ValueError(f"{graph}: cycle detected")


def path_prefixes_overlap(left: str, right: str) -> bool:
    left_norm = left.strip("/")
    right_norm = right.strip("/")
    return (
        left_norm == right_norm
        or left_norm.startswith(right_norm + "/")
        or right_norm.startswith(left_norm + "/")
        or left_norm in {"*", "**", "UNKNOWN"}
        or right_norm in {"*", "**", "UNKNOWN"}
    )
