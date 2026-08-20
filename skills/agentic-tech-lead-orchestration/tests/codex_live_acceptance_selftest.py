#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "compile_codex_live_acceptance.py"
spec = importlib.util.spec_from_file_location("live", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
H64 = "c" * 64


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        env=env,
    ).strip()


def snapshot_tree(repo: Path, base_sha: str) -> str:
    with tempfile.TemporaryDirectory(prefix="codex-live-selftest-index-") as td:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(td) / "index")
        subprocess.run(["git", "-C", str(repo), "read-tree", base_sha], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "add", "-A", "--", "."], check=True, env=env)
        return git(repo, "write-tree", env=env)


with tempfile.TemporaryDirectory(prefix="codex-live-acceptance-") as td:
    repo = Path(td)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "fixture"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
    (repo / "src").mkdir()
    (repo / "src/a.py").write_text("VALUE = 0\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "src/a.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    base_sha = git(repo, "rev-parse", "HEAD")
    base_tree = git(repo, "rev-parse", "HEAD^{tree}")

    (repo / "src/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    result_tree = snapshot_tree(repo, base_sha)

    def packet():
        worker = {
            "task_id": "T1",
            "attempt_id": "A1",
            "repo": "ed3c/skills-shared",
            "base_sha": base_sha,
            "base_tree_sha": base_tree,
            "tree_sha": result_tree,
            "worktree": str(repo),
            "prompt_digest": H64,
            "adapter_state": "RUNTIME_RETURNED",
            "sdk_execution": "EXERCISED",
            "controller_readback_required": True,
            "lease_readback": "PASS",
            "changed_files": ["src/a.py"],
            "turn_status": "completed",
            "thread_id": "thread-1",
            "final_response_digest": "d" * 64,
        }
        controller = {
            "task_id": "T1",
            "attempt_id": "A1",
            "repo": "ed3c/skills-shared",
            "base_sha": base_sha,
            "tree_sha": result_tree,
            "changed_files": ["src/a.py"],
            "source_diff_readback": "PASS",
            "tests_readback": "PASS",
            "commands": [
                {
                    "command_sha256": "e" * 64,
                    "exit_code": 0,
                    "output_sha256": "f" * 64,
                }
            ],
        }
        return {"worker_result": worker, "controller": controller}

    receipt = mod.compile_receipt(packet())
    assert receipt["schema_version"] == 2
    assert receipt["base_tree_sha"] == base_tree
    assert receipt["tree_sha"] == result_tree
    assert receipt["result_tree_readback"] == "PASS"
    assert receipt["acceptance_state"] == "LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE"
    assert receipt["shadow_review_required"] is True

    def fail(mutator):
        data = copy.deepcopy(packet())
        mutator(data)
        try:
            mod.compile_receipt(data)
        except mod.ContractError:
            return
        raise AssertionError("mutation passed")

    fail(lambda x: x["worker_result"].update(sdk_execution="NOT_EXERCISED"))
    fail(lambda x: x["worker_result"].update(lease_readback="FAIL"))
    fail(lambda x: x["worker_result"].update(adapter_state="STATIC_VALIDATED"))
    fail(lambda x: x["worker_result"].update(turn_status="failed"))
    fail(lambda x: x["controller"].update(attempt_id="A2"))
    fail(lambda x: x["controller"].update(changed_files=["src/b.py"]))
    fail(lambda x: x["controller"].update(source_diff_readback="FAIL"))
    fail(lambda x: x["controller"].update(tests_readback="FAIL"))
    fail(lambda x: x["controller"].update(commands=[]))
    fail(lambda x: x["controller"]["commands"][0].update(exit_code=1))
    fail(lambda x: x["worker_result"].update(base_sha="abc"))
    fail(lambda x: x["worker_result"].update(final_response="raw model prose"))

    # M13: the exact false-PASS found by the first real #464 run. Worker and
    # controller agree with each other, but their bound result tree is the
    # unchanged pre-turn tree and therefore does not contain the claimed path.
    def missing_claimed_change(x):
        x["worker_result"]["tree_sha"] = base_tree
        x["controller"]["tree_sha"] = base_tree
    fail(missing_claimed_change)

    # M14: a result tree with an additional undeclared change must not pass just
    # because worker/controller repeat the same incomplete changed_files list.
    (repo / "src/b.py").write_text("EXTRA = 1\n", encoding="utf-8")
    extra_tree = snapshot_tree(repo, base_sha)
    def hidden_extra_change(x):
        x["worker_result"]["tree_sha"] = extra_tree
        x["controller"]["tree_sha"] = extra_tree
    fail(hidden_extra_change)
    (repo / "src/b.py").unlink()

    # M15: a syntactically valid SHA that is not a present Git object is not an
    # immutable result subject.
    def missing_tree_object(x):
        missing = "1" * 40
        x["worker_result"]["tree_sha"] = missing
        x["controller"]["tree_sha"] = missing
    fail(missing_tree_object)

    # M16: the base commit and declared base tree must also agree; otherwise the
    # result comparison has no reproducible pre-turn denominator.
    fail(lambda x: x["worker_result"].update(base_tree_sha="2" * 40))

print("codex-live-acceptance selftest: PASS (positive=1 mutations=16 live=NOT_EXERCISED)")
