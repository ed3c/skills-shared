#!/usr/bin/env python3
"""Compile exact snapshot and acceptance packets into the seven-graph portfolio model."""

from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
from pathlib import Path
from typing import Any

from portfolio_control_lib import (
    assert_digest,
    bind_digest,
    canonical_bytes,
    load_json,
    path_prefixes_overlap,
    write_json,
)


def edge(source: str, target: str, relation: str, reason: str, subject_digest: str) -> dict[str, str]:
    return {
        "from": source,
        "to": target,
        "relation": relation,
        "reason": reason,
        "subject_digest": subject_digest,
    }


def pair_digest(left: str, right: str, reason: str) -> str:
    return hashlib.sha256(canonical_bytes([left, right, reason])).hexdigest()


def compile_graph(snapshot: dict[str, Any], acceptances: list[dict[str, Any]]) -> dict[str, Any]:
    assert_digest(snapshot, label="snapshot")
    by_id: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, str]] = []
    for packet in acceptances:
        assert_digest(packet, label=f"acceptance:{packet.get('unit_id', '<missing>')}")
        unit_id = packet["unit_id"]
        if unit_id in by_id:
            raise ValueError(f"duplicate acceptance unit_id: {unit_id}")
        by_id[unit_id] = packet
        blocked = any(item["state"] != "PASS" for item in packet["prerequisites"])
        nodes.append(
            {
                "id": unit_id,
                "acceptance_digest": packet["digest"],
                "state": "BLOCKED_BY_RUNTIME" if blocked else "READY",
            }
        )

    graphs: dict[str, list[dict[str, str]]] = {name: [] for name in ("G1", "G2", "G3", "G4", "G5", "G6", "G7")}
    completion_parent_count: dict[str, int] = {unit_id: 0 for unit_id in by_id}

    for unit_id, packet in by_id.items():
        for dependency in packet["start_dependencies"]:
            parent = dependency["unit_id"]
            if parent not in by_id:
                raise ValueError(f"{unit_id}: missing start dependency packet {parent}")
            graphs["G1"].append(edge(parent, unit_id, "START_DEPENDENCY", dependency["reason"], dependency["subject_digest"]))
        for dependency in packet["completion_dependencies"]:
            parent = dependency["unit_id"]
            if parent not in by_id:
                raise ValueError(f"{unit_id}: missing completion dependency packet {parent}")
            completion_parent_count[unit_id] += 1
            graphs["G2"].append(edge(parent, unit_id, "COMPLETION_DEPENDENCY", dependency["reason"], dependency["subject_digest"]))
            graphs["G7"].append(edge(parent, unit_id, "PUBLICATION_DEPENDENCY", "completion admission precedes publication", dependency["subject_digest"]))
            if dependency["reason"].startswith("TRUE_CHILD:"):
                graphs["G3"].append(edge(parent, unit_id, "TRUE_CHILD", dependency["reason"], dependency["subject_digest"]))
            elif dependency["reason"].startswith("EXTERNAL_EVIDENCE:"):
                graphs["G6"].append(edge(parent, unit_id, "EXTERNAL_EVIDENCE", dependency["reason"], dependency["subject_digest"]))

    for left_id, right_id in combinations(sorted(by_id), 2):
        left = by_id[left_id]
        right = by_id[right_id]
        overlaps = sorted(
            {
                f"{left_path} <> {right_path}"
                for left_path in left["leases"]["exclusive"]
                for right_path in right["leases"]["exclusive"]
                if path_prefixes_overlap(left_path, right_path)
            }
        )
        if overlaps:
            reason = "exclusive writer overlap: " + "; ".join(overlaps)
            graphs["G4"].append(edge(left_id, right_id, "PATH_CONFLICT", reason, pair_digest(left_id, right_id, reason)))

        left_resources = {item["id"] for item in left["prerequisites"] if item["id"].startswith("exclusive-resource:")}
        right_resources = {item["id"] for item in right["prerequisites"] if item["id"].startswith("exclusive-resource:")}
        for resource in sorted(left_resources & right_resources):
            reason = f"exclusive runtime resource: {resource}"
            graphs["G5"].append(edge(left_id, right_id, "RESOURCE_CONFLICT", reason, pair_digest(left_id, right_id, reason)))

    predecessors: dict[str, set[str]] = {unit_id: set() for unit_id in by_id}
    for graph_name in ("G1", "G2"):
        for relation in graphs[graph_name]:
            predecessors[relation["to"]].add(relation["from"])
    conflicts = {
        frozenset((relation["from"], relation["to"]))
        for graph_name in ("G4", "G5")
        for relation in graphs[graph_name]
    }

    ready = {node["id"] for node in nodes if node["state"] == "READY"}
    completed: set[str] = set()
    waves: list[list[str]] = []
    while ready - completed:
        candidates = sorted(node for node in ready - completed if predecessors[node] <= completed)
        if not candidates:
            remaining = sorted(ready - completed)
            raise ValueError(f"dependency deadlock or cycle among: {remaining}")
        wave: list[str] = []
        for candidate in candidates:
            if all(frozenset((candidate, selected)) not in conflicts for selected in wave):
                wave.append(candidate)
        if not wave:
            raise ValueError("ready-wave compiler made no progress")
        waves.append(wave)
        completed.update(wave)

    convergence_owners = {
        unit_id: unit_id
        for unit_id, count in completion_parent_count.items()
        if count > 1
    }
    output = {
        "schema": "portfolio-multigraph/v1",
        "epoch_digest": snapshot["digest"],
        "nodes": sorted(nodes, key=lambda item: item["id"]),
        "graphs": {name: sorted(values, key=lambda item: (item["from"], item["to"], item["relation"])) for name, values in graphs.items()},
        "ready_waves": waves,
        "convergence_owners": convergence_owners,
    }
    return bind_digest(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--acceptance", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    snapshot = load_json(args.snapshot)
    acceptances = [load_json(path) for path in args.acceptance]
    write_json(args.output, compile_graph(snapshot, acceptances))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
