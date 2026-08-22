#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
SCRIPT = ROOT / "scripts" / "assert_task_contract.py"
SCHEMA_SCRIPT = ROOT / "scripts" / "check_task_contract_schema.py"
EXAMPLE = ROOT / "references" / "example-stack-contract.json"
CASE_GRAPH_REF = "skills/spatial-loop-systems-engineering/tests/case-graph/fixtures/good.json"


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

# --- #410 residual controls: drive the composed gate end to end -------------
# The blocks above assert failure ids in process. The two controls below are
# planted-defect controls on the shipped entrypoint itself: exit status, receipt
# verdict, and the exact failure detail must all turn red for the stated reason.

GRAPH_BYTES = (REPO_ROOT / CASE_GRAPH_REF).read_bytes()
GRAPH_SHA256 = hashlib.sha256(GRAPH_BYTES).hexdigest()
GRAPH_REQUIRED = [
    item["id"]
    for item in json.loads(GRAPH_BYTES)["cases"]
    if item.get("classification") == "REQUIRED_CASE"
]
# Absence is reported, never silently green: a one-case graph cannot express a
# packet that is closed over its own scope while a graph case stays unowned.
assert len(GRAPH_REQUIRED) >= 2, GRAPH_REQUIRED


def rebound(contract: dict) -> dict:
    """Deep copy whose ICPG binding is taken live from the graph bytes on disk.

    These controls are about the denominator/ownership law, not the digest law
    (already covered above), so they must not inherit a pinned example digest.
    """
    fresh = copy.deepcopy(contract)
    fresh["case_obligations"]["case_graph_ref"] = CASE_GRAPH_REF
    fresh["case_obligations"]["case_graph_sha256"] = GRAPH_SHA256
    return fresh


def planted(before: dict, after: dict, label: str) -> dict:
    """A mutation that changed nothing is itself a defect, not a green control."""
    assert before != after, f"planted defect {label} did not change the packet"
    return after


def gate(contract: dict) -> tuple[int, dict]:
    """Run the shipped composed gate over one packet and read its receipt back."""
    with tempfile.TemporaryDirectory() as sandbox:
        contract_path = Path(sandbox) / "contract.json"
        receipt_path = Path(sandbox) / "receipt.json"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        code = module.main(
            ["--contract", str(contract_path), "--receipt", str(receipt_path)]
        )
        return code, json.loads(receipt_path.read_text(encoding="utf-8"))


def reported(receipt: dict) -> set[tuple[str, str]]:
    return {
        (failure["assertion"], failure["detail"])
        for failure in receipt["assertions"]["failures"]
    }


# #410: local task PASS never closes a global case gap. Positive control first:
# a packet whose denominator equals the graph denominator, fully owned, passes.
closed = rebound(base)
closed["case_obligations"]["required_case_ids"] = list(GRAPH_REQUIRED)
closed["case_obligations"]["branch_case_owners"] = [
    {"branch": "feature/contract", "case_ids": GRAPH_REQUIRED[:1]},
    {"branch": "feature/core", "case_ids": GRAPH_REQUIRED[1:]},
]
code, receipt = gate(closed)
assert code == 0, receipt
assert receipt["verdict"] == "PASS", receipt

# Planted defect: shrink denominator and ownership map together, so the packet
# is still closed over its own scope while the bound graph keeps an orphan
# REQUIRED_CASE that no branch owns.
orphan = GRAPH_REQUIRED[-1]
retained = [case_id for case_id in GRAPH_REQUIRED if case_id != orphan]
gap = copy.deepcopy(closed)
gap["case_obligations"]["required_case_ids"] = retained
gap["case_obligations"]["branch_case_owners"] = [
    {"branch": "feature/contract", "case_ids": retained}
]
planted(closed, gap, "global-case-gap")
code, receipt = gate(gap)
assert code == 2, receipt
assert receipt["verdict"] == "FAIL", receipt
assert (
    "CASE_DENOMINATOR_SHRINK",
    f"task packet omits required graph cases: {orphan}",
) in reported(receipt), receipt
# The gap must be the only red: that is what proves the packet passed its own
# scope and was refused solely for the global case it left unowned.
assert {assertion for assertion, _ in reported(receipt)} == {
    "CASE_DENOMINATOR_SHRINK"
}, receipt

# #410: PATH_LEASE_OVERLAP had zero red coverage. The shipped example is a
# parent/child stack, where the sibling check legitimately abstains, so the
# control needs true siblings. Positive control: disjoint sibling leases pass.
siblings = rebound(base)
siblings["branches"][1]["parent"] = siblings["branches"][0]["parent"]
code, receipt = gate(siblings)
assert code == 0, receipt
assert receipt["verdict"] == "PASS", receipt

overlap = copy.deepcopy(siblings)
shared_lease = overlap["branches"][0]["write"][0]
overlap["branches"][1]["write"].append(shared_lease)
planted(siblings, overlap, "path-lease-overlap")
left, right = sorted(branch["name"] for branch in overlap["branches"])
code, receipt = gate(overlap)
assert code == 2, receipt
assert receipt["verdict"] == "FAIL", receipt
assert (
    "PATH_LEASE_OVERLAP",
    f"sibling branches {left} and {right} overlap at {shared_lease}",
) in reported(receipt), receipt
assert {assertion for assertion, _ in reported(receipt)} == {
    "PATH_LEASE_OVERLAP"
}, receipt

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

print(
    "agentic-tech-lead selftest: PASS baseline + exact-byte ICPG controls; "
    "the global-case-gap and sibling path-lease-overlap packets each turn the "
    "shipped gate red on their own exact failure detail"
)
