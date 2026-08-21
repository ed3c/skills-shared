#!/usr/bin/env python3
"""Validate a canary-receipt/v1 record for #235's production-like canaries.

Exit codes:
  0   the receipt is schema-valid and none of the 8 named controls fire
  2   structurally valid receipt violates one of #235's required controls
  64  missing, unreadable, or schema-invalid input
  70  required validator dependency is unavailable

This validates one already-run canary's receipt. It does not run a canary,
call a consumer repository, or promote evals/live-evidence-state.json's
235_production_like lane -- that lane stays NOT_EXERCISED until three
authorized canaries across two observation windows actually exist, matching
its own "why" field.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from _json_schema_validation import (
    load_json_document,
    require_draft202012_validator,
    schema_errors as shared_schema_errors,
)

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2
SCHEMA_NAME = "canary-receipt.schema.json"
PREFIX = "CANARY-RECEIPT"
Draft202012Validator = require_draft202012_validator(PREFIX)


def semantic_errors(receipt: dict[str, Any]) -> list[str]:
    """The 8 controls #235's 'Required controls' section names, one check each."""
    errors: list[str] = []

    staleness = receipt["staleness"]
    if staleness["material_identity_changed_since_bound"] and not staleness["revalidated"]:
        errors.append("stale-receipt-reused-after-subject-movement")

    reachable = receipt["service_status"]["external_service_reachable"]
    outages_recorded_as_defects = [
        probe["probe_id"]
        for probe in receipt["probes"]["positive"] + receipt["probes"]["falsifying"]
        if probe["outcome"] == "FAIL_REPOSITORY_DEFECT" and not reachable
    ]
    if outages_recorded_as_defects:
        errors.append(
            "external-service-outage-recorded-as-repository-defect: "
            + ",".join(sorted(outages_recorded_as_defects))
        )

    credential = receipt["credential_authorization"]
    denial_reason = credential["denial_reason"]
    credential_present = credential["credential_present"]
    if denial_reason == "POLICY_DENIED" and not credential_present:
        errors.append("credential-missing-recorded-as-policy-denial")
    if denial_reason == "CREDENTIAL_MISSING" and credential_present:
        errors.append("policy-denial-recorded-as-credential-missing")

    publication = receipt["publication"]
    missing_artifacts = sorted(
        set(publication["required_artifacts"]) - set(publication["published_artifacts"])
    )
    if publication["all_required_artifacts_published"] and missing_artifacts:
        errors.append(
            "partial-publication-accepted-as-complete: " + ",".join(missing_artifacts)
        )

    gate_state = receipt["gate_state"]
    if gate_state["is_first_green"] and not gate_state["production_like_gate_executed"]:
        errors.append("first-green-with-skipped-production-like-gate")

    rollback = receipt["rollback"]
    if rollback["rollback_subject_digest"] == rollback["candidate_subject_digest"]:
        errors.append("rollback-target-equals-candidate")

    shadow = receipt["module_shadowing"]
    if shadow["consumer_local_module_present"] and shadow["shadows_canonical_digest"]:
        errors.append("consumer-local-module-shadows-canonical")

    if credential["private_data_present"] and not credential["data_egress_provider_approved"]:
        errors.append("private-data-routed-to-unapproved-provider")

    return errors


def check(path: Path, schema_root: Path) -> int:
    receipt = load_json_document(path, prefix=PREFIX, invalid_exit=SCHEMA_INVALID)
    schema = load_json_document(
        schema_root / SCHEMA_NAME, prefix=PREFIX, invalid_exit=SCHEMA_INVALID
    )

    schema_errors = shared_schema_errors(receipt, schema, Draft202012Validator)
    if schema_errors:
        for error in schema_errors:
            print(f"{PREFIX}-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = semantic_errors(receipt)
    if errors:
        for error in errors:
            print(f"{PREFIX}-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    print(
        "CANARY-RECEIPT-GREEN "
        f"canary={receipt['canary_id']} "
        f"consumer={receipt['consumer']['repository_id']} "
        f"evaluator={receipt['evaluator']['owner']} "
        "-- admissible as one canary in one observation window, "
        "not the required three-canary/two-window acceptance state"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "references",
    )
    args = parser.parse_args(argv)
    return check(args.receipt, args.schema_root)


if __name__ == "__main__":
    raise SystemExit(main())
