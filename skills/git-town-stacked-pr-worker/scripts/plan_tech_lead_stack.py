#!/usr/bin/env python3
"""Compile a Tech Lead goal graph into Git Town Worker task packets.

This script validates and emits plan artifacts. It does not create branches,
worktrees, issues, PRs, provider indexes, or Agent processes.

Exit codes: 0 accepted, 2 contract failure, 64 invalid input, 70 mechanism error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PASS, FAIL, USAGE, MECHANISM = 0, 2, 64, 70
SCHEMA = "git-town-stacked-pr-worker/tech-lead-plan/v1"
RECEIPT_SCHEMA = "git-town-stacked-pr-worker/tech-lead-compile-receipt/v1"
PACKET_SCHEMA = "git-town-stacked-pr-worker/task-packet/v2"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BRANCH_RE = re.compile(r"^(?!/)(?!.*\.\.)(?!.*//)(?!.*[~^:?*\\\[\]])[A-Za-z0-9._/-]+(?<![./])$")
STACK_CLASSES = {"foundation", "child", "sibling", "convergence", "hotfix"}
BLINDSPOT_LANES = {"grepai", "scip", "tree-sitter", "serena", "lancedb", "source-readback", "test"}
DISCOVERY_LANES = {"grepai", "scip", "tree-sitter", "serena"}


class InputError(Exception):
    pass


class MechanismError(Exception):
    pass


@dataclass(frozen=True)
class Failure:
    id: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "detail": self.detail}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"input absent: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON at {path}: {exc}") from exc
    except OSError as exc:
        raise MechanismError(f"cannot read {path}: {exc}") from exc


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    return value


def strings(value: Any, label: str, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise InputError(f"{label} must be an array of non-empty strings")
    items = [item.strip() for item in value]
    if nonempty and not items:
        raise InputError(f"{label} must not be empty")
    return items


def path_root(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    if not value or value.startswith(("/", "~")):
        raise InputError(f"path lease must be repository-relative: {raw!r}")
    if "\x00" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise InputError(f"invalid path lease: {raw!r}")
    if "*" in value[:-3] or "?" in value or "[" in value or "]" in value:
        raise InputError(f"unsupported glob syntax: {raw!r}")
    if value.endswith("/**"):
        value = value[:-3].rstrip("/")
    return value.rstrip("/")


def overlaps(a: str, b: str) -> bool:
    return a == b or a.startswith(f"{b}/") or b.startswith(f"{a}/")


def cycle_path(tasks: dict[str, dict[str, Any]]) -> list[str] | None:
    temp: set[str] = set()
    done: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in done:
            return None
        if node in temp:
            start = stack.index(node) if node in stack else 0
            return stack[start:] + [node]
        temp.add(node)
        stack.append(node)
        for dep in tasks[node]["depends_on"]:
            found = visit(dep)
            if found:
                return found
        stack.pop()
        temp.remove(node)
        done.add(node)
        return None

    for node in sorted(tasks):
        found = visit(node)
        if found:
            return found
    return None


def topo(tasks: dict[str, dict[str, Any]]) -> list[str]:
    indegree = {task_id: len(task["depends_on"]) for task_id, task in tasks.items()}
    children = {task_id: [] for task_id in tasks}
    for task_id, task in tasks.items():
        for dep in task["depends_on"]:
            children[dep].append(task_id)
    ready = sorted(key for key, value in indegree.items() if value == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(tasks):
        raise MechanismError("topological order requested for cyclic plan")
    return order


def validate_plan(raw: Any) -> tuple[dict[str, Any], list[Failure]]:
    plan = require_object(raw, "plan")
    failures: list[Failure] = []
    if plan.get("schema") != SCHEMA:
        raise InputError(f"plan.schema must be {SCHEMA}")

    subject = require_object(plan.get("subject"), "subject")
    repository, base_branch = subject.get("repository"), subject.get("base_branch")
    base_commit, tree = subject.get("base_commit"), subject.get("tree")
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        failures.append(Failure("SUBJECT_REPOSITORY_INVALID", "subject.repository must be owner/repository"))
    if not isinstance(base_branch, str) or not BRANCH_RE.fullmatch(base_branch):
        failures.append(Failure("SUBJECT_BASE_BRANCH_INVALID", "subject.base_branch is invalid"))
    if not isinstance(base_commit, str) or not SHA_RE.fullmatch(base_commit):
        failures.append(Failure("SUBJECT_MUTABLE", "subject.base_commit must be immutable 40-hex"))
    if not isinstance(tree, str) or not SHA_RE.fullmatch(tree):
        failures.append(Failure("SUBJECT_TREE_INVALID", "subject.tree must be immutable 40-hex"))
    goal = plan.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        failures.append(Failure("GOAL_ABSENT", "plan.goal must not be empty"))

    raw_constraints = plan.get("architecture_constraints")
    if not isinstance(raw_constraints, list) or not raw_constraints:
        failures.append(Failure("ARCHITECTURE_CONSTRAINT_ABSENT", "architecture_constraints must not be empty"))
        raw_constraints = []
    raw_tasks = plan.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise InputError("tasks must be a non-empty array")

    tasks: dict[str, dict[str, Any]] = {}
    branches: dict[str, str] = {}
    for index, raw_task in enumerate(raw_tasks):
        try:
            task = require_object(raw_task, f"tasks[{index}]")
            task_id = task.get("id")
            if not isinstance(task_id, str) or not ID_RE.fullmatch(task_id):
                failures.append(Failure("TASK_ID_INVALID", f"tasks[{index}].id must be lower-kebab-case"))
                continue
            if task_id in tasks:
                failures.append(Failure("TASK_ID_DUPLICATE", task_id))
                continue
            title, stack_class = task.get("title"), task.get("stack_class")
            if not isinstance(title, str) or not title.strip():
                failures.append(Failure("TASK_TITLE_ABSENT", task_id))
            if stack_class not in STACK_CLASSES:
                failures.append(Failure("TASK_STACK_CLASS_INVALID", f"{task_id}: {stack_class!r}"))
            head_branch = task.get("head_branch")
            if not isinstance(head_branch, str) or not BRANCH_RE.fullmatch(head_branch):
                failures.append(Failure("TASK_BRANCH_INVALID", task_id))
            elif head_branch == base_branch:
                failures.append(Failure("TASK_BRANCH_EQUALS_BASE", task_id))
            elif head_branch in branches:
                failures.append(Failure("TASK_BRANCH_DUPLICATE", f"{head_branch}: {branches[head_branch]}, {task_id}"))
            else:
                branches[head_branch] = task_id
            parent = task.get("parent")
            if not isinstance(parent, str) or not parent.strip():
                failures.append(Failure("TASK_PARENT_ABSENT", task_id))
            depends_on = strings(task.get("depends_on", []), f"{task_id}.depends_on")
            if task_id in depends_on:
                failures.append(Failure("TASK_SELF_DEPENDENCY", task_id))
            try:
                allowed_paths = sorted(set(path_root(path) for path in strings(task.get("allowed_paths"), f"{task_id}.allowed_paths", True)))
                excluded_paths = sorted(set(path_root(path) for path in strings(task.get("excluded_paths", []), f"{task_id}.excluded_paths")))
            except InputError as exc:
                failures.append(Failure("TASK_PATH_INVALID", f"{task_id}: {exc}"))
                allowed_paths, excluded_paths = [], []
            for allowed in allowed_paths:
                if any(allowed == excluded or allowed.startswith(f"{excluded}/") for excluded in excluded_paths):
                    failures.append(Failure("TASK_PATH_SELF_EXCLUDED", f"{task_id}: {allowed}"))
            provides = strings(task.get("provides_contracts", []), f"{task_id}.provides_contracts")
            consumes = strings(task.get("consumes_contracts", []), f"{task_id}.consumes_contracts")
            non_goals = strings(task.get("non_goals"), f"{task_id}.non_goals", True)
            evals = strings(task.get("required_evals"), f"{task_id}.required_evals", True)
            controls = strings(task.get("negative_controls"), f"{task_id}.negative_controls", True)
            human_ops = strings(task.get("human_owned_operations"), f"{task_id}.human_owned_operations", True)
            if "merge" not in {item.lower() for item in human_ops}:
                failures.append(Failure("HUMAN_MERGE_BOUNDARY_ABSENT", task_id))
            evidence, cleanup, rollback = task.get("evidence_boundary"), task.get("cleanup_contract"), task.get("rollback_subject")
            if not isinstance(evidence, str) or not evidence.strip():
                failures.append(Failure("EVIDENCE_BOUNDARY_ABSENT", task_id))
            if not isinstance(cleanup, str) or not cleanup.strip():
                failures.append(Failure("CLEANUP_CONTRACT_ABSENT", task_id))
            if not isinstance(rollback, str) or not SHA_RE.fullmatch(rollback):
                failures.append(Failure("ROLLBACK_SUBJECT_MUTABLE", task_id))

            raw_queries = task.get("blindspot_queries")
            if not isinstance(raw_queries, list) or not raw_queries:
                failures.append(Failure("BLINDSPOT_QUERY_ABSENT", task_id))
                raw_queries = []
            queries: list[dict[str, Any]] = []
            query_ids: set[str] = set()
            for qindex, raw_query in enumerate(raw_queries):
                if not isinstance(raw_query, dict):
                    failures.append(Failure("BLINDSPOT_QUERY_INVALID", f"{task_id}[{qindex}]"))
                    continue
                query_id, intent = raw_query.get("id"), raw_query.get("intent")
                try:
                    lanes = strings(raw_query.get("lanes"), f"{task_id}.{query_id}.lanes", True)
                except InputError as exc:
                    failures.append(Failure("BLINDSPOT_QUERY_INVALID", f"{task_id}: {exc}"))
                    continue
                if not isinstance(query_id, str) or not ID_RE.fullmatch(query_id) or query_id in query_ids:
                    failures.append(Failure("BLINDSPOT_QUERY_ID_INVALID", f"{task_id}[{qindex}]"))
                    continue
                query_ids.add(query_id)
                if not isinstance(intent, str) or not intent.strip():
                    failures.append(Failure("BLINDSPOT_QUERY_INTENT_ABSENT", f"{task_id}:{query_id}"))
                unknown = sorted(set(lanes) - BLINDSPOT_LANES)
                if unknown:
                    failures.append(Failure("BLINDSPOT_QUERY_LANE_UNKNOWN", f"{task_id}:{query_id}:{','.join(unknown)}"))
                if not set(lanes) & DISCOVERY_LANES:
                    failures.append(Failure("BLINDSPOT_QUERY_DISCOVERY_ABSENT", f"{task_id}:{query_id}"))
                if "source-readback" not in lanes or raw_query.get("readback_required") is not True:
                    failures.append(Failure("BLINDSPOT_QUERY_INCOMPLETE", f"{task_id}:{query_id} requires source-readback"))
                if "lancedb" in lanes and not (set(lanes) - {"lancedb", "source-readback", "test"}):
                    failures.append(Failure("VECTOR_PROJECTION_WITHOUT_SOURCE_LANE", f"{task_id}:{query_id}"))
                queries.append({"id": query_id, "intent": intent.strip() if isinstance(intent, str) else "", "lanes": sorted(set(lanes)), "readback_required": raw_query.get("readback_required") is True, "negative_control": raw_query.get("negative_control", "")})

            tasks[task_id] = {
                "id": task_id, "title": title.strip() if isinstance(title, str) else "", "stack_class": stack_class,
                "head_branch": head_branch, "parent": parent, "depends_on": sorted(set(depends_on)),
                "allowed_paths": allowed_paths, "excluded_paths": excluded_paths,
                "provides_contracts": sorted(set(provides)), "consumes_contracts": sorted(set(consumes)),
                "non_goals": non_goals, "required_evals": evals, "negative_controls": controls,
                "blindspot_queries": sorted(queries, key=lambda item: item["id"]),
                "evidence_boundary": evidence.strip() if isinstance(evidence, str) else "",
                "cleanup_contract": cleanup.strip() if isinstance(cleanup, str) else "",
                "rollback_subject": rollback, "human_owned_operations": human_ops,
            }
        except InputError as exc:
            failures.append(Failure("TASK_INPUT_INVALID", f"tasks[{index}]: {exc}"))

    task_ids = set(tasks)
    for task_id, task in tasks.items():
        missing = sorted(set(task["depends_on"]) - task_ids)
        if missing:
            failures.append(Failure("TASK_DEPENDENCY_UNKNOWN", f"{task_id}: {','.join(missing)}"))
        parent = task["parent"]
        parent_is_base, parent_is_task = parent == base_branch, parent in task_ids
        if not parent_is_base and not parent_is_task:
            failures.append(Failure("TASK_PARENT_UNKNOWN", f"{task_id}: {parent}"))
        if task["stack_class"] in {"foundation", "sibling", "hotfix"} and not parent_is_base:
            failures.append(Failure("STACK_CLASS_PARENT_INVALID", f"{task_id}: {task['stack_class']} must parent {base_branch}"))
        if task["stack_class"] == "child":
            if not parent_is_task or parent not in task["depends_on"]:
                failures.append(Failure("CHILD_PARENT_DEPENDENCY_ABSENT", task_id))
            elif not set(task["consumes_contracts"]) & set(tasks[parent]["provides_contracts"]):
                failures.append(Failure("FAKE_LINEAR_CHILD", f"{task_id} consumes no contract from {parent}"))
        if task["stack_class"] == "convergence":
            if len(task["depends_on"]) < 2:
                failures.append(Failure("CONVERGENCE_INPUTS_INSUFFICIENT", task_id))
            if not parent_is_base:
                failures.append(Failure("CONVERGENCE_PARENT_INVALID", f"{task_id} must branch from {base_branch}"))

    if all(set(task["depends_on"]) <= task_ids for task in tasks.values()):
        found_cycle = cycle_path(tasks)
        if found_cycle:
            failures.append(Failure("TASK_DAG_CYCLE", " -> ".join(found_cycle)))

    def reachable(start: str, target: str, seen: set[str] | None = None) -> bool:
        seen = set() if seen is None else seen
        if start in seen:
            return False
        seen.add(start)
        if target in tasks[start]["depends_on"]:
            return True
        return any(reachable(dep, target, seen) for dep in tasks[start]["depends_on"] if dep in tasks)

    ordered_ids = sorted(tasks)
    for pos, left_id in enumerate(ordered_ids):
        for right_id in ordered_ids[pos + 1:]:
            if reachable(left_id, right_id) or reachable(right_id, left_id):
                continue
            left, right = tasks[left_id], tasks[right_id]
            if "convergence" in {left["stack_class"], right["stack_class"]}:
                continue
            collisions = sorted({f"{a} <-> {b}" for a in left["allowed_paths"] for b in right["allowed_paths"] if overlaps(a, b)})
            if collisions:
                failures.append(Failure("PATH_LEASE_COLLISION", f"{left_id}/{right_id}: {'; '.join(collisions)}"))

    constraints: list[dict[str, Any]] = []
    constraint_ids: set[str] = set()
    for index, raw_constraint in enumerate(raw_constraints):
        if not isinstance(raw_constraint, dict):
            failures.append(Failure("ARCHITECTURE_CONSTRAINT_INVALID", f"constraint[{index}]"))
            continue
        cid, statement = raw_constraint.get("id"), raw_constraint.get("statement")
        try:
            owners = strings(raw_constraint.get("enforced_by"), f"constraint[{index}].enforced_by", True)
            verification = strings(raw_constraint.get("verification"), f"constraint[{index}].verification", True)
        except InputError as exc:
            failures.append(Failure("ARCHITECTURE_CONSTRAINT_INVALID", str(exc)))
            continue
        if not isinstance(cid, str) or not ID_RE.fullmatch(cid) or cid in constraint_ids:
            failures.append(Failure("ARCHITECTURE_CONSTRAINT_ID_INVALID", f"constraint[{index}]"))
            continue
        constraint_ids.add(cid)
        if not isinstance(statement, str) or not statement.strip():
            failures.append(Failure("ARCHITECTURE_CONSTRAINT_STATEMENT_ABSENT", cid))
        unknown = sorted(set(owners) - task_ids)
        if unknown:
            failures.append(Failure("ARCHITECTURE_CONSTRAINT_OWNER_UNKNOWN", f"{cid}: {','.join(unknown)}"))
        constraints.append({"id": cid, "statement": statement.strip() if isinstance(statement, str) else "", "enforced_by": sorted(set(owners)), "verification": verification})

    max_parallel = plan.get("max_parallel_workers", 1)
    if not isinstance(max_parallel, int) or isinstance(max_parallel, bool) or max_parallel < 1:
        failures.append(Failure("MAX_PARALLEL_INVALID", str(max_parallel)))
        max_parallel = 1
    if isinstance(max_parallel, int) and max_parallel > max(1, len(tasks)):
        failures.append(Failure("MAX_PARALLEL_EXCEEDS_TASKS", str(max_parallel)))

    normalized = {
        "schema": SCHEMA,
        "subject": {"repository": repository, "base_branch": base_branch, "base_commit": base_commit, "tree": tree},
        "goal": goal.strip() if isinstance(goal, str) else "",
        "architecture_constraints": sorted(constraints, key=lambda item: item["id"]),
        "max_parallel_workers": max_parallel,
        "tasks": [tasks[task_id] for task_id in sorted(tasks)],
    }
    return normalized, sorted(failures, key=lambda item: (item.id, item.detail))


def packet(plan: dict[str, Any], task: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base = plan["subject"]["base_branch"]
    parent_id = task["parent"] if task["parent"] in tasks else None
    parent_branch = tasks[parent_id]["head_branch"] if parent_id else base
    assigned = [item for item in plan["architecture_constraints"] if task["id"] in item["enforced_by"]]
    parallel_safe = []
    for other_id, other in tasks.items():
        if other_id == task["id"] or "convergence" in {other["stack_class"], task["stack_class"]}:
            continue
        if other_id in task["depends_on"] or task["id"] in other["depends_on"]:
            continue
        if not any(overlaps(a, b) for a in task["allowed_paths"] for b in other["allowed_paths"]):
            parallel_safe.append(other_id)
    return {
        "schema": PACKET_SCHEMA, "issue_id": f"PLAN:{task['id']}", "parent_issue_id": f"PLAN:{parent_id}" if parent_id else "NONE",
        "repository": plan["subject"]["repository"], "subject_commit": plan["subject"]["base_commit"], "subject_tree": plan["subject"]["tree"],
        "goal": task["title"], "non_goals": task["non_goals"], "base_branch": base, "parent_branch": parent_branch,
        "head_branch": task["head_branch"], "stack_class": task["stack_class"], "allowed_paths": task["allowed_paths"],
        "excluded_paths": task["excluded_paths"], "dependencies": task["depends_on"], "parallel_safe_siblings": sorted(parallel_safe),
        "provided_contracts": task["provides_contracts"], "required_contracts": task["consumes_contracts"],
        "architecture_constraints": assigned, "blindspot_queries": task["blindspot_queries"], "required_evals": task["required_evals"],
        "negative_or_mutation_controls": task["negative_controls"], "evidence_boundary": task["evidence_boundary"],
        "cleanup_contract": task["cleanup_contract"], "rollback_subject": task["rollback_subject"], "human_owned_operations": task["human_owned_operations"],
    }


def render_dot(plan: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> str:
    base = plan["subject"]["base_branch"]
    lines = ["digraph tech_lead_stack {", "  rankdir=LR;", f'  "{base}" [shape=box];']
    for task_id in sorted(tasks):
        task = tasks[task_id]
        label = f"{task_id}\\n{task['stack_class']}\\n{task['head_branch']}"
        lines.append(f'  "{task_id}" [label="{label}"];')
        parent = task["parent"] if task["parent"] in tasks else base
        lines.append(f'  "{parent}" -> "{task_id}" [label="branch parent"];')
        for dep in task["depends_on"]:
            if dep != parent:
                lines.append(f'  "{dep}" -> "{task_id}" [style=dashed,label="contract dependency"];')
    return "\n".join(lines + ["}"]) + "\n"


def compile_plan(plan: dict[str, Any], output: Path) -> dict[str, Any]:
    tasks = {task["id"]: task for task in plan["tasks"]}
    order = topo(tasks)
    output.mkdir(parents=True, exist_ok=True)
    packet_dir = output / "worker-packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    (output / "normalized-plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    packet_records = []
    for task_id in order:
        value = packet(plan, tasks[task_id], tasks)
        path = packet_dir / f"{task_id}.json"
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        packet_records.append({"task_id": task_id, "path": str(path.relative_to(output)), "sha256": digest(value)})
    dot = render_dot(plan, tasks)
    (output / "stack.dot").write_text(dot)
    receipt = {
        "schema": RECEIPT_SCHEMA, "plan_sha256": digest(plan), "repository": plan["subject"]["repository"],
        "base_commit": plan["subject"]["base_commit"], "topological_order": order,
        "max_parallel_workers": plan["max_parallel_workers"], "worker_packets": packet_records,
        "stack_dot_sha256": hashlib.sha256(dot.encode()).hexdigest(),
        "effects": {"branches_created": False, "worktrees_created": False, "agents_spawned": False, "providers_invoked": False, "remote_publication": False},
        "evidence_state": "PASS", "runtime_state": "NOT_EXERCISED",
    }
    (output / "compile-receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--plan", required=True, type=Path)
    compile_cmd = commands.add_parser("compile")
    compile_cmd.add_argument("--plan", required=True, type=Path)
    compile_cmd.add_argument("--output", required=True, type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        normalized, failures = validate_plan(read_json(args.plan))
        if failures:
            print(json.dumps({"state": "FAIL", "failures": [item.as_dict() for item in failures]}, indent=2), file=sys.stderr)
            return FAIL
        if args.command == "verify":
            print(json.dumps({"state": "PASS", "plan_sha256": digest(normalized), "tasks": len(normalized["tasks"])}, sort_keys=True))
            return PASS
        print(json.dumps(compile_plan(normalized, args.output), sort_keys=True))
        return PASS
    except InputError as exc:
        print(f"INVALID_INPUT: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, MechanismError) as exc:
        print(f"MECHANISM_ERROR: {exc}", file=sys.stderr)
        return MECHANISM


if __name__ == "__main__":
    raise SystemExit(main())
