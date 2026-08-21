#!/usr/bin/env python3
"""Validate executable Issue/PR acceptance contracts.

Salvaged from PR#564 (efb224d) `assert_issue_pr_acceptance.py`
(ISSUE_WITHOUT_FROZEN_ACCEPTANCE / BLOCKED_BY_MISSING_ACCEPTANCE gate), adapted
to the merged `issue-pr-acceptance/v1` field names (`runtime_requirements`,
`leases.exclusive_paths`, typed `start_dependencies`/`completion_dependencies`
edges -- #566 mandatory fix 4 -- and literal `digest`).
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from portfolio_control_lib import bind_digest, content_digest, leases_overlap, load_json, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "contracts" / "issue-pr-acceptance.schema.json"
BLOCKING_RUNTIME = {"FAIL", "ABSENT", "NOT_IMPLEMENTED", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}


def validate(contract: dict[str, Any]) -> tuple[list[str], str]:
    schema = load_json(SCHEMA)
    errors = validate_schema(contract, schema)
    item = contract.get("item", {})
    if not str(contract.get("objective", "")).strip() or not contract.get("oracles") or not contract.get("negative_controls"):
        errors.append("ISSUE_WITHOUT_FROZEN_ACCEPTANCE")
    if not contract.get("non_goals"):
        errors.append("acceptance non-goals missing")
    if item.get("kind") == "PULL_REQUEST":
        for field in ("base_commit", "base_tree", "head_commit", "head_tree"):
            if not item.get(field):
                errors.append(f"PULL_REQUEST item missing {field}")
        if item.get("head_commit") and item.get("head_commit") == contract.get("rollback", {}).get("commit"):
            errors.append("rollback subject equals candidate head")
        if item.get("observed_state") == "MERGED" and item.get("head_commit") != item.get("main_readback_commit"):
            errors.append("MERGED_WITHOUT_EXACT_MAIN_READBACK")
    if item.get("kind") == "ISSUE" and item.get("observed_state") == "CLOSED":
        unresolved = bool(errors) or any(
            requirement.get("state") in BLOCKING_RUNTIME for requirement in contract.get("runtime_requirements", [])
        )
        if unresolved:
            errors.append("ISSUE_CLOSED_WITH_UNRESOLVED_ACCEPTANCE")
    leases = contract.get("leases", {})
    exclusive = leases.get("exclusive_paths", [])
    for category in ("read_only_paths", "forbidden_paths"):
        for left in exclusive:
            for right in leases.get(category, []):
                if leases_overlap(str(left), str(right)):
                    errors.append(f"exclusive path overlaps {category}: {left} <> {right}")
    if set(contract.get("oracles", [])) & set(contract.get("negative_controls", [])):
        errors.append("oracle and negative-control identities overlap")
    if not contract.get("residual_owner"):
        errors.append("residual owner missing")
    if content_digest(contract) != contract.get("digest"):
        errors.append("acceptance contract digest drifted")
    blocked = [
        requirement for requirement in contract.get("runtime_requirements", [])
        if requirement.get("state") in BLOCKING_RUNTIME
    ]
    readiness = "BLOCKED_BY_RUNTIME" if blocked else "READY"
    if errors:
        readiness = "BLOCKED_BY_MISSING_ACCEPTANCE"
    return errors, readiness


def positive_fixture() -> dict[str, Any]:
    contract = {
        "schema_version": "agentic-tech-lead/issue-pr-acceptance/v1",
        "unit_id": "ISSUE-566",
        "epoch_id": "fixture-epoch",
        "repository": "ed3c/skills-shared",
        "item": {"kind": "ISSUE", "number": 566, "observed_state": "OPEN"},
        "objective": "Prove the merged acceptance contract validates end to end.",
        "non_goals": ["merge, release and production"],
        "start_dependencies": [],
        "completion_dependencies": [],
        "leases": {
            "exclusive_paths": ["skills/agentic-tech-lead-orchestration/scripts/**"],
            "read_only_paths": ["AGENTS.md"],
            "forbidden_paths": ["secrets/**"],
            "exclusive_resources": [],
        },
        "runtime_requirements": [
            {"capability": "runtime", "state": "PASS", "owner": "test", "unblock_condition": "already admitted"}
        ],
        "oracles": ["deterministic checker exits zero"],
        "negative_controls": ["stale subject turns red"],
        "evidence": {"required_lanes": ["DETERMINISTIC"], "ceiling": "fixture-only deterministic mechanics"},
        "rollback": {"commit": "3" * 40, "strategy": "revert the merge commit"},
        "allowed_terminal_states": ["READY", "BLOCKED", "REJECTED"],
        "residual_owner": "issue-560",
    }
    return bind_digest(contract)


def selftest() -> None:
    base = positive_fixture()
    errors, state = validate(base)
    assert errors == [], errors
    assert state == "READY", state

    stripped = copy.deepcopy(base)
    stripped["oracles"] = []
    stripped = bind_digest(stripped)
    errors, state = validate(stripped)
    assert "ISSUE_WITHOUT_FROZEN_ACCEPTANCE" in errors, errors
    assert state == "BLOCKED_BY_MISSING_ACCEPTANCE", state
    print("REFUSED ISSUE_WITHOUT_FROZEN_ACCEPTANCE")

    absent_runtime = copy.deepcopy(base)
    absent_runtime["runtime_requirements"][0]["state"] = "ABSENT"
    absent_runtime = bind_digest(absent_runtime)
    errors, state = validate(absent_runtime)
    assert errors == [], errors
    assert state == "BLOCKED_BY_RUNTIME", state
    print("REFUSED_STATE BLOCKED_BY_RUNTIME (absent runtime, no acceptance defect)")

    merged_pr = copy.deepcopy(base)
    merged_pr["item"] = {
        "kind": "PULL_REQUEST", "number": 566, "observed_state": "MERGED",
        "base_commit": "4" * 40, "base_tree": "5" * 40, "head_commit": "6" * 40, "head_tree": "7" * 40,
    }
    merged_pr = bind_digest(merged_pr)
    errors, _ = validate(merged_pr)
    assert "MERGED_WITHOUT_EXACT_MAIN_READBACK" in errors, errors
    print("REFUSED MERGED_WITHOUT_EXACT_MAIN_READBACK")

    readback_pr = copy.deepcopy(merged_pr)
    readback_pr["item"]["main_readback_commit"] = readback_pr["item"]["head_commit"]
    readback_pr = bind_digest(readback_pr)
    errors, _ = validate(readback_pr)
    assert "MERGED_WITHOUT_EXACT_MAIN_READBACK" not in errors, errors
    print("PASS main_readback_commit == head_commit (exact readback accepted)")

    closed_issue = copy.deepcopy(stripped)
    closed_issue["item"] = {"kind": "ISSUE", "number": 566, "observed_state": "CLOSED"}
    closed_issue = bind_digest(closed_issue)
    errors, _ = validate(closed_issue)
    assert "ISSUE_CLOSED_WITH_UNRESOLVED_ACCEPTANCE" in errors, errors
    print("REFUSED ISSUE_CLOSED_WITH_UNRESOLVED_ACCEPTANCE")

    print("ISSUE-PR-ACCEPTANCE-GREEN positives=2 mutations=4")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.contract:
        parser.error("--contract is required without --selftest")
    try:
        contract = load_json(args.contract)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors, readiness = validate(contract)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"STATE: {readiness}")
        return 2
    print(f"PASS: acceptance {contract['repository']}#{contract['item']['number']} state={readiness}")
    return 0 if readiness == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
