#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

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

POSITIVE = 0
MUTATIONS = 0
# Negative controls for the two manifest fields the 2026-08-22 amendment added
# (herdr_session, expected_agent_session_source). Counted separately so the
# historical `mutations=` reject denominator stays comparable across attempts.
INPUT_CONTROLS = 0


def positive() -> None:
    global POSITIVE
    POSITIVE += 1


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
                "state_change_seq": 7,
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
    # `state` is herdr's real `agent explain` root key; the former `final_state`
    # resolved to no herdr surface at all (#466).
    return {"result": {"state": "working", "observed_at_unix": NOW - 10}}


def done_agent():
    value = running_agent()
    value["result"]["agent"].update(
        state="done", state_change_seq=8, process_alive=False,
        cleanup_state="clean", residue_count=0
    )
    return value


def done_explain():
    return {
        "result": {
            "state": "done",
            "observed_at_unix": NOW - 5,
            "cleanup_state": "clean",
            "residue_count": 0,
        }
    }


def blocked_agent():
    # herdr's AgentInfo publishes `agent_status`, never `state`. This fixture
    # therefore exercises the agent_status branch of the state mapping.
    value = running_agent()
    agent = value["result"]["agent"]
    agent.pop("state")
    agent["agent_status"] = "blocked"
    agent["state_change_seq"] = 9
    return value


m = manifest()
mod.validate_manifest(m)
positive()

fallback = mod.fallback_receipt(m)
assert fallback["observer_state"] == "UNAVAILABLE_FALLBACK"
assert fallback["authoritative"] is False
positive()

running = mod.reduce_observation(m, running_agent(), running_explain(), now_unix=NOW)
assert running["observer_state"] == "RUNNING"
assert running["process_alive"] is True
assert running["observation_age_seconds"] == 10
assert running["process_started_at_unix"] == STARTED
assert running["observation_time_source"] == "HERDR_SOURCE_CLOCK"
assert running["state_change_seq"] == 7
assert running["agent_session_source"] == "herdr:codex"
positive()

done = mod.reduce_observation(m, done_agent(), done_explain(), now_unix=NOW)
assert done["observer_state"] == "DONE_CANDIDATE"
assert done["cleanup_state"] == "CLEAN" and done["residue_count"] == 0
assert done["authoritative"] is False and done["controller_readback_required"] is True
assert done["cleanup_source"] == "HERDR_PUBLISHED"
assert done["evidence_ceiling"] == "OBSERVER_IDENTITY_FRESHNESS_CLEANUP_WITH_TYPED_AUXILIARY"
assert "transcript" not in done
positive()

# herdr publishes no wall clock, so this leg also pins the OBSERVER_LOCAL_CLOCK
# branch: the observer stamps its own time and the receipt says so.
blocked = mod.reduce_observation(m, blocked_agent(), {"result": {}}, now_unix=NOW)
assert blocked["observer_state"] == "BLOCKED"
assert blocked["raw_state"] == "blocked"
assert blocked["observation_time_source"] == "OBSERVER_LOCAL_CLOCK"
assert blocked["state_change_seq"] == 9
assert blocked["cleanup_source"] == "NOT_OBSERVED"
positive()

# The producer and the frozen contract may not drift.
schema = json.loads(
    (HERE.parent / "references/contracts/herdr-observer-receipt.schema.json").read_text()
)
Draft202012Validator.check_schema(schema)
for receipt in (running, done, blocked, fallback):
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert not errors, [e.message for e in errors]


def manifest_must_fail(mutator):
    global MUTATIONS
    MUTATIONS += 1
    data = copy.deepcopy(manifest())
    mutator(data)
    try:
        mod.validate_manifest(data)
    except mod.ContractError:
        return
    raise AssertionError("manifest mutation unexpectedly passed")


manifest_must_fail(lambda d: d.update(authoritative=True))
manifest_must_fail(lambda d: d.update(access_token="nope"))
manifest_must_fail(lambda d: d.update(transcript="terminal bytes"))
manifest_must_fail(lambda d: d.pop("attempt_id"))
manifest_must_fail(lambda d: d.update(require_foreground_cwd="yes"))
manifest_must_fail(lambda d: d.update(base_sha="85e6723"))
manifest_must_fail(lambda d: d.update(tree_sha="85e6723"))
manifest_must_fail(lambda d: d.update(max_observation_age_seconds=0))


def input_control_must_fail(mutator):
    global INPUT_CONTROLS
    INPUT_CONTROLS += 1
    data = copy.deepcopy(manifest())
    mutator(data)
    try:
        mod.validate_manifest(data)
    except mod.ContractError:
        return
    raise AssertionError("manifest input control unexpectedly passed")


input_control_must_fail(lambda d: d.update(herdr_session=""))
input_control_must_fail(lambda d: d.update(expected_agent_session_source=" "))


def observation_must_fail(*, mutate_agent=None, mutate_explain=None, mutate_manifest=None):
    global MUTATIONS
    MUTATIONS += 1
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


observation_must_fail(mutate_manifest=lambda d: d.update(expected_pane_id="w9:p9"))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].update(foreground_cwd="/tmp/other"))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].pop("foreground_cwd"))
observation_must_fail(mutate_manifest=lambda d: d.update(expected_agent_session_id="wrong-thread"))
observation_must_fail(mutate_manifest=lambda d: d.update(expected_process_started_at_unix=STARTED + 1))
observation_must_fail(mutate_explain=lambda e: e["result"].update(observed_at_unix=NOW - 121))
observation_must_fail(mutate_explain=lambda e: e["result"].update(observed_at_unix=NOW + 1))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].update(process_alive=False))
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].pop("process_alive"))
observation_must_fail(mutate_manifest=lambda d: d.update(expected_process_id=999))
# Mechanical refusal of forbidden promotion manual_report_agent_to_clean_terminal_receipt:
# `herdr pane report-agent` can set state and --seq, so a manifest that expects a
# herdr-managed session source must reject a manually reported agent.
observation_must_fail(mutate_manifest=lambda d: d.update(expected_agent_session_source="herdr:claude"))
# Ordering rests on herdr's own monotonic counter; without it there is no anchor.
observation_must_fail(mutate_agent=lambda a: a["result"]["agent"].pop("state_change_seq"))

MUTATIONS += 1
try:
    dirty_explain = done_explain()
    dirty_explain["result"].update(cleanup_state="dirty", residue_count=1)
    mod.reduce_observation(manifest(), done_agent(), dirty_explain, now_unix=NOW)
except mod.ContractError:
    pass
else:
    raise AssertionError("terminal residue mutation unexpectedly passed")

print(
    f"herdr-observer selftest: PASS (positive={POSITIVE} mutations={MUTATIONS} "
    f"contract_input_controls={INPUT_CONTROLS} live=NOT_EXERCISED)"
)
