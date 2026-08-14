#!/usr/bin/env python3
"""Validate a Git Town Intent-Bound Stack contract.

Exit codes: 0 pass, 2 contract failure, 64 input/usage, 70 evaluator failure.
"""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_HUMAN = {
    "semantic_conflict_resolution",
    "merge_or_ship",
    "permission_widening",
    "release_promotion",
    "destructive_rollback",
}


def _strings(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _overlap(left: str, right: str) -> bool:
    a = left.strip("/")
    b = right.strip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def validate_stack(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "git-town-intent-stack/v1":
        errors.append("schema_version must be git-town-intent-stack/v1")
    repository = data.get("repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        errors.append("repository must use owner/name form")
    subject = data.get("subject_identity")
    if not isinstance(subject, dict) or not isinstance(subject.get("commit_sha"), str) or not SHA40.fullmatch(subject["commit_sha"]):
        errors.append("subject_identity.commit_sha must be a 40-character lowercase SHA")
    main = data.get("main_branch")
    if not isinstance(main, str) or not main.strip():
        errors.append("main_branch must be non-empty")
        main = "main"

    human = data.get("human_owned_operations")
    if not isinstance(human, list):
        errors.append("human_owned_operations must be an array")
        human = []
    missing_human = sorted(REQUIRED_HUMAN - set(human))
    if missing_human:
        errors.append("missing Human-owned operations: " + ", ".join(missing_human))

    branches = data.get("branches")
    if not isinstance(branches, list) or not branches:
        errors.append("branches must be a non-empty list")
        return errors

    by_name: dict[str, dict[str, Any]] = {}
    ids: set[str] = set()
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            errors.append(f"branches[{index}] must be an object")
            continue
        branch_id = branch.get("id")
        name = branch.get("branch")
        if not isinstance(branch_id, str) or not branch_id.startswith("STACK-"):
            errors.append(f"branches[{index}].id must start with STACK-")
        elif branch_id in ids:
            errors.append(f"duplicate branch id: {branch_id}")
        else:
            ids.add(branch_id)
        if not isinstance(name, str) or not name.strip():
            errors.append(f"branches[{index}].branch must be non-empty")
            continue
        if name in by_name:
            errors.append(f"duplicate branch name: {name}")
        by_name[name] = branch

    # Per-branch exact-parent, PR-base, evidence, and dependency checks.
    for name, branch in by_name.items():
        parent = branch.get("parent_branch")
        stack_class = branch.get("stack_class")
        if parent != main and parent not in by_name:
            errors.append(f"{name} references unknown parent branch {parent}")
        if branch.get("pr_base") != parent:
            errors.append(f"{name} PR base does not equal declared parent branch")
        declared = branch.get("declared_parent_head_sha")
        observed = branch.get("observed_parent_head_sha")
        merge_base = branch.get("merge_base_sha")
        if declared != observed:
            errors.append(f"{name} observed parent head differs from the declared parent head")
        if merge_base != declared:
            errors.append(f"{name} merge base is not the exact declared parent head")
        if branch.get("behind_by") != 0:
            errors.append(f"{name} is stale: behind_by must be 0")
        if branch.get("evidence_subject_sha") != branch.get("head_sha"):
            errors.append(f"{name} evidence subject does not equal the exact branch head")
        if not isinstance(branch.get("ahead_by"), int) or branch.get("ahead_by", 0) < 1:
            errors.append(f"{name} ahead_by must be at least 1")
        if not _strings(branch.get("allowed_paths"), allow_empty=False):
            errors.append(f"{name} must declare at least one allowed path")
        if not _strings(branch.get("excluded_paths")):
            errors.append(f"{name}.excluded_paths must be a string array")
        if not _strings(branch.get("consumes_contracts")):
            errors.append(f"{name}.consumes_contracts must be a string array")
        if not _strings(branch.get("consumes_paths")):
            errors.append(f"{name}.consumes_paths must be a string array")
        if not _strings(branch.get("provides_contracts")):
            errors.append(f"{name}.provides_contracts must be a string array")
        if not _strings(branch.get("depends_on_branches")):
            errors.append(f"{name}.depends_on_branches must be a string array")

        consumes = branch.get("consumes_contracts") or []
        consumes_paths = branch.get("consumes_paths") or []
        reason = branch.get("dependency_reason")
        dependencies = branch.get("depends_on_branches") or []
        if stack_class == "foundation":
            if parent != main:
                errors.append(f"{name} foundation must target the main branch")
            if consumes or consumes_paths:
                errors.append(f"{name} foundation must not consume an unmerged parent contract or path")
            if dependencies:
                errors.append(f"{name} foundation must not depend on another feature branch")
        elif stack_class == "child":
            if parent == main:
                errors.append(f"{name} child must name a non-main parent")
            if not consumes and not consumes_paths:
                errors.append(f"{name} is fake serialization: child has no consumed contract or byte dependency")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{name} child must explain the consumed contract or byte dependency")
            if parent not in dependencies:
                errors.append(f"{name} child dependency list must include its parent branch")
        elif stack_class == "sibling":
            sibling_dependencies = [item for item in dependencies if item != parent]
            if sibling_dependencies:
                errors.append(f"{name} sibling depends on another sibling: {', '.join(sibling_dependencies)}")
        elif stack_class == "hotfix":
            if parent != main:
                errors.append(f"{name} hotfix must target the main branch")
            if dependencies:
                errors.append(f"{name} hotfix must not depend on an active feature branch")
        else:
            errors.append(f"{name} has invalid stack_class {stack_class}")

    # Cycle detection across branch-parent edges.
    for start in by_name:
        seen: set[str] = set()
        current = start
        while current in by_name:
            if current in seen:
                errors.append(f"branch ancestry cycle detected from {start}")
                break
            seen.add(current)
            current = str(by_name[current].get("parent_branch"))

    # Active siblings with the same parent must have disjoint path leases.
    names = sorted(by_name)
    for index, left_name in enumerate(names):
        left = by_name[left_name]
        if left.get("state") != "ACTIVE" or left.get("stack_class") != "sibling":
            continue
        for right_name in names[index + 1 :]:
            right = by_name[right_name]
            if right.get("state") != "ACTIVE" or right.get("stack_class") != "sibling":
                continue
            if left.get("parent_branch") != right.get("parent_branch"):
                continue
            for left_path in left.get("allowed_paths", []):
                for right_path in right.get("allowed_paths", []):
                    if _overlap(left_path, right_path):
                        errors.append(
                            f"sibling path lease overlap: {left_name}:{left_path} and {right_name}:{right_path}"
                        )

    convergence = data.get("convergence_plan")
    if not isinstance(convergence, dict):
        errors.append("convergence_plan must be an object")
    else:
        prerequisites = convergence.get("prerequisites")
        if not _strings(prerequisites, allow_empty=False):
            errors.append("convergence_plan must declare prerequisites")
            prerequisites = []
        unknown = sorted(set(prerequisites) - set(by_name))
        if unknown:
            errors.append("convergence_plan references unknown prerequisites: " + ", ".join(unknown))
        all_admitted = bool(prerequisites) and all(
            by_name.get(item, {}).get("state") == "ADMITTED" for item in prerequisites
        )
        state = convergence.get("state")
        if not all_admitted and state != "NOT_CREATED":
            errors.append("convergence branch must remain NOT_CREATED until all prerequisites are ADMITTED")
        if all_admitted and state not in {"READY", "CREATED", "ADMITTED"}:
            errors.append("convergence plan is ready but state does not permit creation")
        if not isinstance(convergence.get("owner_issue"), int):
            errors.append("convergence_plan must name one owner_issue")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.contract.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("contract root must be an object")
        errors = validate_stack(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 64
    except Exception as exc:
        print(f"internal evaluator error: {exc}", file=sys.stderr)
        return 70

    result = {
        "schema_version": "git-town-stack-validation-receipt/v1",
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
    }
    if args.json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
    else:
        print("PASS: Git Town Stack contract verified")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
