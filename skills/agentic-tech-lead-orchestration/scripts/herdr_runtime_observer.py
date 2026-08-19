#!/usr/bin/env python3
"""Optional Herdr runtime observer.

Herdr state is advisory. This adapter reduces Herdr CLI JSON to an identity-bound,
non-authoritative receipt and never persists terminal transcript content.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, time
from pathlib import Path
from typing import Any

STATES={"working":"RUNNING","blocked":"BLOCKED","idle":"IDLE","done":"DONE_CANDIDATE","unknown":"UNKNOWN"}
FORBIDDEN=("api_key","apikey","token","credential","secret","reasoning","transcript","visible_text","screen_text")

class ContractError(ValueError): pass

def _keys(v:Any,p=""):
    if isinstance(v,dict):
        for k,x in v.items():
            q=f"{p}.{k}" if p else str(k)
            yield q.lower(); yield from _keys(x,q)
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from _keys(x,f"{p}[{i}]")

def validate_manifest(d:dict[str,Any])->None:
    req={"task_id","attempt_id","repo","base_sha","tree_sha","worktree","target"}
    miss=sorted(req-d.keys())
    if miss: raise ContractError("missing required fields: "+", ".join(miss))
    for k in req:
        if not isinstance(d[k],str) or not d[k].strip(): raise ContractError(f"{k} must be non-empty string")
    if d.get("authoritative") is True: raise ContractError("Herdr observer can never be authoritative")
    if "require_foreground_cwd" in d and not isinstance(d["require_foreground_cwd"],bool):
        raise ContractError("require_foreground_cwd must be boolean")
    for key in _keys(d):
        leaf=key.rsplit(".",1)[-1].replace("-","_")
        if any(x in leaf for x in FORBIDDEN): raise ContractError(f"forbidden durable field: {key}")

def fallback_receipt(d:dict[str,Any])->dict[str,Any]:
    validate_manifest(d)
    return {
      "schema_version":1,"task_id":d["task_id"],"attempt_id":d["attempt_id"],"repo":d["repo"],
      "base_sha":d["base_sha"],"tree_sha":d["tree_sha"],"worktree":d["worktree"],"target":d["target"],
      "observer_state":"UNAVAILABLE_FALLBACK","herdr_available":False,"authoritative":False,
      "controller_readback_required":True,"evidence_ceiling":"NO_HERDR_OBSERVATION",
    }

def _run(argv:list[str])->dict[str,Any]:
    p=subprocess.run(argv,text=True,capture_output=True)
    if p.returncode: raise ContractError(f"Herdr command failed ({p.returncode}): {p.stderr.strip()}")
    try:return json.loads(p.stdout)
    except json.JSONDecodeError as e: raise ContractError(f"Herdr did not return JSON: {e}") from e

def _find(v:Any,*names:str):
    wanted=set(names)
    if isinstance(v,dict):
        for k,x in v.items():
            if k in wanted and x not in (None,""): return x
        for x in v.values():
            got=_find(x,*names)
            if got not in (None,""): return got
    elif isinstance(v,list):
        for x in v:
            got=_find(x,*names)
            if got not in (None,""): return got
    return None

def _native_session_id(agent:dict[str,Any]):
    session=_find(agent,"agent_session","agentSession")
    if isinstance(session,dict):
        value=session.get("value") or session.get("id") or session.get("session_id") or session.get("sessionId")
        if value not in (None,""): return value
    return _find(agent,"agent_session_id","agentSessionId")

def reduce_observation(d:dict[str,Any], agent:dict[str,Any], explain:dict[str,Any])->dict[str,Any]:
    validate_manifest(d)
    raw_state=_find(explain,"final_state","state") or _find(agent,"state","status") or "unknown"
    raw_state=str(raw_state).lower()
    mapped=STATES.get(raw_state,"UNKNOWN")
    pane=_find(agent,"pane_id","paneId") or _find(explain,"pane_id","paneId")
    workspace=_find(agent,"workspace_id","workspaceId") or _find(explain,"workspace_id","workspaceId")
    process=_find(agent,"process_id","processId","pid")
    foreground_cwd=_find(agent,"foreground_cwd","foregroundCwd")
    native_session=_native_session_id(agent)

    require_cwd=d.get("require_foreground_cwd",True)
    if require_cwd and foreground_cwd in (None,""):
        raise ContractError("Herdr observation lacks foreground_cwd; cannot bind agent to worktree")
    if foreground_cwd not in (None,""):
        if Path(str(foreground_cwd)).resolve() != Path(d["worktree"]).resolve():
            raise ContractError(
                f"foreground_cwd/worktree mismatch: observed {foreground_cwd!r}, expected {d['worktree']!r}"
            )

    for field,expected,actual in (
        ("pane_id",d.get("expected_pane_id"),pane),
        ("workspace_id",d.get("expected_workspace_id"),workspace),
        ("process_id",d.get("expected_process_id"),process),
        ("agent_session_id",d.get("expected_agent_session_id"),native_session),
    ):
        if expected is not None and str(expected)!=str(actual):
            raise ContractError(f"{field} mismatch: expected {expected!r}, observed {actual!r}")
    return {
      "schema_version":1,"task_id":d["task_id"],"attempt_id":d["attempt_id"],"repo":d["repo"],
      "base_sha":d["base_sha"],"tree_sha":d["tree_sha"],"worktree":d["worktree"],"target":d["target"],
      "pane_id":pane,"workspace_id":workspace,"process_id":process,"agent_session_id":native_session,
      "foreground_cwd":foreground_cwd,"observed_at_unix":int(time.time()),
      "raw_state":raw_state,"observer_state":mapped,
      "herdr_available":True,"authoritative":False,"controller_readback_required":True,
      "evidence_ceiling":"OBSERVER_IDENTITY_STATE_ONLY",
    }

def observe(d:dict[str,Any])->dict[str,Any]:
    validate_manifest(d)
    if shutil.which("herdr") is None:return fallback_receipt(d)
    agent=_run(["herdr","agent","get",d["target"]])
    explain=_run(["herdr","agent","explain",d["target"],"--json"])
    return reduce_observation(d,agent,explain)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("--output")
    a=ap.parse_args(); d=json.loads(Path(a.manifest).read_text()); receipt=observe(d)
    text=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")
    return 0
if __name__=="__main__":raise SystemExit(main())
