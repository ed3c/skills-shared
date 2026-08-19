#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception as exc:
    print(json.dumps({"status": "INPUT_ERROR", "exit_code": 64, "errors": [{"code": "JSONSCHEMA_UNAVAILABLE", "subject": "runtime", "message": str(exc)}]}, sort_keys=True))
    raise SystemExit(64)

import check_case_delivery_binding as delivery_gate
import check_trace_graph as projection_gate

EXIT_PASS = 0
EXIT_BLOCK = 2
EXIT_INPUT = 64
LEVEL = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
PROOF_CLASSES = {"VERIFIER", "TEST", "EVIDENCE_RECEIPT", "HUMAN_AUTHORITY"}
DOC_CLASSES = {"NAVIGATION", "PROCEDURE", "PORTABLE_METHOD"}
DOC_TYPES = {"AGENTS", "README", "SKILL"}
RELATION_UTILITY: dict[str, set[str]] = {
    "DERIVED_FROM": {"CAUSAL", "RETRIEVAL"},
    "DECOMPOSES_TO": {"CAUSAL", "IMPLEMENTATION"},
    "PROTECTS_CASE": {"AUTHORITY", "RETRIEVAL"},
    "DOCUMENTS_INVARIANT": {"AUTHORITY", "RETRIEVAL"},
    "TRACKED_BY": {"IMPLEMENTATION"},
    "OWNED_BY": {"AUTHORITY", "IMPLEMENTATION"},
    "REALIZED_BY": {"IMPLEMENTATION"},
    "TOUCHES": {"IMPLEMENTATION"},
    "ROUTED_BY": {"AUTHORITY", "RETRIEVAL"},
    "GOVERNED_BY": {"AUTHORITY"},
    "VERIFIED_BY": {"EVIDENCE"},
    "PRODUCES": {"EVIDENCE", "IMPLEMENTATION"},
    "CONSUMES": {"IMPLEMENTATION"},
    "BLOCKED_BY": {"CAUSAL"},
    "UNBLOCKS": {"CAUSAL"},
    "SIBLING": {"IMPLEMENTATION"},
    "TRUE_CHILD": {"IMPLEMENTATION"},
    "CONVERGENCE": {"IMPLEMENTATION"},
    "PROCESS_DEPENDENCY": {"CAUSAL"},
    "EXTERNAL_EVIDENCE": {"EVIDENCE"},
    "HISTORICAL": {"RETRIEVAL", "EVIDENCE"},
    "SUPERSEDES": {"CAUSAL", "RETRIEVAL"},
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"{path}: {exc}") from None


def schema_errors(value: Any, schema: dict[str, Any], label: str) -> list[dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    out: list[dict[str, str]] = []
    for err in sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(item) for item in err.absolute_path) or "$"
        out.append({"code": "SCHEMA_INVALID", "subject": f"{label}:{path}", "message": err.message})
    return out


def artifact_path(artifact: dict[str, Any]) -> str | None:
    external = artifact.get("external_identity", "")
    if not isinstance(external, str) or not external.startswith("path:"):
        return None
    parts = external.split(":", 2)
    return parts[2] if len(parts) == 3 else None


def nearest_doc(source: dict[str, Any], docs: list[dict[str, Any]]) -> str | None:
    source_path = artifact_path(source)
    if source_path is None:
        return docs[0]["artifact_id"] if len(docs) == 1 else None
    source_parts = Path(source_path).parts[:-1]
    ranked: list[tuple[int, str]] = []
    for doc in docs:
        doc_path = artifact_path(doc)
        if doc_path is None:
            continue
        doc_parent = Path(doc_path).parts[:-1]
        common = 0
        for left, right in zip(source_parts, doc_parent):
            if left != right:
                break
            common += 1
        ranked.append((common, doc["artifact_id"]))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def add_edge(adjacency: dict[str, list[tuple[str, str]]], source: str, target: str, relation: str) -> None:
    adjacency.setdefault(source, []).append((target, relation))


def bfs(adjacency: dict[str, list[tuple[str, str]]], start: str, terminal: str, max_hops: int) -> tuple[list[str], list[str]] | None:
    queue: deque[tuple[str, list[str], list[str]]] = deque([(start, [start], [])])
    seen: dict[str, int] = {start: 0}
    while queue:
        node, path, relations = queue.popleft()
        if node == terminal:
            return path, relations
        if len(relations) >= max_hops:
            continue
        for target, relation in adjacency.get(node, []):
            depth = len(relations) + 1
            if seen.get(target, 10**9) <= depth:
                continue
            seen[target] = depth
            queue.append((target, path + [target], relations + [relation]))
    return None


def check(
    plan: dict[str, Any],
    case_graph: dict[str, Any],
    case_graph_path: Path,
    task: dict[str, Any],
    binding: dict[str, Any],
    trace: dict[str, Any],
    authority: dict[str, Any],
    plan_schema: dict[str, Any],
    case_schema: dict[str, Any],
    expected_sha: str | None,
    reference_dir: Path,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    routes: list[dict[str, Any]] = []

    def fail(code: str, subject: Any, message: str) -> None:
        errors.append({"code": code, "subject": str(subject), "message": message})

    errors.extend(schema_errors(plan, plan_schema, "plan"))
    errors.extend(schema_errors(case_graph, case_schema, "case_graph"))

    if expected_sha and plan.get("subject", {}).get("sha") != expected_sha:
        fail("EXACT_SUBJECT_MISMATCH", "plan.subject.sha", f"expected {expected_sha}")

    for edge in trace.get("edges", []):
        relation = edge.get("relation")
        utility = edge.get("utility")
        if relation == "DEPENDS_ON":
            fail("FALSE_DEPENDS_ON_ANCESTRY", f"{edge.get('from')}->{edge.get('to')}", "generic DEPENDS_ON cannot stand in for Stack relation semantics")
            continue
        allowed = RELATION_UTILITY.get(str(relation))
        if allowed is None:
            fail("UNKNOWN_TRACE_RELATION", relation, "relation is not admitted by traversal contract")
        elif utility not in allowed:
            fail("CONNECTIVITY_INFLATION", f"{edge.get('from')}->{edge.get('to')}", f"{relation} cannot claim utility {utility!r}; allowed={sorted(allowed)}")

    # Reuse the already-frozen #414 and #415 semantic gates instead of creating
    # competing validators for the same subjects.
    projection_report = projection_gate.check(trace, reference_dir, authority, expected_sha)
    if projection_report.get("status") != "PASS":
        for item in projection_report.get("errors", []):
            fail("UPSTREAM_PROJECTION_BLOCK", item.get("subject"), f"{item.get('code')}: {item.get('message')}")

    delivery_schema = read_json(reference_dir / "case-delivery-binding.schema.json")
    delivery_report = delivery_gate.check(binding, task, trace, delivery_schema, expected_sha)
    if delivery_report.get("status") != "PASS":
        for item in delivery_report.get("errors", []):
            fail("UPSTREAM_DELIVERY_BLOCK", item.get("subject"), f"{item.get('code')}: {item.get('message')}")

    sidecar = task.get("case_obligations") if isinstance(task.get("case_obligations"), dict) else {}
    measured_case_sha = sha256_file(case_graph_path)
    if measured_case_sha != sidecar.get("case_graph_sha256"):
        fail("ICPG_FILE_DIGEST_MISMATCH", "case_graph", f"measured {measured_case_sha}, expected {sidecar.get('case_graph_sha256')}")
    intent_projection = {item.get("intent_id"): item for item in trace.get("intents", []) if isinstance(item, dict)}
    artifacts = {item.get("artifact_id"): item for item in trace.get("artifacts", []) if isinstance(item, dict)}
    cases = {item.get("id"): item for item in case_graph.get("cases", []) if isinstance(item, dict)}
    oracles = {item.get("id"): item for item in case_graph.get("oracles", []) if isinstance(item, dict)}
    evidence = {item.get("id"): item for item in case_graph.get("evidence", []) if isinstance(item, dict)}

    required_cases = set(sidecar.get("required_case_ids") or [])
    missing_required = sorted(required_cases - set(cases))
    if missing_required:
        fail("ICPG_CASE_ABSENT", "case_graph", f"required cases absent from canonical ICPG: {missing_required}")

    forward: dict[str, list[tuple[str, str]]] = {}
    reverse: dict[str, list[tuple[str, str]]] = {}

    def edge(source: str, target: str, relation: str) -> None:
        add_edge(forward, source, target, relation)
        add_edge(reverse, target, source, relation)

    # Knowledge Intent projection -> canonical case IDs only. No second case body.
    for intent_id, intent in intent_projection.items():
        inode = f"intent|{intent_id}"
        for case_id in intent.get("icpg", {}).get("case_ids", []) or []:
            if case_id in cases:
                edge(inode, f"case|{case_id}", "ICPG_CASE")

    for case_id, case in cases.items():
        cnode = f"case|{case_id}"
        for invariant_id in case.get("invariant_or_state_refs", []) or []:
            edge(cnode, f"invariant|{invariant_id}", "PROTECTS_INVARIANT")
        for oracle_id in case.get("oracle_ids", []) or []:
            if oracle_id in oracles:
                edge(cnode, f"oracle|{oracle_id}", "HAS_ORACLE")
        for evidence_id in case.get("evidence_ids", []) or []:
            if evidence_id in evidence:
                edge(cnode, f"evidence|{evidence_id}", "HAS_ICPG_EVIDENCE")

    task_node = f"task|{task.get('task_id')}"
    convergence = binding.get("convergence_owner")
    binding_by_case = {item.get("case_id"): item for item in binding.get("case_bindings", []) if isinstance(item, dict)}
    for case_id, item in binding_by_case.items():
        cnode = f"case|{case_id}"
        inode = item.get("issue")
        branch = item.get("branch")
        issue_node = f"issue|{inode}"
        branch_node = f"branch|{branch}"
        edge(cnode, task_node, "OWNED_BY_TASK")
        edge(task_node, issue_node, "TRACKED_BY_ISSUE")
        edge(issue_node, branch_node, "OWNED_BY_BRANCH")
        for artifact_id in item.get("artifact_ids", []) + item.get("document_artifact_ids", []):
            if artifact_id in artifacts:
                edge(branch_node, f"artifact|{artifact_id}", "REALIZED_BY_ARTIFACT")
        case = cases.get(case_id) or {}
        if case.get("classification") == "UNKNOWN_BLOCKING" and convergence:
            edge(branch_node, f"branch|{convergence}", "BLOCKS_CONVERGENCE")
            for intent_id, intent in intent_projection.items():
                if case_id in set(intent.get("icpg", {}).get("case_ids", []) or []):
                    edge(f"branch|{convergence}", f"intent|{intent_id}", "BLOCKS_INTENT")

    stack_by_branch = {node.get("branch"): node for node in binding.get("stack_nodes", []) if isinstance(node, dict)}
    for branch, node in stack_by_branch.items():
        parent = node.get("parent")
        if parent in stack_by_branch:
            edge(f"branch|{parent}", f"branch|{branch}", str(node.get("relation")))

    def trace_node(raw: str) -> str | None:
        if raw in artifacts:
            return f"artifact|{raw}"
        if raw in intent_projection:
            return f"intent|{raw}"
        return None

    for item in trace.get("edges", []):
        source = trace_node(str(item.get("from")))
        target = trace_node(str(item.get("to")))
        if source and target:
            edge(source, target, str(item.get("relation")))

    # Agent context is a retrieval edge derived only from already-bound governed
    # documents. It does not make the document an execution authority.
    for case_id, item in binding_by_case.items():
        docs = [artifacts[artifact_id] for artifact_id in item.get("document_artifact_ids", []) if artifact_id in artifacts]
        if not docs:
            continue
        for artifact_id in item.get("artifact_ids", []):
            source = artifacts.get(artifact_id)
            if not source or source.get("artifact_type") in DOC_TYPES:
                continue
            doc_id = nearest_doc(source, docs)
            if doc_id:
                edge(f"artifact|{artifact_id}", f"artifact|{doc_id}", "CONTEXT_ROUTE")

    authority_entries = authority.get("artifacts", {}) if isinstance(authority.get("artifacts"), dict) else {}
    seen_kinds: set[str] = set()
    for query in plan.get("queries", []):
        query_id = query.get("query_id")
        kind = query.get("kind")
        seen_kinds.add(str(kind))
        adjacency = reverse if kind == "IMPLEMENTATION_TO_WHY" else forward
        result = bfs(adjacency, query["start_node"], query["expected_terminal"], int(query["max_hops"]))
        if result is None:
            code = "REVERSE_TRACE_INCOMPLETE" if kind == "IMPLEMENTATION_TO_WHY" else "TRAVERSAL_INCOMPLETE"
            fail(code, query_id, f"no path {query['start_node']} -> {query['expected_terminal']} within {query['max_hops']} hops")
            continue
        path, relations = result

        terminal_artifact: dict[str, Any] | None = None
        if query["expected_terminal"].startswith("artifact|"):
            terminal_artifact = artifacts.get(query["expected_terminal"].split("|", 1)[1])

        if kind == "WHY_TO_PROOF":
            if terminal_artifact is None or terminal_artifact.get("authority_class") not in PROOF_CLASSES:
                fail("AUTHORITY_INVERSION", query_id, "WHY_TO_PROOF must terminate at verifier/test/receipt/Human authority, not prose/navigation")
                available = 0
            else:
                available = LEVEL[terminal_artifact["evidence_ceiling"]]
        elif kind == "IMPLEMENTATION_TO_WHY":
            start_artifact = artifacts.get(query["start_node"].split("|", 1)[1]) if query["start_node"].startswith("artifact|") else None
            available = LEVEL[start_artifact["evidence_ceiling"]] if start_artifact else 1
        else:
            available = 1

        claimed = LEVEL[query["claimed_evidence_ceiling"]]
        if claimed > available:
            fail("EVIDENCE_LAUNDERING", query_id, f"claimed {query['claimed_evidence_ceiling']} exceeds traversal ceiling L{available}")

        if query.get("decision_use"):
            for node in path:
                if not node.startswith("artifact|"):
                    continue
                artifact_id = node.split("|", 1)[1]
                artifact = artifacts.get(artifact_id)
                if not artifact or not artifact.get("mutable"):
                    continue
                current = authority_entries.get(artifact_id)
                if not isinstance(current, dict):
                    fail("STALE_DECISION_SUBJECT", f"{query_id}:{artifact_id}", "decision path mutable artifact lacks authority refresh")
                    continue
                observed = artifact.get("observed_subject", {})
                if current.get("external_identity") != artifact.get("external_identity") or current.get("sha") != observed.get("sha") or current.get("observed_at") != observed.get("observed_at"):
                    fail("STALE_DECISION_SUBJECT", f"{query_id}:{artifact_id}", "mutable projection differs from refreshed authority subject/time")

        if query.get("decision_use") and terminal_artifact and terminal_artifact.get("authority_class") in DOC_CLASSES:
            fail("AUTHORITY_INVERSION", query_id, "navigation/procedure/method prose cannot be decision authority")

        routes.append({
            "query_id": query_id,
            "kind": kind,
            "path": path,
            "relations": relations,
            "claimed_evidence_ceiling": query["claimed_evidence_ceiling"],
            "available_evidence_ceiling": f"L{available}",
        })

    required_kinds = {"WHY_TO_PROOF", "IMPLEMENTATION_TO_WHY", "GAP_PROPAGATION", "AGENT_CONTEXT_ROUTE"}
    missing_kinds = sorted(required_kinds - seen_kinds)
    if missing_kinds:
        fail("TRAVERSAL_KIND_MISSING", "plan.queries", f"required query kinds absent: {missing_kinds}")

    errors = sorted(errors, key=lambda item: (item["code"], item["subject"], item["message"]))
    return {
        "status": "PASS" if not errors else "BLOCK",
        "exit_code": EXIT_PASS if not errors else EXIT_BLOCK,
        "subject": plan.get("subject"),
        "routes": routes,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate authority-aware multi-hop Intent-to-Evidence traversal.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--case-graph", required=True, type=Path)
    parser.add_argument("--task-contract", required=True, type=Path)
    parser.add_argument("--delivery-binding", required=True, type=Path)
    parser.add_argument("--trace-graph", required=True, type=Path)
    parser.add_argument("--authority-snapshot", required=True, type=Path)
    parser.add_argument("--plan-schema", type=Path)
    parser.add_argument("--case-schema", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)

    script = Path(__file__).resolve()
    skill_root = script.parents[1]
    repo_root = script.parents[3]
    reference_dir = skill_root / "references"
    try:
        plan = read_json(args.plan)
        case_graph = read_json(args.case_graph)
        task = read_json(args.task_contract)
        binding = read_json(args.delivery_binding)
        trace = read_json(args.trace_graph)
        authority = read_json(args.authority_snapshot)
        plan_schema = read_json(args.plan_schema or reference_dir / "traversal-plan.schema.json")
        case_schema = read_json(args.case_schema or repo_root / "skills/spatial-loop-systems-engineering/references/case-graph.schema.json")
        report = check(plan, case_graph, args.case_graph, task, binding, trace, authority, plan_schema, case_schema, args.expected_sha, reference_dir)
    except ValueError as exc:
        report = {"status": "INPUT_ERROR", "exit_code": EXIT_INPUT, "errors": [{"code": "INPUT_JSON_ERROR", "subject": "input", "message": str(exc)}]}

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(rendered + "\n", encoding="utf-8")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
