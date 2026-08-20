#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile

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
assert r["lease_readback"] == "NOT_EXERCISED"
assert r["base_tree_sha"] == m["tree_sha"] == r["tree_sha"]
assert "final_response" not in r

must_fail(lambda d: d.update(base_sha="85e6723"))
must_fail(lambda d: d.update(tree_sha="not-a-40-hex-subject"))
must_fail(lambda d: d.update(prompt_digest="0" * 64))
must_fail(lambda d: d["read_only_paths"].append(d["allowed_paths"][0]))
must_fail(lambda d: d["read_only_paths"].append("skills/agentic-tech-lead-orchestration/scripts/private.py"))
must_fail(lambda d: d["allowed_paths"].append("../outside-repo"))
must_fail(lambda d: d.update(api_key="sk-should-never-be-here"))
must_fail(lambda d: d.update(thread_policy="resume-compatible"))
must_fail(lambda d: d.update(resume_thread_id="thread-x"))
must_fail(lambda d: d.pop("attempt_id"))

resume = base_manifest()
resume["thread_policy"] = "resume-compatible"
resume["resume_thread_id"] = "thread_123"
mod.validate_manifest(resume)

mod._assert_lease_readback(m, ["skills/agentic-tech-lead-orchestration/scripts/new.py"])
try:
    mod._assert_lease_readback(m, ["skills/agentic-tech-lead-orchestration/README.md"])
except mod.ContractError:
    pass
else:
    raise AssertionError("read-only mutation unexpectedly passed")
try:
    mod._assert_lease_readback(m, ["docs/outside.md"])
except mod.ContractError:
    pass
else:
    raise AssertionError("out-of-lease mutation unexpectedly passed")

with tempfile.TemporaryDirectory() as td:
    repo = Path(td)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "fixture"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
    subject = copy.deepcopy(m)
    subject["worktree"] = str(repo)
    subject["base_sha"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    subject["tree_sha"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True).strip()
    mod._validate_worktree_subject(repo, subject)

    # The live adapter snapshots post-turn bytes through a private temporary
    # index. The normal branch/index remain untouched; only an immutable tree
    # object is produced for later controller/binder readback.
    (repo / "a.txt").write_text("b\n", encoding="utf-8")
    result_tree = mod._materialize_result_tree(repo, subject["base_sha"], ["a.txt"])
    assert result_tree != subject["tree_sha"]
    assert mod._tree_changed_paths(repo, subject["base_sha"], result_tree) == ["a.txt"]
    assert subprocess.check_output(["git", "-C", str(repo), "diff", "--cached", "--name-only"], text=True).strip() == ""

    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    (repo / "outside.txt").write_text("x\n", encoding="utf-8")
    try:
        mod._validate_worktree_subject(repo, subject)
    except mod.ContractError:
        pass
    else:
        raise AssertionError("dirty worktree unexpectedly passed")

print("codex-sdk-controller selftest: PASS (positive=4 mutations=14 live=NOT_EXERCISED)")
