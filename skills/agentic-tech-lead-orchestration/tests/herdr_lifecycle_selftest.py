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

POSITIVE = 0
MUTATIONS = 0


def positive():
    global POSITIVE
    POSITIVE += 1


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


def sample(state, ts, alive=True, cleanup=None, residue=None, seq=1):
    # The amended (2026-08-22) observer contract types every fact herdr 0.8.0
    # does not publish, and anchors ordering on herdr's own state_change_seq
    # rather than on a herdr clock that does not exist.
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
        "state_change_seq": seq,
        "observation_time_source": "OBSERVER_LOCAL_CLOCK",
        "process_facts_source": "HERDR_PANE_PROCESS_INFO_PLUS_OS_PS",
        "cleanup_source": "OBSERVER_DERIVED_PANE_PROCESS_INFO",
        "cleanup_state": cleanup,
        "residue_count": residue,
        "observer_state": state,
    }


seq_running = iter([
    sample("RUNNING", 1000, seq=1),
    sample("DONE_CANDIDATE", 1001, seq=2, alive=False, cleanup="CLEAN", residue=0),
])
r = mod.collect(plan(), observer=lambda _: next(seq_running))
assert r["lifecycle_state"] == "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE"
assert r["sample_count"] == 2
positive()

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
positive()

# BLOCKED is a real herdr AgentStatus and must survive a bounded lifecycle.
seq_blocked = iter([
    sample("RUNNING", 1000, seq=1),
    sample("BLOCKED", 1001, seq=2),
    sample("DONE_CANDIDATE", 1002, seq=3, alive=False, cleanup="CLEAN", residue=0),
])
rb = mod.collect(plan(), observer=lambda _: next(seq_blocked))
assert rb["lifecycle_state"] == "LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE"
assert rb["sample_count"] == 3
assert rb["final_observer_state"] == "DONE_CANDIDATE"
positive()


def must_fail(samples, require_terminal=True):
    global MUTATIONS
    MUTATIONS += 1
    try:
        mod.validate_sequence(samples, require_terminal=require_terminal)
    except mod.ContractError:
        return
    raise AssertionError("mutation passed")


bad = sample("RUNNING", 1000, seq=2)
bad["attempt_id"] = "A2"
must_fail([
    sample("RUNNING", 999, seq=1),
    bad,
    sample("DONE_CANDIDATE", 1001, seq=3, alive=False, cleanup="CLEAN", residue=0),
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

# Identity drift on target and on process_id: both were untested reject controls.
tgt = sample("RUNNING", 1000, seq=2)
tgt["target"] = "worker-2"
must_fail([sample("RUNNING", 999, seq=1), tgt])
pidchg = sample("RUNNING", 1000, seq=2)
pidchg["process_id"] = 99
must_fail([sample("RUNNING", 999, seq=1), pidchg])

# A sample whose source timestamp is not a positive integer must be refused.
# This matters more under the amended contract: when herdr publishes no clock
# the observer stamps its own, so a zero/absent stamp is a producer defect,
# not a freshness question.
must_fail([sample("RUNNING", 0)])

# KNOWN GAP, deliberately not asserted here: state_change_seq regression.
# The reject would have to live in collect_herdr_lifecycle.validate_sequence
# (a non-negative-int check plus a "decreased" refusal next to the timestamp
# check), which this change does not own. Until it lands, the seq carried in
# every sample above is recorded evidence, not an enforced ordering anchor.

print(f"herdr-lifecycle selftest: PASS (positive={POSITIVE} mutations={MUTATIONS} live=NOT_EXERCISED)")
