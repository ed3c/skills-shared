#!/usr/bin/env python3
"""Validate executable Issue/PR acceptance contracts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from repository_portfolio_common import digest_object, leases_overlap, load_json, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts" / "issue-pr-acceptance.schema.json"
DEFAULT = SKILL_ROOT / "references" / "repository-portfolio-control" / "examples" / "good-acceptance.json"
BLOCKING_RUNTIME = {"FAIL", "ABSENT", "NOT_IMPLEMENTED", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}


def validate(contract: dict[str, Any]) -> tuple[list[str], str]:
    errors = validate_schema(contract, SCHEMA)
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
    if digest_object(contract, "contract_digest") != contract.get("contract_digest"):
        errors.append("acceptance contract digest drifted")
    blocked = [
        requirement for requirement in contract.get("runtime_requirements", [])
        if requirement.get("state") in BLOCKING_RUNTIME
    ]
    readiness = "BLOCKED_BY_RUNTIME" if blocked else "READY"
    if errors:
        readiness = "BLOCKED_BY_MISSING_ACCEPTANCE"
    return errors, readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT)
    args = parser.parse_args()
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
