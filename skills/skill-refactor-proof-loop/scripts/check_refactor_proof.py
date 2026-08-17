#!/usr/bin/env python3
"""Validate proof-carrying Skill refactor contracts without claiming live execution."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

LAYERS = [
    "L0_SOURCE_FREEZE",
    "L1_STRUCTURAL_REACHABILITY",
    "L2_EXECUTABLE_CONTRACT",
    "L3_HERMETIC_REAL_TASK",
    "L4_MATCHED_LIVE_MODEL_RUNTIME",
    "L5_DELIVERY_AND_HUMAN_ADMIT",
]
PASS = "PASS"
NON_PASS = {"FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "HUMAN_ADMIT_REQUIRED"}
ROLES = {"OLD_CANONICAL", "REFACTOR_AS_LANDED", "REPAIRED_CANDIDATE"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
AUTHORITY_FIELDS = {
    "provider_activation", "publication", "semantic_conflict_resolution",
    "merge", "release", "promotion", "rollback",
}


class ProofError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProofError("contract root must be an object")
    return value


def validate_shape_with_jsonschema(value: dict[str, Any], schema: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ProofError("jsonschema Draft 2020-12 validator unavailable") from exc
    try:
        schema_value = json.loads(schema.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema_value)
    except Exception as exc:
        raise ProofError(f"invalid/unreadable schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema_value).iter_errors(value), key=lambda e: list(e.absolute_path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise ProofError(f"schema failure: {details}")


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    treatments = value.get("treatments") if isinstance(value.get("treatments"), list) else []
    ids: set[str] = set()
    roles: list[str] = []
    for row in treatments:
        if not isinstance(row, dict):
            errors.append("TREATMENT_NOT_OBJECT")
            continue
        tid = row.get("id")
        if not isinstance(tid, str) or not tid or tid in ids:
            errors.append(f"TREATMENT_ID_INVALID {tid!r}")
        else:
            ids.add(tid)
        role = row.get("role")
        roles.append(str(role))
        if role not in ROLES:
            errors.append(f"TREATMENT_ROLE_INVALID {tid}:{role}")
        path = row.get("path")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"TREATMENT_PATH_UNSAFE {tid}")
        if not isinstance(row.get("blob_sha"), str) or not HEX40.fullmatch(row["blob_sha"]):
            errors.append(f"TREATMENT_BLOB_INVALID {tid}")
        if role in {"OLD_CANONICAL", "REFACTOR_AS_LANDED"} and row.get("state") != "FROZEN":
            errors.append(f"HISTORICAL_TREATMENT_NOT_FROZEN {tid}")
    if roles.count("OLD_CANONICAL") != 1:
        errors.append("EXACTLY_ONE_OLD_CANONICAL_REQUIRED")
    if roles.count("REFACTOR_AS_LANDED") != 1:
        errors.append("EXACTLY_ONE_REFACTOR_AS_LANDED_REQUIRED")
    if roles.count("REPAIRED_CANDIDATE") < 1:
        errors.append("REPAIRED_CANDIDATE_REQUIRED")

    strengths = value.get("protected_strengths") if isinstance(value.get("protected_strengths"), list) else []
    strength_ids: set[str] = set()
    for row in strengths:
        if not isinstance(row, dict):
            errors.append("PROTECTED_STRENGTH_NOT_OBJECT")
            continue
        sid = row.get("id")
        if not isinstance(sid, str) or not sid or sid in strength_ids:
            errors.append(f"PROTECTED_STRENGTH_ID_INVALID {sid!r}")
        else:
            strength_ids.add(sid)
        if not isinstance(row.get("old_evidence"), str) or not row["old_evidence"].strip():
            errors.append(f"OLD_STRENGTH_EVIDENCE_ABSENT {sid}")
        if not isinstance(row.get("new_assertion"), str) or not row["new_assertion"].strip():
            errors.append(f"NEW_STRENGTH_ASSERTION_ABSENT {sid}")

    layers = value.get("proof_layers") if isinstance(value.get("proof_layers"), dict) else {}
    seen_gap = False
    highest_pass = -1
    for index, layer in enumerate(LAYERS):
        state = layers.get(layer)
        if state == PASS:
            if seen_gap:
                errors.append(f"PROOF_LAYER_GAP {layer}")
            highest_pass = index
        elif state in NON_PASS:
            seen_gap = True
        else:
            errors.append(f"PROOF_LAYER_STATE_INVALID {layer}:{state}")
            seen_gap = True

    task = value.get("matched_task") if isinstance(value.get("matched_task"), dict) else {}
    if highest_pass >= LAYERS.index("L3_HERMETIC_REAL_TASK"):
        if task.get("required") is not True:
            errors.append("L3_REQUIRES_MATCHED_TASK")
        for field in ("same_base_tree", "same_contracts_tests", "same_budget", "same_carrier", "global_objective"):
            if task.get(field) is not True:
                errors.append(f"UNFAIR_MATCHED_TASK {field}")
    elif task.get("required") is True and any(task.get(field) is not True for field in ("same_base_tree", "same_contracts_tests", "same_budget", "same_carrier", "global_objective")):
        errors.append("DECLARED_MATCHED_TASK_IS_INCOMPLETE")

    denominator = value.get("denominator_policy") if isinstance(value.get("denominator_policy"), dict) else {}
    if highest_pass >= LAYERS.index("L3_HERMETIC_REAL_TASK"):
        for field in ("failed_retained", "stale_retained", "blocked_retained", "cancelled_retained", "superseded_retained"):
            if denominator.get(field) is not True:
                errors.append(f"DENOMINATOR_ERASURE {field}")

    evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else {}
    if layers.get("L4_MATCHED_LIVE_MODEL_RUNTIME") == PASS and not evidence.get("live_runtime_receipts"):
        errors.append("LIVE_RUNTIME_RECEIPTS_ABSENT")
    if layers.get("L5_DELIVERY_AND_HUMAN_ADMIT") == PASS:
        if not evidence.get("delivery_receipts"):
            errors.append("DELIVERY_RECEIPTS_ABSENT")
        if not evidence.get("human_admit_receipts"):
            errors.append("HUMAN_ADMIT_RECEIPTS_ABSENT")

    cleanup = value.get("cleanup") if isinstance(value.get("cleanup"), dict) else {}
    if highest_pass >= LAYERS.index("L3_HERMETIC_REAL_TASK"):
        for field in ("processes", "worktrees", "branches", "leases", "temporary_state"):
            if cleanup.get(field) != "CLEAN":
                errors.append(f"RESIDUE_NOT_CLEAN {field}:{cleanup.get(field)}")

    authority = value.get("authority") if isinstance(value.get("authority"), dict) else {}
    if set(authority) != AUTHORITY_FIELDS:
        errors.append("AUTHORITY_FIELDS_DRIFT")
    for field in AUTHORITY_FIELDS:
        if authority.get(field) is not False:
            errors.append(f"AUTHORITY_WIDENING {field}")

    remaining = value.get("remaining_issues")
    if not isinstance(remaining, list) or any(not isinstance(item, int) or isinstance(item, bool) or item < 1 for item in remaining):
        errors.append("REMAINING_ISSUES_INVALID")
    if layers.get("L4_MATCHED_LIVE_MODEL_RUNTIME") != PASS and not remaining:
        errors.append("UNEXERCISED_LIVE_LAYER_HAS_NO_OWNER")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    schema = args.schema or (root / "references/refactor-proof-contract.schema.json")
    try:
        value = load(args.contract)
        validate_shape_with_jsonschema(value, schema)
        errors = validate(value)
    except ProofError as exc:
        print(f"REFACTOR-PROOF-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    if errors:
        for error in errors:
            print(f"REFACTOR-PROOF-RED {error}", file=sys.stderr)
        return 2
    print(f"REFACTOR-PROOF-GREEN proof={value['proof_id']} owner={value['owner_skill']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
