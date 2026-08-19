#!/usr/bin/env python3
import copy, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; SCRIPT=HERE.parent/"scripts"/"github_issue_dag_live_canary.py"
spec=importlib.util.spec_from_file_location("canary",SCRIPT); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
def plan(): return {"repo":"ed3c/skills-shared","repo_visibility":"PUBLIC","default_branch":"main","blocker_issue":9001,"blocked_issue":9002,"canary_label":"ctl-live-canary","expected_before_blocked_by":[8999]}
class Remote:
    def __init__(self): self.blocked=[8999]; self.cleanup_fail=False; self.missing_label=False; self.closed=False
    def run(self,a):
        if a[:3]==["gh","repo","view"]: return json.dumps({"nameWithOwner":"ed3c/skills-shared","visibility":"PUBLIC","defaultBranchRef":{"name":"main"}})
        if a[:3]==["gh","issue","view"]:
            n=int(a[3]); fields=a[-1]
            if fields=="number,state,labels": return json.dumps({"number":n,"state":"CLOSED" if self.closed and n==9002 else "OPEN","labels":[] if self.missing_label and n==9001 else [{"name":"ctl-live-canary"}]})
            if fields=="blockedBy": return json.dumps({"blockedBy":[{"number":x} for x in self.blocked]})
        if a[:3]==["gh","issue","edit"]:
            if "--add-blocked-by" in a:
                n=int(a[a.index("--add-blocked-by")+1]); self.blocked=sorted(set(self.blocked+[n])); return ""
            if "--remove-blocked-by" in a:
                if self.cleanup_fail: raise mod.ContractError("forced cleanup failure")
                n=int(a[a.index("--remove-blocked-by")+1]); self.blocked=[x for x in self.blocked if x!=n]; return ""
        raise AssertionError(a)
orig=mod._run; r=Remote(); mod._run=r.run
try:
    out=mod.execute(plan()); assert out["canary_state"]=="LIVE_GITHUB_DEPENDENCY_CANARY_PASS" and r.blocked==[8999]
finally: mod._run=orig
def fail(pm=lambda p:None,rm=lambda r:None):
    p=copy.deepcopy(plan()); pm(p); r=Remote(); rm(r); mod._run=r.run
    try: mod.execute(p)
    except mod.ContractError: return
    finally: mod._run=orig
    raise AssertionError("mutation passed")
fail(lambda p:p.update(blocker_issue=9002)); fail(lambda p:p.update(expected_before_blocked_by=[8999,9001])); fail(rm=lambda r:setattr(r,"blocked",[8998])); fail(rm=lambda r:setattr(r,"missing_label",True)); fail(rm=lambda r:setattr(r,"closed",True)); fail(rm=lambda r:setattr(r,"cleanup_fail",True))
print("github-dag-live-canary selftest: PASS (positive=1 mutations=6 live=NOT_EXERCISED)")
