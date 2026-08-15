#!/usr/bin/env python3
"""Executable 100-point Agent Architecture rubric shared by standalone/meta gates."""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
from typing import Any

ARCHITECTURE_SCHEMA="agent-architecture-eval/v1"; RUBRIC_SCHEMA="agent-architecture-rubric/v1"
HEX40=re.compile(r"^[0-9a-f]{40}$"); HEX64=re.compile(r"^[0-9a-f]{64}$")
MODES={"STATIC_ASSERTION","RUNTIME_PROBE","TRACE_ASSERTION","NEGATIVE_CONTROL"}
POS={"VERIFIED","FAILED","NOT_EXERCISED"}; VIBES={"NOT_DETECTED","DETECTED","NOT_EXERCISED"}

class ArchitectureContractError(ValueError): pass

def req(x:bool,m:str)->None:
    if not x: raise ArchitectureContractError(m)
def obj(x:Any,p:str)->dict[str,Any]: req(isinstance(x,dict),f"{p} must be object"); return x
def arr(x:Any,p:str)->list[Any]: req(isinstance(x,list),f"{p} must be array"); return x
def txt(x:Any,p:str)->str: req(isinstance(x,str) and x.strip(),f"{p} must be non-empty string"); return x
def num(x:Any,p:str,lo:float|None=None,hi:float|None=None)->float:
    req(isinstance(x,(int,float)) and not isinstance(x,bool),f"{p} must be numeric"); v=float(x); req(math.isfinite(v),f"{p} must be finite")
    if lo is not None:req(v>=lo,f"{p} must be >= {lo}")
    if hi is not None:req(v<=hi,f"{p} must be <= {hi}")
    return v
def keys(x:dict[str,Any], expected:list[str],p:str)->None:
    e,a=set(expected),set(x); req(e==a,f"{p} keys mismatch missing={sorted(e-a)} unknown={sorted(a-e)}")
def dig(x:Any,pat:re.Pattern[str],p:str)->str: v=txt(x,p); req(pat.fullmatch(v) is not None,f"{p} invalid digest"); return v
def close(a:float,d:Any,p:str,t:float=.01)->None: req(abs(a-num(d,p))-0<=t,f"{p} declared {d}, recomputed {a}")
def band(s:float)->str:return "VIBE_CODER" if s<60 else "COMPETENT_AGENT_ENGINEER" if s<85 else "AGENT_ARCHITECT"

def parse(path:Path)->dict[str,Any]:
    try:return obj(json.loads(path.read_text()),"$")
    except OSError as e: raise RuntimeError(f"cannot read {path}: {e}") from e
    except json.JSONDecodeError as e: raise RuntimeError(f"malformed JSON: {e}") from e

def _rubric()->tuple[str,dict[str,dict[str,Any]],dict[str,dict[str,Any]],dict[str,float],dict[str,str]]:
    p=Path(__file__).resolve().parents[1]/"references"/"agent-architecture-rubric.json"
    try: raw=p.read_bytes(); d=obj(json.loads(raw),"$rubric")
    except (OSError,json.JSONDecodeError) as e: raise ArchitectureContractError(f"cannot load rubric: {e}") from e
    keys(d,["schema","title","source_basis","evidence_modes","dimensions","bands"],"$rubric"); req(d["schema"]==RUBRIC_SCHEMA,"rubric schema mismatch"); req(set(d["evidence_modes"])==MODES,"rubric evidence modes mismatch")
    cs:dict[str,dict[str,Any]]={}; ss:dict[str,dict[str,Any]]={}; pts:dict[str,float]={}; dims:dict[str,str]={}; total=0.0
    for di,dr in enumerate(arr(d["dimensions"],"$rubric.dimensions")):
        q=f"$rubric.dimensions[{di}]"; x=obj(dr,q); keys(x,["dimension_id","weight","positive_criteria","vibe_signals"],q); dim=txt(x["dimension_id"],q+".dimension_id"); w=num(x["weight"],q+".weight",.0001,100); total+=w; positives=arr(x["positive_criteria"],q+".positive_criteria"); req(bool(positives),q+" positives empty"); each=w/len(positives)
        for ci,cr in enumerate(positives):
            z=obj(cr,f"{q}.positive_criteria[{ci}]"); keys(z,["criterion_id","description","required_any_modes"],q); cid=txt(z["criterion_id"],q); req(cid not in cs,"duplicate criterion "+cid); modes=set(z["required_any_modes"]); req(bool(modes) and modes<=MODES,cid+" modes invalid"); cs[cid]={**z,"dimension_id":dim}; pts[cid]=each; dims[cid]=dim
        for si,sr in enumerate(arr(x["vibe_signals"],q+".vibe_signals")):
            z=obj(sr,f"{q}.vibe_signals[{si}]"); allowed={"signal_id","description","contradicts","required_any_modes","score_ceiling"}; req(set(z)<=allowed and {"signal_id","description","contradicts","required_any_modes"}<=set(z),"signal keys invalid"); sid=txt(z["signal_id"],q); req(sid not in ss,"duplicate signal "+sid); req(bool(z["contradicts"]),sid+" contradictions empty"); req(set(z["required_any_modes"])<=MODES,sid+" modes invalid"); ss[sid]={**z,"dimension_id":dim}
    req(abs(total-100)<.001,"rubric weights must sum to 100")
    for sid,s in ss.items():
        for cid in s["contradicts"]: req(cid in cs,f"{sid} contradicts unknown {cid}")
    return hashlib.sha256(raw).hexdigest(),cs,ss,pts,dims

def _evidence(raw:Any,p:str,subject:str,polarity:str|None,modes:set[str],required:bool)->None:
    xs=arr(raw,p)
    if not required: req(not xs,p+" must be empty"); return
    req(bool(xs),p+" must contain executable evidence"); seen=set(); used=set()
    for i,er in enumerate(xs):
        q=f"{p}[{i}]"; e=obj(er,q); keys(e,["evidence_id","mode","assertion_id","polarity","subject_digest","artifact_sha256","exit_code"],q); eid=txt(e["evidence_id"],q); req(eid not in seen,"duplicate evidence "+eid); seen.add(eid); mode=txt(e["mode"],q); req(mode in MODES,q+" non-executable mode"); used.add(mode); txt(e["assertion_id"],q); req(e["polarity"] in {"PROVES_PRESENT","PROVES_ABSENT"},q+" polarity invalid"); req(polarity is None or e["polarity"]==polarity,q+" polarity mismatch"); req(dig(e["subject_digest"],HEX64,q)==subject,q+" subject mismatch"); dig(e["artifact_sha256"],HEX64,q); req(isinstance(e["exit_code"],int) and not isinstance(e["exit_code"],bool),q+" exit_code invalid")
    req(bool(used&modes),p+" lacks required evidence mode")

def validate_architecture_receipt(raw:Any,expected_subject:dict[str,str]|None=None)->dict[str,Any]:
    d=obj(raw,"$.architecture"); keys(d,["schema","receipt_id","subject","rubric","criteria","vibe_signals","authority","declared"],"$.architecture"); req(d["schema"]==ARCHITECTURE_SCHEMA,"architecture schema mismatch"); txt(d["receipt_id"],"$.architecture.receipt_id")
    s=obj(d["subject"],"$.architecture.subject"); keys(s,["repository","current_sha","runtime","subject_digest","eval_run_id"],"$.architecture.subject"); repo=txt(s["repository"],"repository"); sha=dig(s["current_sha"],HEX40,"current_sha"); runtime=txt(s["runtime"],"runtime"); subject=dig(s["subject_digest"],HEX64,"subject_digest"); run=txt(s["eval_run_id"],"eval_run_id")
    if expected_subject:
        for k in ("repository","current_sha","runtime","eval_run_id"): req(s[k]==expected_subject[k],f"architecture subject {k} mismatch")
    rubric_sha,cm,sm,pts,cdim=_rubric(); r=obj(d["rubric"],"rubric"); keys(r,["version","content_sha256"],"rubric"); req(r["version"]==RUBRIC_SCHEMA,"rubric version mismatch"); req(dig(r["content_sha256"],HEX64,"rubric digest")==rubric_sha,"rubric digest mismatch")
    cstate:dict[str,str]={}
    for i,cr in enumerate(arr(d["criteria"],"criteria")):
        q=f"criteria[{i}]"; x=obj(cr,q); keys(x,["criterion_id","status","evidence"],q); cid=txt(x["criterion_id"],q); req(cid in cm and cid not in cstate,"unknown/duplicate criterion "+cid); st=txt(x["status"],q); req(st in POS,q+" status invalid"); _evidence(x["evidence"],q+".evidence",subject,None if st=="NOT_EXERCISED" else ("PROVES_PRESENT" if st=="VERIFIED" else "PROVES_ABSENT"),set(cm[cid]["required_any_modes"]),st!="NOT_EXERCISED"); cstate[cid]=st
    req(set(cstate)==set(cm),"criteria must cover rubric exactly")
    vstate:dict[str,str]={}
    for i,sr in enumerate(arr(d["vibe_signals"],"vibe_signals")):
        q=f"vibe_signals[{i}]"; x=obj(sr,q); keys(x,["signal_id","status","evidence"],q); sid=txt(x["signal_id"],q); req(sid in sm and sid not in vstate,"unknown/duplicate signal "+sid); st=txt(x["status"],q); req(st in VIBES,q+" status invalid"); _evidence(x["evidence"],q+".evidence",subject,None if st=="NOT_EXERCISED" else ("PROVES_PRESENT" if st=="DETECTED" else "PROVES_ABSENT"),set(sm[sid]["required_any_modes"]),st!="NOT_EXERCISED"); vstate[sid]=st
    req(set(vstate)==set(sm),"signals must cover rubric exactly")
    detected=sorted(k for k,v in vstate.items() if v=="DETECTED"); contradicted={cid for sid in detected for cid in sm[sid]["contradicts"]}; ceiling=100.0; reasons=[]
    for sid in detected:
        if "score_ceiling" in sm[sid]: ceiling=min(ceiling,float(sm[sid]["score_ceiling"])); reasons.append(f"{sid}:score_ceiling={float(sm[sid]['score_ceiling']):g}")
    for cid in contradicted:req(cstate[cid]!="VERIFIED",f"{cid} VERIFIED while mapped Vibe DETECTED")
    dimensions={k:0.0 for k in {"control_flow_state","tool_boundary_idempotency","context_budget_memory","fault_tolerance_self_heal_hitl","evals_observability"}}; earned=0.0
    for cid,st in cstate.items():
        if st=="VERIFIED": earned+=pts[cid]; dimensions[cdim[cid]]+=pts[cid]
    deductions=sum(pts[cid] for cid in contradicted); effective=min(earned,ceiling); computed_band=band(effective)
    a=obj(d["authority"],"authority"); keys(a,["raw_private_reasoning","capability_widening","private_data_egress","source_rights_reviewed","human_review_authority"],"authority"); req(a=={"raw_private_reasoning":False,"capability_widening":False,"private_data_egress":False,"source_rights_reviewed":True,"human_review_authority":True},"authority boundary failed")
    dec=obj(d["declared"],"declared"); keys(dec,["dimension_scores","earned_points","deduction_points","score_ceiling","ceiling_reasons","effective_score","band","detected_vibe_signals","evidence_state"],"declared"); dd=obj(dec["dimension_scores"],"declared.dimension_scores"); req(set(dd)==set(dimensions),"dimension keys mismatch")
    for k,v in dimensions.items():close(v,dd[k],"dimension "+k)
    close(earned,dec["earned_points"],"earned_points"); close(deductions,dec["deduction_points"],"deduction_points"); close(ceiling,dec["score_ceiling"],"score_ceiling"); req(dec["ceiling_reasons"]==reasons,"ceiling reasons mismatch"); close(effective,dec["effective_score"],"effective_score"); req(dec["band"]==computed_band,"band mismatch"); req(dec["detected_vibe_signals"]==detected,"detected signals mismatch")
    terminal=all(v!="NOT_EXERCISED" for v in [*cstate.values(),*vstate.values()]); state=dec["evidence_state"]; req(state in {"PASS","NOT_EXERCISED"},"evidence_state invalid"); req((state=="PASS" and terminal) or (state=="NOT_EXERCISED" and not terminal),"evidence_state/terminal mismatch")
    return {"receipt_id":d["receipt_id"],"repository":repo,"current_sha":sha,"runtime":runtime,"eval_run_id":run,"rubric_sha256":rubric_sha,"dimension_scores":{k:round(v,6) for k,v in sorted(dimensions.items())},"earned_points":round(earned,6),"deduction_points":round(deductions,6),"score_ceiling":round(ceiling,6),"ceiling_reasons":reasons,"effective_score":round(effective,6),"band":computed_band,"detected_vibe_signals":detected,"evidence_state":state}
