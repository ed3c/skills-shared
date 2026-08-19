from __future__ import annotations

import importlib.util
import json
import sys
import unittest
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


class ProductizationPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = load_verifier()

    def assert_has_error(self, value: dict, needle: str) -> None:
        errors = self.verifier.validate(value)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_current_productization_preflight_is_consistent(self) -> None:
        self.assertEqual(self.verifier.validate(current_value()), [])

    def test_missing_owner_fails(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-C0")["owner"] = ""
        self.assert_has_error(value, "missing owner")

    def test_stage1_cannot_start_without_c0(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-M")["start_dependencies"] = []
        self.assert_has_error(value, "POL-M missing C0")

    def test_stage1_cannot_be_marked_ready_early(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-U")["state"] = "READY_TO_START"
        self.assert_has_error(value, "POL-U must remain blocked")

    def test_compiler_requires_all_stage1_receipts(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-K")["completion_dependencies"].remove("POL-B receipt")
        self.assert_has_error(value, "POL-K missing Stage-1")

    def test_compiler_and_shadow_cannot_share_writer_path(self) -> None:
        value = deepcopy(current_value())
        shared = atom(value, "POL-K")["planned_paths"][0]
        atom(value, "POL-E")["planned_paths"].append(shared)
        errors = self.verifier.validate(value)
        self.assertTrue(
            any(
                "POL-K and POL-E writer paths overlap" in error
                or "exact path lease overlap" in error
                for error in errors
            ),
            errors,
        )

    def test_convergence_relation_cannot_be_downgraded(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-D")["relation"] = "SIBLING"
        self.assert_has_error(value, "POL-D must be the convergence owner")

    def test_bootstrap_cannot_start_before_method_admission(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-A")["state"] = "READY_TO_START"
        self.assert_has_error(value, "POL-A cannot start")

    def test_kaw_cannot_become_portable_core_owner(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-KAW")["relation"] = "TRUE_CHILD"
        self.assert_has_error(value, "POL-KAW must remain an external consumer adapter")

    def test_live_evidence_cannot_become_implementation_ready(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-LIVE")["state"] = "READY_TO_START"
        self.assert_has_error(value, "POL-LIVE cannot be implementation-ready")

    def test_human_payment_authority_cannot_disappear(self) -> None:
        value = deepcopy(current_value())
        value["human_external_authority"].remove("user/customer/payment truth")
        self.assert_has_error(value, "required Human/external authority disappeared")

    def test_market_demand_law_cannot_disappear(self) -> None:
        value = deepcopy(current_value())
        value["laws"].remove("market attention != demand")
        self.assert_has_error(value, "load-bearing productization law disappeared")


if __name__ == "__main__":
    unittest.main()
