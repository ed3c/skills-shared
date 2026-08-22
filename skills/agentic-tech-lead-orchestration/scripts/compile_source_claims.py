#!/usr/bin/env python3
"""Compile immutable issue/article/PDF/PRD claim inputs into a problem-closure ledger skeleton."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

KINDS={"GITHUB_ISSUE","ARTICLE","PDF","PRD"}
APPLICABILITY={"APPLICABLE","NOT_APPLICABLE","SUPERSEDED"}
HEX40=re.compile(r"^[0-9a-f]{40}$"); HEX64=re.compile(r"^[0-9a-f]{64}$")
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_REF=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
SHA256_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
WORKTREE=re.compile(r"^[A-Za-z0-9_.:@-]+$")
CLAIM_REQUIRED={"problem_id","kind","identity","location","claim","applicability","task_nodes","dag_nodes","issue_nodes"}
CLAIM_OPTIONAL={"claim_sha256","applicability_rationale","superseded_by","requires_human","session_attempts","implementation_evidence","shadow_review"}
IMPL_KINDS={"COMMIT","PR","MERGE_SUBJECT","SOURCE_DIFF","GENERATED_ARTIFACT"}
IMPL_STATUS={"CURRENT","HISTORICAL","SUPERSEDED"}
SHADOW_REVIEW_FIELDS={"repo_subject","reviewer_task_id","reviewer_attempt_id"}
class ContractError(ValueError): pass

def _canonical(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def _digest_obj(v:Any)->str:return hashlib.sha256(_canonical(v)).hexdigest()
def _claim_digest(text:str)->str:return hashlib.sha256(text.encode("utf-8")).hexdigest()
def _nonempty(v:Any)->bool:return isinstance(v,str) and bool(v.strip())
def _subject(v:Any)->dict[str,str]:
    if not isinstance(v,dict) or set(v)!={"repo","commit","tree"}: raise ContractError("repo_subject fields invalid")
    if not isinstance(v["repo"],str) or not REPO.fullmatch(v["repo"]): raise ContractError("repo_subject.repo must be owner/name")
    if not isinstance(v["commit"],str) or not HEX40.fullmatch(v["commit"]): raise ContractError("repo_subject.commit must be exact 40-hex")
    if not isinstance(v["tree"],str) or not HEX40.fullmatch(v["tree"]): raise ContractError("repo_subject.tree must be exact 40-hex")
    return dict(v)
def _source(kind:Any,identity:Any,location:Any)->None:
    if kind not in KINDS: raise ContractError("unsupported source kind")
    if not _nonempty(location): raise ContractError("exact source location required")
    if kind=="GITHUB_ISSUE":
        if not isinstance(identity,str) or not GITHUB_REF.fullmatch(identity): raise ContractError("GitHub issue identity must be owner/repo#number")
    elif not isinstance(identity,str) or not SHA256_ID.fullmatch(identity): raise ContractError(f"{kind} identity must be immutable sha256:<64-hex>")
def _strings(v:Any,label:str)->list[str]:
    if not isinstance(v,list) or not all(_nonempty(x) for x in v) or len(set(v))!=len(v): raise ContractError(f"{label} invalid")
    return list(v)
def _issues(v:Any)->list[int]:
    if not isinstance(v,list) or not all(isinstance(x,int) and not isinstance(x,bool) and x>0 for x in v) or len(set(v))!=len(v): raise ContractError("issue_nodes invalid")
    return list(v)
def _attempts(v:Any)->list[dict[str,Any]]:
    if v is None:return []
    if not isinstance(v,list):raise ContractError("session_attempts must be list")
    out=[]; seen=set()
    for r in v:
        if not isinstance(r,dict) or set(r) not in ({"task_id","attempt_id","worktree"},{"task_id","attempt_id","worktree","thread_id"}): raise ContractError("session attempt fields invalid")
        if not _nonempty(r["task_id"]) or not _nonempty(r["attempt_id"]): raise ContractError("session task/attempt required")
        if not isinstance(r["worktree"],str) or not WORKTREE.fullmatch(r["worktree"]): raise ContractError("worktree must be portable identity")
        if "thread_id" in r and r["thread_id"] is not None and not _nonempty(r["thread_id"]): raise ContractError("thread_id invalid")
        k=(r["task_id"],r["attempt_id"])
        if k in seen:raise ContractError("duplicate task/attempt")
        seen.add(k);out.append(dict(r))
    return out
def _evidence_subject(kind:str,subject:Any)->None:
    if not _nonempty(subject):raise ContractError("implementation subject required")
    if kind in {"COMMIT","MERGE_SUBJECT"} and not HEX40.fullmatch(subject):raise ContractError("commit/merge subject must be exact 40-hex")
    if kind=="PR" and not GITHUB_REF.fullmatch(subject):raise ContractError("PR subject must be owner/repo#number")
    if kind in {"SOURCE_DIFF","GENERATED_ARTIFACT"} and not SHA256_ID.fullmatch(subject):raise ContractError("artifact subject must be sha256 identity")
def _impls(v:Any,current:dict[str,str])->list[dict[str,Any]]:
    if v is None:return []
    if not isinstance(v,list):raise ContractError("implementation_evidence must be list")
    out=[];seen=set()
    for r in v:
        if not isinstance(r,dict) or set(r)!={"kind","subject","repo_subject","status"}:raise ContractError("implementation evidence fields invalid")
        if r["kind"] not in IMPL_KINDS or r["status"] not in IMPL_STATUS:raise ContractError("implementation evidence kind/status invalid")
        rs=_subject(r["repo_subject"]);_evidence_subject(r["kind"],r["subject"])
        if rs["repo"]!=current["repo"]:raise ContractError("implementation evidence repo mismatch")
        if r["status"]=="CURRENT" and rs!=current:raise ContractError("CURRENT implementation evidence is stale")
        k=(r["kind"],r["subject"],tuple(sorted(rs.items())),r["status"])
        if k in seen:raise ContractError("duplicate implementation evidence")
        seen.add(k);out.append({"kind":r["kind"],"subject":r["subject"],"repo_subject":rs,"status":r["status"]})
    return out
def _shadow_review(v:Any,current:dict[str,str],attempt_keys:set[tuple[str,str]])->dict[str,Any]|None:
    # Mirrors check_problem_closure.py's shadow_review binding (same-subject + reviewer
    # independent of every implementer attempt). Note: compile_claims() always emits
    # shadow_verdict="NOT_REVIEWED" below, so the checker's "required when verdict is not
    # NOT_REVIEWED" gate can never fire through this path -- a hand-authored ledger is
    # where shadow_review actually becomes load-bearing. This still validates shape/
    # subject/independence unconditionally whenever a caller supplies shadow_review, so a
    # source-claims.json can carry a pre-validated review through compilation.
    if v is None:return None
    if not isinstance(v,dict) or set(v)!=SHADOW_REVIEW_FIELDS:raise ContractError("shadow_review fields invalid")
    rs=_subject(v["repo_subject"])
    if rs!=current:raise ContractError("shadow_review is stale for current repo subject")
    if not _nonempty(v["reviewer_task_id"]) or not _nonempty(v["reviewer_attempt_id"]):raise ContractError("shadow_review reviewer identity required")
    key=(v["reviewer_task_id"],v["reviewer_attempt_id"])
    if key in attempt_keys:raise ContractError("shadow_review reviewer attempt is not independent of implementer attempts")
    return {"repo_subject":rs,"reviewer_task_id":v["reviewer_task_id"],"reviewer_attempt_id":v["reviewer_attempt_id"]}

def compile_claims(data:dict[str,Any])->dict[str,Any]:
    if not isinstance(data,dict) or set(data)!={"schema_version","repo_subject","claims"} or data["schema_version"]!=1:raise ContractError("input fields/schema invalid")
    subject=_subject(data["repo_subject"]); claims=data["claims"]
    if not isinstance(claims,list) or not claims:raise ContractError("claims must be non-empty list")
    ids=[];source_keys=[];normalized=[]
    for raw in claims:
        if not isinstance(raw,dict):raise ContractError("claim row must be object")
        actual=set(raw)
        if not CLAIM_REQUIRED<=actual or actual-(CLAIM_REQUIRED|CLAIM_OPTIONAL):raise ContractError("claim fields invalid")
        pid=raw["problem_id"]
        if not _nonempty(pid) or pid in ids:raise ContractError("problem_id missing/duplicate")
        ids.append(pid);_source(raw["kind"],raw["identity"],raw["location"])
        sk=(raw["kind"],raw["identity"],raw["location"])
        if sk in source_keys:raise ContractError("duplicate source tuple")
        source_keys.append(sk)
        if not _nonempty(raw["claim"]):raise ContractError("claim text required")
        digest=_claim_digest(raw["claim"])
        supplied=raw.get("claim_sha256")
        if supplied is not None and (not isinstance(supplied,str) or not HEX64.fullmatch(supplied) or supplied!=digest):raise ContractError("caller claim_sha256 mismatch")
        app=raw["applicability"]
        if app not in APPLICABILITY:raise ContractError("applicability invalid")
        tasks=_strings(raw["task_nodes"],"task_nodes"); dags=_strings(raw["dag_nodes"],"dag_nodes"); issues=_issues(raw["issue_nodes"])
        if app!="NOT_APPLICABLE" and (not tasks or not dags or not issues):raise ContractError("applicable/superseded claim needs task/DAG/issue lineage")
        if app=="NOT_APPLICABLE" and not _nonempty(raw.get("applicability_rationale")):raise ContractError("NOT_APPLICABLE requires rationale")
        if app=="SUPERSEDED" and not _nonempty(raw.get("superseded_by")):raise ContractError("SUPERSEDED requires target")
        attempts=_attempts(raw.get("session_attempts")); impls=_impls(raw.get("implementation_evidence"),subject)
        if any(x["status"]=="CURRENT" for x in impls) and not attempts:raise ContractError("current implementation evidence requires session lineage")
        attempt_keys={(a["task_id"],a["attempt_id"]) for a in attempts}
        shadow_review=_shadow_review(raw.get("shadow_review"),subject,attempt_keys)
        normalized.append((raw,digest,tasks,dags,issues,attempts,impls,shadow_review))
    idset=set(ids)
    for raw,*_ in normalized:
        if raw["applicability"]=="SUPERSEDED" and raw["superseded_by"] not in idset:raise ContractError("SUPERSEDED target absent from denominator")
    manifest=[];problems=[]
    for raw,digest,tasks,dags,issues,attempts,impls,shadow_review in normalized:
        manifest.append({"problem_id":raw["problem_id"],"kind":raw["kind"],"identity":raw["identity"],"location":raw["location"],"claim_sha256":digest})
        current=any(x["status"]=="CURRENT" for x in impls)
        if raw["applicability"]=="NOT_APPLICABLE":closure="NOT_APPLICABLE"
        elif raw["applicability"]=="SUPERSEDED":closure="PARTIAL"
        elif raw.get("requires_human") is True:closure="HUMAN_ADMIT_REQUIRED"
        elif current:closure="IMPLEMENTED_UNVERIFIED"
        else:closure="OPEN"
        p={"problem_id":raw["problem_id"],"source":{"kind":raw["kind"],"identity":raw["identity"],"location":raw["location"]},"claim":raw["claim"],"applicability":raw["applicability"],"repo_subject":dict(subject),"task_nodes":tasks,"dag_nodes":dags,"issue_nodes":issues,"session_attempts":attempts,"implementation_evidence":impls,"verification_evidence":[],"receipts":[],"merge_subjects":[],"shadow_verdict":"NOT_REVIEWED","residual_gaps":[],"closure":closure}
        if shadow_review is not None:p["shadow_review"]=shadow_review
        for f in("applicability_rationale","superseded_by","requires_human"):
            if f in raw:p[f]=raw[f]
        problems.append(p)
    manifest=sorted(manifest,key=lambda x:x["problem_id"]);problems=sorted(problems,key=lambda x:x["problem_id"]);ids=sorted(ids)
    return {"schema_version":1,"denominator":{"problem_ids":ids,"source_manifest_sha256":_digest_obj(manifest)},"source_manifest":manifest,"problems":problems}
def main():
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("--output");a=p.parse_args();r=compile_claims(json.loads(Path(a.input).read_text(encoding="utf-8")));out=json.dumps(r,indent=2,sort_keys=True)+"\n";Path(a.output).write_text(out,encoding="utf-8") if a.output else print(out,end="");return 0
if __name__=="__main__":raise SystemExit(main())
