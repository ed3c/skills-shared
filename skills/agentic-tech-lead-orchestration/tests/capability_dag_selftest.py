#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "assert_capability_dag.py"
CONTRACT = ROOT / "references" / "example-stack-contract.json"
PLAN = ROOT / "references" / "example-capability-plan.json"
RECEIPTS = ROOT / "references" / "example-capability-receipts.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run(plan: dict, receipts: dict, *, fixture: bool = True, admit: str = "DELIVERY_HANDOFF") -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="capability-dag-") as tmp:
        tmpdir = Path(tmp)
        plan_path = tmpdir / "plan.json"
        receipts_path = tmpdir / "receipts.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        receipts_path.write_text(json.dumps(receipts), encoding="utf-8")
        argv = [
            sys.executable,
            str(CHECKER),
            "--contract", str(CONTRACT),
            "--plan", str(plan_path),
            "--receipts", str(receipts_path),
            "--admit-state", admit,
        ]
        if fixture:
            argv.append("--fixture-mode")
        proc = subprocess.run(argv, text=True, capture_output=True)
        return proc.returncode, proc.stdout + proc.stderr


def require_red(name: str, plan: dict, receipts: dict, needle: str) -> None:
    code, output = run(plan, receipts)
    if code == 0 or needle not in output:
        raise AssertionError(f"{name} survived: code={code} output={output}")


def transition(plan: dict, tid: str) -> dict:
    return next(item for item in plan["transitions"] if item["id"] == tid)


def receipt(receipts: dict, tid: str) -> dict:
    return next(item for item in receipts["receipts"] if item["transition_id"] == tid)


def main() -> int:
    base_plan = load(PLAN)
    base_receipts = load(RECEIPTS)

    code, output = run(base_plan, base_receipts)
    assert code == 0, output

    # Fixture evidence must never become production admission evidence.
    code, output = run(base_plan, base_receipts, fixture=False)
    assert code == 2 and "LIVE_RECEIPT_REQUIRED" in output, output

    cases: list[tuple[str, dict, dict, str]] = []

    plan = copy.deepcopy(base_plan)
    transition(plan, "deterministic-context")["predecessor_transitions"] = ["missing-anchor"]
    cases.append(("absent-predecessor", plan, copy.deepcopy(base_receipts), "ABSENT_PREDECESSOR"))

    plan = copy.deepcopy(base_plan)
    transition(plan, "intent-anchor")["predecessor_transitions"] = ["deterministic-context"]
    cases.append(("cycle", plan, copy.deepcopy(base_receipts), "DAG_CYCLE"))

    plan = copy.deepcopy(base_plan)
    transition(plan, "intent-anchor")["predecessor_transitions"] = ["intent-anchor"]
    cases.append(("self-edge", plan, copy.deepcopy(base_receipts), "SELF_DEPENDENCY"))

    plan = copy.deepcopy(base_plan)
    transition(plan, "intent-anchor")["trigger"]["matched"] = False
    cases.append(("selected-without-trigger", plan, copy.deepcopy(base_receipts), "SELECTED_WITHOUT_TRIGGER"))

    plan = copy.deepcopy(base_plan)
    transition(plan, "vector-examples")["trigger"]["matched"] = True
    cases.append(("trigger-without-selection", plan, copy.deepcopy(base_receipts), "TRIGGER_WITHOUT_SELECTION"))

    receipts = copy.deepcopy(base_receipts)
    rogue = copy.deepcopy(receipt(receipts, "intent-anchor"))
    rogue["transition_id"] = "vector-examples"
    rogue["module_path"] = "modules/vector-store.md"
    rogue["output_state"] = "VECTOR_CONTEXT_READY"
    receipts["receipts"].append(rogue)
    cases.append(("receipt-for-unselected", copy.deepcopy(base_plan), receipts, "RECEIPT_FOR_UNSELECTED_MODULE"))

    receipts = copy.deepcopy(base_receipts)
    receipt(receipts, "deterministic-context")["subject"]["base_tree"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    cases.append(("receipt-subject", copy.deepcopy(base_plan), receipts, "RECEIPT_SUBJECT_MISMATCH"))

    receipts = copy.deepcopy(base_receipts)
    receipt(receipts, "worker-execution")["module_path"] = "modules/vector-store.md"
    cases.append(("receipt-module", copy.deepcopy(base_plan), receipts, "RECEIPT_MODULE_MISMATCH"))

    receipts = copy.deepcopy(base_receipts)
    receipt(receipts, "worker-execution")["output_state"] = "RESULTS_VERIFIED"
    cases.append(("receipt-output", copy.deepcopy(base_plan), receipts, "RECEIPT_OUTPUT_STATE_MISMATCH"))

    receipts = copy.deepcopy(base_receipts)
    receipt(receipts, "deterministic-context")["input_states"] = ["SYSTEM_CONTRACT_EXTRACTED"]
    cases.append(("predecessor-not-consumed", copy.deepcopy(base_plan), receipts, "RECEIPT_INPUT_STATE_MISSING"))

    receipts = copy.deepcopy(base_receipts)
    receipts["receipts"] = [r for r in receipts["receipts"] if r["transition_id"] != "worker-execution"]
    cases.append(("missing-admission-receipt", copy.deepcopy(base_plan), receipts, "ADMISSION_RECEIPT_ABSENT"))

    plan = copy.deepcopy(base_plan)
    transition(plan, "intent-anchor")["authority"]["merge"] = True
    cases.append(("authority-widening", plan, copy.deepcopy(base_receipts), "SCHEMA_FAIL"))

    for name, plan, receipts, needle in cases:
        require_red(name, plan, receipts, needle)

    print(f"CAPABILITY-DAG-SELFTEST-GREEN positive + live-evidence refusal + {len(cases)} planted causal defects closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
