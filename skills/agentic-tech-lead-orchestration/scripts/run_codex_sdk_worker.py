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
from pathlib import Path
from typing import Any

TERMINAL_STATES = {"completed", "failed", "interrupted"}
FORBIDDEN_KEY_FRAGMENTS = ("api_key", "apikey", "access_token", "refresh_token", "credential", "secret")
THREAD_POLICIES = {"new", "resume-compatible"}


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

    if len(data["base_sha"]) < 7 or len(data["tree_sha"]) < 7:
        raise ContractError("base_sha/tree_sha must identify immutable git subjects")

    for field in ("allowed_paths", "read_only_paths", "predecessor_receipts"):
        if not isinstance(data[field], list) or not all(isinstance(x, str) and x for x in data[field]):
            raise ContractError(f"{field} must be a list of non-empty strings")

    overlap = sorted(set(data["allowed_paths"]) & set(data["read_only_paths"]))
    if overlap:
        raise ContractError(f"writable/read-only lease overlap: {overlap}")

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
        "tree_sha": data["tree_sha"],
        "worktree": data["worktree"],
        "prompt_digest": data["prompt_digest"],
        "thread_policy": data["thread_policy"],
        "thread_id": data.get("resume_thread_id"),
        "adapter_state": "STATIC_VALIDATED",
        "sdk_execution": "NOT_EXERCISED",
        "controller_readback_required": True,
        "evidence_ceiling": "STATIC_CONTRACT_ONLY",
    }


def _status_value(status: Any) -> str:
    return str(getattr(status, "value", status)).lower()


def execute(data: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(data)

    worktree = Path(data["worktree"]).resolve()
    if not worktree.is_dir():
        raise ContractError(f"worktree does not exist: {worktree}")

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
        thread_id = getattr(thread, "id", None)
        if not thread_id:
            try:
                thread_id = getattr(thread.read(), "id", None)
            except Exception:
                thread_id = None

    return {
        "schema_version": 1,
        "task_id": data["task_id"],
        "attempt_id": data["attempt_id"],
        "repo": data["repo"],
        "base_sha": data["base_sha"],
        "tree_sha": data["tree_sha"],
        "worktree": str(worktree),
        "prompt_digest": data["prompt_digest"],
        "thread_policy": data["thread_policy"],
        "thread_id": thread_id,
        "turn_id": getattr(result, "id", None),
        "turn_status": status,
        "adapter_state": "RUNTIME_RETURNED" if status in TERMINAL_STATES else "RUNTIME_NONTERMINAL",
        "sdk_execution": "EXERCISED",
        "controller_readback_required": True,
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
