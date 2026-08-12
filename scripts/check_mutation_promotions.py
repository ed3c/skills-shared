#!/usr/bin/env python3
"""Admit only deterministically won mutation candidates into the promotion registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.check_mutation_lineage import validate

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mutations" / "promotions.json"


def _repo_path(root: Path, ref: str, label: str) -> Path:
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError(f"{label} must be a non-empty repository-relative path")
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be repository-relative")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository") from exc
    return resolved


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _lineage_record(root: Path, ref: str, line_number: int) -> dict:
    path = _repo_path(root, ref, "lineage_ref")
    if path.suffix != ".jsonl":
        raise ValueError("lineage_ref must point to a .jsonl lineage file")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read lineage_ref {ref}: {exc}") from exc
    if not isinstance(line_number, int) or line_number < 1 or line_number > len(lines):
        raise ValueError(f"line_number {line_number!r} is outside lineage file {ref}")
    raw = lines[line_number - 1]
    if not raw.strip():
        raise ValueError(f"lineage_ref {ref}:{line_number} is blank")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"lineage_ref {ref}:{line_number} is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"lineage_ref {ref}:{line_number} must contain an object")
    return value


def validate_promotion(entry: dict, root: Path) -> None:
    required = {"skill", "candidate_sha", "lineage_ref", "line_number", "evaluation_receipt"}
    missing = required - entry.keys()
    if missing:
        raise ValueError(f"promotion missing fields: {', '.join(sorted(missing))}")
    record = _lineage_record(root, entry["lineage_ref"], entry["line_number"])
    if record.get("skill") != entry.get("skill"):
        raise ValueError("promotion skill does not match lineage record")
    if record.get("candidate_sha") != entry.get("candidate_sha"):
        raise ValueError("promotion candidate_sha does not match lineage record")
    if record.get("evaluation_receipt") != entry.get("evaluation_receipt"):
        raise ValueError("promotion evaluation_receipt does not match lineage record")
    if record.get("status") != "won":
        raise ValueError(f"promotion candidate is {record.get('status')!r}, not won")
    # Recompute the terminal decision from landed evidence instead of trusting the
    # status string that the optimizer wrote into its lineage record.
    validate(record, root)


def check(root: Path) -> tuple[int, list[str]]:
    registry_path = root / "mutations" / "promotions.json"
    try:
        registry = _load_object(registry_path, "mutation promotion registry")
    except ValueError as exc:
        return 0, [str(exc)]
    if registry.get("schema_version") != "skill-mutation-promotion-registry/v1":
        return 0, ["unsupported mutation promotion registry schema"]
    promotions = registry.get("promotions")
    if not isinstance(promotions, list):
        return 0, ["mutation promotion registry promotions must be an array"]
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(promotions):
        if not isinstance(entry, dict):
            errors.append(f"promotions[{index}] must be an object")
            continue
        identity = (str(entry.get("skill", "")), str(entry.get("candidate_sha", "")))
        if identity in seen:
            errors.append(f"promotions[{index}] duplicates promoted candidate {identity[0]}@{identity[1]}")
            continue
        seen.add(identity)
        try:
            validate_promotion(entry, root)
        except ValueError as exc:
            errors.append(f"promotions[{index}]: {exc}")
    return len(promotions), errors


def main() -> int:
    count, errors = check(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS mutation promotion registry: {count} admitted candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
