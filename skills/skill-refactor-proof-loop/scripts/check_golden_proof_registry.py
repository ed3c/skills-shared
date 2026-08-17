#!/usr/bin/env python3
"""Validate golden proof registry entries against exact current repository bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
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
AUTHORITY_FIELDS = {
    "provider_activation", "publication", "semantic_conflict_resolution",
    "merge", "release", "promotion", "rollback",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class RegistryError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryError("registry root must be an object")
    return value


def validate_schema(value: dict[str, Any], schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RegistryError("jsonschema Draft 2020-12 validator unavailable") from exc
    try:
        schema = read_json(schema_path)
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise RegistryError(f"invalid/unreadable schema: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.absolute_path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise RegistryError(f"schema failure: {details}")


def safe_repo_path(repo: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RegistryError(f"unsafe path {value!r}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or pure.parts[:1] == (".git",):
        raise RegistryError(f"unsafe path {value!r}")
    path = repo.joinpath(*pure.parts)
    try:
        path.resolve().relative_to(repo.resolve())
    except ValueError as exc:
        raise RegistryError(f"path escapes repository {value!r}") from exc
    return path


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def validate(repo: Path, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    for proof in value.get("proofs", []):
        if not isinstance(proof, dict):
            errors.append("PROOF_NOT_OBJECT")
            continue
        pid = str(proof.get("id"))
        if pid in ids:
            errors.append(f"DUPLICATE_PROOF_ID {pid}")
        ids.add(pid)

        try:
            owner_root = safe_repo_path(repo, f"skills/{proof.get('owner_skill')}")
            entrypoint = safe_repo_path(repo, proof.get("entrypoint"))
            runner = safe_repo_path(repo, proof.get("runner"))
        except RegistryError as exc:
            errors.append(f"{pid} {exc}")
            continue
        if not (owner_root / "SKILL.md").is_file():
            errors.append(f"OWNER_SKILL_ABSENT {pid}")
        if not entrypoint.is_file():
            errors.append(f"ENTRYPOINT_ABSENT {pid}")
        if not runner.is_file():
            errors.append(f"RUNNER_ABSENT {pid}")
        elif entrypoint.is_file():
            try:
                runner_text = runner.read_text(encoding="utf-8")
            except OSError:
                runner_text = ""
            entry_rel = Path(proof["entrypoint"]).relative_to(Path("skills") / proof["owner_skill"]).as_posix()
            if entrypoint.name not in runner_text and entry_rel not in runner_text:
                errors.append(f"RUNNER_DOES_NOT_INVOKE_ENTRYPOINT {pid}")

        roles: list[str] = []
        treatment_ids: set[str] = set()
        for treatment in proof.get("treatments", []):
            if not isinstance(treatment, dict):
                errors.append(f"TREATMENT_NOT_OBJECT {pid}")
                continue
            tid = str(treatment.get("id"))
            if tid in treatment_ids:
                errors.append(f"DUPLICATE_TREATMENT_ID {pid}:{tid}")
            treatment_ids.add(tid)
            roles.append(str(treatment.get("role")))
            expected = treatment.get("blob_sha")
            if not isinstance(expected, str) or not HEX40.fullmatch(expected):
                errors.append(f"TREATMENT_BLOB_INVALID {pid}:{tid}")
                continue
            try:
                path = safe_repo_path(repo, treatment.get("path"))
            except RegistryError as exc:
                errors.append(f"{pid}:{tid} {exc}")
                continue
            if not path.is_file():
                errors.append(f"TREATMENT_PATH_ABSENT {pid}:{tid}")
            elif git_blob(path) != expected:
                errors.append(f"TREATMENT_BLOB_DRIFT {pid}:{tid}")
        if roles.count("OLD_CANONICAL") != 1:
            errors.append(f"OLD_CANONICAL_COUNT {pid}")
        if roles.count("REFACTOR_AS_LANDED") != 1:
            errors.append(f"REFACTOR_AS_LANDED_COUNT {pid}")
        if roles.count("REPAIRED_CANDIDATE") < 1:
            errors.append(f"REPAIRED_CANDIDATE_ABSENT {pid}")

        layers = proof.get("proof_layers") if isinstance(proof.get("proof_layers"), dict) else {}
        highest = proof.get("highest_layer")
        if highest not in LAYERS:
            errors.append(f"HIGHEST_LAYER_INVALID {pid}:{highest}")
            highest_index = -1
        else:
            highest_index = LAYERS.index(highest)
        for index, layer in enumerate(LAYERS):
            state = layers.get(layer)
            if index <= highest_index and state != PASS:
                errors.append(f"CLAIMED_LAYER_NOT_PASS {pid}:{layer}:{state}")
            if index > highest_index and state == PASS:
                errors.append(f"EVIDENCE_PROMOTION_ABOVE_HIGHEST {pid}:{layer}")
            if state != PASS and state not in NON_PASS:
                errors.append(f"LAYER_STATE_INVALID {pid}:{layer}:{state}")

        denominator = proof.get("denominator") if isinstance(proof.get("denominator"), dict) else {}
        for field in ("failed_retained", "stale_retained", "blocked_retained", "cancelled_retained", "superseded_retained"):
            if denominator.get(field) is not True:
                errors.append(f"DENOMINATOR_ERASURE {pid}:{field}")
        if proof.get("cleanup") != "CLEAN":
            errors.append(f"RESIDUE_NOT_CLEAN {pid}")

        authority = proof.get("authority") if isinstance(proof.get("authority"), dict) else {}
        if set(authority) != AUTHORITY_FIELDS:
            errors.append(f"AUTHORITY_FIELDS_DRIFT {pid}")
        for field in AUTHORITY_FIELDS:
            if authority.get(field) is not False:
                errors.append(f"AUTHORITY_WIDENING {pid}:{field}")

        remaining = proof.get("remaining_issues")
        if not isinstance(remaining, list) or not remaining:
            if layers.get("L4_MATCHED_LIVE_MODEL_RUNTIME") != PASS or layers.get("L5_DELIVERY_AND_HUMAN_ADMIT") != PASS:
                errors.append(f"UNEXERCISED_LAYER_HAS_NO_OWNER {pid}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    repo = (args.repo_root or root.parents[1]).resolve()
    schema = args.schema or (root / "references/golden-proof-registry.schema.json")
    try:
        value = read_json(args.registry)
        validate_schema(value, schema)
        errors = validate(repo, value)
    except RegistryError as exc:
        print(f"GOLDEN-PROOF-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    if errors:
        for error in errors:
            print(f"GOLDEN-PROOF-RED {error}", file=sys.stderr)
        return 2
    print(f"GOLDEN-PROOF-GREEN proofs={len(value['proofs'])}; live/delivery authority not inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
