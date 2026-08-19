#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent; SCRIPT=HERE.parent/"scripts"/"herdr_runtime_observer.py"
spec=importlib.util.spec_from_file_location("h",SCRIPT); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def manifest():
  return {"task_id":"issue-377/T1","attempt_id":"a01","repo":"ed3c/skills-shared",
          "base_sha":"85e6723869","tree_sha":"85e6723869","worktree":"/tmp/wt","target":"worker-377",
          "expected_pane_id":"w1:p3","expected_workspace_id":"w1","expected_agent_session_id":"codex-thread-1"}
x=manifest(); m.validate_manifest(x)
f=m.fallback_receipt(x); assert f["authoritative"] is False and f["controller_readback_required"]
agent={"result":{"agent":{"state":"done","pane_id":"w1:p3","workspace_id":"w1","pid":123,
                           "foreground_cwd":"/tmp/wt","agent_session":{"source":"herdr:codex","kind":"id","value":"codex-thread-1"}}}}
explain={"result":{"final_state":"done"}}
r=m.reduce_observation(x,agent,explain)
assert r["observer_state"]=="DONE_CANDIDATE" and r["authoritative"] is False
assert r["foreground_cwd"]=="/tmp/wt" and r["agent_session_id"]=="codex-thread-1"
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
fail(lambda y:y.update(require_foreground_cwd="yes"))

def observation_must_fail(mut_agent=None, mut_manifest=None):
  a=copy.deepcopy(agent); d=manifest()
  if mut_agent: mut_agent(a)
  if mut_manifest: mut_manifest(d)
  try:m.reduce_observation(d,a,explain)
  except m.ContractError:return
  raise AssertionError("observation identity mutation passed")
observation_must_fail(mut_manifest=lambda d:d.update(expected_pane_id="w9:p9"))
observation_must_fail(mut_agent=lambda a:a["result"]["agent"].update(foreground_cwd="/tmp/other"))
observation_must_fail(mut_agent=lambda a:a["result"]["agent"].pop("foreground_cwd"))
observation_must_fail(mut_manifest=lambda d:d.update(expected_agent_session_id="wrong-thread"))
print("herdr-observer selftest: PASS (positive=4 mutations=9 live=NOT_EXERCISED)")
