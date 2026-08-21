#!/usr/bin/env python3
"""Fail-closed semantic verifier for portfolio-multigraph/v1."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from portfolio_control_lib import assert_acyclic, assert_digest, bind_digest, duplicate_values, load_json


def verify(graph: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    if schema is not None:
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(graph), key=lambda item: list(item.absolute_path))
        if errors:
            raise ValueError("shape: " + "; ".join(error.message for error in errors))
    assert_digest(graph, label="portfolio-multigraph")
    node_ids = [node["id"] for node in graph["nodes"]]
    duplicates = duplicate_values(node_ids)
    if duplicates:
        raise ValueError(f"duplicate nodes: {sorted(duplicates)}")
    nodes = set(node_ids)

    seen_edges: set[tuple[str, str, str, str]] = set()
    for graph_name, edges in graph["graphs"].items():
        for edge in edges:
            source, target = edge["from"], edge["to"]
            if source not in nodes or target not in nodes:
                raise ValueError(f"{graph_name}: unknown node in {source}->{target}")
            if source == target:
                raise ValueError(f"{graph_name}: self edge {source}")
            identity = (graph_name, source, target, edge["relation"])
            if identity in seen_edges:
                raise ValueError(f"{graph_name}: duplicate edge {identity}")
            seen_edges.add(identity)
            if graph_name in {"G4", "G5"} and source >= target:
                raise ValueError(f"{graph_name}: conflict edge must use lexical canonical order")
            if graph_name == "G3" and edge["relation"] == "TRUE_CHILD" and not edge["reason"].startswith("TRUE_CHILD:"):
                raise ValueError("G3: TRUE_CHILD lacks named consumed-byte reason")

    for graph_name in ("G1", "G2", "G3"):
        assert_acyclic(nodes, graph["graphs"][graph_name], graph=graph_name)

    conflicts = {
        frozenset((edge["from"], edge["to"]))
        for graph_name in ("G4", "G5")
        for edge in graph["graphs"][graph_name]
    }
    predecessors: dict[str, set[str]] = {node: set() for node in nodes}
    for graph_name in ("G1", "G2"):
        for edge in graph["graphs"][graph_name]:
            predecessors[edge["to"]].add(edge["from"])

    scheduled: set[str] = set()
    for index, wave in enumerate(graph["ready_waves"]):
        wave_set = set(wave)
        if len(wave_set) != len(wave):
            raise ValueError(f"wave {index}: duplicate node")
        if not wave_set <= nodes:
            raise ValueError(f"wave {index}: unknown nodes {sorted(wave_set - nodes)}")
        if wave_set & scheduled:
            raise ValueError(f"wave {index}: node scheduled twice")
        for node in wave:
            if not predecessors[node] <= scheduled:
                raise ValueError(f"wave {index}: {node} scheduled before predecessors {sorted(predecessors[node] - scheduled)}")
        for left in wave:
            for right in wave:
                if left < right and frozenset((left, right)) in conflicts:
                    raise ValueError(f"wave {index}: conflicting nodes {left} and {right}")
        scheduled.update(wave_set)

    ready_nodes = {node["id"] for node in graph["nodes"] if node["state"] == "READY"}
    if scheduled != ready_nodes:
        raise ValueError(f"ready-wave denominator mismatch: missing={sorted(ready_nodes - scheduled)} extra={sorted(scheduled - ready_nodes)}")

    completion_counts: dict[str, int] = {node: 0 for node in nodes}
    for edge in graph["graphs"]["G2"]:
        completion_counts[edge["to"]] += 1
    expected_convergence = {node for node, count in completion_counts.items() if count > 1}
    observed_convergence = set(graph["convergence_owners"])
    if expected_convergence != observed_convergence:
        raise ValueError(f"convergence owner mismatch: expected={sorted(expected_convergence)} observed={sorted(observed_convergence)}")
    for node, owner in graph["convergence_owners"].items():
        if owner not in nodes:
            raise ValueError(f"convergence owner {owner!r} for {node!r} is not a node")


def positive_fixture() -> dict[str, Any]:
    z = "0" * 64
    graph = {
        "schema": "portfolio-multigraph/v1",
        "epoch_digest": "1" * 64,
        "nodes": [
            {"id": "A", "acceptance_digest": "2" * 64, "state": "READY"},
            {"id": "B", "acceptance_digest": "3" * 64, "state": "READY"},
            {"id": "C", "acceptance_digest": "4" * 64, "state": "READY"},
        ],
        "graphs": {
            "G1": [{"from": "A", "to": "C", "relation": "START_DEPENDENCY", "reason": "contract readable", "subject_digest": z}],
            "G2": [{"from": "A", "to": "C", "relation": "COMPLETION_DEPENDENCY", "reason": "contract admitted", "subject_digest": z}],
            "G3": [],
            "G4": [{"from": "A", "to": "B", "relation": "PATH_CONFLICT", "reason": "same path", "subject_digest": z}],
            "G5": [],
            "G6": [],
            "G7": [{"from": "A", "to": "C", "relation": "PUBLICATION_DEPENDENCY", "reason": "land first", "subject_digest": z}],
        },
        "ready_waves": [["A"], ["B", "C"]],
        "convergence_owners": {},
    }
    return bind_digest(graph)


def selftest(schema: dict[str, Any] | None) -> None:
    base = positive_fixture()
    verify(base, schema)
    mutations: list[tuple[str, Any]] = []

    cycle = copy.deepcopy(base)
    cycle["graphs"]["G1"].append({"from": "C", "to": "A", "relation": "START_DEPENDENCY", "reason": "planted cycle", "subject_digest": "0" * 64})
    mutations.append(("CYCLE", bind_digest(cycle)))

    false_parallel = copy.deepcopy(base)
    false_parallel["ready_waves"] = [["A", "B"], ["C"]]
    mutations.append(("OVERLAPPING_WRITERS_FALSELY_PARALLELIZED", bind_digest(false_parallel)))

    dropped = copy.deepcopy(base)
    dropped["ready_waves"] = [["A"], ["C"]]
    mutations.append(("READY_DENOMINATOR_SHRINK", bind_digest(dropped)))

    premature = copy.deepcopy(base)
    premature["ready_waves"] = [["C"], ["A"], ["B"]]
    mutations.append(("COMPLETION_DEPENDENCY_BYPASSED", bind_digest(premature)))

    false_child = copy.deepcopy(base)
    false_child["graphs"]["G3"] = [{"from": "A", "to": "C", "relation": "TRUE_CHILD", "reason": "chronology only", "subject_digest": "0" * 64}]
    mutations.append(("TRUE_CHILD_WITHOUT_CONSUMED_PARENT_BYTES", bind_digest(false_child)))

    hidden_convergence = copy.deepcopy(base)
    hidden_convergence["graphs"]["G2"].append({"from": "B", "to": "C", "relation": "COMPLETION_DEPENDENCY", "reason": "second parent", "subject_digest": "0" * 64})
    mutations.append(("HIDDEN_CONVERGENCE", bind_digest(hidden_convergence)))

    for name, mutation in mutations:
        try:
            verify(mutation, schema)
        except ValueError:
            print(f"REFUSED {name}")
        else:
            raise AssertionError(f"mutation passed: {name}")
    print(f"PORTFOLIO-MULTIGRAPH-GREEN positives=1 mutations={len(mutations)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph")
    parser.add_argument("--schema")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    schema_path = args.schema or str(Path(__file__).resolve().parents[1] / "references/contracts/portfolio-multigraph.schema.json")
    schema = load_json(schema_path)
    if args.selftest:
        selftest(schema)
        return 0
    if not args.graph:
        parser.error("--graph is required without --selftest")
    verify(load_json(args.graph), schema)
    print("PORTFOLIO-MULTIGRAPH-PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
