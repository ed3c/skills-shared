#!/usr/bin/env python3
"""Fail closed when GitHub Issue closure outruns acceptance or landed evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SHA = set("0123456789abcdef")
DISPOSITIONS = {"DIRECTLY_LANDED", "CONSUMED_BY_CONVERGENCE", "SCOPE_TRANSFERRED", "SUPERSEDED", "NOT_PLANNED"}
RESOLVED = {"SATISFIED", "TRANSFERRED", "NOT_APPLICABLE", "SUPERSEDED"}
CEILING = {"SOURCE_ONLY": 0, "STATIC": 1, "DETERMINISTIC": 2, "LIVE": 3, "HUMAN_ADMITTED": 4, "RELEASED": 5}


def sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(c in SHA for c in text)


def validate(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != "agentic-tech-lead/issue-closure-contract/v1":
        errors.append("schema_version drifted")
    issue = doc.get("issue", {})
    disposition = doc.get("disposition")
    if disposition not in DISPOSITIONS:
        errors.append("invalid closure disposition")
    acceptance = doc.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance:
        return errors + ["acceptance must be non-empty"]
    for row in acceptance:
        status = row.get("status")
        if issue.get("github_state") == "CLOSED" and issue.get("github_state_reason") == "COMPLETED" and status not in RESOLVED:
            errors.append(f"{row.get('id')}: completed Issue has unresolved acceptance")
        if status == "TRANSFERRED" and not row.get("successor"):
            errors.append(f"{row.get('id')}: transferred acceptance has no successor")
        if status in {"NOT_APPLICABLE", "SUPERSEDED"} and not row.get("rationale"):
            errors.append(f"{row.get('id')}: {status} acceptance has no rationale")

    impl = doc.get("implementation", {})
    candidates = impl.get("candidate_prs", []) if isinstance(impl, dict) else []
    landing = impl.get("landing") if isinstance(impl, dict) else None
    if disposition in {"DIRECTLY_LANDED", "CONSUMED_BY_CONVERGENCE"}:
        if not isinstance(landing, dict) or not sha40(landing.get("commit")) or not sha40(landing.get("tree")):
            errors.append(f"{disposition} requires immutable landed_via commit/tree")
    if disposition == "DIRECTLY_LANDED":
        direct = [p for p in candidates if p.get("classification") == "DIRECT" and p.get("merged") is True]
        if not direct:
            errors.append("DIRECTLY_LANDED requires a merged DIRECT candidate")
    if disposition == "CONSUMED_BY_CONVERGENCE":
        consumed = [p for p in candidates if p.get("classification") == "CONSUMED" and p.get("merged") is False]
        if not consumed:
            errors.append("CONSUMED_BY_CONVERGENCE requires a closed-unmerged CONSUMED candidate")
    if disposition == "SCOPE_TRANSFERRED":
        if not any(r.get("status") == "TRANSFERRED" and r.get("successor") for r in acceptance):
            errors.append("SCOPE_TRANSFERRED requires successor-bound acceptance")
    if disposition == "NOT_PLANNED" and issue.get("github_state_reason") != "NOT_PLANNED":
        errors.append("NOT_PLANNED disposition requires GitHub not_planned reason")

    ceiling = doc.get("evidence_ceiling")
    if ceiling not in CEILING:
        errors.append("invalid evidence ceiling")
    residual = doc.get("residual", [])
    if isinstance(residual, list) and ceiling in CEILING:
        if any(r.get("state") in {"NOT_IMPLEMENTED", "NOT_EXERCISED", "TRANSFERRED"} for r in residual) and CEILING[ceiling] >= CEILING["RELEASED"]:
            errors.append("unresolved residual cannot be promoted to RELEASED")
    shadow = doc.get("shadow_review", {})
    if issue.get("github_state") == "CLOSED" and shadow.get("verdict") not in {"PASS", "HUMAN_ADMIT_REQUIRED"}:
        errors.append("closed Issue lacks admissible independent Shadow verdict")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    doc = json.loads(args.contract.read_text(encoding="utf-8"))
    errors = validate(doc)
    if errors:
        for error in errors:
            print(f"ISSUE CLOSURE DRIFT: {error}")
        return 2
    print("ISSUE CLOSURE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
