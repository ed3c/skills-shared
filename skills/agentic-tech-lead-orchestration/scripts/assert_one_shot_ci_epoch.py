#!/usr/bin/env python3
"""Validate one-shot exact-head GitHub Actions evidence."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from repository_portfolio_common import digest_object, load_json, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts" / "one-shot-ci-epoch.schema.json"
DEFAULT = SKILL_ROOT / "references" / "repository-portfolio-control" / "examples" / "good-ci-epoch.json"


def validate(epoch: dict[str, Any]) -> tuple[list[str], str]:
    errors = validate_schema(epoch, SCHEMA)
    candidate = epoch.get("candidate", {})
    local_gate = epoch.get("local_gate", {})
    publication = epoch.get("publication", {})
    runs = epoch.get("workflow_runs", [])

    if local_gate.get("state") != "PASS":
        errors.append("local gate must PASS before publication")
    if publication.get("draft_first") is not True:
        errors.append("DRAFT_OR_SYNCHRONIZE_CI_SPAM: Draft-first publication missing")
    if publication.get("code_push_count") != 1:
        errors.append("one final code push is required")
    if publication.get("ready_transition_count") != 1:
        errors.append("exactly one ready-for-review transition is required")
    if publication.get("code_push_after_ready") is not False:
        errors.append("code push occurred after ready-for-review")
    reruns = int(publication.get("rerun_count", 0) or 0)
    classification = publication.get("rerun_classification")
    if reruns > 0 and classification != "INFRASTRUCTURE_FLAKE":
        errors.append("BLIND_RERUN_AFTER_CODE_FAILURE")
    if reruns == 0 and classification != "NONE":
        errors.append("rerun classification without rerun")
    successes = 0
    for run in runs:
        if run.get("head_sha") != candidate.get("commit"):
            errors.append("OLD_HEAD_WORKFLOW_RECEIPT_REUSED")
        if run.get("state") == "SUCCESS":
            if int(run.get("jobs", 0)) <= 0 or int(run.get("steps", 0)) <= 0:
                errors.append("EMPTY_OR_SKIPPED_WORKFLOW_PROMOTED_TO_PASS")
            else:
                successes += 1
        if run.get("state") == "SKIPPED":
            errors.append("skipped workflow cannot satisfy exact-head evidence")
    computed = "PASS" if not errors and successes >= 1 else ("NOT_EXERCISED" if not runs else "REJECT")
    if epoch.get("verdict") != computed:
        errors.append(f"verdict drifted: expected {computed}")
    if digest_object(epoch, "digest") != epoch.get("digest"):
        errors.append("CI epoch digest drifted")
    return errors, computed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        epoch = load_json(args.epoch)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors, verdict = validate(epoch)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(f"PASS: one-shot CI epoch verdict={verdict} head={epoch['candidate']['commit']}")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
