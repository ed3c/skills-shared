#!/usr/bin/env python3
"""Deterministic problem-closure ledger checker."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

CLOSURES={"OPEN","PARTIAL","IMPLEMENTED_UNVERIFIED","VERIFIED_LOCAL","VERIFIED_LIVE","NOT_APPLICABLE","HUMAN_ADMIT_REQUIRED"}
APPLICABILITY={"APPLICABLE","NOT_APPLICABLE","SUPERSEDED"}
SHADOW={"PASS","FAIL","PARTIAL","NOT_REVIEWED"}
VERIFY_LANES={"LOCAL","CI","PROVIDER_LIVE","HUMAN","RELEASE"}
IMPLEMENTATION_KINDS={"COMMIT","PR","MERGE_SUBJECT","SOURCE_DIFF","GENERATED_ARTIFACT"}
IMPLEMENTATION_STATUS={"CURRENT","HISTORICAL","SUPERSEDED"}
SOURCE_KINDS={"GITHUB_ISSUE","ARTICLE","PDF","PRD"}
HEX40=re.compile(r"^[0-9a-f]{40}$")
HEX64=re.compile(r"^[0-9a-f]{64}$")
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_REF=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
SHA256_ID=re.compile(r"^sha256:[0-9a-f]{64}$")
PORTABLE_WORKTREE=re.compile(r"^[A-Za-z0-9_.:@-]+$")

LEDGER_FIELDS={"schema_version","denominator","source_manifest","problems"}
DENOMINATOR_FIELDS={"problem_ids","source_manifest_sha256"}
SOURCE_FIELDS={"kind","identity","location"}
MANIFEST_FIELDS={"problem_id","kind","identity","location","claim_sha256"}
SUBJECT_FIELDS={"repo","commit","tree"}
SESSION_BASE_FIELDS={"task_id","attempt_id","worktree"}
IMPLEMENTATION_FIELDS={"kind","subject","repo_subject","status"}
VERIFICATION_FIELDS={"lane","subject","repo_subject"}
SHADOW_REVIEW_FIELDS={"repo_subject","reviewer_task_id","reviewer_attempt_id"}
PROBLEM_REQUIRED={"problem_id","source","claim","applicability","repo_subject","task_nodes","dag_nodes","issue_nodes","session_attempts","implementation_evidence","verification_evidence","receipts","merge_subjects","shadow_verdict","residual_gaps","closure"}
PROBLEM_OPTIONAL={"applicability_rationale","superseded_by","requires_human","shadow_review"}

class ContractError(ValueError):
    pass

def _nonempty(value:Any)->bool:
    return isinstance(value,str) and bool(value.strip())

def _canonical(value:Any)->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def _digest(value:Any)->str:
    return hashlib.sha256(_canonical(value)).hexdigest()

def _exact_fields(value:Any,expected:set[str],label:str)->None:
    if not isinstance(value,dict):
        raise ContractError(f"{label} must be an object")
    actual=set(value)
    if actual!=expected:
        raise ContractError(f"{label} fields drifted: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

def _validate_repo(value:Any,label:str)->str:
    if not isinstance(value,str) or not REPO.fullmatch(value):
        raise ContractError(f"{label} must be exact owner/name")
    return value

def _validate_subject(value:Any,label:str)->dict[str,str]:
    _exact_fields(value,SUBJECT_FIELDS,label)
    repo=_validate_repo(value["repo"],f"{label}.repo")
    commit=value["commit"]; tree=value["tree"]
    if not isinstance(commit,str) or not HEX40.fullmatch(commit):
        raise ContractError(f"{label}.commit must be exact 40-hex")
    if not isinstance(tree,str) or not HEX40.fullmatch(tree):
        raise ContractError(f"{label}.tree must be exact 40-hex")
    return {"repo":repo,"commit":commit,"tree":tree}

def _subject_key(value:dict[str,str])->tuple[str,str,str]:
    return value["repo"],value["commit"],value["tree"]

def _validate_source(kind:Any,identity:Any,location:Any,label:str)->None:
    if kind not in SOURCE_KINDS:
        raise ContractError(f"{label}.kind is unsupported")
    if not _nonempty(location):
        raise ContractError(f"{label}.location must be exact and non-empty")
    if kind=="GITHUB_ISSUE":
        if not isinstance(identity,str) or not GITHUB_REF.fullmatch(identity):
            raise ContractError(f"{label}.identity must be owner/repo#issue")
    elif not isinstance(identity,str) or not SHA256_ID.fullmatch(identity):
        raise ContractError(f"{label}.identity must be immutable sha256:<64-hex> for {kind}")

def _validate_evidence_subject(kind:str,subject:str,label:str)->None:
    if kind in {"COMMIT","MERGE_SUBJECT"}:
        if not HEX40.fullmatch(subject):
            raise ContractError(f"{label}.subject must be exact 40-hex for {kind}")
    elif kind=="PR":
        if not GITHUB_REF.fullmatch(subject):
            raise ContractError(f"{label}.subject must be owner/repo#number for PR")
    elif kind in {"SOURCE_DIFF","GENERATED_ARTIFACT"}:
        if not SHA256_ID.fullmatch(subject):
            raise ContractError(f"{label}.subject must be sha256:<64-hex> for {kind}")

def _validate_worktree(value:Any,label:str)->None:
    if not isinstance(value,str) or not PORTABLE_WORKTREE.fullmatch(value):
        raise ContractError(f"{label} must be a portable worktree identity, not a machine-local path")

def _validate_manifest_entry(entry:Any,label:str)->None:
    _exact_fields(entry,MANIFEST_FIELDS,label)
    if not _nonempty(entry["problem_id"]):
        raise ContractError(f"{label}.problem_id must be non-empty")
    _validate_source(entry["kind"],entry["identity"],entry["location"],label)
    if not isinstance(entry["claim_sha256"],str) or not HEX64.fullmatch(entry["claim_sha256"]):
        raise ContractError(f"{label}.claim_sha256 must be 64-hex")

def validate_problem(problem:Any,manifest_entry:dict[str,Any])->None:
    if not isinstance(problem,dict):
        raise ContractError("problem must be an object")
    actual=set(problem)
    if not PROBLEM_REQUIRED.issubset(actual) or actual-(PROBLEM_REQUIRED|PROBLEM_OPTIONAL):
        raise ContractError(f"{problem.get('problem_id','?')}: problem fields drifted: missing={sorted(PROBLEM_REQUIRED-actual)} extra={sorted(actual-(PROBLEM_REQUIRED|PROBLEM_OPTIONAL))}")
    pid=problem["problem_id"]
    if not _nonempty(pid):
        raise ContractError("problem_id must be non-empty")
    if manifest_entry["problem_id"]!=pid:
        raise ContractError(f"{pid}: source manifest problem_id mismatch")

    source=problem["source"]
    _exact_fields(source,SOURCE_FIELDS,f"{pid}.source")
    _validate_source(source["kind"],source["identity"],source["location"],f"{pid}.source")
    if any(source[k]!=manifest_entry[k] for k in ("kind","identity","location")):
        raise ContractError(f"{pid}: source identity/location differs from frozen manifest")
    if not _nonempty(problem["claim"]):
        raise ContractError(f"{pid}: claim required")
    if hashlib.sha256(problem["claim"].encode("utf-8")).hexdigest()!=manifest_entry["claim_sha256"]:
        raise ContractError(f"{pid}: claim digest differs from frozen source manifest")

    if problem["applicability"] not in APPLICABILITY:
        raise ContractError(f"{pid}: invalid applicability")
    if problem["closure"] not in CLOSURES:
        raise ContractError(f"{pid}: invalid closure")
    if problem["shadow_verdict"] not in SHADOW:
        raise ContractError(f"{pid}: invalid shadow verdict")

    current_subject=_validate_subject(problem["repo_subject"],f"{pid}.repo_subject")
    for field in ("task_nodes","dag_nodes","issue_nodes","session_attempts","implementation_evidence","verification_evidence","receipts","merge_subjects","residual_gaps"):
        if not isinstance(problem[field],list):
            raise ContractError(f"{pid}: {field} must be a list")
    if not all(_nonempty(x) for x in problem["task_nodes"]) or len(set(problem["task_nodes"]))!=len(problem["task_nodes"]):
        raise ContractError(f"{pid}: invalid or duplicate task node")
    if not all(_nonempty(x) for x in problem["dag_nodes"]) or len(set(problem["dag_nodes"]))!=len(problem["dag_nodes"]):
        raise ContractError(f"{pid}: invalid or duplicate DAG node")
    if not all(isinstance(x,int) and not isinstance(x,bool) and x>0 for x in problem["issue_nodes"]) or len(set(problem["issue_nodes"]))!=len(problem["issue_nodes"]):
        raise ContractError(f"{pid}: invalid or duplicate issue node")
    if problem["applicability"]!="NOT_APPLICABLE" and (not problem["task_nodes"] or not problem["dag_nodes"] or not problem["issue_nodes"]):
        raise ContractError(f"{pid}: applicable/superseded claim requires task/DAG/issue lineage")
    if problem["applicability"]=="NOT_APPLICABLE" and not _nonempty(problem.get("applicability_rationale")):
        raise ContractError(f"{pid}: NOT_APPLICABLE requires rationale")
    if problem["applicability"]=="SUPERSEDED" and not _nonempty(problem.get("superseded_by")):
        raise ContractError(f"{pid}: SUPERSEDED requires superseded_by")

    attempts=set()
    for i,attempt in enumerate(problem["session_attempts"]):
        expected=SESSION_BASE_FIELDS|({"thread_id"} if isinstance(attempt,dict) and "thread_id" in attempt else set())
        _exact_fields(attempt,expected,f"{pid}.session_attempts[{i}]")
        if not _nonempty(attempt["task_id"]) or not _nonempty(attempt["attempt_id"]):
            raise ContractError(f"{pid}: invalid session task/attempt identity")
        _validate_worktree(attempt["worktree"],f"{pid}.session_attempts[{i}].worktree")
        if "thread_id" in attempt and attempt["thread_id"] is not None and not _nonempty(attempt["thread_id"]):
            raise ContractError(f"{pid}: invalid thread_id")
        key=(attempt["task_id"],attempt["attempt_id"])
        if key in attempts:
            raise ContractError(f"{pid}: duplicate task/attempt identity {key}")
        attempts.add(key)

    # Shadow O8: shadow_verdict is a bare enum with no receipt of its own, so any
    # non-NOT_REVIEWED verdict must carry a shadow_review binding the same exact
    # repo subject and a reviewer attempt identity distinct from every implementer
    # attempt -- otherwise "Shadow agreement" degenerates into an unverifiable
    # hand-written string (the forbidden substitution TECH_LEAD_SHADOW_CLOSURE.md warns against).
    if problem["shadow_verdict"]!="NOT_REVIEWED":
        if "shadow_review" not in problem:
            raise ContractError(f"{pid}: shadow_review required when shadow_verdict is not NOT_REVIEWED")
        review=problem["shadow_review"]
        _exact_fields(review,SHADOW_REVIEW_FIELDS,f"{pid}.shadow_review")
        review_subject=_validate_subject(review["repo_subject"],f"{pid}.shadow_review.repo_subject")
        if review_subject!=current_subject:
            raise ContractError(f"{pid}: shadow_review is stale for current repo subject")
        if not _nonempty(review["reviewer_task_id"]) or not _nonempty(review["reviewer_attempt_id"]):
            raise ContractError(f"{pid}: shadow_review reviewer identity required")
        reviewer_key=(review["reviewer_task_id"],review["reviewer_attempt_id"])
        if reviewer_key in attempts:
            raise ContractError(f"{pid}: shadow_review reviewer attempt is not independent of implementer attempts")

    merge_keys=set()
    for i,subject in enumerate(problem["merge_subjects"]):
        normalized=_validate_subject(subject,f"{pid}.merge_subjects[{i}]")
        if normalized["repo"]!=current_subject["repo"]:
            raise ContractError(f"{pid}: merge subject repository mismatch")
        key=_subject_key(normalized)
        if key in merge_keys:
            raise ContractError(f"{pid}: duplicate merge subject")
        merge_keys.add(key)

    current_impl=0
    seen_impl=set()
    for i,evidence in enumerate(problem["implementation_evidence"]):
        _exact_fields(evidence,IMPLEMENTATION_FIELDS,f"{pid}.implementation_evidence[{i}]")
        kind=evidence["kind"]; status=evidence["status"]; subject=evidence["subject"]
        if kind not in IMPLEMENTATION_KINDS or status not in IMPLEMENTATION_STATUS or not _nonempty(subject):
            raise ContractError(f"{pid}: invalid implementation evidence")
        _validate_evidence_subject(kind,subject,f"{pid}.implementation_evidence[{i}]")
        ev_subject=_validate_subject(evidence["repo_subject"],f"{pid}.implementation_evidence[{i}].repo_subject")
        if ev_subject["repo"]!=current_subject["repo"]:
            raise ContractError(f"{pid}: implementation evidence repository mismatch")
        key=(kind,subject,_subject_key(ev_subject),status)
        if key in seen_impl:
            raise ContractError(f"{pid}: duplicate implementation evidence")
        seen_impl.add(key)
        if status=="CURRENT":
            if ev_subject!=current_subject:
                raise ContractError(f"{pid}: CURRENT implementation evidence is stale")
            current_impl+=1
        if kind=="MERGE_SUBJECT" and _subject_key(ev_subject) not in merge_keys:
            raise ContractError(f"{pid}: merge evidence must bind a declared merge_subject")
    if current_impl and not problem["session_attempts"]:
        raise ContractError(f"{pid}: current implementation evidence requires session/attempt/worktree lineage")

    receipt_keys=set()
    for i,receipt in enumerate(problem["receipts"]):
        _exact_fields(receipt,VERIFICATION_FIELDS,f"{pid}.receipts[{i}]")
        if receipt["lane"] not in VERIFY_LANES or not _nonempty(receipt["subject"]):
            raise ContractError(f"{pid}: invalid receipt")
        rs=_validate_subject(receipt["repo_subject"],f"{pid}.receipts[{i}].repo_subject")
        if rs!=current_subject:
            raise ContractError(f"{pid}: receipt is stale for current repo subject")
        key=(receipt["lane"],receipt["subject"],_subject_key(rs))
        if key in receipt_keys:
            raise ContractError(f"{pid}: duplicate receipt")
        receipt_keys.add(key)

    seen_verify=set()
    for i,evidence in enumerate(problem["verification_evidence"]):
        _exact_fields(evidence,VERIFICATION_FIELDS,f"{pid}.verification_evidence[{i}]")
        if evidence["lane"] not in VERIFY_LANES or not _nonempty(evidence["subject"]):
            raise ContractError(f"{pid}: invalid verification evidence")
        rs=_validate_subject(evidence["repo_subject"],f"{pid}.verification_evidence[{i}].repo_subject")
        if rs!=current_subject:
            raise ContractError(f"{pid}: verification evidence is stale for current repo subject")
        key=(evidence["lane"],evidence["subject"],_subject_key(rs))
        if key in seen_verify:
            raise ContractError(f"{pid}: duplicate verification evidence")
        seen_verify.add(key)
        if key not in receipt_keys:
            raise ContractError(f"{pid}: verification evidence lacks matching receipt")
    if problem["verification_evidence"] and current_impl==0:
        raise ContractError(f"{pid}: verification evidence cannot exist without current implementation evidence")

    if not all(_nonempty(gap) for gap in problem["residual_gaps"]) or len(set(problem["residual_gaps"]))!=len(problem["residual_gaps"]):
        raise ContractError(f"{pid}: invalid or duplicate residual gap")

def recompute(problem:dict[str,Any])->str:
    if problem["applicability"]=="NOT_APPLICABLE":
        return "NOT_APPLICABLE"
    if problem["applicability"]=="SUPERSEDED":
        return "PARTIAL"
    current=problem["repo_subject"]
    impl=any(item["status"]=="CURRENT" and item["repo_subject"]==current for item in problem["implementation_evidence"])
    verify={item["lane"] for item in problem["verification_evidence"]}
    if problem.get("requires_human") is True and "HUMAN" not in verify:
        return "HUMAN_ADMIT_REQUIRED"
    if not impl:
        return "OPEN"
    if problem["residual_gaps"] or problem["shadow_verdict"] in {"FAIL","PARTIAL"}:
        return "PARTIAL"
    if not verify or problem["shadow_verdict"]=="NOT_REVIEWED":
        return "IMPLEMENTED_UNVERIFIED"
    if "PROVIDER_LIVE" in verify and problem["shadow_verdict"]=="PASS":
        return "VERIFIED_LIVE"
    if verify & {"LOCAL","CI"} and problem["shadow_verdict"]=="PASS":
        return "VERIFIED_LOCAL"
    return "IMPLEMENTED_UNVERIFIED"

def _validate_supersession(problems:dict[str,dict[str,Any]])->None:
    for pid,p in problems.items():
        if p["applicability"]!="SUPERSEDED":
            continue
        successor=p["superseded_by"]
        if successor==pid:
            raise ContractError(f"{pid}: superseded_by cannot point to itself")
        if successor not in problems:
            raise ContractError(f"{pid}: superseded_by target is absent from denominator")
    for start in problems:
        seen=set(); current=start
        while problems[current]["applicability"]=="SUPERSEDED":
            if current in seen:
                raise ContractError(f"supersession cycle detected from {start}")
            seen.add(current)
            current=problems[current]["superseded_by"]

def check_ledger(data:Any)->dict[str,Any]:
    _exact_fields(data,LEDGER_FIELDS,"ledger")
    if data["schema_version"]!=1:
        raise ContractError("unsupported schema_version")
    denominator=data["denominator"]
    _exact_fields(denominator,DENOMINATOR_FIELDS,"denominator")
    ids=denominator["problem_ids"]
    if not isinstance(ids,list) or not ids or not all(_nonempty(pid) for pid in ids):
        raise ContractError("denominator.problem_ids must be a non-empty string list")
    if ids!=sorted(set(ids)):
        raise ContractError("denominator.problem_ids must be sorted and unique")

    manifest=data["source_manifest"]
    if not isinstance(manifest,list) or not manifest:
        raise ContractError("source_manifest must be a non-empty list")
    manifest_by_id={}
    for i,entry in enumerate(manifest):
        _validate_manifest_entry(entry,f"source_manifest[{i}]")
        pid=entry["problem_id"]
        if pid in manifest_by_id:
            raise ContractError(f"duplicate source_manifest problem_id: {pid}")
        manifest_by_id[pid]=entry
    if sorted(manifest_by_id)!=ids:
        raise ContractError("source_manifest IDs differ from frozen denominator")
    digest=denominator["source_manifest_sha256"]
    if not isinstance(digest,str) or not HEX64.fullmatch(digest):
        raise ContractError("denominator.source_manifest_sha256 must be 64-hex")
    canonical_manifest=[manifest_by_id[pid] for pid in ids]
    if _digest(canonical_manifest)!=digest:
        raise ContractError("source_manifest digest is stale")

    raw_problems=data["problems"]
    if not isinstance(raw_problems,list):
        raise ContractError("problems must be a list")
    problems={}
    for problem in raw_problems:
        if not isinstance(problem,dict) or not _nonempty(problem.get("problem_id")):
            raise ContractError("problem_id must be non-empty")
        pid=problem["problem_id"]
        if pid in problems:
            raise ContractError(f"duplicate problem_id: {pid}")
        if pid not in manifest_by_id:
            raise ContractError(f"{pid}: problem absent from frozen source manifest")
        validate_problem(problem,manifest_by_id[pid])
        problems[pid]=problem
    if sorted(problems)!=ids:
        raise ContractError(f"problem denominator drift: missing={sorted(set(ids)-set(problems))} extra={sorted(set(problems)-set(ids))}")
    _validate_supersession(problems)

    counts={state:0 for state in CLOSURES}; mismatches=[]
    for pid in ids:
        expected=recompute(problems[pid]); counts[expected]+=1
        if problems[pid]["closure"]!=expected:
            mismatches.append({"problem_id":pid,"declared":problems[pid]["closure"],"expected":expected})
    if mismatches:
        raise ContractError(f"closure laundering/drift: {mismatches}")
    residual=[pid for pid in ids if problems[pid]["closure"] in {"OPEN","PARTIAL","IMPLEMENTED_UNVERIFIED","HUMAN_ADMIT_REQUIRED"}]
    return {"problem_count":len(ids),"source_manifest_sha256":digest,"counts":counts,"residual_problem_ids":residual,"evidence_ceiling":"LEDGER_DETERMINISTIC_CHECKED"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("ledger"); args=ap.parse_args()
    data=json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    print(json.dumps(check_ledger(data),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
