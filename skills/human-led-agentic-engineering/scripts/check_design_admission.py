#!/usr/bin/env python3
"""Validate Human Design Admission receipts without granting implementation authority."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUIRED = {
    "schema_version",
    "repository",
    "subject",
    "problem_statement_digest",
    "design_digest",
    "human_actor",
    "admitted_at",
    "adversary_receipt_digest",
    "material_decisions",
    "non_goals",
    "disposition",
}


def fail(message: str, code: int = 2) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return code


def check(data: object) -> int:
    if not isinstance(data, dict):
        return fail("receipt must be a JSON object", 64)

    missing = sorted(REQUIRED - data.keys())
    if missing:
        return fail(f"missing required fields: {', '.join(missing)}", 64)

    if data.get("schema_version") != "human-design-admission/v1":
        return fail("unsupported schema_version")
    if data.get("disposition") != "HUMAN_DESIGN_ADMITTED":
        return fail("disposition must be HUMAN_DESIGN_ADMITTED")

    for field in ("repository", "subject", "human_actor", "admitted_at"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return fail(f"{field} must be a non-empty string", 64)

    for field in ("problem_statement_digest", "design_digest", "adversary_receipt_digest"):
        value = data.get(field)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            return fail(f"{field} must be sha256:<64 lowercase hex>", 64)

    decisions = data.get("material_decisions")
    if not isinstance(decisions, list) or not decisions or any(not isinstance(x, str) or not x.strip() for x in decisions):
        return fail("material_decisions must contain at least one non-empty decision")

    non_goals = data.get("non_goals")
    if not isinstance(non_goals, list) or any(not isinstance(x, str) or not x.strip() for x in non_goals):
        return fail("non_goals must be an array of non-empty strings", 64)

    dissent = data.get("unresolved_dissent", [])
    if not isinstance(dissent, list):
        return fail("unresolved_dissent must be an array", 64)
    for item in dissent:
        if not isinstance(item, dict):
            return fail("each unresolved_dissent entry must be an object", 64)
        if not str(item.get("claim", "")).strip() or not str(item.get("human_disposition", "")).strip():
            return fail("each unresolved dissent requires claim and human_disposition")

    print("PASS: human design admission receipt is structurally and semantically admissible")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(str(exc), 64)
    return check(data)


if __name__ == "__main__":
    raise SystemExit(main())
