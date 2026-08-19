#!/usr/bin/env python3
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
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

print("herdr-lifecycle selftest: PASS (positive=2 mutations=7 live=NOT_EXERCISED)")
