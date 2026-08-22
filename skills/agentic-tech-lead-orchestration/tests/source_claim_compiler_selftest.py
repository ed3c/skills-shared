#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parent/"scripts"/"compile_source_claims.py"
spec=importlib.util.spec_from_file_location("compiler",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
H="a"*40; T="b"*40

def base():
    return {"schema_version":1,"repo_subject":{"repo":"ed3c/skills-shared","commit":H,"tree":T},"claims":[
        {"problem_id":"P1","kind":"GITHUB_ISSUE","identity":"ed3c/skills-shared#378","location":"issue body / Goal","claim":"Issue state must not be mistaken for real problem closure.","applicability":"APPLICABLE","task_nodes":["T1"],"dag_nodes":["D1"],"issue_nodes":[378]},
        {"problem_id":"P2","kind":"ARTICLE","identity":"sha256:"+"c"*64,"location":"section 2 paragraph 3","claim":"Article claim enters as source proposal only.","applicability":"APPLICABLE","task_nodes":["T2"],"dag_nodes":["D2"],"issue_nodes":[467]},
        {"problem_id":"P3","kind":"PDF","identity":"sha256:"+"d"*64,"location":"page 12 / claim 4","claim":"This PDF claim is outside the current repository contract.","applicability":"NOT_APPLICABLE","applicability_rationale":"consumer-only deployment concern","task_nodes":[],"dag_nodes":[],"issue_nodes":[]},
        {"problem_id":"P4","kind":"PRD","identity":"sha256:"+"e"*64,"location":"REQ-17","claim":"A compiled claim may point at current implementation but remains unverified.","applicability":"APPLICABLE","task_nodes":["T4"],"dag_nodes":["D4"],"issue_nodes":[467],"session_attempts":[{"task_id":"T4","attempt_id":"A1","worktree":"wt:467"}],"implementation_evidence":[{"kind":"PR","subject":"ed3c/skills-shared#455","repo_subject":{"repo":"ed3c/skills-shared","commit":H,"tree":T},"status":"CURRENT"}]}
    ]}

out=mod.compile_claims(base())
assert len(out["source_manifest"])==4
closures={p["problem_id"]:p["closure"] for p in out["problems"]}
assert closures=={"P1":"OPEN","P2":"OPEN","P3":"NOT_APPLICABLE","P4":"IMPLEMENTED_UNVERIFIED"}
assert len(out["denominator"]["source_manifest_sha256"])==64

def fail(fn):
    x=copy.deepcopy(base());fn(x)
    try:mod.compile_claims(x)
    except mod.ContractError:return
    raise AssertionError("mutation passed")

fail(lambda x:x["claims"].__setitem__(1,{**x["claims"][1],"problem_id":"P1"}))
fail(lambda x:x["claims"][1].update(identity="https://mutable.example/article"))
fail(lambda x:x["claims"][1].update(location=""))
fail(lambda x:x["repo_subject"].update(commit="abc"))
fail(lambda x:x["claims"][0].update(task_nodes=[]))
fail(lambda x:x["claims"][0].update(issue_nodes=[]))
fail(lambda x:x["claims"][3]["session_attempts"][0].update(worktree="/tmp/local"))
fail(lambda x:x["claims"][0].update(claim_sha256="0"*64))
fail(lambda x:x["claims"][0].update(hidden="nope"))
fail(lambda x:x["claims"][3].update(session_attempts=[]))
fail(lambda x:x["claims"][0].update(applicability="SUPERSEDED",superseded_by="P404"))

# shadow_verdict passthrough: a real verdict must ride WITH a same-subject
# independent shadow_review, and reaches the emitted problem unchanged.
sv=copy.deepcopy(base())
sv["claims"][3]["shadow_verdict"]="PASS"
sv["claims"][3]["shadow_review"]={"repo_subject":{"repo":"ed3c/skills-shared","commit":H,"tree":T},"reviewer_task_id":"shadow/T1","reviewer_attempt_id":"s01"}
outv=mod.compile_claims(sv)
assert {p["problem_id"]:p["shadow_verdict"] for p in outv["problems"]}["P4"]=="PASS"
fail(lambda x:x["claims"][3].update(shadow_verdict="PASS"))  # verdict without review
fail(lambda x:x["claims"][3].update(shadow_verdict="MAYBE"))  # verdict outside enum
print("source-claim-compiler selftest: PASS (positive=5-source denominator mutations=13 live=NOT_EXERCISED)")
