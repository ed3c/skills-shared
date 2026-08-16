#!/usr/bin/env python3
"""Validate the local retirement inventory without claiming provider erasure.

`check_provider_retention.py` covers what the provider still holds. This covers
what the *local* side still holds after a private lineage moves: the clones,
worktrees, mirrors, bundles, caches, forks, and credentials that keep private
objects reachable long after the origin repository is sealed.

Two laws separate this from its provider sibling:

  1. The inventory is bound to an exact observed head. An inventory with no
     checkout behind it is a claim, not an observation, and `RETIRED` on every
     surface is exactly the shape a claim takes.
  2. `ERASED` is refused here as it is there. Retiring a local copy says nothing
     about provider-side backups, and a local inventory that could say `ERASED`
     would let one evidence lane speak for the other.

Exits: 0 inventory valid, 2 contract violated, 64 input unreadable.
"""
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
SCHEMA = "private-retirement-inventory/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SURFACES = {
    "clones",
    "worktrees",
    "mirrors",
    "bundles",
    "caches",
    "forks",
    "credentials",
}
STATES = {
    "RETIRED",
    "ABSENT",
    "PRESENT",
    "DISPOSITION_REQUIRED",
    "ACCEPTED_LIMITATION",
}
# A surface in one of these still reaches private objects, so the inventory as a
# whole is not terminal however many other surfaces are clean.
OUTSTANDING = {"PRESENT", "DISPOSITION_REQUIRED", "ACCEPTED_LIMITATION"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        raw = args.inventory.read_bytes()
        document = json.loads(raw)
        problems: list[str] = []
        if not isinstance(document, dict) or set(document) != {
            "schema",
            "repository_identity_digest",
            "observed_at_head",
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
            head = document.get("observed_at_head")
            if not isinstance(head, str) or not HEX40.fullmatch(head):
                problems.append(
                    "observed_at_head must be an exact 40-hex commit; an inventory "
                    "with no checkout behind it is a claim, not an observation"
                )
            surfaces = document.get("surfaces")
            if not isinstance(surfaces, dict) or set(surfaces) != SURFACES:
                problems.append("surfaces must enumerate the complete canonical inventory")
                surfaces = surfaces if isinstance(surfaces, dict) else {}
        for name, value in sorted(surfaces.items()):
            if value == "ERASED":
                problems.append(
                    f"{name}: local retirement cannot claim provider erasure"
                )
            elif value not in STATES:
                problems.append(f"{name}: unsupported disposition {value!r}")
        outstanding = sum(value in OUTSTANDING for value in surfaces.values())
        overall = "OUTSTANDING" if outstanding else "TERMINAL"
        receipt = {
            "schema": "private-retirement-verification/v1",
            "input_sha256": hashlib.sha256(raw).hexdigest(),
            "overall_state": overall,
            "outstanding_surface_count": outstanding,
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
        print(f"RETIREMENT-INVENTORY GREEN overall={overall}")
        return PASS
    except (OSError, json.JSONDecodeError) as error:
        print(f"RETIREMENT-INVENTORY ERROR: {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    raise SystemExit(main())
