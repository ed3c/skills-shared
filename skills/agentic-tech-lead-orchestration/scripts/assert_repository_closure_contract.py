#!/usr/bin/env python3
"""Assert the portable Repository Closure Contract and Issue dual-dependency DAG.

Two documents, one gate, because they answer the same question from opposite
ends: the closure contract says what the tree really contains and what evidence
really closed each real problem; the dual DAG says which Issue may *start* and
which Issue may *complete*. Reconciling them separately is how an existing
directory stays `PLANNED`, a Draft PR becomes "admitted", and a source sentence
becomes a runtime `PASS`.

Exit codes: 0 pass, 2 contract failure, 64 input/usage.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "references" / "example-repository-closure-contract.json"
DEFAULT_DAG = ROOT / "references" / "example-issue-dual-dag.json"

SHA40 = set("0123456789abcdef")
LANES = {"CLOUD", "LOCAL", "PRIVATE", "HUMAN", "PROVIDER", "PRODUCTION"}
DOC_STATES = {"PLANNED", "OPEN_DESIGN", "NOT_PLANNED", "IMPLEMENTED_DRAFT", "PARTIAL_CONTRACT", "IMPLEMENTED"}
ABSENT_ONLY_STATES = {"PLANNED", "OPEN_DESIGN", "NOT_PLANNED"}
EXISTING_FORBIDDEN_STATES = {"PLANNED", "NOT_PLANNED"}
CLOSURE_STATES = {
    "IMPLEMENTED_DRAFT",
    "PARTIAL_CONTRACT",
    "SYNTHETIC_CLOSED",
    "INTEGRATION_ADMISSION_OPEN",
    "OPEN_DESIGN",
    "BLOCKED_LIVE_SUBSTRATE",
}
EVIDENCE_KINDS = {
    "SOURCE_REPORTED",
    "PRIMARY_SOURCE_CONFIRMED",
    "SYNTHETIC_ANALOG_ONLY",
    "HUMAN_ADMIT_REQUIRED",
    "DETERMINISTIC_RUN_OBSERVED",
    "LIVE_SUBSTRATE_OBSERVED",
}
# Only an observed execution may carry runtime PASS. A confirmed primary source
# is still documentation, and a fixture is still a fixture.
PASS_ELIGIBLE_KINDS = {"DETERMINISTIC_RUN_OBSERVED", "LIVE_SUBSTRATE_OBSERVED"}
RUNTIME_STATES = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED"}
PR_STATES = {"NOT_CREATED", "DRAFT", "READY", "MERGED"}
UNADMITTABLE_PR_STATES = {"NOT_CREATED", "DRAFT"}
ADMISSION_STATES = {"NOT_ADMITTED", "ADMITTED"}


def load(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return value


def is_sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(ch in SHA40 for ch in text)


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != "agentic-tech-lead/repository-closure-contract/v1":
        errors.append("closure schema_version drifted")

    subject = contract.get("subject", {})
    if not isinstance(subject, dict):
        return errors + ["subject must be an object"]
    if not subject.get("repository"):
        errors.append("subject.repository missing")
    for key in ("commit", "tree"):
        if not is_sha40(subject.get(key)):
            errors.append(f"subject.{key} must be exact SHA-40")

    inventory = contract.get("tree_inventory")
    if not isinstance(inventory, list) or not inventory:
        errors.append("tree_inventory must be a non-empty array")
        inventory = []
    for index, entry in enumerate(inventory):
        if not isinstance(entry, dict):
            errors.append(f"tree_inventory[{index}] must be an object")
            continue
        path = str(entry.get("path"))
        status = entry.get("documented_status")
        exists = entry.get("exists")
        if status not in DOC_STATES:
            errors.append(f"{path}: invalid documented_status")
            continue
        if not isinstance(exists, bool):
            errors.append(f"{path}: exists must be a boolean readback")
            continue
        if exists and status in EXISTING_FORBIDDEN_STATES:
            errors.append(f"{path}: existing path marked {status}")
        if not exists and status not in ABSENT_ONLY_STATES:
            errors.append(f"{path}: absent path marked implemented as {status}")
        if exists and not entry.get("nearest_readme"):
            errors.append(f"{path}: existing path has no nearest README owner")

    matrix = contract.get("closure_matrix")
    if not isinstance(matrix, list) or not matrix:
        return errors + ["closure_matrix must be a non-empty array"]
    seen: set[str] = set()
    for index, row in enumerate(matrix):
        if not isinstance(row, dict):
            errors.append(f"closure_matrix[{index}] must be an object")
            continue
        row_id = str(row.get("id"))
        if row_id in seen:
            errors.append(f"{row_id}: duplicate closure row id")
        seen.add(row_id)
        if not row.get("real_problem"):
            errors.append(f"{row_id}: real_problem missing")
        closure_state = row.get("closure_state")
        if closure_state not in CLOSURE_STATES:
            errors.append(f"{row_id}: invalid closure_state")
        if closure_state == "INTEGRATION_ADMISSION_OPEN" and row.get("human_admit_required") is not True:
            errors.append(f"{row_id}: open integration admission must keep human_admit_required")

        evidence = row.get("evidence", {})
        if not isinstance(evidence, dict):
            errors.append(f"{row_id}: evidence must be an object")
            continue
        kind = evidence.get("kind")
        required_lane = evidence.get("required_lane")
        if kind not in EVIDENCE_KINDS:
            errors.append(f"{row_id}: invalid evidence kind")
        if required_lane not in LANES:
            errors.append(f"{row_id}: invalid required_lane")
        receipt = evidence.get("receipt", {})
        if not isinstance(receipt, dict):
            errors.append(f"{row_id}: evidence receipt missing")
            continue
        receipt_lane = receipt.get("lane")
        runtime_state = receipt.get("runtime_state")
        if runtime_state not in RUNTIME_STATES:
            errors.append(f"{row_id}: invalid runtime_state")
        if runtime_state == "PASS" and kind not in PASS_ELIGIBLE_KINDS:
            errors.append(f"{row_id}: {kind} evidence cannot report runtime PASS")
        if receipt_lane != required_lane:
            errors.append(f"{row_id}: {receipt_lane} receipt cannot satisfy {required_lane} lane")
        if receipt.get("subject_commit") != subject.get("commit"):
            errors.append(f"{row_id}: receipt is not bound to the exact contract subject")
    return errors


def validate_dag(dag: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if dag.get("schema_version") != "agentic-tech-lead/issue-dual-dag/v1":
        errors.append("dual DAG schema_version drifted")

    subject = dag.get("subject", {})
    if not isinstance(subject, dict) or not is_sha40(subject.get("commit")):
        errors.append("subject.commit must be exact SHA-40")
        subject = subject if isinstance(subject, dict) else {}

    nodes = dag.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["nodes must be a non-empty array"]
    by_id: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] must be an object")
            continue
        node_id = str(node.get("id"))
        if node_id in by_id:
            errors.append(f"{node_id}: duplicate node id")
        by_id[node_id] = node

    owner = dag.get("convergence_owner")
    if owner not in by_id:
        errors.append("convergence_owner names an unknown node")

    for node_id, node in by_id.items():
        if node.get("lane") not in LANES:
            errors.append(f"{node_id}: invalid lane")
        pr_state = node.get("pr_state")
        admission_state = node.get("admission_state")
        if pr_state not in PR_STATES:
            errors.append(f"{node_id}: invalid pr_state")
        if admission_state not in ADMISSION_STATES:
            errors.append(f"{node_id}: invalid admission_state")
        if pr_state in UNADMITTABLE_PR_STATES and admission_state == "ADMITTED":
            errors.append(f"{node_id}: {pr_state} publication promoted to ADMITTED")

        start_edges = node.get("start_dependencies")
        completion_edges = node.get("completion_dependencies")
        if not isinstance(start_edges, list) or not isinstance(completion_edges, list):
            errors.append(f"{node_id}: dependency edges must be arrays")
            continue

        for edge in start_edges:
            if not isinstance(edge, dict):
                errors.append(f"{node_id}: start dependency must be an object")
                continue
            ref = str(edge.get("node"))
            if ref not in by_id:
                errors.append(f"{node_id}: unknown start dependency {ref}")
            if edge.get("edge_class") != "START":
                errors.append(f"{node_id}: start dependency {ref} must use START edge class")

        for edge in completion_edges:
            if not isinstance(edge, dict):
                errors.append(f"{node_id}: completion dependency must be an object")
                continue
            ref = str(edge.get("node"))
            if edge.get("edge_class") != "COMPLETION":
                errors.append(f"{node_id}: completion dependency {ref} must use COMPLETION edge class")
            prerequisite = by_id.get(ref)
            if prerequisite is None:
                errors.append(f"{node_id}: unknown completion dependency {ref}")
                continue
            receipt = edge.get("receipt")
            if not isinstance(receipt, dict):
                errors.append(f"{node_id}: completion dependency {ref} has no exact admitted receipt")
                continue
            if receipt.get("subject_commit") != subject.get("commit") or receipt.get("admission_state") != "ADMITTED":
                errors.append(f"{node_id}: completion dependency {ref} has no exact admitted receipt")
            if prerequisite.get("admission_state") != "ADMITTED":
                errors.append(f"{node_id}: completion dependency {ref} is not itself ADMITTED")
            receipt_lane = receipt.get("lane")
            prerequisite_lane = prerequisite.get("lane")
            if receipt_lane != prerequisite_lane:
                errors.append(f"{node_id}: {receipt_lane} receipt cannot satisfy {prerequisite_lane} lane")

        if len(completion_edges) > 1 and node_id != owner:
            errors.append(f"{node_id}: multi-parent convergence is not the declared convergence owner")
    return errors


def selftest(contract: dict[str, Any], dag: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if validate_contract(contract):
        return [f"positive closure contract is already red: {error}" for error in validate_contract(contract)]
    if validate_dag(dag):
        return [f"positive dual DAG is already red: {error}" for error in validate_dag(dag)]

    contract_cases: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("EXISTING_DIRECTORY_MARKED_PLANNED",
         lambda c: c["tree_inventory"][0].__setitem__("documented_status", "PLANNED"),
         "existing path marked PLANNED"),
        ("ABSENT_DIRECTORY_MARKED_IMPLEMENTED",
         lambda c: c["tree_inventory"][2].__setitem__("documented_status", "IMPLEMENTED"),
         "absent path marked implemented"),
        ("SOURCE_REPORTED_PROMOTED_TO_RUNTIME_PASS",
         lambda c: c["closure_matrix"][2]["evidence"]["receipt"].__setitem__("runtime_state", "PASS"),
         "cannot report runtime PASS"),
        ("CLOUD_RECEIPT_USED_FOR_LOCAL_LANE",
         lambda c: c["closure_matrix"][0]["evidence"]["receipt"].__setitem__("lane", "CLOUD"),
         "CLOUD receipt cannot satisfy LOCAL lane"),
        ("LOCAL_RECEIPT_USED_FOR_PROVIDER_OR_PRODUCTION_LANE",
         lambda c: c["closure_matrix"][2]["evidence"]["receipt"].__setitem__("lane", "LOCAL"),
         "LOCAL receipt cannot satisfy PRODUCTION lane"),
        ("STALE_CLOSURE_SUBJECT",
         lambda c: c["closure_matrix"][0]["evidence"]["receipt"].__setitem__("subject_commit", "f" * 40),
         "not bound to the exact contract subject"),
        ("ADMISSION_LAUNDERED_OUT_OF_CLOSURE_ROW",
         lambda c: c["closure_matrix"][1].__setitem__("human_admit_required", False),
         "must keep human_admit_required"),
    ]
    dag_cases: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("DRAFT_PR_PROMOTED_TO_ADMITTED",
         lambda d: d["nodes"][3].__setitem__("admission_state", "ADMITTED"),
         "DRAFT publication promoted to ADMITTED"),
        ("START_DEPENDENCY_USED_AS_COMPLETION_DEPENDENCY",
         lambda d: d["nodes"][3]["completion_dependencies"][0].__setitem__("edge_class", "START"),
         "must use COMPLETION edge class"),
        ("COMPLETION_EDGE_WITHOUT_EXACT_RECEIPT",
         lambda d: d["nodes"][1]["completion_dependencies"][0].__setitem__("receipt", None),
         "has no exact admitted receipt"),
        ("STALE_COMPLETION_RECEIPT_SUBJECT",
         lambda d: d["nodes"][1]["completion_dependencies"][0]["receipt"].__setitem__("subject_commit", "f" * 40),
         "has no exact admitted receipt"),
        ("CLOUD_RECEIPT_USED_FOR_LOCAL_LANE",
         lambda d: d["nodes"][1]["completion_dependencies"][0]["receipt"].__setitem__("lane", "CLOUD"),
         "CLOUD receipt cannot satisfy LOCAL lane"),
        ("LOCAL_RECEIPT_USED_FOR_PROVIDER_OR_PRODUCTION_LANE",
         lambda d: d["nodes"][3]["completion_dependencies"][1]["receipt"].__setitem__("lane", "LOCAL"),
         "LOCAL receipt cannot satisfy CLOUD lane"),
        ("HIDDEN_MULTI_PARENT_CONVERGENCE",
         lambda d: d.__setitem__("convergence_owner", "ISSUE-C"),
         "not the declared convergence owner"),
        ("UNADMITTED_PREREQUISITE_CLOSED_A_COMPLETION_EDGE",
         lambda d: d["nodes"][1].__setitem__("admission_state", "NOT_ADMITTED"),
         "is not itself ADMITTED"),
    ]

    for name, mutate, needle in contract_cases:
        candidate = copy.deepcopy(contract)
        mutate(candidate)
        if not any(needle.lower() in error.lower() for error in validate_contract(candidate)):
            failures.append(f"closure control did not turn red: {name}")
    for name, mutate, needle in dag_cases:
        candidate = copy.deepcopy(dag)
        mutate(candidate)
        if not any(needle.lower() in error.lower() for error in validate_dag(candidate)):
            failures.append(f"dual DAG control did not turn red: {name}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--dag", type=Path, default=DEFAULT_DAG)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    try:
        contract = load(args.contract, "closure contract")
        dag = load(args.dag, "issue dual DAG")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64

    if args.selftest:
        errors = selftest(contract, dag)
    else:
        errors = validate_contract(contract) + validate_dag(dag)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    if args.selftest:
        print("SELFTEST GREEN: repository closure and Issue dual-DAG controls (15 mutations killed)")
    else:
        print(
            "PASS: repository closure contract "
            f"({len(contract['tree_inventory'])} inventory row(s), {len(contract['closure_matrix'])} real problem(s)) "
            f"and Issue dual DAG ({len(dag['nodes'])} node(s), convergence owner={dag['convergence_owner']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
