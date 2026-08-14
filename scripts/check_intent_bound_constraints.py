#!/usr/bin/env python3
"""Validate Intent-Bound Constraint contracts and diagnostic receipts.

The checker is dependency-free. JSON Schema files define interchange shape; this
script owns semantic closure checks that JSON Schema cannot express.

Exit codes:
  0  declared subject passed
  2  evaluated contract or receipt failed
  64 usage or input error
  70 evaluator failure
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

MODULE_POLICY = {
    "may_add_constraints": True,
    "may_tighten_constraints": True,
    "may_weaken_constraints": False,
    "may_widen_effects": False,
    "may_bypass_human_admit": False,
    "ambiguity_action": "BLOCK",
}
COMPLETION_POLICY = {
    "deterministic_failure_vetoes_advisory": True,
    "stale_evidence_blocks": True,
    "no_improvement_action": "STOP",
    "ambiguity_action": "BLOCK",
    "private_chain_of_thought": "FORBIDDEN",
}
REQUIRED_FORBIDDEN_REPAIR_CODES = {
    "WEAKEN_CONSTRAINT",
    "EDIT_EVALUATOR_FOR_PASS",
    "DELETE_CONTROL",
    "WIDEN_EFFECTS",
    "BYPASS_HUMAN_ADMIT",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _nonempty_strings(value: Any, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if not value:
        return allow_empty
    return all(isinstance(item, str) and item.strip() for item in value)


def _load_object(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("root must be a JSON object")
    return parsed, raw


def _valid_subject_identity(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    repository = value.get("repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        return False
    immutable = 0
    if "commit_sha" in value:
        immutable += int(isinstance(value["commit_sha"], str) and bool(SHA40.fullmatch(value["commit_sha"])))
    if "tree_sha" in value:
        immutable += int(isinstance(value["tree_sha"], str) and bool(SHA40.fullmatch(value["tree_sha"])))
    if "artifact_digest" in value:
        digest = value["artifact_digest"]
        immutable += int(
            isinstance(digest, str)
            and digest.startswith("sha256:")
            and bool(SHA256.fullmatch(digest.removeprefix("sha256:")))
        )
    return immutable >= 1


def validate_contract(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != "intent-bound-constraint/v1":
        errors.append("schema_version must be intent-bound-constraint/v1")
    if not isinstance(data.get("contract_id"), str) or not data["contract_id"].strip():
        errors.append("contract_id must be a non-empty string")
    if not isinstance(data.get("contract_version"), str) or not data["contract_version"].strip():
        errors.append("contract_version must be a non-empty string")
    if not _valid_subject_identity(data.get("subject_identity")):
        errors.append("subject_identity must bind a repository and at least one immutable identity")
    if data.get("module_policy") != MODULE_POLICY:
        errors.append("module_policy must be monotonic and block ambiguous routing")
    if data.get("completion_policy") != COMPLETION_POLICY:
        errors.append("completion_policy must preserve veto, freshness, stop, ambiguity, and reflection laws")
    if data.get("diagnostic_reflection_schema") != "evals/schema/diagnostic-reflection-receipt.schema.json":
        errors.append("diagnostic_reflection_schema must point to the canonical receipt schema")

    intents = data.get("meta_intents")
    constraints = data.get("constraints")
    if not isinstance(intents, list) or not intents:
        errors.append("meta_intents must be a non-empty list")
        intents = []
    if not isinstance(constraints, list) or not constraints:
        errors.append("constraints must be a non-empty list")
        constraints = []

    intent_ids: set[str] = set()
    obligation_owner: dict[str, str] = {}
    all_obligations: set[str] = set()
    for index, intent in enumerate(intents):
        if not isinstance(intent, dict):
            errors.append(f"meta_intents[{index}] must be an object")
            continue
        intent_id = intent.get("id")
        if not isinstance(intent_id, str) or not intent_id.startswith("MI-"):
            errors.append(f"meta_intents[{index}].id must start with MI-")
            continue
        if intent_id in intent_ids:
            errors.append(f"duplicate meta-intent id: {intent_id}")
        intent_ids.add(intent_id)
        if not _nonempty_strings(intent.get("scope")):
            errors.append(f"{intent_id} must declare scope")
        if not _nonempty_strings(intent.get("forbidden_outcomes")):
            errors.append(f"{intent_id} must declare forbidden outcomes")
        obligations = intent.get("proof_obligations")
        if not _nonempty_strings(obligations):
            errors.append(f"{intent_id} must declare at least one proof obligation")
            obligations = []
        for obligation in obligations:
            if not obligation.startswith("PO-"):
                errors.append(f"{intent_id} proof obligation must start with PO-: {obligation}")
            if obligation in obligation_owner:
                errors.append(
                    f"duplicate proof obligation {obligation} in {obligation_owner[obligation]} and {intent_id}"
                )
            obligation_owner[obligation] = intent_id
            all_obligations.add(obligation)
        if not _nonempty_strings(intent.get("completion_criteria")):
            errors.append(f"{intent_id} must declare observable completion criteria")
        if not _nonempty_strings(intent.get("human_owned_boundaries"), allow_empty=True):
            errors.append(f"{intent_id}.human_owned_boundaries must be a string array")

    constraint_ids: set[str] = set()
    covered_intents: set[str] = set()
    discharged_obligations: set[str] = set()
    for index, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            errors.append(f"constraints[{index}] must be an object")
            continue
        constraint_id = constraint.get("id")
        if not isinstance(constraint_id, str) or not constraint_id.startswith("C-"):
            errors.append(f"constraints[{index}].id must start with C-")
            continue
        if constraint_id in constraint_ids:
            errors.append(f"duplicate constraint id: {constraint_id}")
        constraint_ids.add(constraint_id)

        protected = constraint.get("protects_intents")
        if not _nonempty_strings(protected):
            errors.append(f"{constraint_id} is orphaned: protects_intents is empty")
            protected = []
        for intent_id in protected:
            if intent_id not in intent_ids:
                errors.append(f"{constraint_id} references unknown meta-intent {intent_id}")
            else:
                covered_intents.add(intent_id)

        obligations = constraint.get("discharges_obligations")
        if not _nonempty_strings(obligations):
            errors.append(f"{constraint_id} must discharge at least one proof obligation")
            obligations = []
        for obligation in obligations:
            owner = obligation_owner.get(obligation)
            if owner is None:
                errors.append(f"{constraint_id} references unknown proof obligation {obligation}")
            elif owner not in protected:
                errors.append(
                    f"{constraint_id} discharges {obligation} for {owner} but does not protect that intent"
                )
            else:
                discharged_obligations.add(obligation)

        severity = constraint.get("severity")
        evidence_class = constraint.get("evidence_class")
        evaluator = constraint.get("evaluator")
        if severity not in {"hard", "advisory"}:
            errors.append(f"{constraint_id}.severity must be hard or advisory")
        if evidence_class not in {"deterministic", "advisory", "external"}:
            errors.append(f"{constraint_id}.evidence_class is invalid")
        if severity == "hard" and evidence_class == "advisory":
            errors.append(f"{constraint_id} is hard but relies on advisory evidence")
        if severity == "hard" and not _nonempty_strings(constraint.get("negative_controls")):
            errors.append(f"{constraint_id} is hard but has no negative control")
        if severity == "hard" and not _nonempty_strings(constraint.get("mutation_controls")):
            errors.append(f"{constraint_id} is hard but has no mutation control")

        if not isinstance(evaluator, dict):
            errors.append(f"{constraint_id} evaluator must be an object")
            evaluator = {}
        evaluator_kind = evaluator.get("kind")
        if evidence_class == "deterministic" and evaluator_kind not in {"command", "schema"}:
            errors.append(f"{constraint_id} deterministic evidence needs a command or schema evaluator")
        if evidence_class == "external" and evaluator_kind != "external_observation":
            errors.append(f"{constraint_id} external evidence needs an external_observation evaluator")
        if evaluator_kind == "command":
            if not _nonempty_strings(evaluator.get("argv")):
                errors.append(f"{constraint_id} command evaluator needs a non-empty argv array")
            codes = evaluator.get("success_exit_codes")
            if not isinstance(codes, list) or not codes or not all(isinstance(code, int) for code in codes):
                errors.append(f"{constraint_id} command evaluator needs success_exit_codes")
            timeout = evaluator.get("timeout_seconds")
            if not isinstance(timeout, int) or timeout <= 0:
                errors.append(f"{constraint_id} command evaluator needs a positive timeout_seconds")
        elif evaluator_kind == "schema" and not isinstance(evaluator.get("schema"), str):
            errors.append(f"{constraint_id} schema evaluator needs a schema path")
        elif evaluator_kind == "external_observation" and not isinstance(evaluator.get("authority"), str):
            errors.append(f"{constraint_id} external evaluator needs an authority")

        repairability = constraint.get("repairability")
        retry_budget = constraint.get("retry_budget")
        if not isinstance(retry_budget, int) or retry_budget < 0:
            errors.append(f"{constraint_id}.retry_budget must be a non-negative integer")
        elif repairability == "repairable":
            if retry_budget < 1:
                errors.append(f"{constraint_id} is repairable but has no retry budget")
            if not _nonempty_strings(constraint.get("allowed_repairs")):
                errors.append(f"{constraint_id} is repairable but has no allowed repair")
            metric = constraint.get("expected_delta_metric")
            if not isinstance(metric, str) or not metric.strip():
                errors.append(f"{constraint_id} is repairable but has no expected delta metric")
        elif repairability in {"terminal", "human_owned"}:
            if retry_budget != 0:
                errors.append(f"{constraint_id} is {repairability} and must have retry_budget 0")
            if constraint.get("allowed_repairs") not in ([], None):
                errors.append(f"{constraint_id} is {repairability} and must not allow automatic repairs")
            if constraint.get("expected_delta_metric") is not None:
                errors.append(f"{constraint_id} is {repairability} and must not declare an automatic delta")
        else:
            errors.append(f"{constraint_id}.repairability is invalid")

        forbidden = constraint.get("forbidden_repair_codes")
        if not isinstance(forbidden, list):
            errors.append(f"{constraint_id}.forbidden_repair_codes must be an array")
        else:
            missing = sorted(REQUIRED_FORBIDDEN_REPAIR_CODES - set(forbidden))
            if missing:
                errors.append(f"{constraint_id} is missing forbidden repair codes: {', '.join(missing)}")

    for intent_id in sorted(intent_ids - covered_intents):
        errors.append(f"uncovered meta-intent: {intent_id}")
    for obligation in sorted(all_obligations - discharged_obligations):
        errors.append(f"undischarged proof obligation: {obligation}")

    return errors


def validate_receipt(
    receipt: dict[str, Any],
    contract: dict[str, Any],
    contract_raw: bytes,
) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "diagnostic-reflection-receipt/v1":
        errors.append("receipt schema_version must be diagnostic-reflection-receipt/v1")
    if receipt.get("subject_identity") != contract.get("subject_identity"):
        errors.append("receipt subject_identity does not match the contract subject")

    identity = receipt.get("contract_identity")
    expected_digest = hashlib.sha256(contract_raw).hexdigest()
    if not isinstance(identity, dict):
        errors.append("receipt contract_identity must be an object")
    else:
        if identity.get("contract_id") != contract.get("contract_id"):
            errors.append("receipt contract_id does not match")
        if identity.get("contract_version") != contract.get("contract_version"):
            errors.append("receipt contract_version does not match")
        if identity.get("contract_sha256") != expected_digest:
            errors.append("receipt contract_sha256 does not match the exact contract bytes")

    constraints = {
        item.get("id"): item
        for item in contract.get("constraints", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    failed_id = receipt.get("failed_constraint_id")
    constraint = constraints.get(failed_id)
    if constraint is None:
        errors.append(f"receipt references unknown failed constraint {failed_id}")
        return errors

    at_risk = receipt.get("intent_at_risk")
    if not _nonempty_strings(at_risk):
        errors.append("receipt intent_at_risk must be a non-empty string array")
        at_risk = []
    protected = set(constraint.get("protects_intents", []))
    unknown_risk = sorted(set(at_risk) - protected)
    if unknown_risk:
        errors.append(f"receipt intent_at_risk is outside the failed constraint: {', '.join(unknown_risk)}")

    evaluator_identity = receipt.get("evaluator_identity")
    evaluator = constraint.get("evaluator", {})
    if not isinstance(evaluator_identity, dict):
        errors.append("receipt evaluator_identity must be an object")
    else:
        if evaluator_identity.get("id") != evaluator.get("id"):
            errors.append("receipt evaluator id does not match the failed constraint")
        if evaluator_identity.get("version") != evaluator.get("version"):
            errors.append("receipt evaluator version does not match the failed constraint")

    decision = receipt.get("decision")
    selected_repair = receipt.get("selected_repair")
    expected_delta = receipt.get("expected_delta")
    retry_index = receipt.get("retry_index")
    actual_delta = receipt.get("actual_delta")
    retry_budget = constraint.get("retry_budget", 0)

    if not isinstance(retry_index, int) or retry_index < 0:
        errors.append("receipt retry_index must be a non-negative integer")
    elif retry_index > retry_budget:
        errors.append("receipt retry_index exceeds the constraint retry budget")

    if decision == "REPAIR":
        if constraint.get("repairability") != "repairable":
            errors.append("receipt selects REPAIR for a non-repairable constraint")
        if selected_repair not in constraint.get("allowed_repairs", []):
            errors.append("receipt selected_repair is not allowlisted")
        if not isinstance(expected_delta, dict):
            errors.append("repair receipt must declare expected_delta")
        elif expected_delta.get("metric") != constraint.get("expected_delta_metric"):
            errors.append("receipt expected_delta metric does not match the constraint")
        if isinstance(retry_index, int) and retry_index >= retry_budget:
            errors.append("receipt cannot select REPAIR at or beyond retry exhaustion")
        if isinstance(actual_delta, dict) and actual_delta.get("improved") is False:
            errors.append("receipt cannot continue repair after a measured no-improvement result")
    elif decision == "VERIFIED":
        if not isinstance(actual_delta, dict) or actual_delta.get("improved") is not True:
            errors.append("VERIFIED requires an actual_delta with improved=true")
        if receipt.get("stop_reason") not in (None, ""):
            errors.append("VERIFIED must not include a stop_reason")
    elif decision in {"BLOCK", "REJECT", "HUMAN_ADMIT_REQUIRED"}:
        if selected_repair is not None:
            errors.append(f"{decision} must not select an automatic repair")
        if not isinstance(receipt.get("stop_reason"), str) or not receipt["stop_reason"].strip():
            errors.append(f"{decision} requires a stop_reason")
    else:
        errors.append("receipt decision is invalid")

    if not _nonempty_strings(receipt.get("evidence_refs")):
        errors.append("receipt must contain at least one evidence reference")
    if not isinstance(receipt.get("observation_summary"), str) or not receipt["observation_summary"].strip():
        errors.append("receipt observation_summary must be non-empty")
    if not isinstance(receipt.get("diagnosis_code"), str) or not receipt["diagnosis_code"].strip():
        errors.append("receipt diagnosis_code must be non-empty")

    return errors


def _emit(kind: str, errors: list[str], json_output: bool) -> None:
    receipt = {
        "schema_version": "intent-bound-constraint-validation-receipt/v1",
        "kind": kind,
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
    }
    if json_output:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
    else:
        print(f"PASS: {kind} verified")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("contract", "receipt"))
    parser.add_argument("subject", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    try:
        subject, _subject_raw = _load_object(args.subject)
        if args.kind == "contract":
            errors = validate_contract(subject)
        else:
            if args.contract is None:
                print("input error: receipt validation requires --contract", file=sys.stderr)
                return 64
            contract, contract_raw = _load_object(args.contract)
            contract_errors = validate_contract(contract)
            if contract_errors:
                errors = [f"contract invalid: {item}" for item in contract_errors]
            else:
                errors = validate_receipt(subject, contract, contract_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 64
    except Exception as exc:
        print(f"internal evaluator error: {exc}", file=sys.stderr)
        return 70

    _emit(args.kind, errors, args.json_output)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
