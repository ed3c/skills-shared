#!/usr/bin/env python3
"""Produce trusted GitHub Actions publication snapshots.

`replay` is zero-network. `capture` is the only network lane and calls fixed
`gh api` argv. No push, rerun, PR transition, billing mutation or merge.
Exit: 0 written, 2 unsafe/contradictory state, 64 malformed/API/I/O failure.
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OBSERVATION_SCHEMA="github-actions-publish-observation/v1"
SNAPSHOT_SCHEMA="github-actions-publish-snapshot/v1"
SHA_RE=re.compile(r"^[0-9a-f]{40}$");REPO_RE=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
CONCLUSIONS={"success","failure","cancelled","timed_out","action_required","neutral","skipped"}
ACTIONABLE={"failure","timed_out","action_required"}
BILLING=("recent account payments have failed","spending limit needs to be increased","billing & plans")
class SnapshotError(ValueError):pass
class CaptureError(RuntimeError):pass

def exact(v:dict[str,Any],fields:set[str],label:str)->None:
    if set(v)!=fields:raise SnapshotError(f"{label} fields drifted: missing={sorted(fields-set(v))} extra={sorted(set(v)-fields)}")
def load(path:Path,label:str)->dict[str,Any]:
    try:v=json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:raise SnapshotError(f"missing {label}: {path}") from e
    except (OSError,UnicodeDecodeError,json.JSONDecodeError) as e:raise SnapshotError(f"unreadable {label}: {path}: {e}") from e
    if not isinstance(v,dict):raise SnapshotError(f"{label} root must be object")
    return v
def text(v:Any,label:str)->str:
    if not isinstance(v,str) or not v.strip():raise SnapshotError(f"{label} must be non-empty string")
    return v
def sha(v:Any,label:str)->str:
    s=text(v,label)
    if not SHA_RE.fullmatch(s):raise SnapshotError(f"{label} must be exact lowercase 40-character SHA")
    return s
def timestamp(v:Any,label:str)->str:
    s=text(v,label);s=s[:-1]+"+00:00" if s.endswith("Z") else s
    try:d=datetime.fromisoformat(s)
    except ValueError as e:raise SnapshotError(f"{label} must be ISO-8601 with timezone") from e
    if d.tzinfo is None:raise SnapshotError(f"{label} must include timezone")
    return d.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
def repository(v:Any)->dict[str,Any]:
    if not isinstance(v,dict):raise SnapshotError("repository must be object")
    exact(v,{"full_name","repository_id","owner_login","private"},"repository")
    name=text(v["full_name"],"repository.full_name")
    if not REPO_RE.fullmatch(name):raise SnapshotError("repository must be owner/name")
    rid=v["repository_id"]
    if not isinstance(rid,int) or isinstance(rid,bool) or rid<=0:raise SnapshotError("repository_id must be positive")
    owner=text(v["owner_login"],"owner_login")
    if name.split('/',1)[0].casefold()!=owner.casefold():raise SnapshotError("owner mismatch")
    if v["private"] is not True:raise SnapshotError("publication snapshots require private repository")
    return {"full_name":name,"repository_id":rid,"owner_login":owner,"private":True}
def branch(v:Any)->dict[str,Any]:
    if not isinstance(v,dict):raise SnapshotError("branch must be object")
    exact(v,{"name","head_sha"},"branch");name=text(v["name"],"branch.name")
    if name.startswith('-') or '\n' in name or '\x00' in name:raise SnapshotError("unsafe branch name")
    return {"name":name,"head_sha":None if v["head_sha"] is None else sha(v["head_sha"],"branch.head_sha")}
def pr(v:Any,i:int)->dict[str,Any]:
    if not isinstance(v,dict):raise SnapshotError(f"pull_requests[{i}] must be object")
    exact(v,{"number","draft","head_sha","updated_at"},f"pull_requests[{i}]");n=v["number"]
    if not isinstance(n,int) or isinstance(n,bool) or n<=0:raise SnapshotError("PR number must be positive")
    if not isinstance(v["draft"],bool):raise SnapshotError("PR draft must be boolean")
    return {"number":n,"draft":v["draft"],"head_sha":sha(v["head_sha"],"PR head"),"updated_at":timestamp(v["updated_at"],"PR updated_at")}
def annotation(v:Any,label:str)->dict[str,str]:
    if not isinstance(v,dict):raise SnapshotError(f"{label} must be object")
    exact(v,{"message"},label);return {"message":text(v["message"],f"{label}.message")}
def check(v:Any,i:int)->dict[str,Any]:
    label=f"check_runs[{i}]"
    if not isinstance(v,dict):raise SnapshotError(f"{label} must be object")
    exact(v,{"id","name","head_sha","status","conclusion","completed_at","annotations"},label);cid=v["id"]
    if not isinstance(cid,int) or isinstance(cid,bool) or cid<=0:raise SnapshotError("check id must be positive")
    status=text(v["status"],"check status")
    if status not in {"queued","in_progress","completed"}:raise SnapshotError("unsupported check status")
    conclusion=v["conclusion"];completed=v["completed_at"]
    if status=="completed":
        if conclusion not in CONCLUSIONS:raise SnapshotError("unsupported check conclusion")
        completed=timestamp(completed,"check completed_at")
    elif conclusion is not None or completed is not None:raise SnapshotError("incomplete check may not carry conclusion")
    anns=v["annotations"]
    if not isinstance(anns,list):raise SnapshotError("annotations must be array")
    return {"id":cid,"name":text(v["name"],"check name"),"head_sha":sha(v["head_sha"],"check head"),"status":status,"conclusion":conclusion,"completed_at":completed,"annotations":[annotation(a,f"annotation[{j}]") for j,a in enumerate(anns)]}
def branch_ref(v:Any)->dict[str,Any]:
    """An independently observed refs/heads/<exact> lookup.

    #70: an absent open PR does not prove the remote branch is absent. Without
    this, a repeated or orphaned remote branch is byte-identical to a truly
    unpublished one, and `initial-pr` cannot tell them apart.
    """
    if not isinstance(v,dict):raise SnapshotError("branch_ref must be object")
    exact(v,{"queried_ref","observed","object_sha"},"branch_ref")
    q=text(v["queried_ref"],"branch_ref.queried_ref")
    if not q.startswith("refs/heads/"):raise SnapshotError("branch_ref.queried_ref must be a refs/heads/ ref")
    if v["observed"] not in (True,False):raise SnapshotError("branch_ref.observed must be boolean")
    if v["observed"]:
        if v["object_sha"] is None:raise SnapshotError("an observed ref must carry an object sha")
        return {"queried_ref":q,"observed":True,"object_sha":sha(v["object_sha"],"branch_ref.object_sha")}
    if v["object_sha"] is not None:raise SnapshotError("an unobserved ref must not carry an object sha")
    return {"queried_ref":q,"observed":False,"object_sha":None}
def observation(v:dict[str,Any])->dict[str,Any]:
    fields={"schema","repository","branch","pull_requests","check_runs","captured_at"}
    if "branch_ref" in v:fields=fields|{"branch_ref"}
    exact(v,fields,"observation")
    if v["schema"]!=OBSERVATION_SCHEMA:raise SnapshotError(f"schema must be {OBSERVATION_SCHEMA}")
    pulls=v["pull_requests"];checks=v["check_runs"]
    if not isinstance(pulls,list) or not isinstance(checks,list):raise SnapshotError("pull_requests/check_runs must be arrays")
    out={"schema":OBSERVATION_SCHEMA,"repository":repository(v["repository"]),"branch":branch(v["branch"]),"pull_requests":[pr(x,i) for i,x in enumerate(pulls)],"check_runs":[check(x,i) for i,x in enumerate(checks)],"captured_at":timestamp(v["captured_at"],"captured_at")}
    if "branch_ref" in v:out["branch_ref"]=branch_ref(v["branch_ref"])
    return out
def billing(c:dict[str,Any])->bool:
    m=" ".join(a["message"].casefold() for a in c["annotations"])
    return (BILLING[0] in m and BILLING[1] in m) or (BILLING[0] in m and BILLING[2] in m)
def select(checks:list[dict[str,Any]],name:str,head:str)->dict[str,Any]|None:
    same=[c for c in checks if c["name"]==name];exact_head=[c for c in same if c["head_sha"]==head]
    if same and not exact_head:raise SnapshotError(f"stable check {name!r} exists only for a stale head")
    if not exact_head:return None
    done=[c for c in exact_head if c["status"]=="completed"]
    if not done:raise SnapshotError(f"stable check {name!r} is not completed")
    done.sort(key=lambda c:(timestamp(c["completed_at"],"check completed_at"),c["id"]),reverse=True);return done[0]
def build(raw:dict[str,Any],check_name:str,strict:bool=False)->dict[str,Any]:
    v=observation(raw)
    if strict and "branch_ref" not in v:raise SnapshotError("strict mode requires an independently observed branch_ref")
    if not check_name or '\n' in check_name:raise SnapshotError("check name must be non-empty single line")
    pulls=v["pull_requests"]
    if len(pulls)>1:raise SnapshotError("branch has multiple open pull requests")
    if not pulls:
        if v["check_runs"]:raise SnapshotError("check runs ambiguous when PR absent")
        boundary="unproven"
        if "branch_ref" in v:
            # Exactly two initial states. An absent PR alongside a present
            # remote branch is a repeated or orphaned publication, not an
            # initial one, and reporting it as absent is how a second
            # initial-pr gets admitted.
            if v["branch_ref"]["observed"]:
                if strict:raise SnapshotError("remote branch exists without an open pull request; this is not an initial publication")
                boundary="branch-present-without-pr"
            else:boundary="trusted-initial"
        elif strict:raise SnapshotError("strict mode requires an independently observed branch_ref")
        out={"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"pull_request":{"number":None,"state":"absent","head_sha":None,"last_published_sha":None,"last_published_at":None,"feedback":None},"actions":{"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None}}
        out["initial_boundary"]=boundary
        return out
    p=pulls[0]
    if v["branch"]["head_sha"] is not None and v["branch"]["head_sha"]!=p["head_sha"]:raise SnapshotError("branch head does not match PR head")
    if "branch_ref" in v:
        # One check, not two. An earlier version refused an unobserved ref
        # first and then compared object shas; removing the first changed
        # nothing, because an unobserved ref carries a null sha and the
        # comparison caught it anyway. A guard whose removal changes nothing is
        # not a guard.
        if v["branch_ref"]["object_sha"]!=p["head_sha"]:
            raise SnapshotError("an open pull request exists but its branch ref was not observed" if not v["branch_ref"]["observed"] else "observed branch ref disagrees with the pull request head")
    c=select(v["check_runs"],check_name,p["head_sha"]);feedback=None
    if c is None:actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None}
    elif billing(c):actions={"circuit":"billing-open","observed_at":c["completed_at"],"blocker":"billing-or-spending-limit","latest_check":None}
    else:
        actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":{"head_sha":c["head_sha"],"conclusion":c["conclusion"],"completed_at":c["completed_at"]}}
        if c["conclusion"] in ACTIONABLE:feedback={"id":f"check-run:{c['id']}","kind":"ci","head_sha":c["head_sha"],"observed_at":c["completed_at"],"consumed_by_sha":None}
    out={"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"pull_request":{"number":p["number"],"state":"draft" if p["draft"] else "ready","head_sha":p["head_sha"],"last_published_sha":p["head_sha"],"last_published_at":p["updated_at"],"feedback":feedback},"actions":actions}
    out["initial_boundary"]="not-initial"
    return out
def atomic(path:Path,v:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);payload=json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,prefix=f".{path.name}.",delete=False) as h:h.write(payload);tmp=Path(h.name)
    tmp.replace(path)
def gh_api(gh:str,endpoint:str,timeout:int)->Any:
    try:r=subprocess.run([gh,"api",endpoint],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    except FileNotFoundError as e:raise CaptureError(f"gh absent: {gh}") from e
    except subprocess.TimeoutExpired as e:raise CaptureError(f"gh api timed out: {endpoint}") from e
    if r.returncode:raise CaptureError(f"gh api failed for {endpoint}: {r.stderr.strip() or r.stdout.strip()}")
    try:return json.loads(r.stdout)
    except json.JSONDecodeError as e:raise CaptureError(f"gh api returned non-JSON: {endpoint}") from e
def observe_ref(gh:str,repo:str,branch_name:str,timeout:int)->dict[str,Any]:
    """Query refs/heads/<exact-branch> and refuse anything ambiguous.

    GitHub returns an object for an exact ref and an array for a prefix match,
    so an array here means the branch name matched several refs and no single
    one can be attributed. A 404 is the branch being absent, which is a result;
    any other failure is not, and must not be read as absence.
    """
    ref=f"refs/heads/{branch_name}"
    endpoint=f"repos/{repo}/git/ref/heads/{urllib.parse.quote(branch_name,safe='/')}"
    try:payload=gh_api(gh,endpoint,timeout)
    except CaptureError as e:
        if "404" in str(e) or "Not Found" in str(e):return {"queried_ref":ref,"observed":False,"object_sha":None}
        raise
    if isinstance(payload,list):
        raise CaptureError(f"branch name matched {len(payload)} refs; an ambiguous match cannot prove presence or absence")
    if not isinstance(payload,dict):raise CaptureError("ref response malformed")
    if payload.get("ref")!=ref:
        raise CaptureError(f"ref response is for {payload.get('ref')!r}, not {ref!r}")
    obj=payload.get("object") or {}
    if obj.get("type")!="commit":raise CaptureError(f"ref points at a {obj.get('type')!r}, not a commit")
    return {"queried_ref":ref,"observed":True,"object_sha":sha(obj.get("sha"),"ref object sha")}
def capture(repo:str,branch_name:str,check_name:str,gh:str,timeout:int)->dict[str,Any]:
    if not REPO_RE.fullmatch(repo):raise CaptureError("repository must be owner/name")
    if not branch_name or branch_name.startswith('-') or '\n' in branch_name:raise CaptureError("unsafe branch")
    r=gh_api(gh,f"repos/{repo}",timeout);owner=repo.split('/',1)[0]
    if not isinstance(r,dict):raise CaptureError("repository response malformed")
    rv={"full_name":r.get("full_name"),"repository_id":r.get("id"),"owner_login":(r.get("owner") or {}).get("login"),"private":r.get("private")};repository(rv)
    ps=gh_api(gh,f"repos/{repo}/pulls?state=open&head={owner}:{branch_name}&per_page=100",timeout)
    if not isinstance(ps,list) or any(not isinstance(x,dict) for x in ps):raise CaptureError("PR response malformed")
    pulls=[{"number":x.get("number"),"draft":x.get("draft"),"head_sha":(x.get("head") or {}).get("sha"),"updated_at":x.get("updated_at")} for x in ps]
    if len(pulls)>1:raise SnapshotError("branch has multiple open pull requests")
    checks=[];head=None
    if pulls:
        head=sha(pulls[0]["head_sha"],"live PR head");payload=gh_api(gh,f"repos/{repo}/commits/{head}/check-runs?per_page=100",timeout)
        if not isinstance(payload,dict) or not isinstance(payload.get("check_runs"),list):raise CaptureError("check-runs response malformed")
        for x in payload["check_runs"]:
            if not isinstance(x,dict) or x.get("name")!=check_name:continue
            anns=gh_api(gh,f"repos/{repo}/check-runs/{x.get('id')}/annotations?per_page=100",timeout)
            if not isinstance(anns,list):raise CaptureError("annotations response malformed")
            checks.append({"id":x.get("id"),"name":x.get("name"),"head_sha":x.get("head_sha"),"status":x.get("status"),"conclusion":x.get("conclusion"),"completed_at":x.get("completed_at"),"annotations":[{"message":a.get("message")} for a in anns if isinstance(a,dict)]})
    return {"schema":OBSERVATION_SCHEMA,"repository":rv,"branch":{"name":branch_name,"head_sha":head},"branch_ref":observe_ref(gh,repo,branch_name,timeout),"pull_requests":pulls,"check_runs":checks,"captured_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}
def fixture()->dict[str,Any]:
    h="1"*40
    return {"schema":OBSERVATION_SCHEMA,"repository":{"full_name":"ed3c/skills-shared","repository_id":1326262274,"owner_login":"ed3c","private":True},"branch":{"name":"feature","head_sha":h},"pull_requests":[{"number":42,"draft":False,"head_sha":h,"updated_at":"2026-08-12T05:00:00Z"}],"check_runs":[{"id":9001,"name":"contract","head_sha":h,"status":"completed","conclusion":"failure","completed_at":"2026-08-12T05:01:00Z","annotations":[{"message":"repository test failed"}]}],"captured_at":"2026-08-12T05:02:00Z"}
def selftest()->None:
    if build(fixture(),"contract")["pull_request"]["feedback"]["id"]!="check-run:9001":raise SnapshotError("actionable check lost")
    absent=fixture();absent["branch"]["head_sha"]=None;absent["pull_requests"]=[];absent["check_runs"]=[]
    if build(absent,"contract")["pull_request"]["state"]!="absent":raise SnapshotError("absent PR lost")
    b=fixture();b["check_runs"][0]["annotations"]=[{"message":"The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"}]
    if build(b,"contract")["actions"]["circuit"]!="billing-open":raise SnapshotError("billing collapsed")
    cases=[];m=fixture();m["pull_requests"].append(dict(m["pull_requests"][0],number=43));cases.append(m);p=fixture();p["repository"]["private"]=False;cases.append(p);s=fixture();s["check_runs"][0]["head_sha"]="2"*40;cases.append(s);a=fixture();a["check_runs"][0]["annotations"]=[{}];cases.append(a);i=fixture();i["check_runs"][0].update({"status":"in_progress","conclusion":None,"completed_at":None});cases.append(i)
    for x in cases:
        try:build(x,"contract")
        except SnapshotError:pass
        else:raise SnapshotError("negative observation passed")
    # #70: an absent PR does not prove an absent branch. Before this, the two
    # observations below produced byte-identical snapshots.
    def initial(observed:bool,object_sha:str|None)->dict[str,Any]:
        o=fixture();o["pull_requests"]=[];o["check_runs"]=[];o["branch"]["head_sha"]=None
        o["branch_ref"]={"queried_ref":"refs/heads/feature","observed":observed,"object_sha":object_sha}
        return o
    truly_new=build(initial(False,None),"contract",strict=True)
    if truly_new["initial_boundary"]!="trusted-initial":raise SnapshotError("an unpublished branch is not a trusted initial boundary")
    orphan=initial(True,"3"*40)
    try:build(orphan,"contract",strict=True)
    except SnapshotError:pass
    else:raise SnapshotError("a remote branch with no pull request passed as an initial publication")
    lenient=build(orphan,"contract")
    if lenient["initial_boundary"]!="branch-present-without-pr":raise SnapshotError("orphan branch was not distinguished in lenient mode")
    if truly_new["pull_request"]==lenient["pull_request"] and truly_new["initial_boundary"]==lenient["initial_boundary"]:
        raise SnapshotError("the two initial states are still indistinguishable")

    no_ref=fixture();no_ref["pull_requests"]=[];no_ref["check_runs"]=[];no_ref["branch"]["head_sha"]=None
    try:build(no_ref,"contract",strict=True)
    except SnapshotError:pass
    else:raise SnapshotError("strict mode accepted an observation with no branch_ref")

    agree=fixture();agree["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"1"*40}
    if build(agree,"contract",strict=True)["initial_boundary"]!="not-initial":raise SnapshotError("an open PR was misreported as initial")
    bad=[]
    d=fixture();d["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"9"*40};bad.append(d)
    u=fixture();u["branch_ref"]={"queried_ref":"refs/heads/feature","observed":False,"object_sha":None};bad.append(u)
    n=fixture();n["branch_ref"]={"queried_ref":"feature","observed":True,"object_sha":"1"*40};bad.append(n)
    m=fixture();m["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"zz"};bad.append(m)
    e=fixture();e["branch_ref"]={"queried_ref":"refs/heads/feature","observed":False,"object_sha":"1"*40};bad.append(e)
    o2=fixture();o2["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":None};bad.append(o2)
    for x in bad:
        try:build(x,"contract",strict=True)
        except SnapshotError:pass
        else:raise SnapshotError("a malformed or disagreeing branch_ref passed")
    print("SELFTEST GREEN: trusted GitHub publication snapshots; branch absence proved independently")
def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true");subs=p.add_subparsers(dest="cmd");r=subs.add_parser("replay");r.add_argument("--observation",type=Path,required=True);r.add_argument("--check-name",required=True);r.add_argument("--output",type=Path,required=True);r.add_argument("--strict",action="store_true");c=subs.add_parser("capture");c.add_argument("--repository",required=True);c.add_argument("--branch",required=True);c.add_argument("--check-name",required=True);c.add_argument("--gh",default="gh");c.add_argument("--timeout-seconds",type=int,default=30);c.add_argument("--observation-output",type=Path);c.add_argument("--output",type=Path,required=True);c.add_argument("--strict",action="store_true");a=p.parse_args(argv)
    if a.selftest:
        try:selftest();return 0
        except Exception as e:print(f"SELFTEST RED: {e}",file=sys.stderr);return 1
    try:
        if a.cmd=="replay":v=build(load(a.observation,"observation"),a.check_name,strict=a.strict);atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        if a.cmd=="capture":
            if a.timeout_seconds<1:raise CaptureError("timeout must be positive")
            o=capture(a.repository,a.branch,a.check_name,a.gh,a.timeout_seconds);v=build(o,a.check_name,strict=a.strict)
            if a.observation_output:atomic(a.observation_output.resolve(),o)
            atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        p.error("replay, capture, or --selftest required")
    except SnapshotError as e:print(f"BLOCK snapshot-state: {e}",file=sys.stderr);return 2
    except (CaptureError,OSError) as e:print(f"FATAL snapshot-capture: {e}",file=sys.stderr);return 64
if __name__=="__main__":raise SystemExit(main())
