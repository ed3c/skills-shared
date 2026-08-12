#!/usr/bin/env python3
"""Validate that mutation optimization targets are real, same-skill, visible eval cases."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def repo_path(root: Path, ref: str, label: str) -> Path:
    value = Path(ref)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError(f"{label} must be repository-relative")
    resolved = (root / value).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository") from exc
    return resolved


def case_index(root: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for base in (root / "evals" / "cases", root / "evals" / "holdout"):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json")):
            case = load_object(path)
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id:
                continue
            if case_id in index:
                raise ValueError(f"duplicate eval case id while validating mutation targets: {case_id}")
            index[case_id] = case
    return index


def validate_case_refs(skill: str, ids: object, index: dict[str, dict], *, role: str, forbid_holdout: bool) -> None:
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
        raise ValueError(f"{role} must be a non-empty unique case-id array")
    for case_id in ids:
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{role} contains invalid case id")
        case = index.get(case_id)
        if case is None:
            raise ValueError(f"{role} references missing eval case: {case_id}")
        if case.get("skill") != skill:
            raise ValueError(f"{role} case {case_id} belongs to {case.get('skill')}, not {skill}")
        if forbid_holdout and case.get("split") == "holdout":
            raise ValueError(f"optimizer target case must not be sealed holdout: {case_id}")


def validate_record(root: Path, record: dict, index: dict[str, dict]) -> None:
    skill = record.get("skill")
    effect = record.get("expected_effect")
    if not isinstance(skill, str) or not isinstance(effect, dict):
        raise ValueError("mutation record lacks skill/expected_effect")
    validate_case_refs(
        skill,
        effect.get("case_ids"),
        index,
        role="expected_effect.case_ids",
        forbid_holdout=True,
    )
    receipt_ref = record.get("evaluation_receipt")
    if not receipt_ref:
        return
    if not isinstance(receipt_ref, str):
        raise ValueError("evaluation_receipt must be a repository-relative path")
    receipt = load_object(repo_path(root, receipt_ref, "evaluation_receipt"))
    if receipt.get("schema_version") != "skill-mutation-eval/v1":
        raise ValueError("unsupported mutation evaluation receipt schema")
    validate_case_refs(
        skill,
        receipt.get("target_case_ids"),
        index,
        role="mutation receipt target_case_ids",
        forbid_holdout=True,
    )
    validate_case_refs(
        skill,
        receipt.get("non_target_case_ids"),
        index,
        role="mutation receipt non_target_case_ids",
        forbid_holdout=False,
    )


def check(root: Path) -> tuple[int, list[str]]:
    index = case_index(root)
    errors: list[str] = []
    count = 0
    mutations = root / "mutations"
    for path in sorted(mutations.rglob("*.jsonl")) if mutations.is_dir() else []:
        if "schema" in path.parts:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            count += 1
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record must be object")
                validate_record(root, value, index)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{path.relative_to(root)}:{number}: {exc}")
    return count, errors


def main() -> int:
    root = ROOT
    count, errors = check(root)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS mutation target visibility: {count} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
