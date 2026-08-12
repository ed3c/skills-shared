#!/usr/bin/env python3
"""Fail-closed policy checks for private-repository GitHub Actions workflows."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "github-ci-policy/v1"
SHA_RE = re.compile(r"[0-9a-f]{40}")
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_-]+):(?P<value>.*)$")
PULL_REQUEST_TYPES = {
    "draft-first": {"ready_for_review"},
    "universal": {"opened", "synchronize", "reopened"},
}


class PolicyError(ValueError):
    """The policy or workflow cannot prove the cost-control contract."""


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PolicyError(f"unreadable {label}: {error}") from error
    if not isinstance(value, dict):
        raise PolicyError(f"{label} root must be an object")
    return value


def load_policy(path: Path) -> dict[str, Any]:
    value = _load_object(path, "policy")
    if value.get("schema") != SCHEMA:
        raise PolicyError(f"schema must be {SCHEMA}")
    repository = value.get("repository")
    if not isinstance(repository, str) or REPOSITORY_RE.fullmatch(repository) is None:
        raise PolicyError("repository must be OWNER/REPOSITORY")
    if value.get("private") is not True:
        raise PolicyError("private must be true")
    default_branch = value.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise PolicyError("default_branch must be a non-empty string")
    workflow = value.get("workflow")
    if not isinstance(workflow, str) or not workflow.startswith(".github/workflows/"):
        raise PolicyError("workflow must be under .github/workflows/")
    if Path(workflow).is_absolute() or ".." in Path(workflow).parts:
        raise PolicyError("workflow must be a safe repository-relative path")
    jobs = value.get("required_jobs")
    if not isinstance(jobs, list) or not jobs or not all(
        isinstance(job, str) and job for job in jobs
    ):
        raise PolicyError("required_jobs must be a non-empty string array")
    verification = value.get("local_verification")
    if not isinstance(verification, list) or not verification or not all(
        isinstance(part, str) and part for part in verification
    ):
        raise PolicyError("local_verification must be a non-empty argv array")
    pull_request_mode = value.get("pull_request_mode", "draft-first")
    if not isinstance(pull_request_mode, str) or pull_request_mode not in PULL_REQUEST_TYPES:
        allowed = ", ".join(sorted(PULL_REQUEST_TYPES))
        raise PolicyError(f"pull_request_mode must be one of: {allowed}")
    value["pull_request_mode"] = pull_request_mode
    return value


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _section(lines: list[str], key: str, indent: int = 0) -> list[str]:
    start: int | None = None
    prefix = " " * indent
    for index, raw in enumerate(lines):
        line = _strip_comment(raw)
        match = KEY_RE.match(line)
        if match and len(match.group("indent")) == indent and match.group("key") == key:
            if match.group("value").strip() not in {"", "{}"}:
                raise PolicyError(f"{key} must use an expanded mapping")
            start = index + 1
            break
    if start is None:
        raise PolicyError(f"missing {key} section")
    result: list[str] = []
    for raw in lines[start:]:
        line = _strip_comment(raw)
        if not line.strip():
            result.append(raw)
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent:
            break
        result.append(raw)
    return result


def _mapping_keys(lines: list[str], indent: int) -> set[str]:
    result: set[str] = set()
    for raw in lines:
        match = KEY_RE.match(_strip_comment(raw))
        if match and len(match.group("indent")) == indent:
            result.add(match.group("key"))
    return result


def _list_values(lines: list[str], key: str, indent: int) -> list[str]:
    for index, raw in enumerate(lines):
        line = _strip_comment(raw)
        match = KEY_RE.match(line)
        if not match or len(match.group("indent")) != indent or match.group("key") != key:
            continue
        inline = match.group("value").strip()
        if inline:
            if not (inline.startswith("[") and inline.endswith("]")):
                raise PolicyError(f"{key} must be a YAML list")
            return [part.strip().strip("'\"") for part in inline[1:-1].split(",") if part.strip()]
        values: list[str] = []
        for child in lines[index + 1 :]:
            clean = _strip_comment(child)
            if not clean.strip():
                continue
            child_indent = len(clean) - len(clean.lstrip())
            if child_indent <= indent:
                break
            item = clean.strip()
            if not item.startswith("- "):
                raise PolicyError(f"{key} must contain scalar list items")
            values.append(item[2:].strip().strip("'\""))
        return values
    raise PolicyError(f"missing {key}")


def evaluate_workflow(policy: dict[str, Any], workflow_text: str) -> list[str]:
    lines = workflow_text.splitlines()
    on_lines = _section(lines, "on")
    events = _mapping_keys(on_lines, 2)
    required_events = {"pull_request", "push", "workflow_dispatch"}
    if not required_events.issubset(events):
        raise PolicyError(
            "on must include pull_request, push, and workflow_dispatch"
        )

    pull_lines = _section(on_lines, "pull_request", 2)
    pull_types = set(_list_values(pull_lines, "types", 4))
    pull_request_mode = policy.get("pull_request_mode", "draft-first")
    if not isinstance(pull_request_mode, str):
        raise PolicyError("pull_request_mode must be a string")
    required_pull_types = PULL_REQUEST_TYPES.get(pull_request_mode)
    if required_pull_types is None:
        raise PolicyError(f"unsupported pull_request_mode: {pull_request_mode}")
    if pull_types != required_pull_types:
        expected = ", ".join(sorted(required_pull_types))
        raise PolicyError(
            f"pull_request.types for {pull_request_mode} must contain exactly: {expected}"
        )

    push_lines = _section(on_lines, "push", 2)
    branches = _list_values(push_lines, "branches", 4)
    if branches != [policy["default_branch"]]:
        raise PolicyError("push.branches must contain only the default branch")

    concurrency = _section(lines, "concurrency")
    concurrency_text = "\n".join(_strip_comment(line).strip() for line in concurrency)
    if "group:" not in concurrency_text:
        raise PolicyError("concurrency.group is required")
    if re.search(r"^cancel-in-progress:\s*true$", concurrency_text, re.MULTILINE) is None:
        raise PolicyError("concurrency.cancel-in-progress must be true")

    jobs_lines = _section(lines, "jobs")
    job_names = _mapping_keys(jobs_lines, 2)
    missing_jobs = sorted(set(policy["required_jobs"]) - job_names)
    if missing_jobs:
        raise PolicyError(f"missing required jobs: {', '.join(missing_jobs)}")

    unpinned: list[str] = []
    for number, raw in enumerate(lines, 1):
        match = re.search(r"\buses:\s*([^\s#]+)", raw)
        if match is None:
            continue
        value = match.group(1).strip("'\"")
        if value.startswith("./") or value.startswith("docker://"):
            continue
        if "@" not in value or SHA_RE.fullmatch(value.rsplit("@", 1)[1]) is None:
            unpinned.append(f"line {number}: {value}")
    if unpinned:
        raise PolicyError("actions must use immutable SHAs: " + "; ".join(unpinned))

    return [
        f"repository={policy['repository']}",
        f"workflow={policy['workflow']}",
        f"pull_request_mode={pull_request_mode}",
        f"required_jobs={','.join(policy['required_jobs'])}",
    ]


def check(repo_root: Path, policy_path: Path) -> list[str]:
    root = repo_root.resolve()
    policy = load_policy(policy_path)
    workflow_path = (root / policy["workflow"]).resolve()
    try:
        workflow_path.relative_to(root)
    except ValueError as error:
        raise PolicyError("workflow resolves outside repository") from error
    try:
        workflow_text = workflow_path.read_text(encoding="utf-8")
    except OSError as error:
        raise PolicyError(f"unreadable workflow: {error}") from error
    return evaluate_workflow(policy, workflow_text)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    checker = subparsers.add_parser("check")
    checker.add_argument("--repo-root", type=Path, required=True)
    checker.add_argument("--policy", type=Path)
    args = parser.parse_args()

    policy_path = args.policy or args.repo_root / ".github-delivery" / "ci-policy.json"
    try:
        details = check(args.repo_root, policy_path)
    except PolicyError as error:
        print(f"BLOCK workflow-policy:{error}", file=sys.stderr)
        return 1
    print("ALLOW workflow-policy " + " ".join(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
