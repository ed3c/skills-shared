#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "herdr_runtime_observer.py"
spec = importlib.util.spec_from_file_location("herdr_observer", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

NOW = 2_000_000_000
STARTED = 1_999_999_000
BASE = "85e6723869bdd545666e07b7c5c6a8f491256cb9"
TREE = "0123456789abcdef0123456789abcdef01234567"


def manifest():
    return {
        "task_id": "issue-377/T1",
        "attempt_id": "a01",
        "repo": "ed3c/skills-shared",
        "base_sha": BASE,
        "tree_sha": TREE,
        "worktree": "/tmp/wt",
        "target": "worker-377",
        "max_observation_age_seconds": 120,
        "expected_pane_id": "w1:p3",
        "expected_workspace_id": "w1",
        "expected_process_id": 123,
        "expected_process_started_at_unix": STARTED,
        "expected_agent_session_id": "codex-thread-1",
        "require_foreground_cwd": True,
        "require_process_liveness": True,
        "require_clean_terminal": True,
    }


def running_agent():
    return {
        "result": {
            "agent": {
                "state": "working",
                "pane_id": "w1:p3",
                "workspace_id": "w1",
                "pid": 123,
                "process_alive": True,
                "process_started_at_unix": STARTED,
                "foreground_cwd": "/tmp/wt",
                "agent_session": {
                    "source": "herdr:codex",
                    "kind": "id",
                    "value": "codex-thread-1",
                },
            }
        }
    }


def running_explain():
    return {"result": {"final_state": "working", "observed_at_unix": NOW - 10}}


def done_agent():
    value = running_agent()
    value["result"]["agent"].update(
        state="done", process_alive=False, cleanup_state="clean", residue_count=0
    )
    return value


def done_explain():
    return {
        "result": {
            "final_state": "done",
            "observed_at_unix": NOW - 5,
            "cleanup_state": "clean",
            "residue_count": 0,
        }
    }


# positive=4
m = manifest()
mod.validate_manifest(m)
fallback = mod.fallback_receipt(m)
assert fallback["observer_state"] == "UNAVAILABLE_FALLBACK"
assert fallback["authoritative"] is False

running = mod.reduce_observation(m, running_agent(), running_explain(), now_unix=NOW)
assert running["observer_state"] == "RUNNING"
assert running["process_alive"] is True
assert running["observation_age_seconds"] == 10
assert running["process_started_at_unix"] == STARTED

done = mod.reduce_observation(m, done_agent(), done_explain(), now_unix=NOW)
assert done["observer_state"] == "DONE_CANDIDATE"
assert done["cleanup_state"] == "CLEAN" and done["residue_count"] == 0
assert done["authoritative"] is False and done["controller_readback_required"] is True
assert "transcript" not in done


def manifest_must_fail(mutator):
    data = copy.deepcopy(manifest())
    mutator(data)
    try:
        mod.validate_manifest(data)
    except mod.ContractError:
        return
    raise AssertionError("manifest mutation unexpectedly passed")


# 8 manifest mutations
manifest_must_fail(lambda d: d.update(authoritative=True))
manifest_must_fail(lambda d: d.update(access_token="nope"))
manifest_must_fail(lambda d: d.update(transcript="terminal bytes"))
manifest_must_fail(lambda d: d.pop("attempt_id"))
manifest_must_fail(lambda d: d.update(require_foreground_cwd="yes"))
manifest_must_fail(lambda d: d.update(base_sha="85e6723"))
manifest_must_fail(lambda d: d.update(tree_sha="85e6723"))
manifest_must_fail(lambda d: d.update(max_observation_age_seconds=0))


def observation_must_fail(*, mutate_agent=None, mutate_explain=None, mutate_manifest=None):
    agent = running_agent()
    explain = running_explain()
    data = manifest()
    if mutate_agent:
        mutate_agent(agent)
    if mutate_explain:
        mutate_explain(explain)
    if mutate_manifest:
        mutate_manifest(data)
    try:
        mod.reduce_observation(data, agent, explain, now_unix=NOW)
    except mod.ContractError:
        return
    raise AssertionError("observation mutation unexpectedly passed")


# 10 observation mutations: total mutations=18
observation_must_fail(mutate_manifest=lambda d: d.update(expected_pane_id="w9:p9"))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].update(foreground_cwd="/tmp/other"))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].pop("foreground_cwd"))
observation_must_fail(mutate_manifest=lambda d: d.update(expected_agent_session_id="wrong-thread"))
observation_must_fail(mutate_manifest=lambda d: d.update(expected_process_started_at_unix=STARTED + 1))
observation_must_fail(mutate_explain=lambda e: e["result"].update(observed_at_unix=NOW - 121))
observation_must_fail(mutate_explain=lambda e: e["result"].update(observed_at_unix=NOW + 1))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].update(process_alive=False))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].pop("process_alive"))

try:
    dirty_explain = done_explain()
    dirty_explain["result"].update(cleanup_state="dirty", residue_count=1)
    mod.reduce_observation(manifest(), done_agent(), dirty_explain, now_unix=NOW)
except mod.ContractError:
    pass
else:
    raise AssertionError("terminal residue mutation unexpectedly passed")

print("herdr-observer selftest: PASS (positive=4 mutations=18 live=NOT_EXERCISED)")
