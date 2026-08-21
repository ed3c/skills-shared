#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except Exception as exc:
    print(json.dumps({"status": "INPUT_ERROR", "exit_code": 64, "errors": [{"code": "JSONSCHEMA_UNAVAILABLE", "subject": "runtime", "message": str(exc)}]}, sort_keys=True))
    raise SystemExit(64)

EXIT_PASS = 0
EXIT_BLOCK = 2
EXIT_INPUT = 64
DOC_TYPES = {"AGENTS", "README", "SKILL"}
DOC_RELATIONS = {"PROTECTS_CASE", "DOCUMENTS_INVARIANT", "ROUTED_BY", "GOVERNED_BY"}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def schema_errors(value: Any, schema: dict[str, Any]) -> list[dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    out: list[dict[str, str]] = []
    for err in sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(x) for x in err.absolute_path) or "$"
        out.append({"code": "SCHEMA_INVALID", "subject": path, "message": err.message})
    return out


def norm_path(path: str) -> str:
    return path.rstrip("/").rstrip("*").rstrip("/")


def path_overlaps(left: str, right: str) -> bool:
    a, b = norm_path(left), norm_path(right)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def check(
    binding: dict[str, Any],
    task: dict[str, Any],
    trace: dict[str, Any],
    schema: dict[str, Any],
    expected_sha: str | None,
) -> dict[str, Any]:
    errors = schema_errors(binding, schema)
    if errors:
        return {"status": "BLOCK", "exit_code": EXIT_BLOCK, "errors": errors, "subject": binding.get("subject")}

    def fail(code: str, subject: Any, message: str) -> None:
        errors.append({"code": code, "subject": str(subject), "message": message})

    if expected_sha and binding["subject"]["sha"] != expected_sha:
        fail("EXACT_SUBJECT_MISMATCH", "subject.sha", f"expected {expected_sha}, observed {binding['subject']['sha']}")

    if task.get("schema") != "agentic-tech-lead/task-contract/v1":
        fail("TASK_CONTRACT_INVALID", "task_contract", "unsupported task schema")
        sidecar: dict[str, Any] = {}
    else:
        raw_sidecar = task.get("case_obligations")
        sidecar = raw_sidecar if isinstance(raw_sidecar, dict) else {}
    if not sidecar:
        fail("TASK_CASE_OBLIGATIONS_MISSING", "task_contract.case_obligations", "ICPG case obligations are required")

    expected_task_digest = digest(task)
    declared = binding["task_contract"]
    if declared["contract_digest"] != expected_task_digest:
        fail("TASK_CONTRACT_DIGEST_MISMATCH", "task_contract.contract_digest", f"expected {expected_task_digest}")
    if declared["task_id"] != task.get("task_id"):
        fail("TASK_ID_MISMATCH", "task_contract.task_id", "binding task_id differs from Tech Lead contract")

    if sidecar:
        if declared["case_graph_ref"] != sidecar.get("case_graph_ref"):
            fail("CASE_GRAPH_BINDING_MISMATCH", "task_contract.case_graph_ref", "case graph ref differs from Tech Lead contract")
        if declared["case_graph_sha256"] != sidecar.get("case_graph_sha256"):
            fail("CASE_GRAPH_BINDING_MISMATCH", "task_contract.case_graph_sha256", "case graph digest differs from Tech Lead contract")
        expected_icpg = "sha256:" + str(sidecar.get("case_graph_sha256", ""))
        if binding["intent"]["icpg_graph_digest"] != expected_icpg:
            fail("ICPG_DIGEST_MISMATCH", "intent.icpg_graph_digest", f"expected {expected_icpg}")
        required = list(sidecar.get("required_case_ids") or [])
        if declared["required_case_ids"] != required:
            fail("CASE_DENOMINATOR_MISMATCH", "task_contract.required_case_ids", "binding denominator differs from Tech Lead contract")
    else:
        required = []

    case_bindings = binding["case_bindings"]
    case_ids = [item["case_id"] for item in case_bindings]
    duplicate_cases = sorted({case_id for case_id in case_ids if case_ids.count(case_id) > 1})
    if duplicate_cases:
        fail("DUPLICATE_CASE_OWNER", "case_bindings", f"cases bound more than once: {duplicate_cases}")
    missing_cases = sorted(set(required) - set(case_ids))
    extra_cases = sorted(set(case_ids) - set(required))
    if missing_cases:
        fail("CASE_UNOWNED", "case_bindings", f"required cases missing: {missing_cases}")
    if extra_cases:
        fail("CASE_UNKNOWN_BINDING", "case_bindings", f"bindings outside required denominator: {extra_cases}")

    task_branches = {
        item.get("name"): item
        for item in task.get("branches", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    owner_for_case: dict[str, str | None] = {}
    if sidecar:
        for owner in sidecar.get("branch_case_owners", []) or []:
            if not isinstance(owner, dict):
                continue
            for case_id in owner.get("case_ids", []) or []:
                if case_id in owner_for_case:
                    fail("DUPLICATE_CASE_OWNER", case_id, "Tech Lead case obligations already have multiple branch owners")
                owner_for_case[case_id] = owner.get("branch")

    for item in case_bindings:
        case_id = item["case_id"]
        if item["task_id"] != task.get("task_id"):
            fail("TASK_ID_MISMATCH", case_id, "case binding task_id differs from Tech Lead contract")
        if item["branch"] not in task_branches:
            fail("UNKNOWN_BRANCH_OWNER", case_id, f"branch {item['branch']!r} is not declared")
        elif owner_for_case.get(case_id) != item["branch"]:
            fail("CASE_OWNER_MISMATCH", case_id, f"expected {owner_for_case.get(case_id)!r}, got {item['branch']!r}")
        expected_issue_prefix = f"issue:{binding['subject']['repository']}#"
        if not item["issue"].startswith(expected_issue_prefix):
            fail("ISSUE_IDENTITY_MISMATCH", case_id, "issue identity is outside binding repository")

    stack_nodes = binding["stack_nodes"]
    stack_by_branch: dict[str, dict[str, Any]] = {}
    for node in stack_nodes:
        branch = node["branch"]
        if branch in stack_by_branch:
            fail("DUPLICATE_BRANCH_NODE", branch, "branch appears more than once in Stack projection")
        stack_by_branch[branch] = node
        task_branch = task_branches.get(branch)
        if task_branch is None:
            fail("UNKNOWN_STACK_BRANCH", branch, "Stack branch is not declared in Tech Lead contract")
            continue
        if node["parent"] != task_branch.get("parent"):
            fail("STACK_PARENT_MISMATCH", branch, f"expected parent {task_branch.get('parent')!r}")
        if node["owns_paths"] != task_branch.get("write"):
            fail("PATH_LEASE_MISMATCH", branch, "Stack owns_paths must equal Tech Lead branch write lease")
        issues_for_branch = {item["issue"] for item in case_bindings if item["branch"] == branch}
        if node["issue"] not in issues_for_branch:
            fail("ISSUE_OWNER_MISMATCH", branch, "Stack issue does not own a case on this branch")

    missing_nodes = sorted(set(task_branches) - set(stack_by_branch))
    if missing_nodes:
        fail("STACK_BRANCH_MISSING", "stack_nodes", f"declared branches missing Stack node: {missing_nodes}")

    convergence = binding["convergence_owner"]
    if convergence != sidecar.get("convergence_owner"):
        fail("MISSING_CONVERGENCE_OWNER", "convergence_owner", f"expected {sidecar.get('convergence_owner')!r}")
    convergence_node = stack_by_branch.get(convergence)
    if not convergence_node or convergence_node.get("relation") != "CONVERGENCE":
        fail("MISSING_CONVERGENCE_OWNER", convergence, "convergence owner must have CONVERGENCE Stack relation")

    # True delivery dependency is artifact consumption, never issue order.
    for branch, node in stack_by_branch.items():
        parent = node["parent"]
        relation = node["relation"]
        consumed = set(node["consumed_artifacts"])
        if relation == "TRUE_CHILD" and not consumed:
            fail("FALSE_GIT_ANCESTRY", branch, "TRUE_CHILD requires consumed unmerged artifacts")
        if relation in {"TRUE_CHILD", "CONVERGENCE"} and parent in stack_by_branch:
            provided = set(stack_by_branch[parent]["provided_artifacts"])
            if consumed and not consumed.issubset(provided):
                fail("FALSE_SERIAL_DEPENDENCY", branch, f"consumed artifacts are not provided by parent {parent!r}")
        if relation == "SIBLING" and consumed:
            fail("FALSE_SERIAL_DEPENDENCY", branch, "SIBLING must not consume parent artifacts")

    # Parallel branches must have disjoint path leases. Serial artifact consumers may overlap.
    branches = list(stack_by_branch)
    for index, left in enumerate(branches):
        for right in branches[index + 1:]:
            left_node, right_node = stack_by_branch[left], stack_by_branch[right]
            serial = (
                left_node["parent"] == right and left_node["relation"] in {"TRUE_CHILD", "CONVERGENCE"}
            ) or (
                right_node["parent"] == left and right_node["relation"] in {"TRUE_CHILD", "CONVERGENCE"}
            )
            if serial:
                continue
            for left_path in left_node["owns_paths"]:
                for right_path in right_node["owns_paths"]:
                    if path_overlaps(left_path, right_path):
                        fail("PATH_LEASE_OVERLAP", f"{left}<->{right}", f"{left_path!r} overlaps {right_path!r}")

    intents = {
        item.get("intent_id"): item
        for item in trace.get("intents", [])
        if isinstance(item, dict) and isinstance(item.get("intent_id"), str)
    }
    intent_id = binding["intent"]["intent_id"]
    if intent_id not in intents:
        fail("INTENT_TRACE_MISSING", "intent", "binding intent is absent from Trace Graph")
    else:
        trace_digest = intents[intent_id].get("icpg", {}).get("graph_digest")
        if trace_digest != binding["intent"]["icpg_graph_digest"]:
            fail("ICPG_DIGEST_MISMATCH", "trace.intent", "Trace Graph Intent digest differs from delivery binding")

    artifacts = {
        item.get("artifact_id"): item
        for item in trace.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
    }
    edge_by_source: dict[str, list[dict[str, Any]]] = {}
    for edge in trace.get("edges", []):
        if isinstance(edge, dict):
            edge_by_source.setdefault(str(edge.get("from")), []).append(edge)

    all_bound_artifacts: set[str] = set()
    for item in case_bindings:
        case_id = item["case_id"]
        for artifact_id in item["artifact_ids"] + item["document_artifact_ids"]:
            all_bound_artifacts.add(artifact_id)
            artifact = artifacts.get(artifact_id)
            if not artifact:
                fail("ARTIFACT_PROJECTION_MISSING", f"{case_id}:{artifact_id}", "binding references missing ArtifactProjection")
                continue
            artifact_trace = artifact.get("trace", {})
            if artifact_trace.get("intent_id") != intent_id or case_id not in set(artifact_trace.get("case_ids", []) or []):
                fail("REVERSE_TRACE_INCOMPLETE", f"{case_id}:{artifact_id}", "artifact does not trace to exact Intent + case")
            if artifact_id in item["document_artifact_ids"]:
                if artifact.get("artifact_type") not in DOC_TYPES:
                    fail("DOCUMENT_PROJECTION_INVALID", artifact_id, "document_artifact_ids must reference AGENTS/README/SKILL")
                if not any(edge.get("relation") in DOC_RELATIONS for edge in edge_by_source.get(artifact_id, [])):
                    fail("DOCUMENT_ROUTE_MISSING", artifact_id, "governed document requires PROTECTS_CASE/DOCUMENTS_INVARIANT/ROUTED_BY/GOVERNED_BY edge")

    implementation_types = {"PR", "COMMIT", "FILE", "SCHEMA", "SCRIPT", "TEST", "WORKFLOW", "AGENTS", "README", "SKILL"}
    for artifact_id, artifact in artifacts.items():
        if artifact.get("artifact_type") in implementation_types and artifact_id not in all_bound_artifacts:
            fail("ORPHAN_IMPLEMENTATION", artifact_id, "implementation-oriented projection is not owned by any required case")

    errors = sorted(errors, key=lambda item: (item["code"], item["subject"], item["message"]))
    return {
        "status": "PASS" if not errors else "BLOCK",
        "exit_code": EXIT_PASS if not errors else EXIT_BLOCK,
        "subject": binding.get("subject"),
        "binding_digest": digest(binding),
        "task_contract_digest": expected_task_digest,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ICPG case ownership through Tech Lead and delivery artifacts.")
    parser.add_argument("binding", type=Path)
    parser.add_argument("--task-contract", required=True, type=Path)
    parser.add_argument("--trace-graph", required=True, type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)

    try:
        binding = read_json(args.binding)
        task = read_json(args.task_contract)
        trace = read_json(args.trace_graph)
        schema = read_json(args.schema or Path(__file__).resolve().parents[1] / "references" / "case-delivery-binding.schema.json")
    except ValueError as exc:
        report = {"status": "INPUT_ERROR", "exit_code": EXIT_INPUT, "errors": [{"code": "INPUT_JSON_ERROR", "subject": "input", "message": str(exc)}]}
        print(json.dumps(report, sort_keys=True))
        return EXIT_INPUT

    report = check(binding, task, trace, schema, args.expected_sha)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(rendered + "\n", encoding="utf-8")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
