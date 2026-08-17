#!/usr/bin/env python3
"""Validate a procedural-core refactor contract and optional golden proof.

The checker is zero-network and never invokes a model, provider, forge, Worker,
or consumer command. It distinguishes schema/mechanism failure from an
executable contract refusal and never promotes fixture/synthetic evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
CONTRACT_SCHEMA = SKILL_ROOT / "references" / "refactor-contract.schema.json"
PROOF_SCHEMA = SKILL_ROOT / "references" / "golden-proof.schema.json"
EXPECTED_LAWS = {f"PCR-LAW-{index:03d}" for index in range(1, 12)}
REQUIRED_AUTHORITY = {
    "merge",
    "publication",
    "provider_activation",
    "permission_change",
    "semantic_conflict_resolution",
    "promotion",
}
LIVE_FORBIDDEN_PASS = {"live_model", "provider_runtime", "git_town", "forgejo", "publication"}


class InputError(ValueError):
    pass


class MechanismError(RuntimeError):
    pass


def read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise InputError(f"{label} not found: {path}")
    if path.stat().st_size > 4 * 1024 * 1024:
        raise InputError(f"{label} exceeds 4 MiB: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} root must be an object")
    return value


def canonical_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def schema_errors(value: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        raise MechanismError("jsonschema with Draft 2020-12 support is unavailable") from exc
    schema = read_object(schema_path, "schema")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise MechanismError(f"invalid schema {schema_path}: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    return [
        f"SCHEMA {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def safe_repo_file(raw: object, repo_root: Path) -> bool:
    if not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw:
        return False
    path = Path(raw)
    if ".." in path.parts:
        return False
    try:
        resolved = (repo_root / path).resolve()
        resolved.relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return False
    return resolved.is_file()


def validate_contract(contract: dict[str, Any], *, repo_root: Path = REPO_ROOT, proof_present: bool = False) -> list[str]:
    errors = schema_errors(contract, CONTRACT_SCHEMA)
    if errors:
        return errors

    treatments = contract["treatments"]
    arms = [item["arm"] for item in treatments]
    blobs = [item["blob"] for item in treatments]
    if len(arms) != len(set(arms)):
        errors.append("DUPLICATE_TREATMENT_ARM")
    if len(blobs) != len(set(blobs)):
        errors.append("DUPLICATE_TREATMENT_BLOB")
    by_arm = {item["arm"]: item for item in treatments}
    for required in ("A_OLD_MONOLITH", "B0_REFACTOR_AS_LANDED", "B1_REACHABILITY_REPAIRED"):
        if required not in by_arm:
            errors.append(f"MISSING_TREATMENT {required}")
    baseline = contract["baseline"]
    if "A_OLD_MONOLITH" in by_arm and baseline["skill_blob"] != by_arm["A_OLD_MONOLITH"]["blob"]:
        errors.append("BASELINE_BLOB_MISMATCH")
    if not baseline["strengths"]:
        errors.append("OLD_STRENGTHS_ABSENT")

    owner_by_kind = {
        "PROCEDURE": {"SKILL"},
        "DOMAIN": {"MODULE", "CONSUMER_RUNTIME"},
        "CONTRACT": {"REFERENCE"},
        "ASSERTION": {"SCRIPT"},
        "TEST": {"TEST"},
        "NAVIGATION": {"README"},
        "LIVE_RUNTIME": {"CONSUMER_RUNTIME"},
    }
    atom_ids: set[str] = set()
    for atom in contract["ownership"]:
        atom_id = atom["atom_id"]
        if atom_id in atom_ids:
            errors.append(f"DUPLICATE_OWNERSHIP_ATOM {atom_id}")
        atom_ids.add(atom_id)
        if atom["owner"] not in owner_by_kind[atom["kind"]]:
            errors.append(f"OWNERSHIP_MISMATCH {atom_id}:{atom['kind']}->{atom['owner']}")

    laws = contract["laws"]
    law_ids = [item["id"] for item in laws]
    if set(law_ids) != EXPECTED_LAWS or len(law_ids) != len(EXPECTED_LAWS):
        missing = sorted(EXPECTED_LAWS - set(law_ids))
        extra = sorted(set(law_ids) - EXPECTED_LAWS)
        errors.append(f"LAW_SET_DRIFT missing={missing} extra={extra}")
    for law in laws:
        if not safe_repo_file(law["assertion_owner"], repo_root):
            errors.append(f"ASSERTION_OWNER_UNREACHABLE {law['id']}:{law['assertion_owner']}")
        if not safe_repo_file(law["test_owner"], repo_root):
            errors.append(f"TEST_OWNER_UNREACHABLE {law['id']}:{law['test_owner']}")

    module_ids: set[str] = set()
    for module in contract["modules"]:
        module_id = module["module_id"]
        if module_id in module_ids:
            errors.append(f"DUPLICATE_MODULE {module_id}")
        module_ids.add(module_id)
        selected = module["selection"] in {"REQUIRED", "OPTIONAL_SELECTED"}
        if selected:
            if not module["trigger_evidence"]:
                errors.append(f"SELECTED_WITHOUT_TRIGGER {module_id}")
            if not module["predecessor_states"]:
                errors.append(f"SELECTED_WITHOUT_PREDECESSOR {module_id}")
            if not safe_repo_file(module["path"], repo_root):
                errors.append(f"SELECTED_MODULE_UNREACHABLE {module_id}:{module['path']}")
            if module["selection"] == "REQUIRED" and module["fallback"] != "STOP":
                errors.append(f"REQUIRED_FALLBACK_MUST_STOP {module_id}")
        else:
            if module["trigger_evidence"]:
                errors.append(f"NOT_APPLICABLE_HAS_TRIGGER {module_id}")
            if module["fallback"] != "SKIP":
                errors.append(f"NOT_APPLICABLE_FALLBACK_MUST_SKIP {module_id}")

    ab = contract["ab"]
    matched_fields = ["matched", "same_task", "same_base", "same_tests", "same_budgets", "same_carrier"]
    if ab["real_task_claim"] and not all(ab[field] is True for field in matched_fields):
        errors.append("UNMATCHED_REAL_TASK_AB")
    if not ab["failed_arms_retained"] or not ab["global_objective_required"] or not ab["cleanup_required"]:
        errors.append("AB_CLOSURE_REQUIREMENT_WEAKENED")

    evidence = contract["evidence"]
    if evidence["structural_ab"] == "PASS" and not proof_present:
        errors.append("STRUCTURAL_PASS_REQUIRES_PROOF")
    if evidence["real_task_ab"] == "PASS" and (not proof_present or not ab["real_task_claim"]):
        errors.append("REAL_TASK_PASS_REQUIRES_MATCHED_PROOF")
    for key in ("live_model", "provider_runtime", "delivery"):
        if evidence[key] == "PASS":
            errors.append(f"UNSUPPORTED_LIVE_PASS {key}")
    if evidence["merge"] != "HUMAN_ADMIT_REQUIRED":
        errors.append("MERGE_AUTHORITY_WIDENED")

    forbidden = set(contract["authority"]["automation_forbidden"])
    if not REQUIRED_AUTHORITY.issubset(forbidden):
        errors.append("AUTOMATION_AUTHORITY_WIDENED")
    if not contract["trace"]["issues"] or not contract["trace"]["branches"]:
        errors.append("TRACE_ROOT_ABSENT")
    return errors


def validate_proof(proof: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors = schema_errors(proof, PROOF_SCHEMA)
    if errors:
        return errors

    treatments = proof["treatments"]
    by_arm = {item["arm"]: item for item in treatments}
    required_arms = {
        "A_OLD_MONOLITH",
        "B0_REFACTOR_AS_LANDED",
        "B1_REACHABILITY_REPAIRED",
        "B2_CAUSAL_DAG_REPAIRED",
    }
    if set(by_arm) != required_arms or len(treatments) != len(required_arms):
        errors.append("GOLDEN_TREATMENT_SET_DRIFT")
    contract_by_arm = {item["arm"]: item for item in contract["treatments"]}
    for arm in required_arms:
        if arm not in contract_by_arm:
            errors.append(f"CONTRACT_MISSING_GOLDEN_ARM {arm}")
        elif contract_by_arm[arm]["blob"] != by_arm[arm]["blob"]:
            errors.append(f"TREATMENT_BLOB_MISMATCH {arm}")
    if not by_arm.get("A_OLD_MONOLITH", {}).get("strengths"):
        errors.append("GOLDEN_OLD_STRENGTHS_ABSENT")
    if not by_arm.get("B0_REFACTOR_AS_LANDED", {}).get("regressions"):
        errors.append("B0_REGRESSION_HIDDEN")

    structural = proof["structural_ab"]
    scores = structural["scores"]
    dimensions = structural["dimensions"]
    if any(value > dimensions for value in scores.values()):
        errors.append("STRUCTURAL_SCORE_EXCEEDS_DIMENSIONS")
    if scores["B2_CAUSAL_DAG_REPAIRED"] != dimensions:
        errors.append("B2_NOT_CLOSED_ON_ALL_TESTED_DIMENSIONS")
    if not (
        scores["B2_CAUSAL_DAG_REPAIRED"] > scores["B1_REACHABILITY_REPAIRED"]
        > scores["B0_REFACTOR_AS_LANDED"]
        and scores["A_OLD_MONOLITH"] > scores["B0_REFACTOR_AS_LANDED"]
    ):
        errors.append("STRUCTURAL_REGRESSION_OR_DOMINANCE_DRIFT")

    real = proof["real_task_ab"]
    if real["arms"]["B0_REFACTOR_AS_LANDED"] != "BLOCKED_DISPATCH_ROUTE_ABSENT":
        errors.append("B0_RUNTIME_REGRESSION_HIDDEN")
    for arm in ("A_OLD_MONOLITH", "B1_REACHABILITY_REPAIRED", "B2_CAUSAL_DAG_REPAIRED"):
        if real["arms"][arm] != "PASS":
            errors.append(f"EXECUTED_ARM_NOT_PASS {arm}")
    if not all(real[field] is True for field in ("same_task", "same_base", "same_tests", "same_budgets", "same_carrier")):
        errors.append("REAL_TASK_ARMS_NOT_MATCHED")

    for key in LIVE_FORBIDDEN_PASS:
        if proof["evidence"][key] in {"PASS", "IMPLEMENTED"}:
            errors.append(f"LIVE_EVIDENCE_PROMOTED {key}")
    if proof["evidence"]["merge"] != "HUMAN_ADMIT_REQUIRED":
        errors.append("GOLDEN_MERGE_AUTHORITY_WIDENED")
    if any(proof["authority"].values()):
        errors.append("GOLDEN_AUTHORITY_WIDENED")

    exact_heads = set(proof["trace"]["exact_heads"])
    if structural["proof_head"] not in exact_heads or real["proof_head"] not in exact_heads:
        errors.append("PROOF_HEAD_NOT_TRACED")
    if not {308, 315}.issubset(set(proof["trace"]["pull_requests"])):
        errors.append("PROOF_PR_TRACE_ABSENT")
    for item in proof["trace"]["ci_runs"]:
        if item["state"] == "PASS" and item["run_id"] is None:
            errors.append(f"CI_PASS_WITHOUT_RUN {item['head']}")
        if item["head"] not in exact_heads:
            errors.append(f"CI_HEAD_NOT_TRACED {item['head']}")

    if contract["evidence"]["structural_ab"] != "PASS":
        errors.append("CONTRACT_STRUCTURAL_STATE_NOT_PASS")
    if contract["evidence"]["real_task_ab"] != "PASS" or not contract["ab"]["real_task_claim"]:
        errors.append("CONTRACT_REAL_TASK_STATE_NOT_PASS")
    golden_modules = [item for item in contract["modules"] if item["module_id"] == "golden-proof-tech-lead"]
    if len(golden_modules) != 1 or golden_modules[0]["selection"] != "REQUIRED":
        errors.append("GOLDEN_MODULE_NOT_REQUIRED")
    return errors


def validate_bundle(contract: dict[str, Any], proof: dict[str, Any] | None, *, repo_root: Path = REPO_ROOT) -> list[str]:
    errors = validate_contract(contract, repo_root=repo_root, proof_present=proof is not None)
    if proof is not None:
        errors.extend(validate_proof(proof, contract))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)

    try:
        contract = read_object(args.contract.resolve(), "contract")
        proof = read_object(args.proof.resolve(), "proof") if args.proof else None
        errors = validate_bundle(contract, proof)
    except InputError as exc:
        print(f"PCR-INPUT-RED {exc}", file=sys.stderr)
        return 64
    except MechanismError as exc:
        print(f"PCR-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    except Exception as exc:
        print(f"PCR-MECHANISM-RED unexpected: {exc}", file=sys.stderr)
        return 70

    receipt = {
        "schema": "procedural-core-refactor/validation-receipt/v1",
        "contract": os.fspath(args.contract.resolve()),
        "contract_sha256": canonical_digest(contract),
        "proof": os.fspath(args.proof.resolve()) if args.proof else None,
        "proof_sha256": canonical_digest(proof) if proof else None,
        "verdict": "PASS" if not errors else "FAIL",
        "failures": errors,
        "evidence_class": "DETERMINISTIC_FIXTURE",
        "claims_not_proven": [
            "live model or provider behavior",
            "Git Town or forge delivery",
            "merge, release or production promotion",
        ],
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        for error in errors:
            print(f"PCR-RED {error}", file=sys.stderr)
        return 2
    print("PCR-GREEN contract + golden proof; live model/provider/delivery remain NOT_EXERCISED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
