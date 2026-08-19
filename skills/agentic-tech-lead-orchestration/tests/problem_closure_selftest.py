#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent; SCRIPT=HERE.parent/"scripts"/"check_problem_closure.py"
spec=importlib.util.spec_from_file_location("p",SCRIPT); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def problem():
  return {
   "problem_id":"P-001","source":{"kind":"PDF","identity":"sha256:abc","location":"page:22"},
   "claim":"The repo must preserve independent evidence lanes.","applicability":"APPLICABLE",
   "repo_subject":{"repo":"ed3c/skills-shared","commit":"abc1234","tree":"def5678"},
   "task_nodes":["T1"],"issue_nodes":[378],
   "implementation_evidence":[{"kind":"COMMIT","subject":"abc1234"}],
   "verification_evidence":[{"lane":"LOCAL","subject":"selftest:pass"}],
   "shadow_verdict":"PASS","residual_gaps":[],"closure":"VERIFIED_LOCAL"
  }
d={"problems":[problem()]}; out=m.check_ledger(d); assert out["problem_count"]==1
live=problem(); live["verification_evidence"].append({"lane":"PROVIDER_LIVE","subject":"receipt:r1"}); live["closure"]="VERIFIED_LIVE"
assert m.recompute(live)=="VERIFIED_LIVE"
partial=problem(); partial["residual_gaps"]=["provider live not exercised"]; partial["closure"]="PARTIAL"; m.check_ledger({"problems":[partial]})
human=problem(); human["requires_human"]=True; human["closure"]="HUMAN_ADMIT_REQUIRED"; m.check_ledger({"problems":[human]})

def fail(x):
  try:m.check_ledger({"problems":[x]})
  except m.ContractError:return
  raise AssertionError("mutation passed")

x=problem(); x["source"]["location"]=""; fail(x)
x=problem(); x["verification_evidence"]=[{"lane":"MERGE","subject":"pr#1"}]; fail(x)
x=problem(); x["closure"]="VERIFIED_LIVE"; fail(x)
x=problem(); x["residual_gaps"]=["still open"]; x["closure"]="VERIFIED_LOCAL"; fail(x)
x=problem(); x["applicability"]="NOT_APPLICABLE"; x["closure"]="NOT_APPLICABLE"; fail(x)
try:m.check_ledger({"problems":[problem(),problem()]})
except m.ContractError:pass
else:raise AssertionError("duplicate id passed")
print("problem-closure selftest: PASS (positive=4 mutations=6 live=NOT_EXERCISED)")
