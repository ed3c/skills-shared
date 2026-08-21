#!/usr/bin/env python3
"""Validate one immutable repository portfolio snapshot epoch.

Salvaged from PR#564 (efb224d) `assert_repository_portfolio_snapshot.py`
(#566 mandatory fix 5: per-source observed_at max-skew bound), adapted to the
merged `repository-portfolio-snapshot/v1` field names (`full_name`,
`main_commit`, `main_tree`, literal `digest`) and to `portfolio_control_lib`.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from portfolio_control_lib import bind_digest, content_digest, load_json, parse_timestamp, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "contracts" / "repository-portfolio-snapshot.schema.json"


def validate(snapshot: dict[str, Any], max_skew_seconds: int = 300) -> list[str]:
    schema = load_json(SCHEMA)
    errors = validate_schema(snapshot, schema)
    repos = snapshot.get("repositories", [])
    names = [repo.get("full_name") for repo in repos if isinstance(repo, dict)]
    if len(names) != len(set(names)):
        errors.append("duplicate repository subject")
    try:
        observed_at = parse_timestamp(snapshot["observed_at"])
        times = [observed_at]
        for repo in repos:
            for key in ("issues_observed_at", "prs_observed_at", "workflows_observed_at"):
                value = parse_timestamp(repo[key])
                if value > observed_at:
                    errors.append(f"{repo.get('full_name')}: {key} is after epoch observed_at")
                times.append(value)
        if times and (max(times) - min(times)).total_seconds() > max_skew_seconds:
            errors.append("MIXED_SNAPSHOT_EPOCH: observation skew exceeds bound")
    except (KeyError, ValueError) as exc:
        errors.append(f"timestamp invalid: {exc}")
    if content_digest(snapshot) != snapshot.get("digest"):
        errors.append("epoch digest drifted")
    return errors


def positive_fixture() -> dict[str, Any]:
    when = "2026-08-21T00:00:00Z"
    snapshot = {
        "schema": "repository-portfolio-snapshot/v1",
        "epoch_id": "fixture-epoch",
        "observed_at": when,
        "runtime": {"class": "CLAUDE_CODE_LOCAL", "host": "fixture", "local_checkout": "PASS", "authority_ceiling": "deterministic fixture"},
        "repositories": [{
            "full_name": "ed3c/skills-shared",
            "visibility": "PUBLIC",
            "default_branch": "main",
            "main_commit": "1" * 40,
            "main_tree": "2" * 40,
            "issues": [],
            "pull_requests": [],
            "workflows": [],
            "path_writers": [],
            "issues_observed_at": when,
            "prs_observed_at": when,
            "workflows_observed_at": when,
        }],
    }
    return bind_digest(snapshot)


def selftest() -> None:
    base = positive_fixture()
    assert validate(base) == [], validate(base)

    skewed = copy.deepcopy(base)
    skewed["repositories"][0]["issues_observed_at"] = "2026-08-21T00:10:01Z"
    skewed = bind_digest(skewed)
    errors = validate(skewed)
    assert "MIXED_SNAPSHOT_EPOCH: observation skew exceeds bound" in errors, errors
    print("REFUSED MIXED_SNAPSHOT_EPOCH")

    duplicated = copy.deepcopy(base)
    duplicated["repositories"].append(copy.deepcopy(duplicated["repositories"][0]))
    duplicated = bind_digest(duplicated)
    errors = validate(duplicated)
    assert "duplicate repository subject" in errors, errors
    print("REFUSED DUPLICATE_REPOSITORY_SUBJECT")

    print("REPOSITORY-PORTFOLIO-SNAPSHOT-GREEN positives=1 mutations=2")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--max-skew-seconds", type=int, default=300)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.snapshot:
        parser.error("--snapshot is required without --selftest")
    try:
        snapshot = load_json(args.snapshot)
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = validate(snapshot, args.max_skew_seconds)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print(f"PASS: snapshot epoch {snapshot['epoch_id']} ({len(snapshot['repositories'])} repository subject(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
