#!/usr/bin/env python3
"""Fail closed when GitHub Issue closure outruns acceptance or landed evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA = set("0123456789abcdef")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DISPOSITIONS = {"DIRECTLY_LANDED", "CONSUMED_BY_CONVERGENCE", "SCOPE_TRANSFERRED", "SUPERSEDED", "NOT_PLANNED"}
RESOLVED = {"SATISFIED", "TRANSFERRED", "NOT_APPLICABLE", "SUPERSEDED"}
CEILING = {"SOURCE_ONLY": 0, "STATIC": 1, "DETERMINISTIC": 2, "LIVE": 3, "HUMAN_ADMITTED": 4, "RELEASED": 5}
SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
ENFORCED_FROM = SKILL_ROOT / "references" / "closure-audit" / "enforced-from.json"


def sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(c in SHA for c in text)


def repo_id(value: object) -> bool:
    return bool(REPO.fullmatch(str(value)))


def identity_key(identity: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (identity.get("host_class"), identity.get("session_id"), identity.get("worktree"))


def shadow_binding_errors(shadow: dict[str, Any], root: Path) -> list[str]:
    """A PASS is a claim about a second identity, so it must name one and show its receipt.

    Mirrors live-shadow-case-delta-receipt.schema.json: builder and Shadow are distinct
    runtime identities there, packet author and Shadow are distinct identities here.
    """
    author = shadow.get("packet_author")
    reviewer = shadow.get("shadow_identity")
    if not isinstance(author, dict) or not isinstance(reviewer, dict):
        return ["PASS requires packet_author and shadow_identity; a self-authored packet is HUMAN_ADMIT_REQUIRED"]
    errors: list[str] = []
    if not reviewer.get("session_id"):
        errors.append("PASS requires a named Shadow session_id; an anonymous Shadow cannot be read back")
    if identity_key(author) == identity_key(reviewer):
        errors.append("PASS requires a Shadow identity distinct from the packet author")
    receipt = shadow.get("receipt")
    if not isinstance(receipt, dict):
        errors.append("PASS requires a Shadow receipt binding")
        return errors
    path = root / str(receipt.get("path"))
    if not path.is_file():
        errors.append(f"Shadow receipt {receipt.get('path')} is absent at its bound path")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != receipt.get("sha256"):
        errors.append(f"Shadow receipt {receipt.get('path')} does not match its bound sha256")
    return errors


def is_historical(name: str, doc: dict[str, Any]) -> bool | None:
    """True when this exact file/Issue/verdict predates the #606 binding law.

    None means the ledger itself is missing: that is a broken gate, not an empty
    grandfather set, and the caller must fail closed rather than enforce blindly.
    """
    if not ENFORCED_FROM.is_file():
        return None
    ledger = json.loads(ENFORCED_FROM.read_text(encoding="utf-8"))
    return any(
        entry.get("file") == name
        and entry.get("issue") == doc.get("issue", {}).get("number")
        and entry.get("shadow_verdict") == doc.get("shadow_review", {}).get("verdict")
        for entry in ledger.get("grandfathered_unbound_pass", [])
    )


def validate(doc: dict[str, Any], historical: bool = False, root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    if doc.get("schema_version") != "agentic-tech-lead/issue-closure-contract/v1":
        errors.append("schema_version drifted")
    issue = doc.get("issue", {})
    if not repo_id(issue.get("repository")):
        errors.append("issue.repository must be owner/repo")
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
    for candidate in candidates:
        if not repo_id(candidate.get("repository")):
            errors.append(f"PR #{candidate.get('number')}: candidate repository is ambiguous")
    if disposition in {"DIRECTLY_LANDED", "CONSUMED_BY_CONVERGENCE"}:
        if not isinstance(landing, dict) or not repo_id(landing.get("repository")) or not sha40(landing.get("commit")) or not sha40(landing.get("tree")):
            errors.append(f"{disposition} requires repository-qualified immutable landed_via commit/tree")
    if disposition == "DIRECTLY_LANDED":
        direct = [p for p in candidates if p.get("classification") == "DIRECT" and p.get("merged") is True]
        if not direct:
            errors.append("DIRECTLY_LANDED requires a merged DIRECT candidate")
        elif isinstance(landing, dict) and not any(
            p.get("repository") == landing.get("repository") and p.get("number") == landing.get("via_pr") for p in direct
        ):
            errors.append("DIRECTLY_LANDED landing does not identify the merged DIRECT candidate")
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
    if shadow.get("verdict") == "PASS" and not historical:
        errors.extend(shadow_binding_errors(shadow, root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    doc = json.loads(args.contract.read_text(encoding="utf-8"))
    historical = is_historical(args.contract.name, doc)
    if historical is None:
        print(f"ISSUE CLOSURE DRIFT: {ENFORCED_FROM} is absent; the Shadow-binding start point cannot be read")
        return 2
    errors = validate(doc, historical=historical)
    if errors:
        for error in errors:
            print(f"ISSUE CLOSURE DRIFT: {error}")
        return 2
    print("ISSUE CLOSURE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
