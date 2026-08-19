from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_verifier() -> ModuleType:
    path = ROOT / "scripts" / "check_productization_preflight.py"
    spec = importlib.util.spec_from_file_location("check_productization_preflight", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def current_value() -> dict:
    path = ROOT / "docs" / "traceability" / "productization-operating-loop" / "implementation-preflight.json"
    return json.loads(path.read_text(encoding="utf-8"))


def atom(value: dict, atom_id: str) -> dict:
    return next(item for item in value["atoms"] if item["id"] == atom_id)


def test_current_productization_preflight_is_consistent() -> None:
    verifier = load_verifier()
    assert verifier.validate(current_value()) == []


def test_missing_owner_fails() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-C0")["owner"] = ""
    assert any("missing owner" in e for e in verifier.validate(value))


def test_stage1_cannot_start_without_c0() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-M")["start_dependencies"] = []
    assert any("POL-M missing C0" in e for e in verifier.validate(value))


def test_stage1_cannot_be_marked_ready_early() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-U")["state"] = "READY_TO_START"
    assert any("POL-U must remain blocked" in e for e in verifier.validate(value))


def test_compiler_requires_all_stage1_receipts() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-K")["completion_dependencies"].remove("POL-B receipt")
    assert any("POL-K missing Stage-1" in e for e in verifier.validate(value))


def test_compiler_and_shadow_cannot_share_writer_path() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    shared = atom(value, "POL-K")["planned_paths"][0]
    atom(value, "POL-E")["planned_paths"].append(shared)
    errors = verifier.validate(value)
    assert any("POL-K and POL-E writer paths overlap" in e or "exact path lease overlap" in e for e in errors)


def test_convergence_relation_cannot_be_downgraded() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-D")["relation"] = "SIBLING"
    assert any("POL-D must be the convergence owner" in e for e in verifier.validate(value))


def test_bootstrap_cannot_start_before_method_admission() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-A")["state"] = "READY_TO_START"
    assert any("POL-A cannot start" in e for e in verifier.validate(value))


def test_kaw_cannot_become_portable_core_owner() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-KAW")["relation"] = "TRUE_CHILD"
    assert any("POL-KAW must remain an external consumer adapter" in e for e in verifier.validate(value))


def test_live_evidence_cannot_become_implementation_ready() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    atom(value, "POL-LIVE")["state"] = "READY_TO_START"
    assert any("POL-LIVE cannot be implementation-ready" in e for e in verifier.validate(value))


def test_human_payment_authority_cannot_disappear() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    value["human_external_authority"].remove("user/customer/payment truth")
    assert any("required Human/external authority disappeared" in e for e in verifier.validate(value))


def test_market_demand_law_cannot_disappear() -> None:
    verifier = load_verifier()
    value = deepcopy(current_value())
    value["laws"].remove("market attention != demand")
    assert any("load-bearing productization law disappeared" in e for e in verifier.validate(value))
