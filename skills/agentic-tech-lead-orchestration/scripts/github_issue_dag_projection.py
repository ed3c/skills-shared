#!/usr/bin/env python3
"""Project an asserted semantic issue DAG into GitHub Issue Dependencies.

GitHub blockedBy is treated as a durable projection of completion-readiness
edges, not as semantic authority. Start-readiness edges stay in portable truth.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

class ContractError(ValueError): pass

def canonical_graph_digest(data: dict[str, Any]) -> str:
    subject={"repo":data.get("repo"),"nodes":data.get("nodes"),"edges":data.get("edges")}
    encoded=json.dumps(subject,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def validate_graph(data: dict[str, Any]) -> None:
    if not isinstance(data.get("repo"), str) or data["repo"].count("/") != 1:
        raise ContractError("repo must be exact owner/name")
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ContractError("nodes/edges must be lists")
    expected_digest=data.get("graph_digest")
    if expected_digest is not None and expected_digest != canonical_graph_digest(data):
        raise ContractError("graph_digest does not match frozen graph bytes")
    issues=[]
    for node in nodes:
        if not isinstance(node,dict): raise ContractError("node must be an object")
        issue=node.get("issue")
        if not isinstance(issue,int) or isinstance(issue,bool) or issue <= 0:
            raise ContractError("node issue must be positive integer")
        if issue in issues: raise ContractError(f"duplicate node: {issue}")
        issues.append(issue)
        state=node.get("state",{})
        if not isinstance(state,dict): raise ContractError(f"state must be object for issue {issue}")
        if set(state) - {"start_readable","completion_admitted"}:
            raise ContractError(f"unsupported state fields for issue {issue}")
        if not all(isinstance(v,bool) for v in state.values()):
            raise ContractError(f"readiness state must be boolean for issue {issue}")
    known=set(issues)
    seen=set()
    adjacency=defaultdict(list)
    indeg={i:0 for i in issues}
    for edge in edges:
        if not isinstance(edge,dict): raise ContractError("edge must be an object")
        blocker=edge.get("blocker"); blocked=edge.get("blocked")
        readiness=edge.get("readiness"); project=edge.get("project_to_github",False)
        if not isinstance(project,bool): raise ContractError("project_to_github must be boolean")
        if blocker not in known or blocked not in known:
            raise ContractError("edge references unknown issue")
        if blocker == blocked: raise ContractError("self dependency is forbidden")
        if readiness not in {"start","completion"}:
            raise ContractError("readiness must be start or completion")
        key=(blocker,blocked,readiness)
        if key in seen: raise ContractError(f"duplicate semantic edge: {key}")
        seen.add(key)
        if project and readiness != "completion":
            raise ContractError("GitHub blockedBy may project completion-readiness edges only")
        adjacency[blocker].append(blocked); indeg[blocked]+=1
    q=deque(i for i,d in indeg.items() if d==0); visited=0
    while q:
        n=q.popleft(); visited+=1
        for nxt in adjacency[n]:
            indeg[nxt]-=1
            if indeg[nxt]==0:q.append(nxt)
    if visited != len(issues): raise ContractError("semantic dependency graph contains a cycle")

def desired_blocked_by(data: dict[str, Any]) -> dict[int,list[int]]:
    validate_graph(data)
    desired={n["issue"]:[] for n in data["nodes"]}
    for e in data["edges"]:
        if e.get("project_to_github",False):
            desired[e["blocked"]].append(e["blocker"])
    return {k:sorted(v) for k,v in desired.items()}

def ready_wave(data: dict[str, Any]) -> list[int]:
    validate_graph(data)
    states={n["issue"]: n.get("state",{}) for n in data["nodes"]}
    incoming=defaultdict(list)
    for e in data["edges"]: incoming[e["blocked"]].append(e)
    ready=[]
    for n in data["nodes"]:
        issue=n["issue"]; ok=True
        for e in incoming[issue]:
            src=states[e["blocker"]]
            field="start_readable" if e["readiness"]=="start" else "completion_admitted"
            if src.get(field) is not True:
                ok=False; break
        if ok: ready.append(issue)
    return sorted(ready)

def compare_readback(data: dict[str, Any], readback: dict[str, Any]) -> dict[str, Any]:
    desired=desired_blocked_by(data)
    missing={}; extra={}
    for issue,want in desired.items():
        row=readback.get(str(issue))
        if not isinstance(row,dict) or not isinstance(row.get("blockedBy"),list):
            raise ContractError(f"missing complete blockedBy readback for issue {issue}")
        got=row["blockedBy"]
        if not all(isinstance(v,int) and not isinstance(v,bool) and v>0 for v in got):
            raise ContractError(f"malformed blockedBy readback for issue {issue}")
        got=sorted(got)
        m=sorted(set(want)-set(got)); x=sorted(set(got)-set(want))
        if m: missing[str(issue)]=m
        if x: extra[str(issue)]=x
    return {"match": not missing and not extra, "missing":missing, "extra":extra}

def _run(args:list[str]) -> str:
    p=subprocess.run(args,text=True,capture_output=True)
    if p.returncode:
        raise ContractError(f"command failed ({p.returncode}): {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout

def live_readback(repo:str, issues:list[int]) -> dict[str,Any]:
    result={}
    for issue in issues:
        raw=_run(["gh","issue","view",str(issue),"--repo",repo,"--json","blockedBy"])
        obj=json.loads(raw)
        nums=[]
        for item in obj.get("blockedBy",[]):
            num=item.get("number") if isinstance(item,dict) else None
            if not isinstance(num,int) or isinstance(num,bool) or num<=0:
                raise ContractError(f"malformed GitHub blockedBy item for issue {issue}")
            nums.append(num)
        result[str(issue)]={"blockedBy":sorted(nums)}
    return result

def apply_projection(data:dict[str,Any]) -> dict[str,Any]:
    desired=desired_blocked_by(data)
    before=live_readback(data["repo"], sorted(desired))
    diff=compare_readback(data,before)
    if diff["extra"]:
        raise ContractError(
            "remote contains extra blockedBy edges not owned by this projection; "
            f"refusing destructive reconciliation: {diff['extra']}"
        )
    for issue, vals in diff["missing"].items():
        for blocker in vals:
            _run(["gh","issue","edit",issue,"--repo",data["repo"],"--add-blocked-by",str(blocker)])
    after=live_readback(data["repo"], sorted(desired))
    check=compare_readback(data,after)
    if not check["match"]:
        raise ContractError(f"remote readback drift remains: {check}")
    return {"repo":data["repo"],"graph_digest":canonical_graph_digest(data),"desired":desired,
            "before":before,"after":after,"ready_wave":ready_wave(data),
            "evidence_ceiling":"REMOTE_PROJECTION_READBACK_ONLY"}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("graph")
    ap.add_argument("--readback")
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    data=json.loads(Path(args.graph).read_text())
    out={"repo":data["repo"],"graph_digest":canonical_graph_digest(data),
         "desired":desired_blocked_by(data),"ready_wave":ready_wave(data),
         "evidence_ceiling":"STATIC_PROJECTION_ONLY"}
    if args.readback:
        rb=json.loads(Path(args.readback).read_text())
        out["readback"]=compare_readback(data,rb)
    if args.apply:
        out=apply_projection(data)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
