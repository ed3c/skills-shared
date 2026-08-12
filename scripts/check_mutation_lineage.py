#!/usr/bin/env python3
"""Fail closed on malformed skill-mutation lineage JSONL records."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = ROOT / "mutations"
SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
CLASSES = {"trigger", "routing", "knowledge", "tool-contract", "verification", "recovery", "context-management", "example", "negative-instruction"}
STATUSES = {"proposed", "running", "won", "lost", "tie", "reverted"}
METRICS = {"task_pass_rate", "routing_f1", "recovery_rate", "safety_pass_rate", "capability_unlock_count"}


def nonempty_list(value, name):
    if not isinstance(value, list) or not value or len(value) != len(set(value)) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{name} must be a non-empty unique string array")


def validate(record: dict) -> None:
    required = {"schema_version", "skill", "parent_sha", "candidate_sha", "hypothesis", "mutation_class", "target_failures", "changed_sections", "expected_effect", "regression_budget", "status", "rollback_sha"}
    missing = sorted(required - record.keys())
    if missing: raise ValueError(f"missing fields: {', '.join(missing)}")
    if record["schema_version"] != "skill-mutation/v1": raise ValueError("unsupported schema_version")
    if not isinstance(record["skill"], str) or not record["skill"]: raise ValueError("skill required")
    if not SHA_RE.fullmatch(str(record["parent_sha"])) or not SHA_RE.fullmatch(str(record["candidate_sha"])) or not SHA_RE.fullmatch(str(record["rollback_sha"])):
        raise ValueError("parent/candidate/rollback SHA must be immutable lowercase hex")
    if record["parent_sha"] == record["candidate_sha"]: raise ValueError("candidate_sha must differ from parent_sha")
    if record["rollback_sha"] != record["parent_sha"]: raise ValueError("rollback_sha must pin the parent candidate was derived from")
    if not isinstance(record["hypothesis"], str) or len(record["hypothesis"].strip()) < 10: raise ValueError("one explicit hypothesis is required")
    if record["mutation_class"] not in CLASSES: raise ValueError("invalid mutation_class")
    if record["status"] not in STATUSES: raise ValueError("invalid status")
    nonempty_list(record["target_failures"], "target_failures")
    nonempty_list(record["changed_sections"], "changed_sections")
    effect = record["expected_effect"]
    if not isinstance(effect, dict) or effect.get("metric") not in METRICS or not isinstance(effect.get("minimum_delta"), (int, float)):
        raise ValueError("expected_effect metric/minimum_delta invalid")
    nonempty_list(effect.get("case_ids"), "expected_effect.case_ids")
    if not isinstance(record["regression_budget"], (int, float)) or record["regression_budget"] < 0: raise ValueError("regression_budget must be non-negative")
    if record["status"] in {"won", "lost", "tie", "reverted"} and not record.get("evidence_bundle"):
        raise ValueError("terminal mutation status requires evidence_bundle")


def main() -> int:
    errors, count = [], 0
    for path in sorted(MUTATIONS.rglob("*.jsonl")) if MUTATIONS.exists() else []:
        if "schema" in path.parts: continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip(): continue
            count += 1
            try:
                value = json.loads(line)
                if not isinstance(value, dict): raise ValueError("record must be object")
                validate(value)
            except (json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{path.relative_to(ROOT)}:{number}: {exc}")
    if errors:
        for error in errors: print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS mutation lineage: {count} records")
    return 0

if __name__ == "__main__": raise SystemExit(main())
