#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "run_codex_sdk_worker.py"
spec = importlib.util.spec_from_file_location("codex_adapter", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def base_manifest():
    prompt = "Implement the bounded task. Do not edit read-only paths."
    return {
        "task_id": "issue-375/T1",
        "attempt_id": "a01",
        "repo": "ed3c/skills-shared",
        "base_sha": "85e6723869bdd545666e07b7c5c6a8f491256cb9",
        "tree_sha": "85e6723869bdd545666e07b7c5c6a8f491256cb9",
        "worktree": "/tmp/example",
        "allowed_paths": ["skills/agentic-tech-lead-orchestration/scripts/"],
        "read_only_paths": ["skills/agentic-tech-lead-orchestration/README.md"],
        "prompt": prompt,
        "prompt_digest": hashlib.sha256(prompt.encode()).hexdigest(),
        "predecessor_receipts": [],
        "thread_policy": "new",
    }


def must_fail(mutator):
    data = copy.deepcopy(base_manifest())
    mutator(data)
    try:
        mod.validate_manifest(data)
    except mod.ContractError:
        return
    raise AssertionError("mutation unexpectedly passed")


m = base_manifest()
mod.validate_manifest(m)
r = mod.compile_static_receipt(m)
assert r["sdk_execution"] == "NOT_EXERCISED"
assert r["controller_readback_required"] is True
assert "final_response" not in r

must_fail(lambda d: d.update(prompt_digest="0" * 64))
must_fail(lambda d: d["read_only_paths"].append(d["allowed_paths"][0]))
must_fail(lambda d: d.update(api_key="sk-should-never-be-here"))
must_fail(lambda d: d.update(thread_policy="resume-compatible"))
must_fail(lambda d: d.update(resume_thread_id="thread-x"))
must_fail(lambda d: d.pop("attempt_id"))

resume = base_manifest()
resume["thread_policy"] = "resume-compatible"
resume["resume_thread_id"] = "thread_123"
mod.validate_manifest(resume)

print("codex-sdk-controller selftest: PASS (positive=2 mutations=6 live=NOT_EXERCISED)")
