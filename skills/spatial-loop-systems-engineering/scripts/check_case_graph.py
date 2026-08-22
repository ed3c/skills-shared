#!/usr/bin/env python3
"""Validate spatial-loop-case-graph/v1 semantic closure.

Exit 0: admitted for declared exact subject
Exit 2: checked semantic/traceability violation
Exit 64: missing, malformed or unusable input
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "spatial-loop-case-graph/v1"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DECISION_REQUIRED = {"INTENTIONAL_CHANGE", "DEFER_EXPLICIT", "DROP_EXPLICIT"}
PRESERVATION_DISPOSITIONS = {"PRESERVE_EXACT", "PRESERVE_OBSERVABLE", "ADAPT_WITH_COMPATIBILITY"}
CASE_CLASSES = {
    "REQUIRED_CASE", "INVALID_INPUT_CASE", "IMPOSSIBLE_BY_INVARIANT",
    "OUT_OF_SCOPE_EXPLICIT", "DUPLICATE_EQUIVALENCE_CLASS", "UNKNOWN_BLOCKING",
}
EVIDENCE_STATES = {
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
    "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED",
}
GATES = {"BLOCKED", "READY_FOR_PROTOTYPE", "READY_FOR_IMPLEMENTATION", "READY_FOR_PUBLICATION_REVIEW"}


def fail(msg: str) -> None:
    print(f"CASE-GRAPH-RED {msg}", file=sys.stderr)


def as_list(value: Any, label: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    return value


def index_nodes(values: list[Any], label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i, raw in enumerate(values):
        if not isinstance(raw, dict):
            errors.append(f"{label}[{i}] must be an object")
            continue
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not node_id.strip():
            errors.append(f"{label}[{i}].id must be non-empty")
            continue
        if node_id in out:
            errors.append(f"duplicate id {node_id} within {label}")
        else:
            out[node_id] = raw
    return out


def reject_cross_category_ids(
    categories: list[tuple[str, dict[str, dict[str, Any]]]], errors: list[str]
) -> None:
    owner: dict[str, str] = {}
    for category, nodes in categories:
        for node_id in nodes:
            prior = owner.get(node_id)
            if prior is not None and prior != category:
                errors.append(f"duplicate id {node_id} across {prior} and {category}")
            else:
                owner[node_id] = category


def ratio(num: int, den: int) -> float:
    return 1.0 if den == 0 else num / den


def close_enough(a: Any, b: float) -> bool:
    return isinstance(a, (int, float)) and not isinstance(a, bool) and abs(float(a) - b) <= 1e-9


def detect_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    indegree: dict[str, int] = {n: 0 for n in nodes}
    for src, dst in edges:
        if src in nodes and dst in nodes:
            adj[src].append(dst)
            indegree[dst] += 1
    queue = [n for n, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for nxt in adj[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return visited != len(nodes)


def validate(doc: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["top level must be an object"]
    if doc.get("schema") != SCHEMA:
        errors.append(f"schema must equal {SCHEMA}")

    subject = doc.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
        subject = {}
    for field in ("id", "revision", "digest"):
        if not isinstance(subject.get(field), str) or not subject.get(field):
            errors.append(f"subject.{field} must be non-empty")
    revision = subject.get("revision")
    digest = subject.get("digest")
    if isinstance(digest, str) and digest and not DIGEST_RE.fullmatch(digest):
        errors.append("subject.digest must be sha256:<64 lowercase hex>")

    intents = index_nodes(as_list(doc.get("intent_atoms"), "intent_atoms", errors), "intent_atoms", errors)
    axes = index_nodes(as_list(doc.get("semantic_axes"), "semantic_axes", errors), "semantic_axes", errors)
    behaviors = index_nodes(as_list(doc.get("source_behaviors"), "source_behaviors", errors), "source_behaviors", errors)
    cases = index_nodes(as_list(doc.get("cases"), "cases", errors), "cases", errors)
    impls = index_nodes(as_list(doc.get("implementations"), "implementations", errors), "implementations", errors)
    oracles = index_nodes(as_list(doc.get("oracles"), "oracles", errors), "oracles", errors)
    evidence = index_nodes(as_list(doc.get("evidence"), "evidence", errors), "evidence", errors)
    decisions = index_nodes(as_list(doc.get("decisions", []), "decisions", errors), "decisions", errors)

    reject_cross_category_ids(
        [
            ("intent_atoms", intents), ("semantic_axes", axes),
            ("source_behaviors", behaviors), ("cases", cases),
            ("implementations", impls), ("oracles", oracles),
            ("evidence", evidence), ("decisions", decisions),
        ],
        errors,
    )

    if not intents:
        errors.append("intent_atoms must be non-empty")
    if not axes:
        errors.append("semantic_axes must be non-empty")
    if not cases:
        errors.append("cases must be non-empty")

    for axis_id, axis in axes.items():
        state = axis.get("state")
        if state not in {"APPLICABLE", "NOT_APPLICABLE"}:
            errors.append(f"semantic axis {axis_id} has invalid state")
        if state == "NOT_APPLICABLE" and not str(axis.get("reason", "")).strip():
            errors.append(f"semantic axis {axis_id} NOT_APPLICABLE requires reason")

    for decision_id, decision in decisions.items():
        if not str(decision.get("authority", "")).strip():
            errors.append(f"decision {decision_id} requires authority")
        if not str(decision.get("rationale", "")).strip():
            errors.append(f"decision {decision_id} requires rationale")

    behavior_dispositions: dict[str, str] = {}
    blocking_behavior_count = 0
    allowed_dispositions = PRESERVATION_DISPOSITIONS | DECISION_REQUIRED | {"UNKNOWN_BLOCKING"}
    for behavior_id, behavior in behaviors.items():
        disposition = behavior.get("disposition")
        if disposition not in allowed_dispositions:
            errors.append(f"source behavior {behavior_id} has invalid/unmapped disposition")
            continue
        behavior_dispositions[behavior_id] = disposition
        if disposition == "UNKNOWN_BLOCKING":
            blocking_behavior_count += 1
        if disposition in DECISION_REQUIRED:
            decision_id = behavior.get("decision_id")
            if not isinstance(decision_id, str) or decision_id not in decisions:
                errors.append(f"source behavior {behavior_id} disposition {disposition} requires decision_id")

    required_cases = [c for c in cases.values() if c.get("classification") == "REQUIRED_CASE"]
    blocking_cases = [c for c in cases.values() if c.get("classification") == "UNKNOWN_BLOCKING"]
    case_impl_closed = 0
    case_oracle_closed = 0
    required_case_closed = 0
    executed_evidence_closed = 0
    required_pass_closed = 0
    intent_covered: set[str] = set()

    for case_id, case in cases.items():
        classification = case.get("classification")
        if classification not in CASE_CLASSES:
            errors.append(f"case {case_id} has invalid classification")
            continue
        intent_ids = as_list(case.get("intent_ids"), f"case {case_id}.intent_ids", errors)
        axis_ids = as_list(case.get("axis_ids"), f"case {case_id}.axis_ids", errors)
        inv_refs = as_list(case.get("invariant_or_state_refs"), f"case {case_id}.invariant_or_state_refs", errors)
        impl_ids = as_list(case.get("implementation_ids"), f"case {case_id}.implementation_ids", errors)
        oracle_ids = as_list(case.get("oracle_ids"), f"case {case_id}.oracle_ids", errors)
        evidence_ids = as_list(case.get("evidence_ids"), f"case {case_id}.evidence_ids", errors)

        for ref in intent_ids:
            if ref not in intents:
                errors.append(f"case {case_id} references unknown intent {ref}")
            else:
                intent_covered.add(ref)
        for ref in axis_ids:
            if ref not in axes:
                errors.append(f"case {case_id} references unknown semantic axis {ref}")
        for ref in impl_ids:
            if ref not in impls:
                errors.append(f"case {case_id} references unknown implementation {ref}")
        for ref in oracle_ids:
            if ref not in oracles:
                errors.append(f"case {case_id} references unknown oracle {ref}")

        referenced_evidence_states: list[str] = []
        for ref in evidence_ids:
            if ref not in evidence:
                errors.append(f"case {case_id} references unknown evidence {ref}")
            else:
                referenced_evidence_states.append(str(evidence[ref].get("state")))

        state = case.get("evidence_state")
        if state not in EVIDENCE_STATES:
            errors.append(f"case {case_id} has invalid evidence_state")
        if evidence_ids:
            if state in {"PASS", "FAIL"} and state not in referenced_evidence_states:
                errors.append(f"case {case_id} evidence_state {state} is not backed by referenced evidence")
        elif state in {"PASS", "FAIL"}:
            errors.append(f"case {case_id} {state} requires evidence_ids")

        if classification == "REQUIRED_CASE":
            if not intent_ids:
                errors.append(f"required case {case_id} requires intent_ids")
            if not axis_ids:
                errors.append(f"required case {case_id} requires axis_ids")
            if not inv_refs:
                errors.append(f"required case {case_id} requires invariant_or_state_refs")
            if not impl_ids:
                errors.append(f"required case {case_id} requires implementation_ids")
            else:
                case_impl_closed += 1
            if not oracle_ids:
                errors.append(f"required case {case_id} requires oracle_ids")
            else:
                case_oracle_closed += 1
            if intent_ids and axis_ids and inv_refs and impl_ids and oracle_ids:
                required_case_closed += 1
            if evidence_ids and state in {"PASS", "FAIL"} and state in referenced_evidence_states:
                executed_evidence_closed += 1
            if evidence_ids and state == "PASS" and "PASS" in referenced_evidence_states:
                required_pass_closed += 1

        if classification == "OUT_OF_SCOPE_EXPLICIT":
            decision_id = case.get("decision_id")
            if not isinstance(decision_id, str) or decision_id not in decisions:
                errors.append(f"out-of-scope case {case_id} requires decision_id")

    for impl_id, impl in impls.items():
        if not str(impl.get("owner", "")).strip():
            errors.append(f"implementation {impl_id} requires owner")
        if not str(impl.get("subject_ref", "")).strip():
            errors.append(f"implementation {impl_id} requires subject_ref")
        if impl.get("subject_revision") != revision:
            errors.append(f"implementation {impl_id} subject_revision must equal exact subject revision")
        if impl.get("subject_digest") != digest:
            errors.append(f"implementation {impl_id} subject_digest must equal exact subject digest")

    for oracle_id, oracle in oracles.items():
        if not str(oracle.get("procedure", "")).strip():
            errors.append(f"oracle {oracle_id} requires procedure")
        if not str(oracle.get("pass_condition", "")).strip():
            errors.append(f"oracle {oracle_id} requires pass_condition")

    for evidence_id, item in evidence.items():
        if item.get("state") not in EVIDENCE_STATES:
            errors.append(f"evidence {evidence_id} has invalid state")
        if not str(item.get("subject_ref", "")).strip():
            errors.append(f"evidence {evidence_id} requires subject_ref")
        if item.get("subject_revision") != revision:
            errors.append(f"evidence {evidence_id} subject_revision must equal exact subject revision")
        if item.get("subject_digest") != digest:
            errors.append(f"evidence {evidence_id} subject_digest must equal exact subject digest")

    all_ids = set(intents) | set(axes) | set(behaviors) | set(cases) | set(impls) | set(oracles) | set(evidence) | set(decisions)
    graph_edges: list[tuple[str, str]] = []
    outgoing: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in all_ids}
    for i, edge in enumerate(as_list(doc.get("edges"), "edges", errors)):
        if not isinstance(edge, dict):
            errors.append(f"edges[{i}] must be an object")
            continue
        src, dst, kind = edge.get("from"), edge.get("to"), edge.get("kind")
        if src not in all_ids:
            errors.append(f"edge {i} references unknown source {src}")
        if dst not in all_ids:
            errors.append(f"edge {i} references unknown target {dst}")
        if not isinstance(kind, str) or not kind.strip():
            errors.append(f"edge {i} requires kind")
        if src in all_ids and dst in all_ids:
            graph_edges.append((src, dst))
            outgoing[src].append((dst, str(kind)))
    if detect_cycle(all_ids, graph_edges):
        errors.append("provenance graph contains a cycle")

    behavior_closed = 0
    for behavior_id, disposition in behavior_dispositions.items():
        links = outgoing.get(behavior_id, [])
        case_links = [dst for dst, _ in links if dst in cases]
        decision_id = behaviors[behavior_id].get("decision_id")
        if disposition in PRESERVATION_DISPOSITIONS:
            if not case_links:
                errors.append(f"source behavior {behavior_id} disposition {disposition} requires a case edge")
            else:
                behavior_closed += 1
        elif disposition in DECISION_REQUIRED:
            if isinstance(decision_id, str) and decision_id in decisions:
                behavior_closed += 1
        elif disposition == "UNKNOWN_BLOCKING":
            behavior_closed += 1

    computed = {
        "intent": ratio(len(intent_covered), len(intents)),
        "source_behavior_disposition": ratio(behavior_closed, len(behaviors)),
        "required_case": ratio(required_case_closed, len(required_cases)),
        "implementation_binding": ratio(case_impl_closed, len(required_cases)),
        "oracle": ratio(case_oracle_closed, len(required_cases)),
        "executed_evidence": ratio(executed_evidence_closed, len(required_cases)),
        "unknown_blocking_count": len(blocking_cases) + blocking_behavior_count,
    }
    coverage = doc.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage must be an object")
        coverage = {}
    for field, expected in computed.items():
        actual = coverage.get(field)
        if field == "unknown_blocking_count":
            if actual != expected:
                errors.append(f"coverage.{field} must be recomputed as {expected}, found {actual}")
        elif not close_enough(actual, float(expected)):
            errors.append(f"coverage.{field} must be recomputed as {expected:.6f}, found {actual}")

    gate = doc.get("gate")
    if not isinstance(gate, dict):
        errors.append("gate must be an object")
        gate = {}
    status = gate.get("status")
    if status not in GATES:
        errors.append("gate.status is invalid")
    if not str(gate.get("rationale", "")).strip():
        errors.append("gate.rationale must be non-empty")
    if computed["unknown_blocking_count"] > 0 and status != "BLOCKED":
        errors.append("unknown blocking cases/behaviors require gate BLOCKED")
    if status in {"READY_FOR_IMPLEMENTATION", "READY_FOR_PUBLICATION_REVIEW"}:
        if not required_cases:
            errors.append(f"gate {status} requires a non-empty REQUIRED_CASE denominator; empty denominators make every ratio vacuously 1.0")
        for key in ("intent", "source_behavior_disposition", "required_case", "implementation_binding", "oracle"):
            if computed[key] != 1.0:
                errors.append(f"gate {status} requires coverage.{key}=1.0")
    if status == "READY_FOR_PUBLICATION_REVIEW":
        if computed["executed_evidence"] != 1.0:
            errors.append("READY_FOR_PUBLICATION_REVIEW requires executed_evidence=1.0")
        if required_pass_closed != len(required_cases):
            errors.append("READY_FOR_PUBLICATION_REVIEW requires every required case to have subject-bound PASS evidence")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "check":
        print("usage: check_case_graph.py check <case-graph.json>", file=sys.stderr)
        return 64
    path = Path(argv[2])
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"CASE-GRAPH-UNUSABLE {exc}", file=sys.stderr)
        return 64
    errors = validate(doc)
    if errors:
        for error in errors:
            fail(error)
        return 2
    print("CASE-GRAPH-GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
