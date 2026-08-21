#!/usr/bin/env python3
"""Validate G1-G7 graph separation and safe ready waves."""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from repository_portfolio_common import digest_object, leases_overlap, load_json, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts" / "portfolio-multigraph.schema.json"
DEFAULT = SKILL_ROOT / "references" / "repository-portfolio-control" / "examples" / "good-multigraph.json"
DAG_IDS = {"G1", "G2", "G3", "G6", "G7"}
UNDIRECTED_IDS = {"G4", "G5"}


def has_cycle(nodes: set[str], edges: list[dict[str, Any]]) -> bool:
    indegree = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        source, target = edge["source"], edge["target"]
        outgoing[source].append(target)
        indegree[target] += 1
    queue = deque(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in outgoing[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited != len(nodes)


def validate(graph: dict[str, Any]) -> list[str]:
    errors = validate_schema(graph, SCHEMA)
    node_records = graph.get("nodes", [])
    node_ids = [node.get("id") for node in node_records if isinstance(node, dict)]
    if len(node_ids) != len(set(node_ids)):
        errors.append("duplicate node id")
    nodes = {str(node) for node in node_ids}
    node_by_id = {str(node["id"]): node for node in node_records if isinstance(node, dict) and "id" in node}
    graph_records = graph.get("graphs", [])
    graph_ids = [record.get("id") for record in graph_records if isinstance(record, dict)]
    if set(graph_ids) != {"G1","G2","G3","G4","G5","G6","G7"} or len(graph_ids) != 7:
        errors.append("G1-G7 denominator incomplete or duplicated")
    by_id = {record.get("id"): record for record in graph_records if isinstance(record, dict)}
    for gid, record in by_id.items():
        if gid in DAG_IDS and record.get("directed") is not True:
            errors.append(f"{gid} must be directed")
        if gid in UNDIRECTED_IDS and record.get("directed") is not False:
            errors.append(f"{gid} must be undirected")
        seen_undirected: set[tuple[str, str, str]] = set()
        for edge in record.get("edges", []):
            source, target = str(edge.get("source")), str(edge.get("target"))
            if source not in nodes or target not in nodes:
                errors.append(f"{gid}: edge references unknown node")
                continue
            if source == target:
                errors.append(f"{gid}: self edge forbidden")
            if gid == "G3" and edge.get("kind") == "TRUE_CHILD":
                artifact = edge.get("consumed_artifact")
                if not artifact or artifact.get("producer") != source:
                    errors.append("TRUE_CHILD_WITHOUT_CONSUMED_PARENT_BYTES")
            if gid in UNDIRECTED_IDS:
                key = tuple(sorted((source, target))) + (str(edge.get("kind")),)
                if key in seen_undirected:
                    errors.append(f"{gid}: duplicate undirected edge")
                seen_undirected.add(key)
            if gid == "G4" and edge.get("kind") == "PATH_CONFLICT":
                left = node_by_id[source].get("exclusive_paths", [])
                right = node_by_id[target].get("exclusive_paths", [])
                if not any(leases_overlap(a, b) for a in left for b in right):
                    errors.append("PATH_DISJOINT_WORK_FALSELY_SERIALIZED")
        if gid in DAG_IDS and not any("unknown node" in error for error in errors):
            if has_cycle(nodes, record.get("edges", [])):
                errors.append(f"{gid}: cycle detected")

    path_conflict_pairs: set[frozenset[str]] = set()
    resource_conflict_pairs: set[frozenset[str]] = set()
    for gid, target_set in (("G4", path_conflict_pairs), ("G5", resource_conflict_pairs)):
        for edge in by_id.get(gid, {}).get("edges", []):
            target_set.add(frozenset((str(edge.get("source")), str(edge.get("target")))))

    observed_nodes: set[str] = set()
    wave_index: dict[str, int] = {}
    for index, wave in enumerate(graph.get("ready_waves", [])):
        for node in wave:
            node = str(node)
            if node not in nodes:
                errors.append("ready wave references unknown node")
            if node in observed_nodes:
                errors.append("node appears in multiple ready waves")
            observed_nodes.add(node)
            wave_index[node] = index
        for i, left_id in enumerate(wave):
            for right_id in wave[i+1:]:
                left, right = node_by_id[str(left_id)], node_by_id[str(right_id)]
                if any(leases_overlap(a, b) for a in left.get("exclusive_paths", []) for b in right.get("exclusive_paths", [])):
                    errors.append("OVERLAPPING_WRITERS_FALSELY_PARALLELIZED")
                if set(left.get("exclusive_resources", [])) & set(right.get("exclusive_resources", [])):
                    errors.append("RESOURCE_CONFLICT_FALSELY_PARALLELIZED")
                pair = frozenset((str(left_id), str(right_id)))
                if pair in path_conflict_pairs or pair in resource_conflict_pairs:
                    errors.append("CONFLICT_EDGE_PRESENT_IN_READY_WAVE")
    for gid in ("G1", "G2", "G3"):
        for edge in by_id.get(gid, {}).get("edges", []):
            source, target = str(edge["source"]), str(edge["target"])
            if source in wave_index and target in wave_index and wave_index[source] >= wave_index[target]:
                errors.append(f"{gid}: dependency not ordered before dependent")
    if digest_object(graph, "digest") != graph.get("digest"):
        errors.append("multigraph digest drifted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        graph = load_json(args.graph)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = validate(graph)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(f"PASS: G1-G7 multigraph ({len(graph['nodes'])} node(s), {len(graph['ready_waves'])} wave(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
