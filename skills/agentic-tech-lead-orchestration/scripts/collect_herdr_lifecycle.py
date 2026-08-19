#!/usr/bin/env python3
"""Collect a bounded Herdr lifecycle from the existing observer."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, time
from pathlib import Path
from typing import Any, Callable
TERMINAL={"DONE_CANDIDATE"}; NONTERMINAL={"RUNNING","BLOCKED","IDLE","UNKNOWN"}
class ContractError(ValueError): pass

def _canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _digest(v:Any)->str:return hashlib.sha256(_canonical(v)).hexdigest()
def validate_plan(d:dict[str,Any])->None:
    if not isinstance(d,dict) or set(d)!={"manifest","poll_interval_seconds","max_samples","require_terminal"}: raise ContractError("plan fields invalid")
    if not isinstance(d["manifest"],dict): raise ContractError("manifest must be object")
    i=d["poll_interval_seconds"]
    if not isinstance(i,(int,float)) or isinstance(i,bool) or i<0 or i>3600: raise ContractError("poll interval out of range")
    n=d["max_samples"]
    if not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=100: raise ContractError("max_samples must be 1..100")
    if not isinstance(d["require_terminal"],bool): raise ContractError("require_terminal must be boolean")
def _load():
    p=Path(__file__).resolve().with_name("herdr_runtime_observer.py"); s=importlib.util.spec_from_file_location("herdr_runtime_observer",p)
    if s is None or s.loader is None: raise ContractError("cannot load existing Herdr observer")
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def _id(r): return (r.get("task_id"),r.get("attempt_id"),r.get("repo"),r.get("base_sha"),r.get("tree_sha"),r.get("worktree"),r.get("target"),r.get("pane_id"),r.get("workspace_id"),r.get("process_id"),r.get("process_started_at_unix"),r.get("agent_session_id"))
def validate_sequence(samples:list[dict[str,Any]],require_terminal:bool)->None:
    if not samples: raise ContractError("lifecycle requires samples")
    if samples[0].get("observer_state")=="UNAVAILABLE_FALLBACK":
        if len(samples)!=1: raise ContractError("fallback mixed with live samples")
        return
    identity=_id(samples[0]); prev=None; terminal=False
    for i,s in enumerate(samples):
        state=s.get("observer_state")
        if state not in NONTERMINAL|TERMINAL: raise ContractError(f"unsupported state at {i}: {state}")
        if _id(s)!=identity: raise ContractError(f"identity drift at sample {i}")
        ts=s.get("source_observed_at_unix")
        if not isinstance(ts,int) or isinstance(ts,bool) or ts<=0: raise ContractError("source timestamp invalid")
        if prev is not None and ts<prev: raise ContractError("source timestamp regressed")
        prev=ts
        if terminal: raise ContractError("sample after terminal state")
        if state in NONTERMINAL and s.get("process_alive") is not True: raise ContractError("nonterminal sample lacks live process")
        if state in TERMINAL:
            if s.get("cleanup_state")!="CLEAN" or s.get("residue_count")!=0: raise ContractError("terminal sample not clean")
            terminal=True
    if require_terminal and not terminal: raise ContractError("bounded lifecycle ended without DONE_CANDIDATE")
def collect(d:dict[str,Any],observer:Callable[[dict[str,Any]],dict[str,Any]]|None=None,sleep_fn:Callable[[float],None]=time.sleep)->dict[str,Any]:
    validate_plan(d); observer=observer or _load().observe; samples=[]
    for i in range(d["max_samples"]):
        r=observer(d["manifest"])
        if not isinstance(r,dict): raise ContractError("observer receipt must be object")
        samples.append(r)
        if r.get("observer_state") in {"UNAVAILABLE_FALLBACK","DONE_CANDIDATE"}: break
        if i+1<d["max_samples"] and d["poll_interval_seconds"]: sleep_fn(float(d["poll_interval_seconds"]))
    validate_sequence(samples,d["require_terminal"]); first=samples[0]
    if first.get("observer_state")=="UNAVAILABLE_FALLBACK": return {"schema_version":1,"task_id":first.get("task_id"),"attempt_id":first.get("attempt_id"),"repo":first.get("repo"),"base_sha":first.get("base_sha"),"tree_sha":first.get("tree_sha"),"worktree":first.get("worktree"),"target":first.get("target"),"sample_count":1,"sample_digests":[_digest(first)],"lifecycle_state":"UNAVAILABLE_FALLBACK","controller_readback_required":True,"shadow_review_required":True,"evidence_ceiling":"NO_HERDR_OBSERVATION"}
    final=samples[-1]
    return {"schema_version":1,"task_id":final["task_id"],"attempt_id":final["attempt_id"],"repo":final["repo"],"base_sha":final["base_sha"],"tree_sha":final["tree_sha"],"worktree":final["worktree"],"target":final["target"],"pane_id":final.get("pane_id"),"workspace_id":final.get("workspace_id"),"process_id":final.get("process_id"),"process_started_at_unix":final.get("process_started_at_unix"),"agent_session_id":final.get("agent_session_id"),"sample_count":len(samples),"sample_digests":[_digest(x) for x in samples],"first_source_observed_at_unix":samples[0]["source_observed_at_unix"],"last_source_observed_at_unix":final["source_observed_at_unix"],"final_observer_state":final["observer_state"],"lifecycle_state":"LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE","controller_readback_required":True,"shadow_review_required":True,"evidence_ceiling":"LIVE_OBSERVER_LIFECYCLE_SHADOW_PENDING"}
def main():
    p=argparse.ArgumentParser(); p.add_argument("plan"); p.add_argument("--output"); a=p.parse_args(); r=collect(json.loads(Path(a.plan).read_text())); out=json.dumps(r,indent=2,sort_keys=True)+"\n"; Path(a.output).write_text(out) if a.output else print(out,end=""); return 0
if __name__=="__main__": raise SystemExit(main())
