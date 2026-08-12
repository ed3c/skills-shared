#!/usr/bin/env python3
"""Validate capability-unlock registry without granting credit from prose alone."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evals" / "capability-unlocks.json"


def validate_unlock(value: dict) -> None:
    required = {"schema_version", "id", "skill", "skill_sha", "case_ids", "baseline", "candidate", "supported_stacks", "evidence_bundles"}
    missing = required - value.keys()
    if missing: raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    if value["schema_version"] != "capability-unlock/v1": raise ValueError("unsupported unlock schema")
    cases = value["case_ids"]
    if not isinstance(cases, list) or len(set(cases)) < 6: raise ValueError("unlock requires at least six distinct held-out cases")
    baseline, candidate = value["baseline"], value["candidate"]
    total = int(baseline.get("total", 0))
    if total < 6 or int(candidate.get("total", 0)) != total: raise ValueError("baseline/candidate totals must match and be >= 6")
    if int(baseline.get("no_skill_passes", total)) > total / 6: raise ValueError("no-skill baseline is too capable for unlock claim")
    if int(baseline.get("current_skill_passes", total)) > total / 6: raise ValueError("current-skill baseline is too capable for unlock claim")
    if int(candidate.get("passes", 0)) < (2 * total) / 3: raise ValueError("candidate does not meet >= 2/3 held-out pass threshold")
    stacks = value["supported_stacks"]
    identities = {(s.get("model"), s.get("harness")) for s in stacks if isinstance(s, dict)}
    if len(identities) < 2: raise ValueError("unlock requires at least two distinct model/harness stacks")
    bundles = value["evidence_bundles"]
    if not isinstance(bundles, list) or not bundles: raise ValueError("unlock requires evidence bundles")
    for ref in bundles:
        if not isinstance(ref, str) or not ref.strip(): raise ValueError("invalid evidence bundle reference")


def main() -> int:
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if registry.get("schema_version") != "capability-unlock-registry/v1": raise ValueError("unsupported registry schema")
        unlocks = registry.get("unlocks")
        if not isinstance(unlocks, list): raise ValueError("unlocks must be an array")
        ids = set()
        for unlock in unlocks:
            if not isinstance(unlock, dict): raise ValueError("unlock must be object")
            validate_unlock(unlock)
            if unlock["id"] in ids: raise ValueError(f"duplicate unlock id {unlock['id']}")
            ids.add(unlock["id"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 1
    print(f"PASS capability unlock registry: {len(unlocks)} verified unlocks")
    return 0

if __name__ == "__main__": raise SystemExit(main())
