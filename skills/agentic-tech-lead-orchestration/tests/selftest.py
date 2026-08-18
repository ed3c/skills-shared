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
EXAMPLE = ROOT / "references" / "example-stack-contract.json"

spec = importlib.util.spec_from_file_location("assert_task_contract", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
base = json.loads(EXAMPLE.read_text(encoding="utf-8"))

def ids(value: dict) -> set[str]: return {failure.assertion for failure in module.validate(value)}
assert not module.validate(base), module.validate(base)

case=copy.deepcopy(base); case["providers"].append({"id":"code-graph-rag","role":"GRAPH","state":"EXACT"}); assert "NO_CODE_GRAPH_RAG" in ids(case)
case=copy.deepcopy(base); case["paths"]["changed"].append("shared/api.json"); assert "READ_ONLY_PATH" in ids(case)
case=copy.deepcopy(base); case["automation"]["auto_merge"]=True; assert "HUMAN_ADMIT" in ids(case)
case=copy.deepcopy(base)
for provider in case["providers"]:
    if provider["id"]=="scip-sqlite": provider["state"]="DEGRADED"
assert "EVIDENCE_CEILING" in ids(case)
case=copy.deepcopy(base); case["branches"][0]["parent"]=case["branches"][1]["name"]; assert "DAG_CYCLE" in ids(case)
case=copy.deepcopy(base); case["architecture"]["no_double_graph"]=False; assert "NO_DOUBLE_GRAPH" in ids(case)
case=copy.deepcopy(base)
for provider in case["providers"]:
    if provider["id"]=="scip-sqlite": provider["subject"]["tree"]="f"*40
assert "PROVIDER_SUBJECT_MISMATCH" in ids(case)
case=copy.deepcopy(base); case["automation"]["git_town_admitted"]=False; assert "GIT_TOWN_ADMISSION" in ids(case)
case=copy.deepcopy(base); case["automation"]["auto_resolve_conflicts"]=True; assert "SEMANTIC_CONFLICT_BOUNDARY" in ids(case)

# ICPG/Tech Lead closure controls.
case=copy.deepcopy(base); case["case_obligations"]["required_case_ids"].append("CASE-ORPHAN"); assert "CASE_UNOWNED" in ids(case)
case=copy.deepcopy(base); case["case_obligations"]["branch_case_owners"][1]["case_ids"].append("CASE-CONTRACT"); assert "CASE_DUPLICATE_OWNER" in ids(case)
case=copy.deepcopy(base); case["case_obligations"]["branch_case_owners"][0]["branch"]="missing/branch"; assert "CASE_OWNER" in ids(case)
case=copy.deepcopy(base); case["case_obligations"]["convergence_owner"]="missing/branch"; assert "CASE_CONVERGENCE_OWNER" in ids(case)
case=copy.deepcopy(base); case["case_obligations"]["case_graph_sha256"]="latest"; assert "CASE_GRAPH_BINDING" in ids(case)

with tempfile.TemporaryDirectory() as tmp:
    receipt=Path(tmp)/"receipt.json"
    code=module.main(["--contract",str(EXAMPLE),"--receipt",str(receipt)])
    assert code==0
    observed=json.loads(receipt.read_text(encoding="utf-8"))
    assert observed["verdict"]=="PASS"

print("agentic-tech-lead selftest: PASS")
