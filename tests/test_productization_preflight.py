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


def consumer(value: dict, consumer_id: str) -> dict:
    return next(item for item in value["external_consumers"] if item["id"] == consumer_id)


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


class ExternalConsumerRegistryTests(unittest.TestCase):
    """The registry holds program instances; no single carrier is a method atom."""

    def setUp(self) -> None:
        self.verifier = load_verifier()

    def assert_has_error(self, value: dict, needle: str) -> None:
        errors = self.verifier.validate(value)
        self.assertTrue(any(needle in error for error in errors), errors)

    # --- positive controls ------------------------------------------------

    def test_registry_registers_both_current_candidates(self) -> None:
        value = current_value()
        by_id = {item["id"]: item for item in value["external_consumers"]}
        self.assertEqual(sorted(by_id), ["ACTIONGATE", "KAW"])
        self.assertEqual(by_id["KAW"]["owner"], "ed3c/kotlin-auto-webview#135")
        self.assertEqual(by_id["ACTIONGATE"]["owner"], "ed3c/ActionGate#21")
        self.assertEqual(by_id["KAW"]["relation"], "EXTERNAL_CONSUMER_ADAPTER")
        self.assertEqual(by_id["ACTIONGATE"]["relation"], "REFERENCE_CONSUMER")
        for entry in by_id.values():
            self.assertEqual(entry["selected_for"], [])
            self.assertFalse(entry["exact_subject_requirement"]["mutable_ref_allowed"])

    def test_no_consumer_identity_is_a_required_method_atom(self) -> None:
        value = current_value()
        atom_ids = {item["id"] for item in value["atoms"]}
        self.assertEqual(atom_ids & self.verifier.REQUIRED_IDS, self.verifier.REQUIRED_IDS)
        for entry in value["external_consumers"]:
            self.assertNotIn(entry["id"], self.verifier.REQUIRED_IDS)
            self.assertNotIn(entry["owner"], {item["owner"] for item in value["atoms"]})

    def test_a_third_consumer_needs_no_core_law_change(self) -> None:
        value = deepcopy(current_value())
        third = deepcopy(consumer(value, "ACTIONGATE"))
        third["id"] = "REFCON3"
        third["owner"] = "ed3c/example-consumer#1"
        third["repository"] = "ed3c/example-consumer"
        third["planned_consumer_paths"] = ["ed3c/example-consumer:.agents/bindings/**"]
        value["external_consumers"].append(third)
        self.assertEqual(self.verifier.validate(value), [])

    # --- planted mutations ------------------------------------------------

    def test_consumer_paths_cannot_reach_into_portable_core(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["planned_consumer_paths"] = [
            "skills/productization-operating-loop/references/core/**"
        ]
        self.assert_has_error(value, "planned path must stay consumer-owned")

    def test_consumer_cannot_lease_a_skills_shared_path(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "KAW")["planned_consumer_paths"].append(
            "ed3c/skills-shared:skills/productization-operating-loop/references/core/**"
        )
        self.assert_has_error(value, "planned path must stay consumer-owned")

    def test_single_carrier_cannot_be_hard_coded_as_required_core(self) -> None:
        value = deepcopy(current_value())
        carrier = deepcopy(atom(value, "POL-LIVE"))
        carrier["id"] = "POL-KAW"
        carrier["owner"] = "ed3c/kotlin-auto-webview#135"
        value["atoms"].append(carrier)
        self.assert_has_error(value, "consumer identity promoted to method authority")

    def test_consumer_id_cannot_be_pinned_into_the_atom_graph(self) -> None:
        value = deepcopy(current_value())
        atom(value, "POL-LIVE")["start_dependencies"].append("KAW carrier receipt")
        self.assert_has_error(value, "hard-coded into the method atom graph")

    def test_consumer_state_cannot_be_an_inferred_pass(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["state"] = "PASS"
        self.assert_has_error(value, "explicit registration state, never inferred PASS")

    def test_duplicate_consumer_id_is_refused(self) -> None:
        value = deepcopy(current_value())
        clone = deepcopy(consumer(value, "KAW"))
        clone["owner"] = "ed3c/kotlin-auto-webview#999"
        value["external_consumers"].append(clone)
        self.assert_has_error(value, "duplicate consumer id")

    def test_duplicate_consumer_owner_is_refused(self) -> None:
        value = deepcopy(current_value())
        clone = deepcopy(consumer(value, "ACTIONGATE"))
        clone["id"] = "ACTIONGATE_COPY"
        value["external_consumers"].append(clone)
        self.assert_has_error(value, "duplicate consumer owner")

    def test_consumer_without_evidence_ceiling_is_refused(self) -> None:
        value = deepcopy(current_value())
        del consumer(value, "KAW")["evidence_ceiling"]
        self.assert_has_error(value, "consumer KAW missing fields")

    def test_consumer_with_empty_evidence_ceiling_is_refused(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["evidence_ceiling"] = ""
        self.assert_has_error(value, "consumer ACTIONGATE missing evidence_ceiling")

    def test_consumer_cannot_claim_portable_core_authority(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["relation"] = "TOP_LEVEL_IMPLEMENTATION_ROOT"
        self.assert_has_error(value, "relation must stay external")

    def test_consumer_subject_cannot_be_mutable(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "KAW")["exact_subject_requirement"]["mutable_ref_allowed"] = True
        self.assert_has_error(value, "exact immutable subject")

    def test_consumer_visibility_receipt_cannot_be_dropped(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["exact_subject_requirement"]["visibility_receipt"] = "PUBLIC"
        self.assert_has_error(value, "explicit visibility")

    def test_consumer_locator_url_is_refused(self) -> None:
        value = deepcopy(current_value())
        consumer(value, "ACTIONGATE")["outputs"].append("https://example.invalid/private/packet")
        self.assert_has_error(value, "must not persist a locator URL")

    def test_empty_registry_is_refused(self) -> None:
        value = deepcopy(current_value())
        value["external_consumers"] = []
        self.assert_has_error(value, "external_consumers must be a non-empty list")

    def test_registration_law_cannot_disappear(self) -> None:
        value = deepcopy(current_value())
        value["laws"].remove("consumer registration != consumer selection or execution")
        self.assert_has_error(value, "load-bearing productization law disappeared")


if __name__ == "__main__":
    unittest.main()
