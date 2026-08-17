#!/usr/bin/env python3
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lifecycle", ROOT / "scripts" / "assert_scheduler_lifecycle.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)

H40 = "a" * 40
D64 = "b" * 64

BASE = {
    "schema": "agentic-tech-lead/scheduler-lifecycle/v1",
    "repository": {"id": "example/repo", "commit": H40, "tree": "c" * 40},
    "task_graph_digest": D64,
    "attempts": [
        {"task_id": "task-a", "attempt_id": "a1", "parent_attempt_id": None, "state": "SUPERSEDED", "budget": 10, "consumed": 4, "worktree": "/tmp/a1", "head": H40},
        {"task_id": "task-a", "attempt_id": "a2", "parent_attempt_id": "a1", "state": "INTEGRATED", "budget": 10, "consumed": 7, "worktree": "/tmp/a2", "head": "d" * 40},
        {"task_id": "task-b", "attempt_id": "b1", "parent_attempt_id": None, "state": "RUNNING", "budget": 10, "consumed": 3, "worktree": "/tmp/b1", "head": "e" * 40}
    ],
    "leases": [
        {"attempt_id": "a2", "resource": "src/a", "active": False, "expires_at": 100},
        {"attempt_id": "b1", "resource": "src/b", "active": True, "expires_at": 100}
    ],
    "checkpoints": [
        {"attempt_id": "a1", "checkpoint_id": "cp-a1", "artifact_digest": "f" * 64},
        {"attempt_id": "b1", "checkpoint_id": "cp-b1", "artifact_digest": "1" * 64}
    ],
    "results": [
        {"attempt_id": "a1", "result_digest": "2" * 64, "oracle": "PASS", "accepted": False},
        {"attempt_id": "a2", "result_digest": "3" * 64, "oracle": "PASS", "accepted": True}
    ],
    "evidence_state": "NOT_EXERCISED"
}


def rejects(mutator, name):
    doc = copy.deepcopy(BASE)
    mutator(doc)
    try:
        module.validate(doc)
    except module.ContractError:
        return
    raise AssertionError(f"control did not fail: {name}")

receipt = module.validate(copy.deepcopy(BASE))
assert receipt["verdict"] == "PASS"
assert receipt["active_lease_count"] == 1
assert receipt["claims_not_proven"]

rejects(lambda d: d.update(evidence_state="PASS"), "fixture live PASS")
rejects(lambda d: d["attempts"][2].update(consumed=11), "budget overrun")
rejects(lambda d: d["attempts"][1].update(parent_attempt_id="b1"), "cross-task retry")
rejects(lambda d: d["leases"].append({"attempt_id":"a2","resource":"src/b","active":True,"expires_at":100}), "double writer")
rejects(lambda d: d["results"][0].update(accepted=True), "stale result accepted")
rejects(lambda d: d["results"][1].update(oracle="FAIL"), "failed oracle accepted")
rejects(lambda d: d["attempts"][0].update(parent_attempt_id="missing"), "missing parent")

print("scheduler lifecycle planted controls: PASS")
