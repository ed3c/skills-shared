"""Canonical scheduler receipt projection for the real-task canary."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from real_task_fixture import CanaryError, ROOT, dump, graph_controls, proc


def scheduler_doc(arm: str, base: str, tree: str, rows: list[dict[str, Any]], winner: str,
                  receipt: dict[str, Any], convergence: dict[str, str], controls: dict[str, str]) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []; results: list[dict[str, Any]] = []; checkpoints: list[dict[str, Any]] = []; leases: list[dict[str, Any]] = []
    for row in rows:
        integrated = row["name"] == winner
        attempts.append({"task_id": row["name"], "attempt_id": row["attempt"], "parent_attempt_id": None,
                         "state": "INTEGRATED" if integrated else "RESULT_VERIFIED", "budget": 1, "consumed": 1,
                         "worktree": row["worktree"], "head": row["commit"]})
        results.append({"attempt_id": row["attempt"], "result_digest": row["checkpoint"], "oracle": row["oracle"], "accepted": integrated})
        checkpoints.append({"attempt_id": row["attempt"], "checkpoint_id": f"cp-{row['attempt']}", "artifact_digest": row["checkpoint"]})
        leases.append({"attempt_id": row["attempt"], "resource": f"{row['branch']}:{row['path']}", "active": False, "expires_at": 0})
    first, retry = receipt["first_attempt"], receipt["retry_attempt"]
    attempts += [
        {"task_id": "receipt", "attempt_id": first, "parent_attempt_id": None, "state": "FAILED_RETRYABLE", "budget": 2, "consumed": 1, "worktree": receipt["worktree"], "head": base},
        {"task_id": "receipt", "attempt_id": retry, "parent_attempt_id": first, "state": "INTEGRATED", "budget": 2, "consumed": 2, "worktree": receipt["worktree"], "head": receipt["commit"]},
        {"task_id": "checkout-local-control", "attempt_id": controls["local_attempt"], "parent_attempt_id": None, "state": "CANCELLED", "budget": 1, "consumed": 1, "worktree": controls["local_worktree"], "head": controls["integrated_base"]},
        {"task_id": "checkout-wrong-base", "attempt_id": controls["stale_attempt"], "parent_attempt_id": None, "state": "STALE_ATTEMPT", "budget": 1, "consumed": 1, "worktree": controls["stale_worktree"], "head": base},
        {"task_id": "checkout", "attempt_id": convergence["attempt"], "parent_attempt_id": None, "state": "INTEGRATED", "budget": 1, "consumed": 1, "worktree": convergence["worktree"], "head": convergence["commit"]},
    ]
    result_rows = [
        (retry, receipt["checkpoint"], "PASS", True),
        (controls["local_attempt"], controls["local_checkpoint"], "FAIL", False),
        (controls["stale_attempt"], controls["stale_checkpoint"], "FAIL", False),
        (convergence["attempt"], convergence["checkpoint"], "PASS", True),
    ]
    for aid, artifact, oracle, accepted in result_rows:
        results.append({"attempt_id": aid, "result_digest": artifact, "oracle": oracle, "accepted": accepted})
        checkpoints.append({"attempt_id": aid, "checkpoint_id": f"cp-{aid}", "artifact_digest": artifact})
        leases.append({"attempt_id": aid, "resource": f"resource:{aid}", "active": False, "expires_at": 0})
    checkpoints.append({"attempt_id": first, "checkpoint_id": f"cp-{first}", "artifact_digest": receipt["first_checkpoint"]})
    leases.append({"attempt_id": first, "resource": "src/receipt.py", "active": False, "expires_at": 0})
    return {"schema": "agentic-tech-lead/scheduler-lifecycle/v1", "repository": {"id": f"synthetic/{arm.lower()}", "commit": base, "tree": tree},
            "task_graph_digest": graph_controls()["graph_digest"], "attempts": attempts, "leases": leases,
            "checkpoints": checkpoints, "results": results, "evidence_state": "IMPLEMENTED"}


def validate_scheduler(document: dict[str, Any], temp: Path) -> dict[str, Any]:
    source = temp / "lifecycle.json"; receipt = temp / "receipt.json"; dump(source, document)
    command = [sys.executable, str(ROOT / "scripts/assert_scheduler_lifecycle.py"), "--lifecycle", str(source), "--receipt", str(receipt)]
    if proc(command, cwd=ROOT, check=False).returncode: raise CanaryError("canonical scheduler rejected observations")
    planted: dict[str, bool] = {}
    for name, mutate in {
        "two_active_writers": lambda d: (d["leases"][0].update(active=True), d["leases"][1].update(active=True, resource=d["leases"][0]["resource"])),
        "accepted_stale": lambda d: next(r for r in d["results"] if r["attempt_id"] == next(a["attempt_id"] for a in d["attempts"] if a["state"] == "STALE_ATTEMPT")).update(accepted=True, oracle="PASS"),
        "missing_retry_parent": lambda d: next(a for a in d["attempts"] if a["parent_attempt_id"] is not None).update(parent_attempt_id="missing"),
        "fixture_promoted_pass": lambda d: d.update(evidence_state="PASS"),
    }.items():
        bad = copy.deepcopy(document); mutate(bad); path = temp / f"{name}.json"; dump(path, bad)
        planted[name] = proc([sys.executable, str(ROOT / "scripts/assert_scheduler_lifecycle.py"), "--lifecycle", str(path)], cwd=ROOT, check=False).returncode != 0
    if not all(planted.values()): raise CanaryError(f"scheduler mutation survived {planted}")
    value = json.loads(receipt.read_text())
    if value["active_lease_count"] != 0: raise CanaryError("active lease at close")
    return {"receipt": value, "planted": planted}
