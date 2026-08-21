#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "assert_task_contract.py"
SCHEMA_SCRIPT = ROOT / "scripts" / "check_task_contract_schema.py"
EXAMPLE = ROOT / "references" / "example-stack-contract.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


module = load_module("assert_task_contract", SCRIPT)
schema_module = load_module("check_task_contract_schema", SCHEMA_SCRIPT)
base = json.loads(EXAMPLE.read_text(encoding="utf-8"))


def ids(value: dict) -> set[str]:
    return {failure.assertion for failure in module.validate(value)}


# Positive packet must satisfy both the Draft-2020-12 shape gate and the
# composed baseline + exact-byte ICPG semantic gate.
assert not schema_module.validate_object(base), schema_module.validate_object(base)
assert not module.validate(base), module.validate(base)

# v1 compatibility law: case_obligations is additive. Legacy/non-ICPG packets
# remain valid, while an admitted ICPG packet is fail-closed once the sidecar is present.
legacy = copy.deepcopy(base)
legacy.pop("case_obligations")
assert not schema_module.validate_object(legacy), schema_module.validate_object(legacy)
assert not module.validate(legacy), module.validate(legacy)

# Preserve the pre-ICPG hard-law controls.
case = copy.deepcopy(base)
case["providers"].append(
    {"id": "code-graph-rag", "role": "GRAPH", "state": "EXACT"}
)
assert "NO_CODE_GRAPH_RAG" in ids(case)

case = copy.deepcopy(base)
case["paths"]["changed"].append("shared/api.json")
assert "READ_ONLY_PATH" in ids(case)

case = copy.deepcopy(base)
case["automation"]["auto_merge"] = True
assert "HUMAN_ADMIT" in ids(case)

case = copy.deepcopy(base)
for provider in case["providers"]:
    if provider["id"] == "scip-sqlite":
        provider["state"] = "DEGRADED"
assert "EVIDENCE_CEILING" in ids(case)

case = copy.deepcopy(base)
case["branches"][0]["parent"] = case["branches"][1]["name"]
assert "DAG_CYCLE" in ids(case)

case = copy.deepcopy(base)
case["architecture"]["no_double_graph"] = False
assert "NO_DOUBLE_GRAPH" in ids(case)

case = copy.deepcopy(base)
for provider in case["providers"]:
    if provider["id"] == "scip-sqlite":
        provider["subject"]["tree"] = "f" * 40
assert "PROVIDER_SUBJECT_MISMATCH" in ids(case)

case = copy.deepcopy(base)
case["automation"]["git_town_admitted"] = False
assert "GIT_TOWN_ADMISSION" in ids(case)

case = copy.deepcopy(base)
case["automation"]["auto_resolve_conflicts"] = True
assert "SEMANTIC_CONFLICT_BOUNDARY" in ids(case)

# Regression control for the Shadow finding: branch-specific writes must never
# widen beyond the frozen global write lease.
case = copy.deepcopy(base)
case["branches"][0]["write"].append("outside/file.py")
assert "BRANCH_WRITE" in ids(case)

# ICPG -> Tech Lead denominator and ownership controls.
case = copy.deepcopy(base)
case["case_obligations"]["required_case_ids"].append("CASE-ORPHAN")
assert "CASE_DENOMINATOR_DRIFT" in ids(case)
assert "CASE_UNOWNED" in ids(case)

case = copy.deepcopy(base)
case["case_obligations"]["branch_case_owners"][1]["case_ids"].append("CASE-001")
assert "CASE_DUPLICATE_OWNER" in ids(case)

case = copy.deepcopy(base)
case["case_obligations"]["branch_case_owners"][0]["branch"] = "missing/branch"
assert "CASE_OWNER" in ids(case)

case = copy.deepcopy(base)
case["case_obligations"]["convergence_owner"] = "missing/branch"
assert "CASE_CONVERGENCE_OWNER" in ids(case)

# Valid-looking but stale digest must fail against the referenced graph bytes.
case = copy.deepcopy(base)
case["case_obligations"]["case_graph_sha256"] = "d" * 64
assert "CASE_GRAPH_DIGEST_MISMATCH" in ids(case)

# The task denominator must equal the actual REQUIRED_CASE set in the admitted graph.
case = copy.deepcopy(base)
case["case_obligations"]["required_case_ids"] = ["CASE-001"]
case["case_obligations"]["branch_case_owners"] = [
    {"branch": "feature/contract", "case_ids": ["CASE-001"]}
]
assert "CASE_DENOMINATOR_SHRINK" in ids(case)

case = copy.deepcopy(base)
case["case_obligations"]["branch_case_owners"][0]["case_ids"].append("CASE-OUTSIDE")
assert "CASE_UNKNOWN_OWNER" in ids(case)

case = copy.deepcopy(base)
case["case_obligations"]["case_graph_ref"] = "skills/spatial-loop-systems-engineering/tests/case-graph/fixtures/absent.json"
assert "CASE_GRAPH_ABSENT" in ids(case)

# Shape gate must reject a present-but-hollow sidecar even though absence is
# admitted for legacy/non-ICPG v1 packets.
case = copy.deepcopy(base)
del case["case_obligations"]["case_graph_sha256"]
assert schema_module.validate_object(case)

with tempfile.TemporaryDirectory() as tmp:
    receipt = Path(tmp) / "receipt.json"
    code = module.main(
        ["--contract", str(EXAMPLE), "--receipt", str(receipt)]
    )
    assert code == 0
    observed = json.loads(receipt.read_text(encoding="utf-8"))
    assert observed["verdict"] == "PASS"
    assert "case-obligation-denominator-and-ownership" in observed["assertions"]["implemented"]
    assert observed["claims_not_proven"]

print("agentic-tech-lead selftest: PASS baseline + exact-byte ICPG controls")
