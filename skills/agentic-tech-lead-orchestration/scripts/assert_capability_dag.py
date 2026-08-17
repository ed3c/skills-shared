#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

STATE_ORDER = {
    "CONTEXT_ADMITTED": 10,
    "TASK_DAG_COMPILED": 20,
    "WORKERS_ADMITTED": 30,
    "ATTEMPTS_EXECUTED": 40,
    "RESULTS_VERIFIED": 50,
    "CANDIDATES_COMPARED": 60,
    "CONVERGENCE_APPLIED": 70,
    "GLOBAL_OBJECTIVE_ASSERTED": 80,
    "DELIVERY_HANDOFF": 90,
}
SELECTED = {"REQUIRED", "OPTIONAL_SELECTED"}
ACCEPTED_VERDICTS = {"PASS", "DEGRADED", "FALLBACK"}


class ContractError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"ABSENT {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"INVALID_JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"INVALID_ROOT {path}: expected object")
    return value


def validate_schema(value: dict[str, Any], schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ContractError("MECHANISM jsonschema unavailable") from exc
    schema = read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # pragma: no cover - mechanism failure
        raise ContractError(f"MECHANISM invalid schema {schema_path}: {exc}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.absolute_path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(x) for x in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:8]
        )
        raise ContractError(f"SCHEMA_FAIL {schema_path.name}: {detail}")


def subject_of(value: dict[str, Any]) -> tuple[Any, Any]:
    subject = value.get("subject") if isinstance(value.get("subject"), dict) else {}
    return subject.get("base_commit"), subject.get("base_tree")


def transition_map(plan: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    transitions: dict[str, dict[str, Any]] = {}
    for item in plan.get("transitions", []):
        tid = item.get("id")
        if tid in transitions:
            errors.append(f"DUPLICATE_TRANSITION {tid}")
        else:
            transitions[str(tid)] = item

    for tid, item in transitions.items():
        selected = item.get("selection") in SELECTED
        matched = bool((item.get("trigger") or {}).get("matched"))
        evidence = (item.get("trigger") or {}).get("evidence") or []
        if selected and not matched:
            errors.append(f"SELECTED_WITHOUT_TRIGGER {tid}")
        if not selected and matched:
            errors.append(f"TRIGGER_WITHOUT_SELECTION {tid}")
        if selected and not evidence:
            errors.append(f"TRIGGER_EVIDENCE_ABSENT {tid}")
        if item.get("selection") == "REQUIRED" and item.get("fallback") != "STOP":
            errors.append(f"REQUIRED_FALLBACK_MUST_STOP {tid}")
        if item.get("selection") == "NOT_APPLICABLE" and item.get("fallback") != "SKIP":
            errors.append(f"NOT_APPLICABLE_FALLBACK_MUST_SKIP {tid}")
        if item.get("runtime_state") != "NOT_EXERCISED":
            errors.append(f"PLAN_CANNOT_CLAIM_RUNTIME_PASS {tid}")
        authority = item.get("authority") or {}
        if any(authority.get(key) is not False for key in ("merge", "publication", "secret_access")):
            errors.append(f"AUTHORITY_WIDENING {tid}")

        for pred in item.get("predecessor_transitions", []):
            if pred == tid:
                errors.append(f"SELF_DEPENDENCY {tid}")
            elif pred not in transitions:
                errors.append(f"ABSENT_PREDECESSOR {tid}->{pred}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(tid: str) -> None:
        if tid in visited:
            return
        if tid in visiting:
            errors.append(f"DAG_CYCLE {tid}")
            return
        visiting.add(tid)
        for pred in transitions[tid].get("predecessor_transitions", []):
            if pred in transitions:
                visit(pred)
        visiting.remove(tid)
        visited.add(tid)

    for tid in transitions:
        visit(tid)
    return transitions, errors


def receipt_map(receipts_doc: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    receipts: dict[str, dict[str, Any]] = {}
    for receipt in receipts_doc.get("receipts", []):
        tid = str(receipt.get("transition_id"))
        if tid in receipts:
            errors.append(f"DUPLICATE_RECEIPT {tid}")
        else:
            receipts[tid] = receipt
    return receipts, errors


def validate_semantics(
    contract: dict[str, Any],
    plan: dict[str, Any],
    receipts_doc: dict[str, Any],
    *,
    admit_state: str | None,
    fixture_mode: bool,
) -> list[str]:
    errors: list[str] = []
    transitions, transition_errors = transition_map(plan)
    receipts, receipt_errors = receipt_map(receipts_doc)
    errors.extend(transition_errors)
    errors.extend(receipt_errors)

    task_id = contract.get("task_id")
    task_subject = subject_of(contract)
    if plan.get("task_id") != task_id:
        errors.append("PLAN_TASK_MISMATCH")
    if subject_of(plan) != task_subject:
        errors.append("PLAN_SUBJECT_MISMATCH")

    for tid, receipt in receipts.items():
        item = transitions.get(tid)
        if item is None:
            errors.append(f"RECEIPT_UNKNOWN_TRANSITION {tid}")
            continue
        if item.get("selection") not in SELECTED:
            errors.append(f"RECEIPT_FOR_UNSELECTED_MODULE {tid}")
        if receipt.get("task_id") != task_id:
            errors.append(f"RECEIPT_TASK_MISMATCH {tid}")
        if subject_of(receipt) != task_subject:
            errors.append(f"RECEIPT_SUBJECT_MISMATCH {tid}")
        if receipt.get("module_path") != item.get("module_path"):
            errors.append(f"RECEIPT_MODULE_MISMATCH {tid}")
        if receipt.get("output_state") != item.get("produces_state"):
            errors.append(f"RECEIPT_OUTPUT_STATE_MISMATCH {tid}")
        missing_inputs = sorted(set(item.get("requires_states", [])) - set(receipt.get("input_states", [])))
        if missing_inputs:
            errors.append(f"RECEIPT_INPUT_STATE_MISSING {tid}:{','.join(missing_inputs)}")
        if receipt.get("verdict") not in ACCEPTED_VERDICTS:
            errors.append(f"RECEIPT_NOT_ADMISSIBLE {tid}:{receipt.get('verdict')}")
        if receipt.get("verdict") == "FALLBACK" and item.get("fallback") in {"STOP", "SKIP"}:
            errors.append(f"UNADMITTED_FALLBACK {tid}")
        if receipt.get("source_readback") is not True and item.get("module_path") in {
            "modules/semantic-intent-anchor.md",
            "modules/deterministic-code-intelligence.md",
        }:
            errors.append(f"SOURCE_READBACK_REQUIRED {tid}")
        authority = receipt.get("authority") or {}
        if any(authority.get(key) is not False for key in ("merge", "publication", "secret_access")):
            errors.append(f"RECEIPT_AUTHORITY_WIDENING {tid}")

        for pred in item.get("predecessor_transitions", []):
            pred_item = transitions.get(pred)
            if pred_item is None or pred_item.get("selection") not in SELECTED:
                continue
            pred_receipt = receipts.get(pred)
            if pred_receipt is None:
                errors.append(f"PREDECESSOR_RECEIPT_ABSENT {tid}<-{pred}")
                continue
            if pred_receipt.get("output_state") not in receipt.get("input_states", []):
                errors.append(f"PREDECESSOR_OUTPUT_NOT_CONSUMED {tid}<-{pred}")

    if admit_state is not None:
        target_rank = STATE_ORDER[admit_state]
        for tid, item in transitions.items():
            if item.get("selection") not in SELECTED:
                continue
            required_rank = STATE_ORDER[item["required_before_state"]]
            if required_rank > target_rank:
                continue
            receipt = receipts.get(tid)
            if receipt is None:
                errors.append(f"ADMISSION_RECEIPT_ABSENT {admit_state}:{tid}")
                continue
            if not fixture_mode and receipt.get("evidence_kind") != "LIVE":
                errors.append(f"LIVE_RECEIPT_REQUIRED {admit_state}:{tid}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--receipts", required=True)
    parser.add_argument("--admit-state", choices=sorted(STATE_ORDER))
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    try:
        contract = read_json(Path(args.contract))
        plan = read_json(Path(args.plan))
        receipts = read_json(Path(args.receipts))
        validate_schema(plan, root / "references" / "capability-plan.schema.json")
        validate_schema(receipts, root / "references" / "capability-receipts.schema.json")
        errors = validate_semantics(
            contract,
            plan,
            receipts,
            admit_state=args.admit_state,
            fixture_mode=args.fixture_mode,
        )
    except ContractError as exc:
        print(f"CAPABILITY-DAG-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    except Exception as exc:  # pragma: no cover
        print(f"CAPABILITY-DAG-INTERNAL-RED {exc}", file=sys.stderr)
        return 70

    if errors:
        for error in errors:
            print(f"CAPABILITY-DAG-RED {error}")
        return 2

    mode = "FIXTURE" if args.fixture_mode else "LIVE"
    target = args.admit_state or "STRUCTURE_ONLY"
    print(f"CAPABILITY-DAG-GREEN mode={mode} admit={target}; module runtime not inferred from plan presence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
