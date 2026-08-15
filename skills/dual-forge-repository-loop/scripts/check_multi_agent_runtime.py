#!/usr/bin/env python3
"""Validate repository-multi-agent-runtime/v1 contracts.

Exit codes:
  0   schema and semantic closure pass for the exact submitted subject
  2   structurally valid contract violates a runtime invariant
  64  missing, unreadable, malformed, or schema-invalid input
  70  required validator dependency is unavailable

This checker validates static contracts and content-bound worker receipts. It does
not prove that a live model, worktree, forge, Git Town process, CI runner, or merge
actually executed. Provider and host claims remain separate evidence lanes.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "RUNTIME-CONTRACT-RED validator-unavailable: jsonschema is required; "
        "the checker refuses to skip schema validation",
        file=sys.stderr,
    )
    raise SystemExit(70)

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2

VERIFIED_TASK_STATES = {"RESULT_VERIFIED", "INTEGRATED"}
VERIFIED_RESULT_STATES = {"RESULT_VERIFIED", "INTEGRATED"}
POST_PUBLICATION_STATES = {
    "COMMITTED",
    "PUSHED",
    "PR_OPEN",
    "AUTO_MERGE_ELIGIBLE",
    "MERGED",
}
TERMINAL_TASK_STATES = {
    "INTEGRATED",
    "REJECTED_NOT_DECOMPOSABLE",
    "DUPLICATE_SUPPRESSED",
    "STALE_ATTEMPT",
    "LEASE_EXPIRED",
    "TIMED_OUT",
    "CANCELLED",
    "STRAGGLER_DETACHED",
    "FAILED_TERMINAL",
    "BLOCKED_AUTHORITY",
    "BLOCKED_CONFLICT",
    "SUPERSEDED",
}
BUDGET_KEYS = (
    "active_workers",
    "total_workers",
    "spawn_depth",
    "tool_calls",
    "tokens",
    "wall_clock_seconds",
    "ci_runs",
    "pr_count",
)
RESULT_BUDGET_KEYS = ("tool_calls", "tokens", "wall_clock_seconds")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"RUNTIME-CONTRACT-INVALID absent-input: {path}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"RUNTIME-CONTRACT-INVALID unreadable-input: {path}: {exc}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)


def format_schema_error(prefix: str, error: Any) -> str:
    location = "/".join(str(part) for part in error.absolute_path) or "$"
    return f"{prefix} schema-invalid at {location}: {error.message}"


def validate_schema(document: Any, schema: Any, prefix: str) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        format_schema_error(prefix, error)
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]


def normalize_path(path: str) -> str:
    return path.rstrip("/") or "."


def paths_overlap(left: str, right: str) -> bool:
    a = normalize_path(left)
    b = normalize_path(right)
    return a == b or a.startswith(f"{b}/") or b.startswith(f"{a}/")


def any_overlap(left: Iterable[str], right: Iterable[str]) -> tuple[str, str] | None:
    for a in left:
        for b in right:
            if paths_overlap(a, b):
                return a, b
    return None


def graph_cycle(tasks: list[dict[str, Any]]) -> list[str] | None:
    ids = {task["task_id"] for task in tasks}
    indegree = {task_id: 0 for task_id in ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        child = task["task_id"]
        for parent in task["dependencies"]:
            if parent in ids:
                outgoing[parent].append(child)
                indegree[child] += 1
    queue = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    visited: list[str] = []
    while queue:
        current = queue.popleft()
        visited.append(current)
        for child in outgoing[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) == len(ids):
        return None
    return sorted(task_id for task_id, degree in indegree.items() if degree > 0)


def semantic_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    repository = contract["repository"]
    runtime = contract["runtime"]
    topology = contract["topology"]
    shadow = contract["shadow"]
    budget = contract["budget"]
    admission = contract["admission"]
    tasks: list[dict[str, Any]] = contract["tasks"]
    results: list[dict[str, Any]] = contract["results"]
    merge_boundary = contract["merge_boundary"]
    states = contract["states"]

    if repository["base_sha"] not in repository["admitted_subjects"]:
        errors.append("subject-base-not-admitted: repository.base_sha is absent from admitted_subjects")
    if repository["current_sha"] not in repository["admitted_subjects"]:
        errors.append("subject-current-not-admitted: repository.current_sha is absent from admitted_subjects")

    if runtime["identity"] == "UNKNOWN" and states["delivery_state"] in POST_PUBLICATION_STATES:
        errors.append("unknown-runtime-published: UNKNOWN runtime cannot reach commit/publication states")

    if budget["profile_state"] == "ABSENT":
        if topology != "SINGLE_BUILDER":
            errors.append("missing-profile-fanout: absent budget profile requires SINGLE_BUILDER")
        if budget["limits"]["active_workers"] != 1:
            errors.append("missing-profile-active-limit: absent profile requires active_workers limit = 1")
        if budget["limits"]["total_workers"] != 1:
            errors.append("missing-profile-total-limit: absent profile requires total_workers limit = 1")

    for key in BUDGET_KEYS:
        if budget["consumed"][key] > budget["limits"][key]:
            errors.append(
                f"budget-exceeded:{key}: consumed={budget['consumed'][key]} limit={budget['limits'][key]}"
            )

    if topology == "MULTI_WORKER":
        failed_admission = sorted(key for key, value in admission.items() if value is not True)
        if failed_admission:
            errors.append(f"parallelism-not-admitted: false={','.join(failed_admission)}")
        if len(tasks) < 2:
            errors.append("multi-worker-cardinality: MULTI_WORKER requires at least two task packets")
    elif topology == "SINGLE_BUILDER" and len(tasks) != 1:
        errors.append("single-builder-cardinality: SINGLE_BUILDER requires exactly one task packet")

    if shadow["execution"] == "IN_PROCESS_LOGICAL" and shadow["independent_state"] != "NOT_EXERCISED":
        errors.append("shadow-independence-overclaim: in-process logical Shadow is NOT_EXERCISED for independence")
    if shadow["checkpoint_outcome"] == "BLOCKED_AT_MATERIAL_BOUNDARY_L3":
        if shadow["enforcement_state"] != "PASS":
            errors.append("shadow-l3-unenforced: L3 requires PASS enforcement state")
        if states["delivery_state"] != "BLOCKED":
            errors.append("shadow-l3-bypassed: L3 outcome requires BLOCKED delivery state")

    task_ids = [task["task_id"] for task in tasks]
    attempt_ids = [task["attempt_id"] for task in tasks]
    branches = [task["branch"] for task in tasks]
    worktrees = [task["worktree_identity"] for task in tasks]
    for label, values in (
        ("task-id", task_ids),
        ("attempt-id", attempt_ids),
        ("branch", branches),
        ("worktree", worktrees),
    ):
        duplicates = sorted(value for value in set(values) if values.count(value) > 1)
        if duplicates:
            errors.append(f"duplicate-{label}: {','.join(duplicates)}")

    known_tasks = set(task_ids)
    for task in tasks:
        if task["base_subject_sha"] not in repository["admitted_subjects"]:
            errors.append(f"task-base-not-admitted:{task['task_id']}: {task['base_subject_sha']}")
        if task["task_id"] in task["dependencies"]:
            errors.append(f"self-dependency:{task['task_id']}")
        unknown = sorted(set(task["dependencies"]) - known_tasks)
        if unknown:
            errors.append(f"unknown-dependency:{task['task_id']}: {','.join(unknown)}")
        overlap = any_overlap(task["allowed_paths"], task["excluded_paths"])
        if overlap:
            errors.append(
                f"self-path-contradiction:{task['task_id']}: allowed={overlap[0]} excluded={overlap[1]}"
            )
        if task["state"] not in TERMINAL_TASK_STATES and task["lease"]["status"] != "ACTIVE":
            errors.append(
                f"active-task-without-active-lease:{task['task_id']}: state={task['state']} lease={task['lease']['status']}"
            )
        if task["state"] in TERMINAL_TASK_STATES and task["lease"]["status"] == "ACTIVE":
            errors.append(f"terminal-task-retains-lease:{task['task_id']}")

    cycle = graph_cycle(tasks)
    if cycle:
        errors.append(f"dependency-cycle: {','.join(cycle)}")

    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            path_overlap = any_overlap(left["allowed_paths"], right["allowed_paths"])
            if path_overlap:
                errors.append(
                    f"path-lease-overlap:{left['task_id']}:{right['task_id']}: {path_overlap[0]} <> {path_overlap[1]}"
                )
            shared_state = sorted(set(left["owned_mutable_state"]) & set(right["owned_mutable_state"]))
            if shared_state:
                errors.append(
                    f"mutable-state-overlap:{left['task_id']}:{right['task_id']}: {','.join(shared_state)}"
                )
            shared_resources = sorted(
                set(left["external_resource_leases"]) & set(right["external_resource_leases"])
            )
            if shared_resources:
                errors.append(
                    f"resource-lease-overlap:{left['task_id']}:{right['task_id']}: {','.join(shared_resources)}"
                )

    task_by_pair = {(task["task_id"], task["attempt_id"]): task for task in tasks}
    result_pairs: list[tuple[str, str]] = []
    result_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for result in results:
        pair = (result["task_id"], result["attempt_id"])
        result_pairs.append(pair)
        result_by_pair[pair] = result
        task = task_by_pair.get(pair)
        if task is None:
            errors.append(f"orphan-result:{result['task_id']}:{result['attempt_id']}")
            continue
        if result["base_subject_sha"] != task["base_subject_sha"]:
            errors.append(f"stale-result-base:{result['task_id']}:{result['attempt_id']}")
        for owned_path in result["owned_paths"]:
            if not any(
                paths_overlap(owned_path, allowed)
                and normalize_path(owned_path).startswith(normalize_path(allowed))
                for allowed in task["allowed_paths"]
            ):
                errors.append(f"result-outside-path-lease:{result['task_id']}: {owned_path}")
        if result["state"] in VERIFIED_RESULT_STATES:
            for lane_name in ("positive_evals", "negative_controls"):
                for item in result[lane_name]:
                    if item["state"] != "PASS":
                        errors.append(
                            f"verified-result-nonpass:{result['task_id']}:{lane_name}:{item['id']}={item['state']}"
                        )
        for key in RESULT_BUDGET_KEYS:
            if result["budget_consumed"][key] > task["budget"][key]:
                errors.append(
                    f"worker-budget-exceeded:{result['task_id']}:{key}: "
                    f"consumed={result['budget_consumed'][key]} limit={task['budget'][key]}"
                )

    duplicate_results = sorted(pair for pair in set(result_pairs) if result_pairs.count(pair) > 1)
    if duplicate_results:
        errors.append(
            "duplicate-worker-result: "
            + ",".join(f"{task_id}/{attempt_id}" for task_id, attempt_id in duplicate_results)
        )

    for task in tasks:
        pair = (task["task_id"], task["attempt_id"])
        if task["state"] in VERIFIED_TASK_STATES and pair not in result_by_pair:
            errors.append(f"verified-task-missing-result:{task['task_id']}:{task['attempt_id']}")
        if pair in result_by_pair:
            result = result_by_pair[pair]
            if task["state"] in VERIFIED_TASK_STATES and result["state"] not in VERIFIED_RESULT_STATES:
                errors.append(
                    f"task-result-state-mismatch:{task['task_id']}: task={task['state']} result={result['state']}"
                )

    result_totals = {
        key: sum(result["budget_consumed"][key] for result in results)
        for key in RESULT_BUDGET_KEYS
    }
    for key, total in result_totals.items():
        if total != budget["consumed"][key]:
            errors.append(
                f"budget-ledger-mismatch:{key}: results={total} contract={budget['consumed'][key]}"
            )
    if budget["consumed"]["total_workers"] != len(tasks):
        errors.append(
            f"worker-ledger-mismatch: tasks={len(tasks)} total_workers={budget['consumed']['total_workers']}"
        )
    active_count = sum(task["lease"]["status"] == "ACTIVE" for task in tasks)
    if budget["consumed"]["active_workers"] != active_count:
        errors.append(
            f"active-worker-ledger-mismatch: active-leases={active_count} "
            f"active_workers={budget['consumed']['active_workers']}"
        )

    if merge_boundary["agent_merge_action"] != "DENY":
        errors.append("agent-merge-action-not-denied")
    if states["delivery_state"] == "AUTO_MERGE_ELIGIBLE" and states["authority_state"] not in {
        "TRUSTED_AUTOMATION_REQUIRED",
        "HUMAN_ADMIT_REQUIRED",
    }:
        errors.append("merge-eligibility-created-authority: eligibility requires external authority state")
    if states["delivery_state"] == "MERGED" and not merge_boundary["observed_external_merge"]:
        errors.append("merged-without-external-observation")
    if states["delivery_state"] != "MERGED" and merge_boundary["observed_external_merge"]:
        errors.append("external-merge-observation-state-mismatch")

    return errors


def check(contract_path: Path, schema_root: Path) -> int:
    contract = load_json(contract_path)
    root_schema = load_json(schema_root / "multi-agent-runtime-contract.schema.json")
    task_schema = load_json(schema_root / "worker-task.schema.json")
    result_schema = load_json(schema_root / "worker-result.schema.json")

    schema_errors = validate_schema(contract, root_schema, "runtime")
    if not schema_errors:
        for index, task in enumerate(contract["tasks"]):
            schema_errors.extend(validate_schema(task, task_schema, f"task[{index}]"))
        for index, result in enumerate(contract["results"]):
            schema_errors.extend(validate_schema(result, result_schema, f"result[{index}]"))
    if schema_errors:
        for error in schema_errors:
            print(f"RUNTIME-CONTRACT-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = semantic_errors(contract)
    if errors:
        for error in errors:
            print(f"RUNTIME-CONTRACT-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    print(
        "RUNTIME-CONTRACT-GREEN "
        f"repository={contract['repository']['identity']} "
        f"subject={contract['repository']['current_sha']} "
        f"topology={contract['topology']} "
        f"tasks={len(contract['tasks'])} results={len(contract['results'])} "
        f"delivery={contract['states']['delivery_state']} "
        f"authority={contract['states']['authority_state']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "references",
    )
    args = parser.parse_args(argv)
    return check(args.contract, args.schema_root)


if __name__ == "__main__":
    raise SystemExit(main())
