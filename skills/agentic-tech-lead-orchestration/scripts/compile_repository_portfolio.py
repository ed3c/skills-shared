#!/usr/bin/env python3
"""Compile exact snapshot and acceptance packets into the seven-graph portfolio model.

Salvaged from PR#562 (caedeb9). Field access adapted to the merged
`issue-pr-acceptance/v1` shape (#566 mandatory fix 4: `runtime_requirements`
instead of PR#562's `prerequisites`, `leases.exclusive_paths` instead of
`leases.exclusive`, typed dependency edges instead of PR#564's bare strings).
"""

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
        blocked = any(item["state"] != "PASS" for item in packet["runtime_requirements"])
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
                for left_path in left["leases"]["exclusive_paths"]
                for right_path in right["leases"]["exclusive_paths"]
                if path_prefixes_overlap(left_path, right_path)
            }
        )
        if overlaps:
            reason = "exclusive writer overlap: " + "; ".join(overlaps)
            graphs["G4"].append(edge(left_id, right_id, "PATH_CONFLICT", reason, pair_digest(left_id, right_id, reason)))

        left_resources = {
            item["capability"] for item in left["runtime_requirements"] if item["capability"].startswith("exclusive-resource:")
        }
        right_resources = {
            item["capability"] for item in right["runtime_requirements"] if item["capability"].startswith("exclusive-resource:")
        }
        for resource in sorted(left_resources & right_resources):
            reason = f"exclusive runtime resource: {resource}"
            graphs["G5"].append(edge(left_id, right_id, "RESOURCE_CONFLICT", reason, pair_digest(left_id, right_id, reason)))

    # #566 mandatory fix 2: only start_dependencies (G1) gate DISPATCH/wave
    # placement. completion_dependencies (G2) gate the node's own COMPLETION
    # edge only -- already recorded above as a G7 PUBLICATION_DEPENDENCY edge,
    # which nothing in this wave loop consults. Merging G1+G2 into one
    # predecessor set (the pre-#566 shape) is the
    # START_DEPENDENCY_PROMOTED_TO_COMPLETION defect: it wrongly delays a
    # node's DISPATCH until a completion-only parent's wave has fully
    # finished, when the node only ever declared a start dependency (or none)
    # on that parent.
    predecessors: dict[str, set[str]] = {unit_id: set() for unit_id in by_id}
    for relation in graphs["G1"]:
        predecessors[relation["to"]].add(relation["from"])
    conflicts = {
        frozenset((relation["from"], relation["to"]))
        for graph_name in ("G4", "G5")
        for relation in graphs[graph_name]
    }

    ready = {node["id"] for node in nodes if node["state"] == "READY"}
    blocked_ids = {node["id"] for node in nodes if node["state"] != "READY"}
    completed: set[str] = set()
    waves: list[list[str]] = []
    while ready - completed:
        candidates = sorted(node for node in ready - completed if predecessors[node] <= completed)
        if not candidates:
            remaining = sorted(ready - completed)
            # #566 mandatory fix 3: a remaining node blocked only because one
            # of its G1 predecessors is itself BLOCKED_BY_RUNTIME (never
            # enters `ready`, so never enters `completed`) is not a deadlock
            # or cycle -- fail closed with the correct label instead of the
            # pre-#566 generic "deadlock or cycle" message.
            stuck = {node: sorted(predecessors[node] & blocked_ids) for node in remaining if predecessors[node] & blocked_ids}
            if stuck:
                raise ValueError(f"BLOCKED_PREDECESSOR: {stuck}")
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
    # #566 mandatory fix 6: embed the exact ghpc epoch subject this compile
    # ran against so ghpc's own checkers (ghpc/portfolio-epoch/v1's
    # subject.main_commit / subject.tree) and these checkers reconcile on one
    # picture instead of two independently-read snapshots.
    epoch_subject = {
        "main_commit": snapshot["repositories"][0]["main_commit"],
        "tree": snapshot["repositories"][0]["main_tree"],
    }
    output = {
        "schema": "portfolio-multigraph/v1",
        "epoch_digest": snapshot["digest"],
        "epoch_subject": epoch_subject,
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
