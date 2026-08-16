#!/usr/bin/env python3
"""Validate explicit provider-surface dispositions without claiming invisible erasure."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PASS = 0
FAIL = 2
ERROR = 64
SCHEMA = "provider-retention-disposition/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SURFACES = {
    "branches",
    "tags",
    "pull_request_refs",
    "review_diffs",
    "actions_logs",
    "actions_artifacts",
    "actions_caches",
    "releases",
    "packages",
    "pages",
    "wiki",
    "lfs",
    "forks",
    "mirrors",
    "code_search_indexes",
    "backups_replicas",
    "webhooks",
    "deploy_keys",
    "apps",
    "environments",
    "secrets_metadata",
}
STATES = {
    "CLEAN",
    "REMOVED",
    "RECREATED",
    "PROVIDER_DISPOSITION_REQUIRED",
    "REQUESTED",
    "CONFIRMED",
    "PARTIAL",
    "NOT_AVAILABLE",
    "ACCEPTED_LIMITATION",
}
LIMITED = {
    "PROVIDER_DISPOSITION_REQUIRED",
    "REQUESTED",
    "PARTIAL",
    "NOT_AVAILABLE",
    "ACCEPTED_LIMITATION",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disposition", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        raw = args.disposition.read_bytes()
        document = json.loads(raw)
        problems: list[str] = []
        if not isinstance(document, dict) or set(document) != {
            "schema",
            "repository_identity_digest",
            "surfaces",
        }:
            problems.append("top-level fields differ from the contract")
            surfaces = {}
        else:
            if document.get("schema") != SCHEMA:
                problems.append(f"schema must be {SCHEMA}")
            identity = document.get("repository_identity_digest")
            if not isinstance(identity, str) or not HEX64.fullmatch(identity):
                problems.append("repository_identity_digest must be lowercase SHA-256")
            surfaces = document.get("surfaces")
            if not isinstance(surfaces, dict) or set(surfaces) != SURFACES:
                problems.append("surfaces must enumerate the complete canonical inventory")
                surfaces = surfaces if isinstance(surfaces, dict) else {}
        for name, value in surfaces.items():
            if value == "ERASED":
                problems.append(f"{name}: global ERASED claim is forbidden")
            elif value not in STATES:
                problems.append(f"{name}: unsupported disposition {value!r}")
        overall = "INCOMPLETE_OR_LIMITED" if any(value in LIMITED for value in surfaces.values()) else "TERMINAL"
        receipt = {
            "schema": "provider-retention-verification/v1",
            "input_sha256": hashlib.sha256(raw).hexdigest(),
            "overall_state": overall,
            "limited_surface_count": sum(value in LIMITED for value in surfaces.values()),
            "problem_count": len(problems),
            "verdict": "FAIL" if problems else "PASS",
        }
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        if problems:
            return FAIL
        print(f"PROVIDER-RETENTION GREEN overall={overall}")
        return PASS
    except (OSError, json.JSONDecodeError) as error:
        print(f"PROVIDER-RETENTION ERROR: {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    raise SystemExit(main())
