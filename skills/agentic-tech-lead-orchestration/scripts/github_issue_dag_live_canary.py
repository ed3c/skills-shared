#!/usr/bin/env python3
"""Bounded reversible GitHub Issue Dependencies live canary."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from typing import Any

VIS={"PUBLIC","PRIVATE","INTERNAL"}

class ContractError(ValueError):
    pass

def validate_plan(d:dict[str,Any])->None:
    req={"repo","repo_visibility","default_branch","blocker_issue","blocked_issue","canary_label","expected_before_blocked_by"}
    if set(d)!=req:
        raise ContractError("plan fields invalid")
    if not isinstance(d["repo"],str) or d["repo"].count("/")!=1:
        raise ContractError("repo must be owner/name")
    if d["repo_visibility"] not in VIS or not isinstance(d["default_branch"],str) or not d["default_branch"].strip():
        raise ContractError("repo metadata invalid")
    for f in("blocker_issue","blocked_issue"):
        if not isinstance(d[f],int) or isinstance(d[f],bool) or d[f]<=0:
            raise ContractError(f"{f} invalid")
    if d["blocker_issue"]==d["blocked_issue"]:
        raise ContractError("self canary forbidden")
    if not isinstance(d["canary_label"],str) or not d["canary_label"].strip():
        raise ContractError("canary_label required")
    before=d["expected_before_blocked_by"]
    if not isinstance(before,list) or not all(isinstance(x,int) and not isinstance(x,bool) and x>0 for x in before) or len(set(before))!=len(before):
        raise ContractError("expected_before invalid")
    if d["blocker_issue"] in before:
        raise ContractError("canary edge already present")

def _run(a:list[str])->str:
    p=subprocess.run(a,text=True,capture_output=True)
    if p.returncode:
        raise ContractError(f"command failed ({p.returncode}): {' '.join(a)}: {p.stderr.strip()}")
    return p.stdout

def _labels(v:Any)->set[str]:
    if not isinstance(v,list):
        raise ContractError("labels malformed")
    out=set()
    for r in v:
        if not isinstance(r,dict) or not isinstance(r.get("name"),str):
            raise ContractError("label malformed")
        out.add(r["name"])
    return out

def preflight(d:dict[str,Any])->dict[str,Any]:
    validate_plan(d)
    ro=json.loads(_run(["gh","repo","view",d["repo"],"--json","nameWithOwner,visibility,defaultBranchRef"]))
    ref=ro.get("defaultBranchRef")
    branch=ref.get("name") if isinstance(ref,dict) else None
    if ro.get("nameWithOwner")!=d["repo"] or str(ro.get("visibility","")).upper()!=d["repo_visibility"] or branch!=d["default_branch"]:
        raise ContractError("repository preflight drift")
    issues={}
    for f in("blocker_issue","blocked_issue"):
        n=d[f]
        o=json.loads(_run(["gh","issue","view",str(n),"--repo",d["repo"],"--json","number,state,labels"]))
        if o.get("number")!=n or str(o.get("state","")).upper()!="OPEN":
            raise ContractError(f"canary issue identity/state drift: {n}")
        labels=_labels(o.get("labels"))
        if d["canary_label"] not in labels:
            raise ContractError(f"issue {n} lacks canary ownership label")
        issues[str(n)]={"state":"OPEN","labels":sorted(labels)}
    return {"repository":{"nameWithOwner":d["repo"],"visibility":d["repo_visibility"],"default_branch":d["default_branch"]},"issues":issues}

def _linked_issue_numbers(value:Any, repo:str)->list[int]:
    if not isinstance(value,dict) or set(value)!={"nodes","totalCount"}:
        raise ContractError("blockedBy connection malformed")
    nodes=value["nodes"]
    total=value["totalCount"]
    if not isinstance(nodes,list):
        raise ContractError("blockedBy nodes malformed")
    if not isinstance(total,int) or isinstance(total,bool) or total<0:
        raise ContractError("blockedBy totalCount malformed")
    if total!=len(nodes):
        raise ContractError("blockedBy totalCount mismatch")
    vals=[]
    for r in nodes:
        if not isinstance(r,dict):
            raise ContractError("blockedBy node malformed")
        n=r.get("number")
        if not isinstance(n,int) or isinstance(n,bool) or n<=0:
            raise ContractError("blockedBy number malformed")
        repository=r.get("repository")
        if not isinstance(repository,dict) or repository.get("nameWithOwner")!=repo:
            raise ContractError("blockedBy repository drift")
        vals.append(n)
    if len(set(vals))!=len(vals):
        raise ContractError("blockedBy duplicate")
    return sorted(vals)

def read_blocked_by(d:dict[str,Any])->list[int]:
    o=json.loads(_run(["gh","issue","view",str(d["blocked_issue"]),"--repo",d["repo"],"--json","blockedBy"]))
    if not isinstance(o,dict) or set(o)!={"blockedBy"}:
        raise ContractError("blockedBy response malformed")
    return _linked_issue_numbers(o["blockedBy"], d["repo"])

def static_receipt(d):
    validate_plan(d)
    return {"schema_version":1,"repo":d["repo"],"blocker_issue":d["blocker_issue"],"blocked_issue":d["blocked_issue"],"canary_label":d["canary_label"],"expected_before_blocked_by":sorted(d["expected_before_blocked_by"]),"execution":"NOT_EXERCISED","evidence_ceiling":"STATIC_CANARY_PLAN_ONLY"}

def execute(d):
    validate_plan(d)
    pb=preflight(d)
    before=read_blocked_by(d)
    expected=sorted(d["expected_before_blocked_by"])
    if before!=expected:
        raise ContractError(f"unexpected pre-canary denominator: {before}")
    blocker=d["blocker_issue"]
    blocked=d["blocked_issue"]
    added=False
    err=None
    applied=None
    pa=None
    cleanup=None
    try:
        _run(["gh","issue","edit",str(blocked),"--repo",d["repo"],"--add-blocked-by",str(blocker)])
        added=True
        applied=read_blocked_by(d)
        if applied!=sorted([*expected,blocker]):
            raise ContractError(f"applied readback mismatch: {applied}")
        pa=preflight(d)
        if pa!=pb:
            raise ContractError("preflight changed during canary")
    except Exception as e:
        err=e
    finally:
        if added:
            try:
                _run(["gh","issue","edit",str(blocked),"--repo",d["repo"],"--remove-blocked-by",str(blocker)])
                cleanup=read_blocked_by(d)
                if cleanup!=expected:
                    raise ContractError(f"cleanup did not restore denominator: {cleanup}")
            except Exception as ce:
                raise ContractError(f"canary cleanup failed after remote mutation: {ce}") from ce
    if err is not None:
        raise err
    return {"schema_version":1,"repo":d["repo"],"blocker_issue":blocker,"blocked_issue":blocked,"canary_label":d["canary_label"],"preflight":pa,"before":{"blockedBy":before},"applied":{"blockedBy":applied},"cleanup":{"blockedBy":cleanup},"execution":"EXERCISED","canary_state":"LIVE_GITHUB_DEPENDENCY_CANARY_PASS","semantic_authority":False,"evidence_ceiling":"REMOTE_CANARY_EDGE_ONLY"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("plan")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--output")
    a=p.parse_args()
    d=json.loads(Path(a.plan).read_text())
    r=execute(d) if a.execute else static_receipt(d)
    out=json.dumps(r,indent=2,sort_keys=True)+"\n"
    Path(a.output).write_text(out) if a.output else print(out,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
