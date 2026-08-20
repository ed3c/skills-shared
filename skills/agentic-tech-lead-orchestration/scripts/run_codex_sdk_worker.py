#!/usr/bin/env python3
"""Codex SDK worker adapter for agentic-tech-lead-orchestration.

Static validation is dependency-free. Live execution requires `openai-codex`
and reuses the user's existing Codex authentication; this adapter never reads
or persists API keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

TERMINAL_STATES = {"completed", "failed", "interrupted"}
FORBIDDEN_KEY_FRAGMENTS = ("api_key", "apikey", "access_token", "refresh_token", "credential", "secret")
THREAD_POLICIES = {"new", "resume-compatible"}
EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")


class ContractError(ValueError):
    pass


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _walk_keys(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            full = f"{prefix}.{key}" if prefix else str(key)
            yield full.lower()
            yield from _walk_keys(item, full)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            yield from _walk_keys(item, f"{prefix}[{idx}]")


def _repo_path(value: str) -> PurePosixPath:
    raw = value.replace("\\", "/").strip()
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise ContractError(f"lease path must stay repository-relative: {value!r}")
    parts = tuple(part for part in path.parts if part not in (".", ""))
    if not parts:
        raise ContractError(f"lease path must not be empty: {value!r}")
    return PurePosixPath(*parts)


def _paths_overlap(left: str, right: str) -> bool:
    a = _repo_path(left).parts
    b = _repo_path(right).parts
    shorter = min(len(a), len(b))
    return a[:shorter] == b[:shorter]


def _path_within(candidate: str, lease: str) -> bool:
    c = _repo_path(candidate).parts
    l = _repo_path(lease).parts
    return len(c) >= len(l) and c[: len(l)] == l


def _git(
    worktree: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        ["git", "-C", str(worktree), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ContractError(f"git {' '.join(args)} failed: {detail or result.returncode}")
    return result.stdout.strip()


def _validate_worktree_subject(worktree: Path, data: dict[str, Any]) -> None:
    if not worktree.is_dir():
        raise ContractError(f"worktree does not exist: {worktree}")
    if _git(worktree, "rev-parse", "--is-inside-work-tree") != "true":
        raise ContractError("worktree is not a Git worktree")
    head = _git(worktree, "rev-parse", "HEAD")
    tree = _git(worktree, "rev-parse", "HEAD^{tree}")
    if head != data["base_sha"]:
        raise ContractError(f"worktree HEAD drifted: expected {data['base_sha']} observed {head}")
    if tree != data["tree_sha"]:
        raise ContractError(f"worktree tree drifted: expected {data['tree_sha']} observed {tree}")
    if _git(worktree, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ContractError("worktree must be clean before Codex execution")


def _changed_paths(worktree: Path) -> list[str]:
    paths: set[str] = set()
    commands = (
        ("diff", "--name-only", "-z", "HEAD"),
        ("diff", "--cached", "--name-only", "-z", "HEAD"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    )
    for args in commands:
        raw = _git(worktree, *args)
        if not raw:
            continue
        for path in raw.split("\0"):
            if path:
                paths.add(_repo_path(path).as_posix())
    return sorted(paths)


def _tree_changed_paths(worktree: Path, base_sha: str, tree_sha: str) -> list[str]:
    raw = _git(
        worktree,
        "diff",
        "--name-only",
        "-z",
        "--no-renames",
        base_sha,
        tree_sha,
        "--",
    )
    return sorted(_repo_path(path).as_posix() for path in raw.split("\0") if path)


def _materialize_result_tree(
    worktree: Path,
    base_sha: str,
    expected_changed_paths: list[str],
) -> str:
    """Write post-turn worktree bytes as an immutable detached Git tree.

    The normal branch and index are not changed. A private temporary index is
    seeded from the frozen base commit, updated from the current worktree, and
    written as a Git tree object. The resulting tree is independently diffed
    against the base commit before it is returned.
    """

    with tempfile.TemporaryDirectory(prefix="codex-result-tree-") as temp_dir:
        index_path = Path(temp_dir) / "index"
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index_path)
        _git(worktree, "read-tree", base_sha, env=env)
        _git(worktree, "add", "-A", "--", ".", env=env)
        tree_sha = _git(worktree, "write-tree", env=env)

    if not EXACT_SHA.fullmatch(tree_sha):
        raise ContractError("post-turn result tree must be exact 40-hex Git tree")
    observed = _tree_changed_paths(worktree, base_sha, tree_sha)
    if observed != sorted(expected_changed_paths):
        raise ContractError(
            f"post-turn result-tree denominator mismatch: expected {sorted(expected_changed_paths)} observed {observed}"
        )
    return tree_sha


def _assert_lease_readback(data: dict[str, Any], changed_paths: list[str]) -> None:
    for path in changed_paths:
        if any(_path_within(path, ro) for ro in data["read_only_paths"]):
            raise ContractError(f"read-only path changed: {path}")
        if not any(_path_within(path, allowed) for allowed in data["allowed_paths"]):
            raise ContractError(f"out-of-lease path changed: {path}")


def validate_manifest(data: dict[str, Any]) -> None:
    required = {
        "task_id", "attempt_id", "repo", "base_sha", "tree_sha", "worktree",
        "allowed_paths", "read_only_paths", "prompt", "prompt_digest",
        "predecessor_receipts", "thread_policy",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ContractError(f"missing required fields: {', '.join(missing)}")

    for field in ("task_id", "attempt_id", "repo", "base_sha", "tree_sha", "worktree", "prompt"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ContractError(f"{field} must be a non-empty string")

    if not EXACT_SHA.fullmatch(data["base_sha"]) or not EXACT_SHA.fullmatch(data["tree_sha"]):
        raise ContractError("base_sha/tree_sha must be exact 40-hex immutable git subjects")

    for field in ("allowed_paths", "read_only_paths", "predecessor_receipts"):
        if not isinstance(data[field], list) or not all(isinstance(x, str) and x for x in data[field]):
            raise ContractError(f"{field} must be a list of non-empty strings")

    for path in [*data["allowed_paths"], *data["read_only_paths"]]:
        _repo_path(path)
    overlaps = sorted(
        f"{allowed} <-> {readonly}"
        for allowed in data["allowed_paths"]
        for readonly in data["read_only_paths"]
        if _paths_overlap(allowed, readonly)
    )
    if overlaps:
        raise ContractError(f"writable/read-only lease overlap: {overlaps}")

    if data["prompt_digest"] != _digest(data["prompt"]):
        raise ContractError("prompt_digest does not match prompt bytes")

    policy = data["thread_policy"]
    if policy not in THREAD_POLICIES:
        raise ContractError(f"unsupported thread_policy: {policy}")
    resume_id = data.get("resume_thread_id")
    if policy == "new" and resume_id:
        raise ContractError("new thread policy cannot carry resume_thread_id")
    if policy == "resume-compatible" and (not isinstance(resume_id, str) or not resume_id):
        raise ContractError("resume-compatible requires resume_thread_id")

    for key in _walk_keys(data):
        leaf = key.rsplit(".", 1)[-1].replace("-", "_")
        if any(fragment in leaf for fragment in FORBIDDEN_KEY_FRAGMENTS):
            raise ContractError(f"credential-bearing field is forbidden: {key}")

    if data.get("final_response") is not None or data.get("reasoning") is not None:
        raise ContractError("model prose/private reasoning must not be durable manifest state")


def compile_static_receipt(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)
    return {
        "schema_version": 1,
        "task_id": data["task_id"],
        "attempt_id": data["attempt_id"],
        "repo": data["repo"],
        "base_sha": data["base_sha"],
        "base_tree_sha": data["tree_sha"],
        "tree_sha": data["tree_sha"],
        "worktree": data["worktree"],
        "prompt_digest": data["prompt_digest"],
        "thread_policy": data["thread_policy"],
        "thread_id": data.get("resume_thread_id"),
        "adapter_state": "STATIC_VALIDATED",
        "sdk_execution": "NOT_EXERCISED",
        "controller_readback_required": True,
        "lease_readback": "NOT_EXERCISED",
        "evidence_ceiling": "STATIC_CONTRACT_ONLY",
    }


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status)).lower()


def execute(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)

    worktree = Path(data["worktree"]).resolve()
    _validate_worktree_subject(worktree, data)

    # Import only on the live path so static validation has no SDK dependency.
    from openai_codex import Codex, Sandbox  # type: ignore

    with Codex() as codex:
        account = codex.account(refresh_token=False)
        account_obj = getattr(account, "account", account)
        if account_obj is None:
            raise ContractError("no existing Codex authentication; sign in with ChatGPT before execution")

        if data["thread_policy"] == "resume-compatible":
            thread = codex.thread_resume(
                data["resume_thread_id"],
                cwd=str(worktree),
                sandbox=Sandbox.workspace_write,
            )
        else:
            thread = codex.thread_start(
                cwd=str(worktree),
                sandbox=Sandbox.workspace_write,
                ephemeral=False,
            )

        result = thread.run(
            data["prompt"],
            cwd=str(worktree),
            sandbox=Sandbox.workspace_write,
            output_schema=data.get("output_schema"),
        )
        status = _status_value(result.status)
        thread_id = thread.id

    changed_paths = _changed_paths(worktree)
    _assert_lease_readback(data, changed_paths)
    result_tree_sha = _materialize_result_tree(worktree, data["base_sha"], changed_paths)

    return {
        "schema_version": 1,
        "task_id": data["task_id"],
        "attempt_id": data["attempt_id"],
        "repo": data["repo"],
        "base_sha": data["base_sha"],
        "base_tree_sha": data["tree_sha"],
        "tree_sha": result_tree_sha,
        "worktree": str(worktree),
        "prompt_digest": data["prompt_digest"],
        "thread_policy": data["thread_policy"],
        "thread_id": thread_id,
        "turn_id": getattr(result, "id", None),
        "turn_status": status,
        "adapter_state": "RUNTIME_RETURNED" if status in TERMINAL_STATES else "RUNTIME_NONTERMINAL",
        "sdk_execution": "EXERCISED",
        "controller_readback_required": True,
        "lease_readback": "PASS",
        "changed_files": changed_paths,
        "final_response_digest": _digest(result.final_response) if result.final_response else None,
        "evidence_ceiling": "RUNTIME_RESULT_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--execute", action="store_true", help="invoke openai-codex using existing Codex auth")
    parser.add_argument("--output")
    args = parser.parse_args()

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    receipt = execute(data) if args.execute else compile_static_receipt(data)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
