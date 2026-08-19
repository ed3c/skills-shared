#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent; SCRIPT=HERE.parent/"scripts"/"herdr_runtime_observer.py"
spec=importlib.util.spec_from_file_location("h",SCRIPT); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def manifest():
  return {"task_id":"issue-377/T1","attempt_id":"a01","repo":"ed3c/skills-shared",
          "base_sha":"85e6723869","tree_sha":"85e6723869","worktree":"/tmp/wt","target":"worker-377",
          "expected_pane_id":"w1:p3","expected_workspace_id":"w1"}
x=manifest(); m.validate_manifest(x)
f=m.fallback_receipt(x); assert f["authoritative"] is False and f["controller_readback_required"]
agent={"result":{"agent":{"state":"done","pane_id":"w1:p3","workspace_id":"w1","pid":123}}}
explain={"result":{"final_state":"done"}}
r=m.reduce_observation(x,agent,explain)
assert r["observer_state"]=="DONE_CANDIDATE" and r["authoritative"] is False
assert "transcript" not in r

def fail(mut):
  y=copy.deepcopy(manifest()); mut(y)
  try:m.validate_manifest(y)
  except m.ContractError:return
  raise AssertionError("mutation passed")
fail(lambda y:y.update(authoritative=True))
fail(lambda y:y.update(access_token="nope"))
fail(lambda y:y.update(transcript="terminal bytes"))
fail(lambda y:y.pop("attempt_id"))
bad=manifest(); bad["expected_pane_id"]="w9:p9"
try:m.reduce_observation(bad,agent,explain)
except m.ContractError:pass
else:raise AssertionError("identity mismatch passed")
print("herdr-observer selftest: PASS (positive=3 mutations=5 live=NOT_EXERCISED)")
