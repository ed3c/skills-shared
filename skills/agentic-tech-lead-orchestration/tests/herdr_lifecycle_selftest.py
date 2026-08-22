#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCHEMA_PATH = HERE.parent / "references" / "contracts" / "herdr-lifecycle-receipt.schema.json"
QUEUE_PATH = HERE.parent / "runtime-handoff" / "herdr-local-handoff-queue.json"
SCRIPT = HERE.parent / "scripts" / "collect_herdr_lifecycle.py"
spec = importlib.util.spec_from_file_location("life", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

H40 = "a" * 40
T40 = "b" * 40


def plan():
    return {
        "manifest": {
            "task_id": "T1",
            "attempt_id": "A1",
            "repo": "ed3c/skills-shared",
            "base_sha": H40,
            "tree_sha": T40,
            "worktree": "/tmp/wt",
            "target": "worker-1",
        },
        "poll_interval_seconds": 0,
        "max_samples": 3,
        "require_terminal": True,
    }


def sample(state, ts, alive=True, cleanup=None, residue=None):
    return {
        "schema_version": 1,
        "task_id": "T1",
        "attempt_id": "A1",
        "repo": "ed3c/skills-shared",
        "base_sha": H40,
        "tree_sha": T40,
        "worktree": "/tmp/wt",
        "target": "worker-1",
        "pane_id": "p1",
        "workspace_id": "w1",
        "process_id": 12,
        "process_started_at_unix": 100,
        "process_alive": alive,
        "agent_session_id": "s1",
        "source_observed_at_unix": ts,
        "cleanup_state": cleanup,
        "residue_count": residue,
        "observer_state": state,
    }


seq = iter([
    sample("RUNNING", 1000),
    sample("DONE_CANDIDATE", 1001, alive=False, cleanup="CLEAN", residue=0),
])
r = mod.collect(plan(), observer=lambda _: next(seq))
assert r["lifecycle_state"] == "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE"
assert r["sample_count"] == 2

fallback = plan()
fallback["require_terminal"] = False
fb = mod.collect(
    fallback,
    observer=lambda _: {
        "task_id": "T1",
        "attempt_id": "A1",
        "repo": "ed3c/skills-shared",
        "base_sha": H40,
        "tree_sha": T40,
        "worktree": "/tmp/wt",
        "target": "worker-1",
        "observer_state": "UNAVAILABLE_FALLBACK",
    },
)
assert fb["lifecycle_state"] == "UNAVAILABLE_FALLBACK"

# Issue #466 acceptance bullet: the body requires `blocked` to be exercised end
# to end. The observer maps herdr's own `blocked` agent_status to BLOCKED, and
# BLOCKED is nonterminal, so a lifecycle passing through it must still reach the
# terminal branch to be a live candidate.
blocked_seq = iter([
    sample("RUNNING", 1000),
    sample("BLOCKED", 1001),
    sample("DONE_CANDIDATE", 1002, alive=False, cleanup="CLEAN", residue=0),
])
br = mod.collect(plan(), observer=lambda _: next(blocked_seq))
assert br["lifecycle_state"] == "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE"
assert br["sample_count"] == 3 and br["final_observer_state"] == "DONE_CANDIDATE"

# Privacy: the receipt may carry only reduced identity/state/digest fields. The
# real control is additionalProperties:false on the contract, so feed a sample
# carrying terminal text, private reasoning and a credential, and prove none of
# it can reach the emitted receipt.
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
declared = set(schema["properties"])
leaky = sample("DONE_CANDIDATE", 1003, alive=False, cleanup="CLEAN", residue=0)
leaky.update({"screen_text": "$ cat secrets", "transcript": "private reasoning", "api_key": "sk-live-real"})
emitted = mod.collect(plan(), observer=lambda _: leaky)
assert set(emitted) <= declared, sorted(set(emitted) - declared)
serialized = json.dumps(emitted, sort_keys=True)
assert not any(t in serialized for t in ("screen_text", "transcript", "api_key", "sk-live-real"))
Draft202012Validator(schema).validate(emitted)

# Committed-artifact control. The ACTIVE queue item names a receipt path and the
# contract that receipt must satisfy; nothing else in the repository reads
# data/handoff/, which is how a receipt that failed its own declared schema
# stayed committed. Resolve both from the queue rather than hardcoding them, so
# a queue that renames either surface turns this red instead of silently
# validating the wrong pair.
queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
item = next(i for i in queue["items"] if i["id"] == queue["current"]["active_item"])
named_schema = json.loads((ROOT / item["receipt"]["schema"]).read_text(encoding="utf-8"))
assert named_schema["$id"] == schema["$id"], "queue names a different lifecycle contract"
committed = json.loads((ROOT / item["receipt"]["path"]).read_text(encoding="utf-8"))
Draft202012Validator(named_schema).validate(committed)
assert committed["lifecycle_state"] != "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE", (
    "the live lifecycle_state is the queue-plane PASS verdict and may only come from a real run"
)

# The receipt binds to a frozen plan by digest. A receipt describing a different
# subject than the plan it names is the exact drift this binding exists to stop.
plan_path = ROOT / committed["plan"]["path"]
plan_bytes = plan_path.read_bytes()
assert hashlib.sha256(plan_bytes).hexdigest() == committed["plan"]["sha256"], "plan digest drifted"
manifest = json.loads(plan_bytes)["manifest"]
for field in ("task_id", "attempt_id", "repo", "base_sha", "tree_sha", "worktree", "target"):
    assert committed[field] == manifest[field], f"receipt/plan disagree on {field}"


def must_reject(receipt):
    if Draft202012Validator(schema).is_valid(receipt):
        raise AssertionError("receipt mutation passed the contract")


def must_fail(samples, require_terminal=True):
    try:
        mod.validate_sequence(samples, require_terminal=require_terminal)
    except mod.ContractError:
        return
    raise AssertionError("mutation passed")


bad = sample("RUNNING", 1000)
bad["attempt_id"] = "A2"
must_fail([
    sample("RUNNING", 999),
    bad,
    sample("DONE_CANDIDATE", 1001, alive=False, cleanup="CLEAN", residue=0),
])
must_fail([sample("RUNNING", 1000), sample("RUNNING", 999)])
must_fail([sample("RUNNING", 1000, alive=False)])
must_fail([sample("DONE_CANDIDATE", 1000, alive=False, cleanup="DIRTY", residue=1)])
must_fail([sample("RUNNING", 1000)], True)
must_fail([
    sample("DONE_CANDIDATE", 1000, alive=False, cleanup="CLEAN", residue=0),
    sample("RUNNING", 1001),
])
broken = sample("RUNNING", 1000)
broken["observer_state"] = "BROKEN"
must_fail([broken])
must_fail([sample("BLOCKED", 1000, alive=False)])

# Planted receipt mutations: prove the contract turns red on the exact shapes a
# blocked attempt could be laundered into.
leaked = copy.deepcopy(emitted)
leaked["screen_text"] = "$ cat secrets"
must_reject(leaked)
must_reject({**committed, "sample_count": 1})
must_reject({**committed, "sample_digests": ["c" * 64]})
must_reject({k: v for k, v in committed.items() if k != "blockers"})
must_reject({**committed, "lifecycle_state": "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE"})
must_reject({**committed, "evidence_ceiling": "NO_HERDR_OBSERVATION"})

print("herdr-lifecycle selftest: PASS (positive=6 mutations=14 live=NOT_EXERCISED)")
