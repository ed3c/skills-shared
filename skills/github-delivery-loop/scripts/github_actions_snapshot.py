#!/usr/bin/env python3
"""Produce trusted GitHub Actions publication snapshots.

`replay` is zero-network. `capture` is the only network lane and calls fixed
`gh api` argv. No push, rerun, PR transition, billing mutation or merge.
Exit: 0 written, 2 unsafe/contradictory state, 64 malformed/API/I/O failure.
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile
from urllib.parse import quote
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OBSERVATION_SCHEMA="github-actions-publish-observation/v1"
SNAPSHOT_SCHEMA="github-actions-publish-snapshot/v3"
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
def observation(v:dict[str,Any])->dict[str,Any]:
    exact(v,{"schema","repository","branch","pull_requests","check_runs","captured_at"},"observation")
    if v["schema"]!=OBSERVATION_SCHEMA:raise SnapshotError(f"schema must be {OBSERVATION_SCHEMA}")
    pulls=v["pull_requests"];checks=v["check_runs"]
    if not isinstance(pulls,list) or not isinstance(checks,list):raise SnapshotError("pull_requests/check_runs must be arrays")
    return {"schema":OBSERVATION_SCHEMA,"repository":repository(v["repository"]),"branch":branch(v["branch"]),"pull_requests":[pr(x,i) for i,x in enumerate(pulls)],"check_runs":[check(x,i) for i,x in enumerate(checks)],"captured_at":timestamp(v["captured_at"],"captured_at")}
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
def build(raw:dict[str,Any],check_name:str)->dict[str,Any]:
    v=observation(raw)
    if not check_name or '\n' in check_name:raise SnapshotError("check name must be non-empty single line")
    pulls=v["pull_requests"]
    if len(pulls)>1:raise SnapshotError("branch has multiple open pull requests")
    if not pulls:
        if v["check_runs"]:raise SnapshotError("check runs ambiguous when PR absent")
        return {"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"branch":v["branch"],"pull_request":{"number":None,"state":"absent","head_sha":None,"last_published_sha":None,"last_published_at":None,"feedback":None},"actions":{"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None},"captured_at":v["captured_at"]}
    p=pulls[0]
    if v["branch"]["head_sha"] is not None and v["branch"]["head_sha"]!=p["head_sha"]:raise SnapshotError("branch head does not match PR head")
    c=select(v["check_runs"],check_name,p["head_sha"]);feedback=None
    if c is None:actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None}
    elif billing(c):actions={"circuit":"billing-open","observed_at":c["completed_at"],"blocker":"billing-or-spending-limit","latest_check":None}
    else:
        actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":{"head_sha":c["head_sha"],"conclusion":c["conclusion"],"completed_at":c["completed_at"]}}
        if c["conclusion"] in ACTIONABLE:feedback={"id":f"check-run:{c['id']}","kind":"ci","head_sha":c["head_sha"],"observed_at":c["completed_at"],"consumed_by_sha":None}
    return {"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"branch":v["branch"],"pull_request":{"number":p["number"],"state":"draft" if p["draft"] else "ready","head_sha":p["head_sha"],"last_published_sha":p["head_sha"],"last_published_at":p["updated_at"],"feedback":feedback},"actions":actions,"captured_at":v["captured_at"]}
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
def gh_api_optional(gh:str,endpoint:str,timeout:int)->Any|None:
    try:r=subprocess.run([gh,"api",endpoint],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    except FileNotFoundError as e:raise CaptureError(f"gh absent: {gh}") from e
    except subprocess.TimeoutExpired as e:raise CaptureError(f"gh api timed out: {endpoint}") from e
    if r.returncode:
        if "404" in r.stderr or "Not Found" in r.stderr:return None
        raise CaptureError(f"gh api failed for {endpoint}: {r.stderr.strip() or r.stdout.strip()}")
    try:return json.loads(r.stdout)
    except json.JSONDecodeError as e:raise CaptureError(f"gh api returned non-JSON: {endpoint}") from e
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
    else:
        ref=gh_api_optional(gh,f"repos/{repo}/git/ref/heads/{quote(branch_name,safe='')}",timeout)
        if ref is not None:
            if not isinstance(ref,dict) or not isinstance(ref.get("object"),dict):raise CaptureError("branch ref response malformed")
            head=sha(ref["object"].get("sha"),"remote branch head")
    return {"schema":OBSERVATION_SCHEMA,"repository":rv,"branch":{"name":branch_name,"head_sha":head},"pull_requests":pulls,"check_runs":checks,"captured_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}
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
    print("SELFTEST GREEN: trusted GitHub publication snapshots")
def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true");subs=p.add_subparsers(dest="cmd");r=subs.add_parser("replay");r.add_argument("--observation",type=Path,required=True);r.add_argument("--check-name",required=True);r.add_argument("--output",type=Path,required=True);c=subs.add_parser("capture");c.add_argument("--repository",required=True);c.add_argument("--branch",required=True);c.add_argument("--check-name",required=True);c.add_argument("--gh",default="gh");c.add_argument("--timeout-seconds",type=int,default=30);c.add_argument("--observation-output",type=Path);c.add_argument("--output",type=Path,required=True);a=p.parse_args(argv)
    if a.selftest:
        try:selftest();return 0
        except Exception as e:print(f"SELFTEST RED: {e}",file=sys.stderr);return 1
    try:
        if a.cmd=="replay":v=build(load(a.observation,"observation"),a.check_name);atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        if a.cmd=="capture":
            if a.timeout_seconds<1:raise CaptureError("timeout must be positive")
            o=capture(a.repository,a.branch,a.check_name,a.gh,a.timeout_seconds);v=build(o,a.check_name)
            if a.observation_output:atomic(a.observation_output.resolve(),o)
            atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        p.error("replay, capture, or --selftest required")
    except SnapshotError as e:print(f"BLOCK snapshot-state: {e}",file=sys.stderr);return 2
    except (CaptureError,OSError) as e:print(f"FATAL snapshot-capture: {e}",file=sys.stderr);return 64
if __name__=="__main__":raise SystemExit(main())
