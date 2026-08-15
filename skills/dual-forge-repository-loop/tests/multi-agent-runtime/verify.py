#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent.parent
CHECKER = SKILL_ROOT / "scripts" / "check_multi_agent_runtime.py"
SCHEMA_ROOT = SKILL_ROOT / "references"
GOOD = TEST_DIR / "fixtures" / "valid-multi.json"


def run(document: dict) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "contract.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr


def clone_attempt(
    task: dict, attempt_id: str, parent: str | None, state: str, lease_status: str
) -> dict:
    """Another attempt at the same logical slice, with its own physical identity."""
    clone = copy.deepcopy(task)
    clone["attempt_id"] = attempt_id
    clone["parent_attempt_id"] = parent
    clone["state"] = state
    clone["lease"]["status"] = lease_status
    clone["branch"] = f"{task['branch']}-{attempt_id}"
    clone["worktree_identity"] = f"{task['worktree_identity']}-{attempt_id}"
    return clone


def mutate(name: str, document: dict) -> None:
    if name == "admission-false":
        document["admission"]["independent_oracles"] = False
    elif name == "path-overlap":
        document["tasks"][1]["allowed_paths"] = ["src/parser/generated"]
    elif name == "dependency-cycle":
        document["tasks"][0]["dependencies"] = ["worker-b"]
        document["tasks"][1]["dependencies"] = ["worker-a"]
    elif name == "duplicate-attempt":
        document["tasks"][1]["attempt_id"] = document["tasks"][0]["attempt_id"]
        document["results"][1]["attempt_id"] = document["results"][0]["attempt_id"]
    elif name == "budget-exceeded":
        document["budget"]["consumed"]["tokens"] = 50001
    elif name == "missing-profile-fanout":
        document["budget"]["profile_state"] = "ABSENT"
        document["budget"]["limits"]["active_workers"] = 1
        document["budget"]["limits"]["total_workers"] = 1
    elif name == "shadow-overclaim":
        document["shadow"]["execution"] = "IN_PROCESS_LOGICAL"
        document["shadow"]["independent_state"] = "PASS"
    elif name == "l3-bypass":
        document["shadow"]["checkpoint_outcome"] = "BLOCKED_AT_MATERIAL_BOUNDARY_L3"
        document["shadow"]["enforcement_state"] = "NOT_IMPLEMENTED"
    elif name == "agent-merge-enabled":
        document["merge_boundary"]["agent_merge_action"] = "ALLOW"
    elif name == "stale-result":
        document["results"][0]["base_subject_sha"] = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    elif name == "outside-lease":
        document["results"][0]["owned_paths"] = ["src/runtime"]
    elif name == "verified-fail":
        document["results"][0]["negative_controls"][0]["state"] = "FAIL"
    elif name == "missing-result":
        document["results"].pop(0)
        document["budget"]["consumed"]["tool_calls"] = 10
        document["budget"]["consumed"]["tokens"] = 2000
        document["budget"]["consumed"]["wall_clock_seconds"] = 110
    elif name == "duplicate-branch":
        document["tasks"][1]["branch"] = document["tasks"][0]["branch"]
    elif name == "unknown-dependency":
        document["tasks"][0]["dependencies"] = ["worker-z"]
    elif name == "invalid-evidence-state":
        document["states"]["evidence_state"] = "EXTERNAL_AUTHORITY_REQUIRED"
    elif name == "budget-ledger-mismatch":
        document["budget"]["consumed"]["tool_calls"] = 20
    elif name == "single-builder-cardinality":
        document["topology"] = "SINGLE_BUILDER"
    elif name == "resource-overlap":
        document["tasks"][1]["external_resource_leases"] = ["fixture-set-parser"]
    elif name == "merged-without-observation":
        document["states"]["delivery_state"] = "MERGED"
    elif name == "unknown-runtime-published":
        document["runtime"]["identity"] = "UNKNOWN"
    elif name == "expired-lease":
        document["tasks"][0]["lease"]["expiry"] = "2020-01-01T00:00:00Z"
    elif name == "unparsable-lease-expiry":
        document["tasks"][0]["lease"]["expiry"] = "2026-08-15T12:00:00"
    elif name == "invalid-evaluation-time":
        document["evaluation_time"] = "2026-08-15 11:30:00"
    elif name == "checkpoint-mismatch":
        document["results"][0]["checkpoint_identity"] = "9" * 64
    elif name == "foreign-eval":
        document["results"][0]["positive_evals"][0]["id"] = "EVAL-SCHEDULER-001"
    elif name == "foreign-negative-control":
        document["results"][0]["negative_controls"][0]["id"] = "CONTROL-SCHEDULER-001"
    elif name == "unadmitted-result-head":
        document["results"][0]["head_subject_sha"] = "e" * 40
    elif name == "publication-before-closure":
        for task in document["tasks"]:
            task["state"] = "RUNNING"
        document["results"] = []
        for key in ("tool_calls", "tokens", "wall_clock_seconds"):
            document["budget"]["consumed"][key] = 0
    elif name == "concurrent-attempts":
        retry = clone_attempt(
            document["tasks"][0], "worker-a-attempt-2", None, "RUNNING", "ACTIVE"
        )
        document["tasks"].append(retry)
        document["budget"]["consumed"]["total_workers"] = 3
        document["budget"]["consumed"]["active_workers"] = 3
        document["budget"]["limits"]["active_workers"] = 3
    elif name == "attempt-limit-exceeded":
        base = document["tasks"][0]
        parent = base["attempt_id"]
        for index in range(2, 6):
            attempt_id = f"worker-a-attempt-{index}"
            document["tasks"].append(
                clone_attempt(base, attempt_id, parent, "STALE_ATTEMPT", "RELEASED")
            )
            parent = attempt_id
        document["budget"]["consumed"]["total_workers"] = 6
    elif name == "multiple-accepted-attempts":
        extra = clone_attempt(
            document["tasks"][0], "worker-a-attempt-2", None, "INTEGRATED", "RELEASED"
        )
        document["tasks"].append(extra)
        document["budget"]["consumed"]["total_workers"] = 3
    elif name == "unknown-parent-attempt":
        document["tasks"][0]["parent_attempt_id"] = "worker-a-attempt-absent"
    elif name == "retry-over-live-attempt":
        retry = clone_attempt(
            document["tasks"][0], "worker-a-attempt-2", "worker-a-attempt-1", "STALE_ATTEMPT", "RELEASED"
        )
        document["tasks"].append(retry)
        document["budget"]["consumed"]["total_workers"] = 3
    elif name == "unordered-handoff":
        # Same path claimed by two slices with no dependency edge ordering them,
        # and not concurrently leased -- so it is neither a live collision nor a
        # proven handoff.
        document["tasks"][1]["lease"]["status"] = "RELEASED"
        document["tasks"][1]["state"] = "INTEGRATED"
        document["tasks"][1]["excluded_paths"] = ["README.md"]
        document["tasks"][1]["allowed_paths"] = ["src/scheduler", "tests/scheduler", "src/parser"]
        document["budget"]["consumed"]["active_workers"] = 1
    else:
        raise AssertionError(f"unknown mutation: {name}")


def main() -> int:
    good = json.loads(GOOD.read_text(encoding="utf-8"))
    code, stdout, stderr = run(good)
    failures: list[str] = []
    if code != 0 or "RUNTIME-CONTRACT-GREEN" not in stdout or stderr:
        failures.append(f"positive multi fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    single = copy.deepcopy(good)
    single["topology"] = "SINGLE_BUILDER"
    single["budget"]["profile_state"] = "ABSENT"
    single["budget"]["limits"]["active_workers"] = 1
    single["budget"]["limits"]["total_workers"] = 1
    single["budget"]["consumed"]["active_workers"] = 1
    single["budget"]["consumed"]["total_workers"] = 1
    single["budget"]["consumed"]["tool_calls"] = 9
    single["budget"]["consumed"]["tokens"] = 1500
    single["budget"]["consumed"]["wall_clock_seconds"] = 80
    single["tasks"] = single["tasks"][:1]
    single["results"] = single["results"][:1]
    code, stdout, stderr = run(single)
    if code != 0 or "topology=SINGLE_BUILDER" not in stdout or stderr:
        failures.append(f"positive fallback fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    # Bounded retry lineage: two terminal attempts followed by one accepted attempt
    # of the same logical slice is the shape v2.1 promises, and must be admitted
    # rather than rejected as duplicate tasks.
    retry = copy.deepcopy(good)
    accepted = retry["tasks"][0]
    first = clone_attempt(accepted, "worker-a-attempt-0", None, "FAILED_TERMINAL", "RELEASED")
    second = clone_attempt(
        accepted, "worker-a-attempt-0b", "worker-a-attempt-0", "SUPERSEDED", "RELEASED"
    )
    accepted["parent_attempt_id"] = "worker-a-attempt-0b"
    retry["tasks"] = [first, second, accepted, retry["tasks"][1]]
    retry["budget"]["consumed"]["total_workers"] = 4
    code, stdout, stderr = run(retry)
    if code != 0 or stderr:
        failures.append(f"positive retry-lineage fixture: code={code} stderr={stderr!r}")

    # Dependency-ordered handoff: a released predecessor may hand its path, mutable
    # state and resource to a declared successor. Comparing all packets as if
    # concurrent would forbid this valid sequential convergence.
    handoff = copy.deepcopy(good)
    handoff["tasks"][0]["lease"]["status"] = "RELEASED"
    handoff["tasks"][0]["state"] = "INTEGRATED"
    handoff["tasks"][1]["dependencies"] = ["worker-a"]
    handoff["tasks"][1]["excluded_paths"] = ["README.md"]
    handoff["tasks"][1]["allowed_paths"] = ["src/scheduler", "tests/scheduler", "src/parser"]
    handoff["tasks"][1]["owned_mutable_state"] = ["scheduler-contract", "parser-contract"]
    handoff["tasks"][1]["external_resource_leases"] = [
        "fixture-set-scheduler",
        "fixture-set-parser",
    ]
    handoff["budget"]["consumed"]["active_workers"] = 1
    code, stdout, stderr = run(handoff)
    if code != 0 or stderr:
        failures.append(f"positive sequential-handoff fixture: code={code} stderr={stderr!r}")

    # Path containment is segment-aware: src/parser2 is a sibling of src/parser,
    # not a child of it, and must not be reported as a lease collision.
    sibling = copy.deepcopy(good)
    sibling["tasks"][1]["allowed_paths"] = ["src/parser2", "tests/scheduler"]
    sibling["results"][1]["owned_paths"] = ["tests/scheduler"]
    code, stdout, stderr = run(sibling)
    if code != 0 or stderr:
        failures.append(f"positive sibling-path fixture: code={code} stderr={stderr!r}")

    cases = [
        ("admission-false", 2, "parallelism-not-admitted"),
        ("path-overlap", 2, "path-lease-overlap"),
        ("dependency-cycle", 2, "dependency-cycle"),
        ("duplicate-attempt", 2, "duplicate-attempt-id"),
        ("budget-exceeded", 2, "budget-exceeded:tokens"),
        ("missing-profile-fanout", 2, "missing-profile-fanout"),
        ("shadow-overclaim", 2, "shadow-independence-overclaim"),
        ("l3-bypass", 2, "shadow-l3-unenforced"),
        ("agent-merge-enabled", 64, "schema-invalid"),
        ("stale-result", 2, "stale-result-base"),
        ("outside-lease", 2, "result-outside-path-lease"),
        ("verified-fail", 2, "verified-result-nonpass"),
        ("missing-result", 2, "verified-task-missing-result"),
        ("duplicate-branch", 2, "duplicate-branch"),
        ("unknown-dependency", 2, "unknown-dependency"),
        ("invalid-evidence-state", 64, "schema-invalid"),
        ("budget-ledger-mismatch", 2, "budget-ledger-mismatch"),
        ("single-builder-cardinality", 2, "single-builder-cardinality"),
        ("resource-overlap", 2, "resource-lease-overlap"),
        ("merged-without-observation", 2, "merged-without-external-observation"),
        ("unknown-runtime-published", 2, "unknown-runtime-published"),
        ("expired-lease", 2, "expired-active-lease"),
        ("unparsable-lease-expiry", 64, "schema-invalid"),
        ("invalid-evaluation-time", 64, "schema-invalid"),
        ("checkpoint-mismatch", 2, "checkpoint-identity-mismatch"),
        ("foreign-eval", 2, "eval-identity-mismatch"),
        ("foreign-negative-control", 2, "eval-identity-mismatch"),
        ("unadmitted-result-head", 2, "result-head-not-admitted"),
        ("publication-before-closure", 2, "publication-before-closure"),
        ("concurrent-attempts", 2, "concurrent-attempts"),
        ("attempt-limit-exceeded", 2, "attempt-limit-exceeded"),
        ("multiple-accepted-attempts", 2, "multiple-accepted-attempts"),
        ("unknown-parent-attempt", 2, "unknown-parent-attempt"),
        ("retry-over-live-attempt", 2, "retry-over-live-attempt"),
        ("unordered-handoff", 2, "unordered-handoff"),
    ]

    for name, expected_code, marker in cases:
        document = copy.deepcopy(good)
        mutate(name, document)
        code, stdout, stderr = run(document)
        if code != expected_code or marker not in stderr:
            failures.append(
                f"{name}: expected code={expected_code} marker={marker!r}; "
                f"got code={code} stdout={stdout!r} stderr={stderr!r}"
            )

    process = subprocess.run(
        [sys.executable, str(CHECKER), str(TEST_DIR / "fixtures" / "absent.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 64 or "absent-input" not in process.stderr:
        failures.append(
            f"absent input: expected 64/absent-input, got {process.returncode} {process.stderr!r}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(
        "PASS multi-agent-runtime: multi-worker, single-builder fallback, bounded retry "
        "lineage, dependency-ordered handoff, and sibling-path fixtures admitted; "
        f"{len(cases)} planted topology, lease expiry, attempt-model, checkpoint, "
        "eval-identity, subject-admission, closure, budget, Shadow, result, and "
        "merge-boundary defects refused; absent input stayed distinct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
