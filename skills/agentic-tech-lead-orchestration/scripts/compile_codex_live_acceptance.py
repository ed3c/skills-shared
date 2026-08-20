#!/usr/bin/env python3
"""Compile a live Codex worker result plus controller readback into a bounded receipt."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path, PurePosixPath
from typing import Any

HEX40=re.compile(r"^[0-9a-f]{40}$"); HEX64=re.compile(r"^[0-9a-f]{64}$")
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FORBIDDEN={"api_key","apikey","access_token","refresh_token","credential","credentials","secret","secrets","reasoning","transcript","final_response","prompt","auth_json","session_token"}
class ContractError(ValueError): pass

def _canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def _digest(v:Any)->str:return hashlib.sha256(_canonical(v)).hexdigest()
def _keys(v:Any,p=""):
    if isinstance(v,dict):
        for k,c in v.items():
            q=f"{p}.{k}" if p else str(k); yield q; yield from _keys(c,q)
    elif isinstance(v,list):
        for i,c in enumerate(v): yield from _keys(c,f"{p}[{i}]")
def _path(v:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ContractError("changed path required")
    p=PurePosixPath(v.replace("\\","/").strip())
    if p.is_absolute() or ".." in p.parts: raise ContractError("changed path must be repo-relative")
    parts=[x for x in p.parts if x not in("",".")]
    if not parts: raise ContractError("changed path empty")
    return PurePosixPath(*parts).as_posix()
def _no_sensitive(v:Any)->None:
    for q in _keys(v):
        leaf=q.rsplit(".",1)[-1].split("[",1)[0].lower().replace("-","_")
        if leaf in FORBIDDEN: raise ContractError(f"forbidden durable field: {q}")
def _command(r:Any)->None:
    if not isinstance(r,dict) or set(r)!={"command_sha256","exit_code","output_sha256"}: raise ContractError("invalid controller command row")
    if not HEX64.fullmatch(str(r["command_sha256"])) or not HEX64.fullmatch(str(r["output_sha256"])): raise ContractError("command/output digest must be 64 hex")
    if not isinstance(r["exit_code"],int) or isinstance(r["exit_code"],bool) or r["exit_code"]!=0: raise ContractError("controller verification command failed")

def _git(repo_root:Path,*args:str)->str:
    result=subprocess.run(["git","-C",str(repo_root),*args],text=True,capture_output=True,check=False)
    if result.returncode:
        detail=(result.stderr or result.stdout).strip()
        raise ContractError(f"git {' '.join(args)} failed: {detail or result.returncode}")
    return result.stdout.strip()

def _tree_changed_paths(repo_root:Path,base_sha:str,tree_sha:str)->list[str]:
    raw=_git(repo_root,"diff","--name-only","-z","--no-renames",base_sha,tree_sha,"--")
    return sorted(_path(path) for path in raw.split("\0") if path)

def _assert_tree_binding(worker:dict[str,Any],changed_files:list[str])->None:
    repo_root=Path(str(worker["worktree"])).resolve()
    if not repo_root.is_dir(): raise ContractError("worker worktree unavailable for result-tree readback")
    if _git(repo_root,"rev-parse","--is-inside-work-tree")!="true": raise ContractError("worker worktree is not a Git worktree")
    base_tree=_git(repo_root,"rev-parse",f"{worker['base_sha']}^{{tree}}")
    if base_tree!=worker["base_tree_sha"]: raise ContractError("base_sha/base_tree_sha mismatch")
    if _git(repo_root,"cat-file","-t",worker["tree_sha"])!="tree": raise ContractError("tree_sha must resolve to a Git tree")
    observed=_tree_changed_paths(repo_root,worker["base_sha"],worker["tree_sha"])
    if observed!=changed_files:
        raise ContractError(f"bound result tree changed-file denominator mismatch: expected {changed_files} observed {observed}")

def compile_receipt(data:dict[str,Any])->dict[str,Any]:
    if not isinstance(data,dict) or set(data)!={"worker_result","controller"}: raise ContractError("input must contain worker_result/controller only")
    _no_sensitive(data); w=data["worker_result"]; c=data["controller"]
    if not isinstance(w,dict) or not isinstance(c,dict): raise ContractError("worker/controller must be objects")
    rw={"task_id","attempt_id","repo","base_sha","base_tree_sha","tree_sha","worktree","prompt_digest","adapter_state","sdk_execution","controller_readback_required","lease_readback","changed_files","turn_status"}
    if not rw<=w.keys(): raise ContractError(f"worker missing {sorted(rw-w.keys())}")
    if w["adapter_state"]!="RUNTIME_RETURNED" or w["sdk_execution"]!="EXERCISED" or w["lease_readback"]!="PASS" or w["controller_readback_required"] is not True: raise ContractError("worker runtime/lease state not admissible")
    if str(w["turn_status"]).lower()!="completed": raise ContractError("Codex turn must be completed")
    if not REPO.fullmatch(str(w["repo"])): raise ContractError("repo must be owner/name")
    for f in("base_sha","base_tree_sha","tree_sha"):
        if not HEX40.fullmatch(str(w[f])): raise ContractError(f"{f} must be exact 40 hex")
    if not isinstance(w["worktree"],str) or not w["worktree"].strip(): raise ContractError("worker worktree required for result-tree readback")
    if not HEX64.fullmatch(str(w["prompt_digest"])): raise ContractError("prompt_digest must be 64 hex")
    if not isinstance(w["changed_files"],list): raise ContractError("worker changed_files must be list")
    wp=sorted({_path(x) for x in w["changed_files"]})
    if len(wp)!=len(w["changed_files"]): raise ContractError("worker changed_files must be unique")
    rc={"task_id","attempt_id","repo","base_sha","tree_sha","changed_files","source_diff_readback","tests_readback","commands"}
    if set(c)!=rc: raise ContractError("controller fields invalid")
    for f in("task_id","attempt_id","repo","base_sha","tree_sha"):
        if c[f]!=w[f]: raise ContractError(f"controller/worker mismatch: {f}")
    if not isinstance(c["changed_files"],list): raise ContractError("controller changed_files must be list")
    cp=sorted({_path(x) for x in c["changed_files"]})
    if len(cp)!=len(c["changed_files"]) or cp!=wp: raise ContractError("changed-file denominator mismatch")
    if c["source_diff_readback"]!="PASS" or c["tests_readback"]!="PASS": raise ContractError("controller readback not PASS")
    if not isinstance(c["commands"],list) or not c["commands"]: raise ContractError("verification commands required")
    for r in c["commands"]:_command(r)
    _assert_tree_binding(w,wp)
    return {"schema_version":2,"task_id":w["task_id"],"attempt_id":w["attempt_id"],"repo":w["repo"],"base_sha":w["base_sha"],"base_tree_sha":w["base_tree_sha"],"tree_sha":w["tree_sha"],"prompt_digest":w["prompt_digest"],"worker_result_sha256":_digest(w),"changed_files":wp,"controller_commands":c["commands"],"sdk_execution":"EXERCISED","lease_readback":"PASS","result_tree_readback":"PASS","source_diff_readback":"PASS","tests_readback":"PASS","acceptance_state":"LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE","shadow_review_required":True,"evidence_ceiling":"LIVE_EXECUTION_OBSERVED_SHADOW_PENDING"}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("input"); p.add_argument("--output"); a=p.parse_args(); r=compile_receipt(json.loads(Path(a.input).read_text()))
    out=json.dumps(r,indent=2,sort_keys=True)+"\n"; Path(a.output).write_text(out) if a.output else print(out,end=""); return 0
if __name__=="__main__": raise SystemExit(main())
