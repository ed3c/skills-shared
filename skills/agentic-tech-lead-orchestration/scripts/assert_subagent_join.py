#!/usr/bin/env python3
"""Validate the mandatory all-subagent terminal and consolidation barrier."""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from repository_portfolio_common import digest_object, load_json

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts"
JOIN_SCHEMA = CONTRACTS / "subagent-join-receipt.schema.json"
RESULT_SCHEMA = CONTRACTS / "subagent-result.schema.json"
DISPATCH_SCHEMA = CONTRACTS / "subagent-dispatch.schema.json"
DEFAULT = SKILL_ROOT / "references" / "repository-portfolio-control" / "examples" / "good-join-receipt.json"


def schema_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        error.message
        for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    ]


def validate(
    receipt: dict[str, Any],
    dispatches: list[dict[str, Any]] | None = None,
) -> tuple[list[str], str]:
    result_schema = load_json(RESULT_SCHEMA)
    join_schema = copy.deepcopy(load_json(JOIN_SCHEMA))
    # Inline the local result schema so validation is deterministic and zero-network.
    join_schema["properties"]["results"]["items"] = result_schema
    errors = schema_errors(receipt, join_schema)

    for result in receipt.get("results", []):
        errors.extend(schema_errors(result, result_schema))
        if isinstance(result, dict) and digest_object(result, "result_digest") != result.get("result_digest"):
            errors.append(f"{result.get('attempt_id')}: result digest drifted")

    requested = [str(value) for value in receipt.get("requested_attempts", [])]
    if len(requested) != len(set(requested)):
        errors.append("duplicate requested attempt")
    results = receipt.get("results", [])
    result_ids = [str(result.get("attempt_id")) for result in results if isinstance(result, dict)]
    if len(result_ids) != len(set(result_ids)):
        errors.append("duplicate result attempt")
    unrequested = set(result_ids) - set(requested)
    if unrequested:
        errors.append(f"unrequested result attempts: {sorted(unrequested)}")
    missing = sorted(set(requested) - set(result_ids))
    if sorted(receipt.get("missing_attempts", [])) != missing:
        errors.append("missing_attempts denominator drifted")

    pass_count = sum(1 for result in results if result.get("state") == "PASS")
    non_pass = len(results) - pass_count
    expected_denominator = {
        "requested": len(requested),
        "terminal": len(results),
        "pass": pass_count,
        "non_pass": non_pass,
    }
    if receipt.get("denominator", {}) != expected_denominator:
        errors.append("join denominator drifted")

    for result in results:
        if result.get("state") == "PASS":
            lease = result.get("lease_readback", {})
            if (
                lease.get("exclusive_paths_respected") is not True
                or lease.get("resources_released") is not True
            ):
                errors.append(f"{result.get('attempt_id')}: PASS without lease cleanup")
            if result.get("cleanup") in {"RESIDUE", "UNKNOWN"}:
                errors.append(f"{result.get('attempt_id')}: PASS with residue/unknown cleanup")
        if result.get("role") != "implementation-worker" and result.get("changed_paths"):
            errors.append(f"{result.get('attempt_id')}: read-only role changed paths")

    computed = (
        "JOIN_INCOMPLETE"
        if missing
        else ("PASS" if non_pass == 0 else "JOIN_COMPLETE_WITH_BLOCKERS")
    )
    if receipt.get("join_state") != computed:
        errors.append(f"join_state drifted: expected {computed}")

    if dispatches is not None:
        dispatch_schema = load_json(DISPATCH_SCHEMA)
        dispatch_by_attempt: dict[str, dict[str, Any]] = {}
        for dispatch in dispatches:
            errors.extend(schema_errors(dispatch, dispatch_schema))
            attempt_id = str(dispatch.get("attempt_id"))
            if attempt_id in dispatch_by_attempt:
                errors.append(f"duplicate dispatch attempt: {attempt_id}")
            dispatch_by_attempt[attempt_id] = dispatch
            if digest_object(dispatch, "dispatch_digest") != dispatch.get("dispatch_digest"):
                errors.append(f"{attempt_id}: dispatch digest drifted")
            agent = dispatch.get("agent", {})
            alias = agent.get("provider_alias")
            if alias and agent.get("model") == alias:
                errors.append(f"{attempt_id}: MODEL_ALIAS_REPORTED_AS_EXACT_IDENTITY")
            visibility = dispatch.get("subject", {}).get("visibility")
            if visibility in {"PRIVATE", "INTERNAL"} and agent.get("private_egress_admitted") is not True:
                errors.append(f"{attempt_id}: PRIVATE_REPO_DISPATCH_WITHOUT_EGRESS_ADMISSION")
            if visibility in {"PRIVATE", "INTERNAL"} and agent.get("data_boundary") != "PRIVATE_ADMITTED":
                errors.append(f"{attempt_id}: private data boundary not admitted")
        if set(dispatch_by_attempt) != set(requested):
            errors.append("dispatch denominator does not match requested attempts")
        for result in results:
            attempt_id = str(result.get("attempt_id"))
            dispatch = dispatch_by_attempt.get(attempt_id)
            if dispatch is None:
                continue
            if result.get("dispatch_digest") != dispatch.get("dispatch_digest"):
                errors.append(f"{attempt_id}: dispatch digest mismatch")
            for key in ("epoch_id", "task_id", "role"):
                if result.get(key) != dispatch.get(key):
                    errors.append(f"{attempt_id}: {key} mismatch")
            subject = result.get("subject", {})
            dispatch_subject = dispatch.get("subject", {})
            if (
                subject.get("repository") != dispatch_subject.get("repository")
                or subject.get("visibility") != dispatch_subject.get("visibility")
                or subject.get("base_commit") != dispatch_subject.get("commit")
                or subject.get("base_tree") != dispatch_subject.get("tree")
            ):
                errors.append(f"{attempt_id}: subject mismatch")

    if digest_object(receipt, "join_digest") != receipt.get("join_digest"):
        errors.append("join digest drifted")
    return errors, computed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=DEFAULT)
    parser.add_argument("--dispatches", type=Path)
    args = parser.parse_args()
    try:
        receipt = load_json(args.receipt)
        dispatches = load_json(args.dispatches) if args.dispatches else None
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors, state = validate(receipt, dispatches)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(
        "PASS: subagent join structurally valid "
        f"state={state} requested={len(receipt['requested_attempts'])}"
    )
    return 0 if state == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
