#!/usr/bin/env python3
"""Validate one immutable repository portfolio snapshot epoch."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from repository_portfolio_common import digest_object, load_json, parse_timestamp, validate_schema

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "references" / "repository-portfolio-control" / "contracts" / "repository-portfolio-snapshot.schema.json"
DEFAULT = SKILL_ROOT / "references" / "repository-portfolio-control" / "examples" / "good-snapshot.json"


def validate(snapshot: dict[str, Any], max_skew_seconds: int = 300) -> list[str]:
    errors = validate_schema(snapshot, SCHEMA)
    repos = snapshot.get("repositories", [])
    names = [repo.get("repository") for repo in repos if isinstance(repo, dict)]
    if len(names) != len(set(names)):
        errors.append("duplicate repository subject")
    try:
        observed_at = parse_timestamp(snapshot["observed_at"])
        times = [observed_at]
        for repo in repos:
            for key in ("issues_observed_at", "prs_observed_at", "workflows_observed_at"):
                value = parse_timestamp(repo[key])
                if value > observed_at:
                    errors.append(f"{repo.get('repository')}: {key} is after epoch observed_at")
                times.append(value)
        if times and (max(times) - min(times)).total_seconds() > max_skew_seconds:
            errors.append("MIXED_SNAPSHOT_EPOCH: observation skew exceeds bound")
    except Exception as exc:
        errors.append(f"timestamp invalid: {exc}")
    if digest_object(snapshot, "epoch_digest") != snapshot.get("epoch_digest"):
        errors.append("epoch digest drifted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT)
    parser.add_argument("--max-skew-seconds", type=int, default=300)
    args = parser.parse_args()
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
