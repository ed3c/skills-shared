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
from datetime import datetime
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
# States that assert Worker closure has happened. Wider than POST_PUBLICATION_STATES:
# LOCAL_VERIFIED makes the same closure claim without publishing anything.
CLOSURE_GATED_STATES = POST_PUBLICATION_STATES | {"LOCAL_VERIFIED"}
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


def path_contains(root: str, candidate: str) -> bool:
    """True when `candidate` is `root` itself or lies beneath it.

    Segment-aware on purpose. Composing raw `startswith` treats `src/parser2` as
    living under `src/parser`, which silently widens a path lease to siblings that
    merely share a name prefix.
    """
    r = normalize_path(root)
    c = normalize_path(candidate)
    if r == ".":
        return True
    return c == r or c.startswith(f"{r}/")


def paths_overlap(left: str, right: str) -> bool:
    return path_contains(left, right) or path_contains(right, left)


def any_overlap(left: Iterable[str], right: Iterable[str]) -> tuple[str, str] | None:
    for a in left:
        for b in right:
            if paths_overlap(a, b):
                return a, b
    return None


def graph_cycle(tasks: list[dict[str, Any]]) -> list[str] | None:
    ids = {task["task_id"] for task in tasks}
    # Aggregate by logical task: one slice may carry several attempt packets, and
    # counting an edge once per attempt would inflate indegree into a false cycle.
    edges: dict[str, set[str]] = defaultdict(set)
    for task in tasks:
        edges[task["task_id"]].update(task["dependencies"])
    indegree = {task_id: 0 for task_id in ids}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for child, parents in edges.items():
        for parent in sorted(parents):
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


def parse_rfc3339(value: str) -> datetime | None:
    # The schema pattern already constrains the shape; this still refuses rather
    # than guesses, because a comparison against an unparsed string is not a check.
    text = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def dependency_closure(tasks: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Map each logical task to every logical task it transitively depends on."""
    direct: dict[str, set[str]] = defaultdict(set)
    for task in tasks:
        direct[task["task_id"]].update(task["dependencies"])
    closure: dict[str, set[str]] = {}

    def resolve(task_id: str, seen: frozenset[str]) -> set[str]:
        if task_id in closure:
            return closure[task_id]
        if task_id in seen:  # cycles are reported separately; stop descending here
            return set()
        result: set[str] = set()
        for parent in direct.get(task_id, ()):
            result.add(parent)
            result |= resolve(parent, seen | {task_id})
        closure[task_id] = result
        return result

    for task in tasks:
        resolve(task["task_id"], frozenset())
    return closure


def semantic_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    evaluation_time = parse_rfc3339(contract["evaluation_time"])
    if evaluation_time is None:
        errors.append(
            f"evaluation-time-unparsable: {contract['evaluation_time']!r} is not an "
            "offset-bearing RFC3339 instant"
        )
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

    # Cardinality is a property of the logical slice set, not of attempt packets:
    # a single slice that was retried is still one builder.
    logical_task_count = len({task["task_id"] for task in tasks})
    if topology == "MULTI_WORKER":
        failed_admission = sorted(key for key, value in admission.items() if value is not True)
        if failed_admission:
            errors.append(f"parallelism-not-admitted: false={','.join(failed_admission)}")
        if logical_task_count < 2:
            errors.append("multi-worker-cardinality: MULTI_WORKER requires at least two logical tasks")
    elif topology == "SINGLE_BUILDER" and logical_task_count != 1:
        errors.append("single-builder-cardinality: SINGLE_BUILDER requires exactly one logical task")

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
    # task_id names the logical slice and may legitimately repeat across retries;
    # attempt_id, branch and worktree identify one physical attempt and may not.
    for label, values in (
        ("attempt-id", attempt_ids),
        ("branch", branches),
        ("worktree", worktrees),
    ):
        duplicates = sorted(value for value in set(values) if values.count(value) > 1)
        if duplicates:
            errors.append(f"duplicate-{label}: {','.join(duplicates)}")

    attempts_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        attempts_by_task[task["task_id"]].append(task)
    attempt_index = {task["attempt_id"]: task for task in tasks}
    max_attempts = repository["max_attempts_per_task"]

    for task_id, attempts in sorted(attempts_by_task.items()):
        if len(attempts) > max_attempts:
            errors.append(
                f"attempt-limit-exceeded:{task_id}: attempts={len(attempts)} limit={max_attempts}"
            )
        active = [a for a in attempts if a["lease"]["status"] == "ACTIVE"]
        if len(active) > 1:
            errors.append(
                f"concurrent-attempts:{task_id}: "
                + ",".join(sorted(a["attempt_id"] for a in active))
            )
        accepted = [a for a in attempts if a["state"] in VERIFIED_TASK_STATES]
        if len(accepted) > 1:
            errors.append(
                f"multiple-accepted-attempts:{task_id}: "
                + ",".join(sorted(a["attempt_id"] for a in accepted))
            )
        if len(attempts) > 1:
            # A retry must declare which attempt it descends from, otherwise the
            # retry lineage is unauditable and a stale attempt is indistinguishable
            # from an unrelated packet that happens to share the slice name.
            rootless = [a for a in attempts if a["parent_attempt_id"] is None]
            if len(rootless) != 1:
                errors.append(
                    f"attempt-lineage-root:{task_id}: expected exactly one attempt "
                    f"without parent_attempt_id, found {len(rootless)}"
                )
        for attempt in attempts:
            parent_id = attempt["parent_attempt_id"]
            if parent_id is None:
                continue
            parent = attempt_index.get(parent_id)
            if parent is None:
                errors.append(
                    f"unknown-parent-attempt:{attempt['attempt_id']}: {parent_id}"
                )
            elif parent["task_id"] != task_id:
                errors.append(
                    f"cross-task-attempt-lineage:{attempt['attempt_id']}: "
                    f"parent {parent_id} belongs to {parent['task_id']}"
                )
            elif parent["state"] not in TERMINAL_TASK_STATES:
                errors.append(
                    f"retry-over-live-attempt:{attempt['attempt_id']}: "
                    f"parent {parent_id} is {parent['state']}, not terminal"
                )

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
        if task["lease"]["status"] == "ACTIVE" and evaluation_time is not None:
            expiry = parse_rfc3339(task["lease"]["expiry"])
            if expiry is None:
                errors.append(
                    f"lease-expiry-unparsable:{task['attempt_id']}: {task['lease']['expiry']!r}"
                )
            elif expiry <= evaluation_time:
                # An ACTIVE lease past its expiry lets a stale writer's attempts and
                # results be read as current, which is the whole point of the lease.
                errors.append(
                    f"expired-active-lease:{task['attempt_id']}: "
                    f"expiry={task['lease']['expiry']} evaluation_time={contract['evaluation_time']}"
                )

    cycle = graph_cycle(tasks)
    if cycle:
        errors.append(f"dependency-cycle: {','.join(cycle)}")

    # Ownership collides only between writers that can write at the same time.
    # Comparing every packet as if concurrent forbids valid sequential convergence:
    # a released predecessor handing a path to its declared successor is ordered
    # ownership, not a conflict. What must still be refused is an unordered reuse,
    # where nothing in the graph says which writer came first.
    closure = dependency_closure(tasks)
    for index, left in enumerate(tasks):
        for right in tasks[index + 1 :]:
            if left["task_id"] == right["task_id"]:
                continue  # retries of one slice inherit that slice's ownership
            both_active = (
                left["lease"]["status"] == "ACTIVE" and right["lease"]["status"] == "ACTIVE"
            )
            ordered = (
                right["task_id"] in closure.get(left["task_id"], set())
                or left["task_id"] in closure.get(right["task_id"], set())
            )
            if not both_active and ordered:
                continue
            suffix = "" if both_active else ": unordered-handoff"
            path_overlap = any_overlap(left["allowed_paths"], right["allowed_paths"])
            if path_overlap:
                errors.append(
                    f"path-lease-overlap:{left['task_id']}:{right['task_id']}: "
                    f"{path_overlap[0]} <> {path_overlap[1]}{suffix}"
                )
            shared_state = sorted(set(left["owned_mutable_state"]) & set(right["owned_mutable_state"]))
            if shared_state:
                errors.append(
                    f"mutable-state-overlap:{left['task_id']}:{right['task_id']}: "
                    f"{','.join(shared_state)}{suffix}"
                )
            shared_resources = sorted(
                set(left["external_resource_leases"]) & set(right["external_resource_leases"])
            )
            if shared_resources:
                errors.append(
                    f"resource-lease-overlap:{left['task_id']}:{right['task_id']}: "
                    f"{','.join(shared_resources)}{suffix}"
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
        if result["head_subject_sha"] not in repository["admitted_subjects"]:
            # Otherwise an unbound revision enters the contract through a result.
            errors.append(
                f"result-head-not-admitted:{result['task_id']}:{result['attempt_id']}: "
                f"{result['head_subject_sha']}"
            )
        for owned_path in result["owned_paths"]:
            if not any(path_contains(allowed, owned_path) for allowed in task["allowed_paths"]):
                errors.append(f"result-outside-path-lease:{result['task_id']}: {owned_path}")
        if result["state"] in VERIFIED_RESULT_STATES:
            for lane_name in ("positive_evals", "negative_controls"):
                for item in result[lane_name]:
                    if item["state"] != "PASS":
                        errors.append(
                            f"verified-result-nonpass:{result['task_id']}:{lane_name}:{item['id']}={item['state']}"
                        )
            # A passing oracle only counts when it is the oracle the task required.
            # Set equality both ways: a missing ID leaves the slice unproven, an
            # extra one lets an unowned check stand in for the owning check.
            for task_key, result_key in (
                ("required_evals", "positive_evals"),
                ("negative_controls", "negative_controls"),
            ):
                required = set(task[task_key])
                observed = {item["id"] for item in result[result_key]}
                if required != observed:
                    missing = sorted(required - observed)
                    extra = sorted(observed - required)
                    errors.append(
                        f"eval-identity-mismatch:{result['task_id']}:{result_key}: "
                        f"missing={','.join(missing) or '-'} unowned={','.join(extra) or '-'}"
                    )
            # Binds resume/handoff identity: without it a result can be accepted
            # against a checkpoint it never ran from.
            task_digest = (task.get("checkpoint") or {}).get("digest")
            if task_digest is None:
                errors.append(
                    f"verified-result-without-task-checkpoint:{result['task_id']}:{result['attempt_id']}"
                )
            elif result["checkpoint_identity"] != task_digest:
                errors.append(
                    f"checkpoint-identity-mismatch:{result['task_id']}:{result['attempt_id']}: "
                    f"result={result['checkpoint_identity']} task={task_digest}"
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

    # Delivery state is a claim about Worker closure. Without this gate the contract
    # can report PR_OPEN while every task is still RUNNING and no result exists.
    if states["delivery_state"] in CLOSURE_GATED_STATES:
        for task_id, attempts in sorted(attempts_by_task.items()):
            accepted = [a for a in attempts if a["state"] in VERIFIED_TASK_STATES]
            if not accepted:
                errors.append(
                    f"publication-before-closure:{task_id}: "
                    f"delivery_state={states['delivery_state']} with no accepted attempt"
                )
                continue
            attempt = accepted[0]
            result = result_by_pair.get((attempt["task_id"], attempt["attempt_id"]))
            if result is None or result["state"] not in VERIFIED_RESULT_STATES:
                errors.append(
                    f"publication-without-accepted-result:{task_id}:{attempt['attempt_id']}"
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
