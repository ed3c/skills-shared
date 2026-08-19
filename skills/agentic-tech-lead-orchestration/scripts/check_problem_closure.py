#!/usr/bin/env python3
"""Deterministic problem-closure ledger checker."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

CLOSURES={"OPEN","PARTIAL","IMPLEMENTED_UNVERIFIED","VERIFIED_LOCAL","VERIFIED_LIVE","NOT_APPLICABLE","HUMAN_ADMIT_REQUIRED"}
APPLICABILITY={"APPLICABLE","NOT_APPLICABLE","SUPERSEDED"}
SHADOW={"PASS","FAIL","PARTIAL","NOT_REVIEWED"}
VERIFY_LANES={"LOCAL","CI","PROVIDER_LIVE","HUMAN","RELEASE"}
IMPLEMENTATION_KINDS={"COMMIT","PR","MERGE_SUBJECT","SOURCE_DIFF","GENERATED_ARTIFACT"}

class ContractError(ValueError): pass

def _nonempty(v): return isinstance(v,str) and bool(v.strip())

def validate_problem(p:dict[str,Any])->None:
    for key in ("problem_id","source","claim","applicability","repo_subject","task_nodes","issue_nodes",
                "implementation_evidence","verification_evidence","shadow_verdict","residual_gaps","closure"):
        if key not in p: raise ContractError(f"{p.get('problem_id','?')}: missing {key}")
    if not _nonempty(p["problem_id"]): raise ContractError("problem_id must be non-empty")
    src=p["source"]
    if not isinstance(src,dict) or not _nonempty(src.get("kind")) or not _nonempty(src.get("identity")) or not _nonempty(src.get("location")):
        raise ContractError(f"{p['problem_id']}: exact source kind/identity/location required")
    if not _nonempty(p["claim"]): raise ContractError(f"{p['problem_id']}: claim required")
    if p["applicability"] not in APPLICABILITY: raise ContractError(f"{p['problem_id']}: invalid applicability")
    if p["closure"] not in CLOSURES: raise ContractError(f"{p['problem_id']}: invalid closure")
    if p["shadow_verdict"] not in SHADOW: raise ContractError(f"{p['problem_id']}: invalid shadow verdict")
    rs=p["repo_subject"]
    if not isinstance(rs,dict) or not all(_nonempty(rs.get(k)) for k in ("repo","commit","tree")):
        raise ContractError(f"{p['problem_id']}: exact repo/commit/tree required")
    for field in ("task_nodes","issue_nodes","implementation_evidence","verification_evidence","residual_gaps"):
        if not isinstance(p[field],list): raise ContractError(f"{p['problem_id']}: {field} must be a list")
    if p["applicability"]=="NOT_APPLICABLE" and not _nonempty(p.get("applicability_rationale")):
        raise ContractError(f"{p['problem_id']}: NOT_APPLICABLE requires rationale")
    for ev in p["implementation_evidence"]:
        if not isinstance(ev,dict) or ev.get("kind") not in IMPLEMENTATION_KINDS or not _nonempty(ev.get("subject")):
            raise ContractError(f"{p['problem_id']}: invalid implementation evidence")
    for ev in p["verification_evidence"]:
        if not isinstance(ev,dict) or ev.get("lane") not in VERIFY_LANES or not _nonempty(ev.get("subject")):
            raise ContractError(f"{p['problem_id']}: invalid verification evidence lane")
    for gap in p["residual_gaps"]:
        if not _nonempty(gap): raise ContractError(f"{p['problem_id']}: residual gaps must be non-empty strings")

def recompute(p:dict[str,Any])->str:
    validate_problem(p)
    if p["applicability"]=="NOT_APPLICABLE": return "NOT_APPLICABLE"
    impl=bool(p["implementation_evidence"])
    verify={ev["lane"] for ev in p["verification_evidence"]}
    gaps=bool(p["residual_gaps"])
    if p.get("requires_human") is True and "HUMAN" not in verify:
        return "HUMAN_ADMIT_REQUIRED"
    if not impl: return "OPEN"
    if gaps or p["shadow_verdict"] in {"FAIL","PARTIAL"}: return "PARTIAL"
    if not verify or p["shadow_verdict"]=="NOT_REVIEWED": return "IMPLEMENTED_UNVERIFIED"
    if "PROVIDER_LIVE" in verify and p["shadow_verdict"]=="PASS": return "VERIFIED_LIVE"
    if verify & {"LOCAL","CI"} and p["shadow_verdict"]=="PASS": return "VERIFIED_LOCAL"
    if verify <= {"HUMAN","RELEASE"}: return "IMPLEMENTED_UNVERIFIED"
    return "IMPLEMENTED_UNVERIFIED"

def check_ledger(data:dict[str,Any])->dict[str,Any]:
    problems=data.get("problems")
    if not isinstance(problems,list): raise ContractError("problems must be a list")
    ids=[]; mismatches=[]
    counts={state:0 for state in CLOSURES}
    for p in problems:
        validate_problem(p)
        if p["problem_id"] in ids: raise ContractError(f"duplicate problem_id: {p['problem_id']}")
        ids.append(p["problem_id"])
        expected=recompute(p)
        counts[expected]+=1
        if p["closure"]!=expected:
            mismatches.append({"problem_id":p["problem_id"],"declared":p["closure"],"expected":expected})
    if mismatches: raise ContractError(f"closure laundering/drift: {mismatches}")
    open_ids=[p["problem_id"] for p in problems if p["closure"] in {"OPEN","PARTIAL","IMPLEMENTED_UNVERIFIED","HUMAN_ADMIT_REQUIRED"}]
    return {"problem_count":len(problems),"counts":counts,"residual_problem_ids":open_ids,
            "evidence_ceiling":"LEDGER_DETERMINISTIC_CHECKED"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("ledger"); a=ap.parse_args()
    data=json.loads(Path(a.ledger).read_text())
    print(json.dumps(check_ledger(data),indent=2,sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
