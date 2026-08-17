#!/usr/bin/env python3
"""Validate portable scheduler lifecycle invariants without claiming live execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

TERMINAL_STALE = {"STALE_ATTEMPT", "LEASE_EXPIRED", "TIMED_OUT", "STRAGGLER_DETACHED", "FAILED_RETRYABLE", "CANCELLED", "SUPERSEDED"}
ACCEPTABLE_RESULT_STATES = {"RESULT_READY", "RESULT_VERIFIED", "INTEGRATED"}

class ContractError(ValueError):
    pass


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid JSON {path}: {exc}") from exc


def sha256(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(doc: dict) -> dict:
    if not isinstance(doc, dict) or doc.get("schema") != "agentic-tech-lead/scheduler-lifecycle/v1":
        raise ContractError("invalid scheduler lifecycle schema")
    for key in ("repository", "task_graph_digest", "attempts", "leases", "checkpoints", "results", "evidence_state"):
        if key not in doc:
            raise ContractError(f"missing {key}")
    if doc["evidence_state"] == "PASS":
        raise ContractError("portable lifecycle fixture cannot self-promote to live PASS")
    attempts = doc["attempts"]
    if not isinstance(attempts, list) or not attempts:
        raise ContractError("attempts must be a non-empty array")
    by_id = {}
    task_attempts: dict[str, list[dict]] = {}
    for item in attempts:
        if not isinstance(item, dict):
            raise ContractError("attempt must be object")
        aid = item.get("attempt_id")
        tid = item.get("task_id")
        if not isinstance(aid, str) or not aid or aid in by_id:
            raise ContractError("attempt_id must be unique non-empty string")
        if not isinstance(tid, str) or not tid:
            raise ContractError("task_id must be non-empty string")
        if item.get("consumed", 0) > item.get("budget", -1):
            raise ContractError(f"attempt budget exceeded: {aid}")
        by_id[aid] = item
        task_attempts.setdefault(tid, []).append(item)
    for aid, item in by_id.items():
        parent = item.get("parent_attempt_id")
        if parent is not None:
            if parent not in by_id:
                raise ContractError(f"missing parent attempt: {aid} -> {parent}")
            if by_id[parent]["task_id"] != item["task_id"]:
                raise ContractError(f"retry lineage crosses task identity: {aid}")
            if parent == aid:
                raise ContractError(f"self parent attempt: {aid}")
    active_resources: dict[str, str] = {}
    leases = doc["leases"]
    if not isinstance(leases, list):
        raise ContractError("leases must be array")
    for lease in leases:
        aid = lease.get("attempt_id")
        resource = lease.get("resource")
        if aid not in by_id or not isinstance(resource, str) or not resource:
            raise ContractError("lease references invalid attempt/resource")
        if lease.get("active"):
            previous = active_resources.get(resource)
            if previous and previous != aid:
                raise ContractError(f"multiple active writers for resource {resource}")
            if by_id[aid]["state"] in TERMINAL_STALE:
                raise ContractError(f"terminal attempt retains active lease: {aid}")
            active_resources[resource] = aid
    checkpoints = doc["checkpoints"]
    if not isinstance(checkpoints, list):
        raise ContractError("checkpoints must be array")
    checkpoint_ids = set()
    for cp in checkpoints:
        aid = cp.get("attempt_id")
        cid = cp.get("checkpoint_id")
        if aid not in by_id or not isinstance(cid, str) or not cid or cid in checkpoint_ids:
            raise ContractError("checkpoint identity/attempt invalid")
        checkpoint_ids.add(cid)
    results = doc["results"]
    if not isinstance(results, list):
        raise ContractError("results must be array")
    seen_results = set()
    for result in results:
        aid = result.get("attempt_id")
        if aid not in by_id or aid in seen_results:
            raise ContractError("result attempt invalid or duplicated")
        seen_results.add(aid)
        state = by_id[aid]["state"]
        if result.get("accepted"):
            if state not in ACCEPTABLE_RESULT_STATES:
                raise ContractError(f"accepted stale/unready result: {aid} state={state}")
            if result.get("oracle") != "PASS":
                raise ContractError(f"accepted result lacks PASS oracle: {aid}")
        if state in TERMINAL_STALE and result.get("accepted"):
            raise ContractError(f"terminal stale result accepted: {aid}")
    integrated_tasks = {a["task_id"] for a in attempts if a["state"] == "INTEGRATED"}
    for task_id in integrated_tasks:
        accepted = [r for r in results if r.get("accepted") and by_id[r["attempt_id"]]["task_id"] == task_id]
        if len(accepted) != 1:
            raise ContractError(f"integrated task must have exactly one accepted result: {task_id}")
    return {
        "schema": "agentic-tech-lead/scheduler-lifecycle-validation/v1",
        "verdict": "PASS",
        "document_sha256": sha256(doc),
        "attempt_count": len(attempts),
        "active_lease_count": len(active_resources),
        "claims_not_proven": [
            "live worker concurrency",
            "process/worktree execution",
            "Git Town synchronization",
            "Forgejo delivery",
            "merge or promotion"
        ]
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--lifecycle", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = validate(load(args.lifecycle))
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.write_text(encoded, encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
