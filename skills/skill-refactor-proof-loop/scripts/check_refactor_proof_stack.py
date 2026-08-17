#!/usr/bin/env python3
"""Validate a proof-carrying Skill refactor's molecular issue/PR Stack."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
AUTHORITY_FIELDS = {
    "auto_resolve_semantic_conflict",
    "force_push",
    "ship",
    "merge",
    "release",
    "promotion",
}
PR_STATES = {"PR_DRAFT", "PR_OPEN", "READY_FOR_HUMAN_ADMIT", "BLOCKED"}


class StackError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StackError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StackError(f"invalid root {path}: expected object")
    return value


def validate_schema(value: dict[str, Any], schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise StackError("jsonschema Draft 2020-12 validator unavailable") from exc
    try:
        schema = read_json(schema_path)
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise StackError(f"invalid/unreadable schema: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:12]
        )
        raise StackError(f"schema failure: {details}")


def authority_errors(prefix: str, authority: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_FIELDS:
        return [f"AUTHORITY_FIELDS_DRIFT {prefix}"]
    for field in sorted(AUTHORITY_FIELDS):
        if authority.get(field) is not False:
            errors.append(f"AUTHORITY_WIDENING {prefix}:{field}")
    return errors


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes: dict[str, dict[str, Any]] = {}
    issue_owner: dict[int, str] = {}
    pr_owner: dict[int, str] = {}

    for node in value.get("nodes", []):
        if not isinstance(node, dict):
            errors.append("NODE_NOT_OBJECT")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id or node_id in nodes:
            errors.append(f"NODE_ID_INVALID_OR_DUPLICATE {node_id!r}")
            continue
        nodes[node_id] = node
        for issue in node.get("issues", []):
            previous = issue_owner.get(issue)
            if previous is not None:
                errors.append(f"ISSUE_OWNED_BY_MULTIPLE_NODES {issue}:{previous},{node_id}")
            issue_owner[issue] = node_id
        pr = node.get("pull_request")
        if isinstance(pr, int) and not isinstance(pr, bool):
            previous = pr_owner.get(pr)
            if previous is not None:
                errors.append(f"PR_OWNED_BY_MULTIPLE_NODES {pr}:{previous},{node_id}")
            pr_owner[pr] = node_id
        errors.extend(authority_errors(node_id, node.get("authority")))

    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edge_keys: set[tuple[str, str, str]] = set()
    for edge in value.get("edges", []):
        if not isinstance(edge, dict):
            errors.append("EDGE_NOT_OBJECT")
            continue
        source = edge.get("from")
        target = edge.get("to")
        kind = edge.get("type")
        key = (str(source), str(target), str(kind))
        if key in edge_keys:
            errors.append(f"DUPLICATE_EDGE {source}->{target}:{kind}")
        edge_keys.add(key)
        if source not in nodes:
            errors.append(f"EDGE_SOURCE_ABSENT {source}")
        if target not in nodes:
            errors.append(f"EDGE_TARGET_ABSENT {target}")
        if source == target:
            errors.append(f"SELF_EDGE {source}:{kind}")
        if not edge.get("artifacts"):
            errors.append(f"EDGE_ARTIFACTS_ABSENT {source}->{target}:{kind}")
        if source in nodes and target in nodes:
            incoming[target].append(edge)
            outgoing[source].append(edge)
            if kind in {
                "CONSUMES_UNMERGED_BYTES",
                "CONVERGES_VERIFIED_ARTIFACTS",
                "PROCESS_DEPENDENCY",
            }:
                declared = set(nodes[target].get("consumes_artifacts", []))
                missing = sorted(set(edge.get("artifacts", [])) - declared)
                if missing:
                    errors.append(
                        f"EDGE_ARTIFACT_NOT_DECLARED_BY_CONSUMER {source}->{target}:{','.join(missing)}"
                    )

    convergence_nodes = [
        node_id for node_id, node in nodes.items()
        if node.get("stack_class") == "CONVERGENCE"
    ]
    if len(convergence_nodes) != 1:
        errors.append(f"CONVERGENCE_OWNER_COUNT {len(convergence_nodes)}")
    owner = value.get("convergence_owner")
    if owner not in nodes:
        errors.append(f"CONVERGENCE_OWNER_ABSENT {owner}")
    elif nodes[owner].get("stack_class") != "CONVERGENCE":
        errors.append(f"DECLARED_CONVERGENCE_OWNER_WRONG_CLASS {owner}")
    elif convergence_nodes != [owner]:
        errors.append(f"DECLARED_CONVERGENCE_OWNER_MISMATCH {owner}")

    for node_id, node in nodes.items():
        stack_class = node.get("stack_class")
        state = node.get("state")
        pr = node.get("pull_request")
        branch = node.get("branch")
        base_branch = node.get("base_branch")
        head = node.get("head") if isinstance(node.get("head"), dict) else {}
        workflow = node.get("workflow") if isinstance(node.get("workflow"), dict) else {}
        consumes_edges = [
            edge for edge in incoming[node_id]
            if edge.get("type") == "CONSUMES_UNMERGED_BYTES"
        ]

        if stack_class in {"TRUE_CHILD", "CONVERGENCE"}:
            if len(consumes_edges) != 1:
                errors.append(f"CHILD_REQUIRES_EXACTLY_ONE_GIT_PARENT {node_id}:{len(consumes_edges)}")
            else:
                parent = nodes[consumes_edges[0]["from"]]
                if base_branch != parent.get("branch"):
                    errors.append(
                        f"CHILD_BASE_BRANCH_MISMATCH {node_id}:{base_branch}!={parent.get('branch')}"
                    )
        elif consumes_edges:
            errors.append(f"NON_CHILD_CONSUMES_UNMERGED_BYTES {node_id}")

        if stack_class == "ROOT" and incoming[node_id]:
            material = [edge for edge in incoming[node_id] if edge.get("type") != "EXTERNAL_EVIDENCE"]
            if material:
                errors.append(f"ROOT_HAS_MATERIAL_PARENT {node_id}")
        if stack_class == "SIBLING" and consumes_edges:
            errors.append(f"FAKE_SERIAL_SIBLING {node_id}")

        if stack_class == "EXTERNAL_EVIDENCE":
            if node.get("owns_paths"):
                errors.append(f"EXTERNAL_EVIDENCE_OWNS_STACK_PATHS {node_id}")
            if any(item is not None for item in (pr, branch, base_branch)):
                errors.append(f"EXTERNAL_EVIDENCE_HAS_GIT_IDENTITY {node_id}")
            if state != "EXTERNAL_OPEN":
                errors.append(f"EXTERNAL_EVIDENCE_STATE_INVALID {node_id}:{state}")
            for edge in outgoing[node_id]:
                if edge.get("type") != "EXTERNAL_EVIDENCE":
                    errors.append(f"EXTERNAL_EVIDENCE_BECAME_GIT_EDGE {node_id}:{edge.get('type')}")

        if stack_class == "PLANNED_FOLLOWUP":
            if state != "PLANNED" or any(item is not None for item in (pr, branch, base_branch)):
                errors.append(f"PLANNED_FOLLOWUP_PREMATURE_GIT_IDENTITY {node_id}")
            if any(edge.get("type") == "CONSUMES_UNMERGED_BYTES" for edge in incoming[node_id]):
                errors.append(f"PLANNED_FOLLOWUP_FALSE_STACK_CHILD {node_id}")

        if state in PR_STATES:
            if not isinstance(pr, int) or isinstance(pr, bool) or not branch or not base_branch:
                errors.append(f"PR_STATE_MISSING_IDENTITY {node_id}:{state}")
            if head.get("policy") != "READ_FROM_GITHUB_PR_METADATA" or head.get("observed_sha") is not None:
                errors.append(f"OPEN_PR_HEAD_MUST_BE_READ_FROM_GITHUB {node_id}")
        elif state == "BRANCH_CREATED":
            if pr is not None or not branch or not base_branch:
                errors.append(f"BRANCH_CREATED_IDENTITY_INVALID {node_id}")
            if head.get("policy") != "READ_FROM_GITHUB_PR_METADATA" or head.get("observed_sha") is not None:
                errors.append(f"UNPUBLISHED_BRANCH_HEAD_POLICY_INVALID {node_id}")
        elif state == "MERGED":
            observed = head.get("observed_sha")
            if not isinstance(pr, int) or head.get("policy") != "IMMUTABLE_MERGED_COMMIT":
                errors.append(f"MERGED_IDENTITY_INVALID {node_id}")
            if not isinstance(observed, str) or not HEX40.fullmatch(observed):
                errors.append(f"MERGED_HEAD_ABSENT {node_id}")
            if workflow.get("state") != "PASS":
                errors.append(f"MERGED_WITHOUT_PASS_WORKFLOW {node_id}")
            if node.get("terminal_classification") != "MERGED":
                errors.append(f"MERGED_TERMINAL_CLASSIFICATION_INVALID {node_id}")
        elif state in {"PLANNED", "EXTERNAL_OPEN", "CLOSED_NOT_PLANNED"}:
            if head.get("policy") != "NOT_APPLICABLE" or head.get("observed_sha") is not None:
                errors.append(f"NON_GIT_STATE_HEAD_POLICY_INVALID {node_id}:{state}")

    errors.extend(authority_errors("stack", value.get("authority")))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    schema = args.schema or (root / "references/refactor-proof-stack.schema.json")
    try:
        value = read_json(args.stack)
        validate_schema(value, schema)
        errors = validate(value)
    except StackError as exc:
        print(f"REFACTOR-STACK-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    if errors:
        for error in errors:
            print(f"REFACTOR-STACK-RED {error}", file=sys.stderr)
        return 2
    print(
        f"REFACTOR-STACK-GREEN stack={value['stack_id']} nodes={len(value['nodes'])}; "
        "open PR heads remain GitHub metadata"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
