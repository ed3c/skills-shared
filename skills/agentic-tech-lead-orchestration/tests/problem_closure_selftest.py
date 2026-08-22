#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parent/"scripts"/"check_problem_closure.py"
RENDER=HERE.parent/"scripts"/"render_problem_closure.py"

spec=importlib.util.spec_from_file_location("closure",SCRIPT); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)
rspec=importlib.util.spec_from_file_location("projection",RENDER); renderer=importlib.util.module_from_spec(rspec); assert rspec and rspec.loader; rspec.loader.exec_module(renderer)

CURRENT={"repo":"ed3c/skills-shared","commit":"0123456789abcdef0123456789abcdef01234567","tree":"89abcdef0123456789abcdef0123456789abcdef"}
OLD={"repo":"ed3c/skills-shared","commit":"1111111111111111111111111111111111111111","tree":"2222222222222222222222222222222222222222"}

def problem(pid="P-001",claim="Preserve independent evidence lanes."):
    source={"kind":"PDF","identity":"sha256:"+"a"*64,"location":"page:22"}
    return {
      "problem_id":pid,"source":source,"claim":claim,"applicability":"APPLICABLE","repo_subject":copy.deepcopy(CURRENT),
      "task_nodes":["T1"],"dag_nodes":["DAG:T1"],"issue_nodes":[378],
      "session_attempts":[{"task_id":"T1","attempt_id":"a01","worktree":"worktree:T1:a01","thread_id":"thread-1"}],
      "implementation_evidence":[{"kind":"COMMIT","subject":CURRENT["commit"],"repo_subject":copy.deepcopy(CURRENT),"status":"CURRENT"}],
      "verification_evidence":[{"lane":"LOCAL","subject":"receipt:local:1","repo_subject":copy.deepcopy(CURRENT)}],
      "receipts":[{"lane":"LOCAL","subject":"receipt:local:1","repo_subject":copy.deepcopy(CURRENT)}],
      "merge_subjects":[],"shadow_verdict":"PASS",
      "shadow_review":{"repo_subject":copy.deepcopy(CURRENT),"reviewer_task_id":"T1","reviewer_attempt_id":"shadow-a01"},
      "residual_gaps":[],"closure":"VERIFIED_LOCAL"
    }

def ledger(problems):
    manifest=[]
    for p in problems:
        manifest.append({
          "problem_id":p["problem_id"],"kind":p["source"]["kind"],"identity":p["source"]["identity"],"location":p["source"]["location"],
          "claim_sha256":hashlib.sha256(p["claim"].encode()).hexdigest()
        })
    manifest=sorted(manifest,key=lambda x:x["problem_id"]); ids=[x["problem_id"] for x in manifest]
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return {"schema_version":1,"denominator":{"problem_ids":ids,"source_manifest_sha256":digest},"source_manifest":manifest,"problems":problems}

_positive=0
_mutation=0

# Positive 1
base=ledger([problem()]); out=m.check_ledger(base); assert out["problem_count"]==1 and out["counts"]["VERIFIED_LOCAL"]==1
_positive+=1
# Positive 2
live=problem(); live["verification_evidence"].append({"lane":"PROVIDER_LIVE","subject":"receipt:live:1","repo_subject":copy.deepcopy(CURRENT)}); live["receipts"].append({"lane":"PROVIDER_LIVE","subject":"receipt:live:1","repo_subject":copy.deepcopy(CURRENT)}); live["closure"]="VERIFIED_LIVE"; m.check_ledger(ledger([live]))
_positive+=1
# Positive 3
partial=problem(); partial["residual_gaps"]=["provider live not exercised"]; partial["closure"]="PARTIAL"; m.check_ledger(ledger([partial]))
_positive+=1
# Positive 4
human=problem(); human["requires_human"]=True; human["closure"]="HUMAN_ADMIT_REQUIRED"; m.check_ledger(ledger([human]))
_positive+=1
# Positive 5
na=problem(); na["applicability"]="NOT_APPLICABLE"; na["applicability_rationale"]="Outside repository contract."; na["task_nodes"]=[]; na["dag_nodes"]=[]; na["issue_nodes"]=[]; na["session_attempts"]=[]; na["implementation_evidence"]=[]; na["verification_evidence"]=[]; na["receipts"]=[]; na["shadow_verdict"]="NOT_REVIEWED"; del na["shadow_review"]; na["closure"]="NOT_APPLICABLE"; m.check_ledger(ledger([na]))
_positive+=1
# Positive 6
old=problem("P-OLD","Old implementation route."); old["applicability"]="SUPERSEDED"; old["superseded_by"]="P-NEW"; old["implementation_evidence"][0]["status"]="HISTORICAL"; old["implementation_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); old["verification_evidence"]=[]; old["receipts"]=[]; old["closure"]="PARTIAL"
new=problem("P-NEW","Replacement implementation route."); m.check_ledger(ledger([old,new]))
_positive+=1
# Positive 7: shadow_review explicitly reaffirmed (distinct reviewer identity from the default)
reviewed=problem(); reviewed["shadow_review"]={"repo_subject":copy.deepcopy(CURRENT),"reviewer_task_id":"T2","reviewer_attempt_id":"shadow-review-1"}; m.check_ledger(ledger([reviewed]))
_positive+=1
# deterministic projection
assert renderer.render(base)==renderer.render(copy.deepcopy(base))

def must_fail(data):
    global _mutation
    try:m.check_ledger(data)
    except m.ContractError:
        _mutation+=1
        return
    raise AssertionError("mutation unexpectedly passed")

x=ledger([problem()]); x["problems"][0]["source"]["location"]=""; must_fail(x) # 1
x=ledger([problem()]); x["problems"][0]["verification_evidence"][0]["lane"]="MERGE"; must_fail(x) # 2
x=ledger([problem()]); x["problems"][0]["receipts"]=[]; must_fail(x) # 3
x=ledger([problem()]); x["problems"][0]["closure"]="VERIFIED_LIVE"; must_fail(x) # 4
x=ledger([problem()]); x["problems"][0]["residual_gaps"]=["still open"]; must_fail(x) # 5
x=ledger([problem()]); x["problems"][0]["applicability"]="NOT_APPLICABLE"; x["problems"][0]["closure"]="NOT_APPLICABLE"; must_fail(x) # 6
x=ledger([problem(),problem()]); must_fail(x) # 7
x=ledger([problem()]); x["problems"][0]["repo_subject"]["commit"]="abc1234"; must_fail(x) # 8
x=ledger([problem()]); x["problems"][0]["repo_subject"]["tree"]="def5678"; must_fail(x) # 9
x=ledger([problem("P-1"),problem("P-2")]); x["problems"].pop(); must_fail(x) # 10
x=ledger([problem()]); x["denominator"]["source_manifest_sha256"]="0"*64; must_fail(x) # 11
x=ledger([problem()]); x["problems"][0]["claim"]="Changed claim."; must_fail(x) # 12
x=ledger([problem("P-1"),problem("P-2")]); x["source_manifest"].pop(); must_fail(x) # 13
old=problem("P-OLD","Old route."); old["applicability"]="SUPERSEDED"; old["superseded_by"]="P-MISSING"; old["implementation_evidence"][0]["status"]="HISTORICAL"; old["implementation_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); old["verification_evidence"]=[]; old["receipts"]=[]; old["closure"]="PARTIAL"; must_fail(ledger([old])) #14
a=problem("P-A","A"); b=problem("P-B","B")
for item,succ in ((a,"P-B"),(b,"P-A")):
    item["applicability"]="SUPERSEDED"; item["superseded_by"]=succ; item["implementation_evidence"][0]["status"]="HISTORICAL"; item["implementation_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); item["verification_evidence"]=[]; item["receipts"]=[]; item["closure"]="PARTIAL"
must_fail(ledger([a,b])) # 15
x=ledger([problem()]); x["problems"][0]["session_attempts"][0]["worktree"]="/tmp/wt"; must_fail(x) # 16
x=ledger([problem()]); x["problems"][0]["verification_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); must_fail(x) # 17
x=ledger([problem()]); x["problems"][0]["implementation_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); must_fail(x) # 18
x=ledger([problem()]); x["problems"][0]["implementation_evidence"][0]["status"]="HISTORICAL"; x["problems"][0]["implementation_evidence"][0]["repo_subject"]=copy.deepcopy(OLD); must_fail(x) # 19
x=ledger([problem()]); x["problems"][0]["private_reasoning"]="forbidden"; must_fail(x) # 20
x=ledger([problem()]); x["problems"][0]["receipts"].append(copy.deepcopy(x["problems"][0]["receipts"][0])); must_fail(x) # 21
x=ledger([problem()]); x["problems"][0]["source"]["identity"]="https://example.invalid/file.pdf"; must_fail(x) # 22
x=ledger([problem()]); x["problems"][0]["shadow_review"]["repo_subject"]=copy.deepcopy(OLD); must_fail(x) # 23 wrong-subject shadow_review

print(f"problem-closure selftest: PASS (positive={_positive} mutations={_mutation} live=NOT_EXERCISED)")
