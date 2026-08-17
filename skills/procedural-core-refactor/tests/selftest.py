#!/usr/bin/env python3
"""Positive and planted-negative controls for procedural-core-refactor."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_refactor_contract.py"
CONTRACT = ROOT / "references" / "example-refactor-contract.json"
PROOF = ROOT / "references" / "tech-lead-golden-proof.json"

spec = importlib.util.spec_from_file_location("pcr_checker", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("PCR-SELFTEST-RED checker import unavailable")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expect_red(name: str, contract: dict, proof: dict | None, needle: str) -> None:
    errors = checker.validate_bundle(contract, proof)
    if not any(needle.lower() in error.lower() for error in errors):
        raise AssertionError(f"mutation survived {name}: expected {needle!r}, got {errors}")


def main() -> int:
    contract = load(CONTRACT)
    proof = load(PROOF)
    errors = checker.validate_bundle(contract, proof)
    if errors:
        raise AssertionError(f"positive bundle rejected: {errors}")

    mutations: list[tuple[str, dict, dict | None, str]] = []

    candidate = copy.deepcopy(contract)
    candidate["baseline"]["immutable"] = False
    mutations.append(("mutable baseline", candidate, proof, "SCHEMA"))

    candidate = copy.deepcopy(contract)
    candidate["laws"][0]["assertion_owner"] = "skills/procedural-core-refactor/scripts/missing.py"
    mutations.append(("dead assertion", candidate, proof, "ASSERTION_OWNER_UNREACHABLE"))

    candidate = copy.deepcopy(contract)
    next(item for item in candidate["ownership"] if item["kind"] == "DOMAIN")["owner"] = "SKILL"
    mutations.append(("domain in portable core", candidate, proof, "OWNERSHIP_MISMATCH"))

    candidate = copy.deepcopy(contract)
    candidate["modules"][0]["trigger_evidence"] = []
    mutations.append(("selected without trigger", candidate, proof, "SELECTED_WITHOUT_TRIGGER"))

    candidate = copy.deepcopy(contract)
    candidate["modules"][0]["predecessor_states"] = []
    mutations.append(("selected without predecessor", candidate, proof, "SELECTED_WITHOUT_PREDECESSOR"))

    candidate = copy.deepcopy(contract)
    candidate["ab"]["same_budgets"] = False
    mutations.append(("unmatched A/B", candidate, proof, "UNMATCHED_REAL_TASK_AB"))

    candidate = copy.deepcopy(contract)
    candidate["evidence"]["live_model"] = "PASS"
    mutations.append(("contract fixture promotion", candidate, proof, "UNSUPPORTED_LIVE_PASS"))

    candidate = copy.deepcopy(contract)
    candidate["authority"]["automation_forbidden"] = ["merge"]
    mutations.append(("authority widening", candidate, proof, "SCHEMA"))

    planted = copy.deepcopy(proof)
    next(item for item in planted["treatments"] if item["arm"] == "B0_REFACTOR_AS_LANDED")["regressions"] = []
    mutations.append(("hidden B0 regression", contract, planted, "B0_REGRESSION_HIDDEN"))

    planted = copy.deepcopy(proof)
    planted["structural_ab"]["scores"]["B2_CAUSAL_DAG_REPAIRED"] = 10
    mutations.append(("B2 causal dimension missing", contract, planted, "B2_NOT_CLOSED"))

    planted = copy.deepcopy(proof)
    planted["real_task_ab"]["same_carrier"] = False
    mutations.append(("real-task carrier mismatch", contract, planted, "SCHEMA"))

    planted = copy.deepcopy(proof)
    planted["real_task_ab"]["global_objective"] = "FAIL"
    mutations.append(("local PASS global FAIL", contract, planted, "SCHEMA"))

    planted = copy.deepcopy(proof)
    planted["real_task_ab"]["cleanup"] = "DIRTY"
    mutations.append(("cleanup residue", contract, planted, "SCHEMA"))

    planted = copy.deepcopy(proof)
    planted["evidence"]["live_model"] = "PASS"
    mutations.append(("proof fixture promotion", contract, planted, "LIVE_EVIDENCE_PROMOTED"))

    planted = copy.deepcopy(proof)
    planted["trace"]["ci_runs"][0]["state"] = "PASS"
    mutations.append(("CI PASS without run", contract, planted, "CI_PASS_WITHOUT_RUN"))

    planted = copy.deepcopy(proof)
    planted["trace"]["exact_heads"] = planted["trace"]["exact_heads"][1:]
    mutations.append(("untraced proof head", contract, planted, "PROOF_HEAD_NOT_TRACED"))

    planted = copy.deepcopy(proof)
    planted["authority"]["merge"] = True
    mutations.append(("proof merge authority", contract, planted, "SCHEMA"))

    for name, mutated_contract, mutated_proof, needle in mutations:
        expect_red(name, mutated_contract, mutated_proof, needle)

    print(f"PCR-SELFTEST-GREEN positive + {len(mutations)} planted defects closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
