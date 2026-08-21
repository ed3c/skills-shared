#!/usr/bin/env python3
"""Shared deterministic fixture for the Codex v2 carrier/provenance controls (#508).

Builds a real throwaway Git repository, materializes a post-turn result tree the
same way `run_codex_sdk_worker.py` does, publishes a durable carrier, and
assembles a schema-shaped worker result. No Codex, no network, no auth.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
ADAPTER = SCRIPTS / "run_codex_sdk_worker.py"

sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, env=env).strip()


def init_repo(repo: Path) -> tuple[str, str]:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "fixture"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src/a.py").write_text("VALUE = 0\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    return git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "HEAD^{tree}")


def snapshot_tree(repo: Path, base_sha: str) -> str:
    """Same private-index materialization the live adapter performs."""
    env = os.environ.copy()
    index = repo.parent / f".fixture-index-{os.getpid()}"
    env["GIT_INDEX_FILE"] = str(index)
    try:
        subprocess.run(["git", "-C", str(repo), "read-tree", base_sha], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "add", "-A", "--", "."], check=True, env=env)
        return git(repo, "write-tree", env=env)
    finally:
        if index.exists():
            index.unlink()


def fake_sdk(root: Path) -> tuple[str, str, str]:
    """A bundled-executable SDK layout: <site-packages>/openai_codex/bin/codex."""
    module_dir = root / "site-packages" / "openai_codex"
    (module_dir / "bin").mkdir(parents=True, exist_ok=True)
    binary = module_dir / "bin" / "codex"
    binary.write_bytes(b"#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    return str(module_dir), str(binary), sha256_file(binary)


def executor_provenance(root: Path) -> dict[str, Any]:
    module_dir, binary, binary_sha = fake_sdk(root)
    return {
        "adapter_version": "codex-sdk-worker/2",
        "adapter_blob_sha256": sha256_file(ADAPTER),
        "sdk_package": "openai-codex",
        "sdk_version": "0.5.1",
        "sdk_module_dir": module_dir,
        "codex_binary_source": "SDK_BUNDLED",
        "codex_binary_path": binary,
        "codex_binary_sha256": binary_sha,
        "runtime_python": "3.14.6",
        "runtime_platform": "darwin-arm64",
        "harness": "codex-sdk-worker",
        "model": "SDK_DEFAULT",
        "config_identity": "b" * 64,
        "sandbox_policy": "workspace-write",
        "approval_policy": "SDK_DEFAULT",
    }


def build_case(root: Path, *, task_id: str = "issue-508/T1", attempt_id: str = "a01") -> dict[str, Any]:
    """Materialize repo + result tree + durable carrier + worker result."""
    carrier = load("codex_result_carrier")
    repo = root / "origin"
    base_sha, base_tree = init_repo(repo)
    (repo / "src/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    result_tree = snapshot_tree(repo, base_sha)

    out_dir = root / "carrier"
    carrier_id = carrier.carrier_id_for(task_id, attempt_id)
    manifest = carrier.create_carrier(
        repo,
        repo="ed3c/skills-shared",
        base_sha=base_sha,
        base_tree_sha=base_tree,
        result_tree_sha=result_tree,
        changed_paths=["src/a.py"],
        out_dir=out_dir,
        carrier_id=carrier_id,
    )
    worker_result = {
        "schema_version": 2,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "repo": "ed3c/skills-shared",
        "base_sha": base_sha,
        "base_tree_sha": base_tree,
        "tree_sha": result_tree,
        "worktree": str(repo),
        "prompt_digest": "c" * 64,
        "thread_policy": "new",
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "turn_status": "completed",
        "adapter_state": "RUNTIME_RETURNED",
        "sdk_execution": "EXERCISED",
        "controller_readback_required": True,
        "lease_readback": "PASS",
        "changed_files": ["src/a.py"],
        "final_response_digest": "d" * 64,
        "executor_provenance": executor_provenance(root),
        "result_carrier": manifest,
        "evidence_ceiling": "RUNTIME_RESULT_ONLY",
    }
    return {
        "repo": repo,
        "base_sha": base_sha,
        "base_tree": base_tree,
        "result_tree": result_tree,
        "carrier_dir": out_dir,
        "bundle_path": out_dir / manifest["bundle_filename"],
        "manifest": manifest,
        "worker_result": worker_result,
    }


def controller_for(worker_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": worker_result["task_id"],
        "attempt_id": worker_result["attempt_id"],
        "repo": worker_result["repo"],
        "base_sha": worker_result["base_sha"],
        "tree_sha": worker_result["tree_sha"],
        "changed_files": list(worker_result["changed_files"]),
        "source_diff_readback": "PASS",
        "tests_readback": "PASS",
        "commands": [{"command_sha256": "e" * 64, "exit_code": 0, "output_sha256": "f" * 64}],
    }
