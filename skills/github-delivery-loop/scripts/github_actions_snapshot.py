#!/usr/bin/env python3
"""Produce trusted GitHub Actions publication snapshots.

`replay` is zero-network. `capture` is the only network lane and calls fixed
`gh api` argv. No push, rerun, PR transition, billing mutation or merge.
Exit: 0 written, 2 unsafe/contradictory state, 64 malformed/API/I/O failure.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from urllib.parse import quote
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OBSERVATION_SCHEMA="github-actions-publish-observation/v2"
SNAPSHOT_SCHEMA="github-actions-publish-snapshot/v4"
TRANSPORT_SCHEMA="github-actions-publish-transport/v4"
SHA_RE=re.compile(r"^[0-9a-f]{40}$");REPO_RE=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")
GH_CANDIDATES=("/opt/homebrew/bin/gh","/usr/local/bin/gh","/usr/bin/gh","/home/linuxbrew/.linuxbrew/bin/gh")
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
def workflow_path(v:Any,label:str="workflow")->str:
    value=text(v,label)
    if not value.startswith(".github/workflows/") or ".." in value or "\n" in value:
        raise SnapshotError(f"{label} must be a safe .github/workflows/ path")
    return value
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
def branch_ref(v:Any,branch_name:str)->dict[str,Any]:
    if not isinstance(v,dict):raise SnapshotError("branch_ref must be object")
    exact(v,{"queried_ref","observed","object_sha"},"branch_ref")
    queried=text(v["queried_ref"],"branch_ref.queried_ref")
    if queried!=f"refs/heads/{branch_name}":raise SnapshotError("branch_ref does not name the observed branch")
    if v["observed"] not in (True,False):raise SnapshotError("branch_ref.observed must be boolean")
    if v["observed"]:
        if v["object_sha"] is None:raise SnapshotError("observed branch_ref must carry object_sha")
        return {"queried_ref":queried,"observed":True,"object_sha":sha(v["object_sha"],"branch_ref.object_sha")}
    if v["object_sha"] is not None:raise SnapshotError("absent branch_ref must not carry object_sha")
    return {"queried_ref":queried,"observed":False,"object_sha":None}
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
    exact(v,{"id","name","head_sha","status","conclusion","completed_at","annotations","app_id","app_slug","check_suite_id","workflow_run_id","workflow_id","job_id"},label);cid=v["id"]
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
    identities={name:v[name] for name in ("app_id","check_suite_id","workflow_run_id","workflow_id","job_id")}
    if any(not isinstance(value,int) or isinstance(value,bool) or value<=0 for value in identities.values()):raise SnapshotError("Actions app/suite/workflow/run/job identities must be positive integers")
    if v["app_slug"]!="github-actions":raise SnapshotError("required check must come from the GitHub Actions app")
    return {"id":cid,"name":text(v["name"],"check name"),"head_sha":sha(v["head_sha"],"check head"),"status":status,"conclusion":conclusion,"completed_at":completed,"annotations":[annotation(a,f"annotation[{j}]") for j,a in enumerate(anns)],"app_id":identities["app_id"],"app_slug":"github-actions","check_suite_id":identities["check_suite_id"],"workflow_run_id":identities["workflow_run_id"],"workflow_id":identities["workflow_id"],"job_id":identities["job_id"]}
def observation(v:dict[str,Any])->dict[str,Any]:
    fields={"schema","repository","branch","pull_requests","check_runs","captured_at"}
    if "branch_ref" in v:fields.add("branch_ref")
    exact(v,fields,"observation")
    if v["schema"]!=OBSERVATION_SCHEMA:raise SnapshotError(f"schema must be {OBSERVATION_SCHEMA}")
    pulls=v["pull_requests"];checks=v["check_runs"]
    if not isinstance(pulls,list) or not isinstance(checks,list):raise SnapshotError("pull_requests/check_runs must be arrays")
    observed_branch=branch(v["branch"])
    out={"schema":OBSERVATION_SCHEMA,"repository":repository(v["repository"]),"branch":observed_branch,"pull_requests":[pr(x,i) for i,x in enumerate(pulls)],"check_runs":[check(x,i) for i,x in enumerate(checks)],"captured_at":timestamp(v["captured_at"],"captured_at")}
    if "branch_ref" in v:out["branch_ref"]=branch_ref(v["branch_ref"],observed_branch["name"])
    return out
def billing(c:dict[str,Any])->bool:
    m=" ".join(a["message"].casefold() for a in c["annotations"])
    return (BILLING[0] in m and BILLING[1] in m) or (BILLING[0] in m and BILLING[2] in m)
def select(checks:list[dict[str,Any]],name:str,head:str)->dict[str,Any]|None:
    same=[c for c in checks if c["name"]==name];exact_head=[c for c in same if c["head_sha"]==head]
    if same and not exact_head:raise SnapshotError(f"stable check {name!r} exists only for a stale head")
    if not exact_head:return None
    if len(exact_head)!=1:raise SnapshotError(f"stable check {name!r} ran more than once for the exact head")
    done=[c for c in exact_head if c["status"]=="completed"]
    if not done:raise SnapshotError(f"stable check {name!r} is not completed")
    return done[0]
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
            ref=v["branch_ref"]
            if ref["observed"]:
                if ref["object_sha"]!=v["branch"]["head_sha"]:raise SnapshotError("observed branch ref disagrees with branch head")
                boundary="branch-present-without-pr"
            else:
                if v["branch"]["head_sha"] is not None:raise SnapshotError("absent branch ref disagrees with branch head")
                boundary="trusted-initial"
        elif strict:raise SnapshotError("strict mode requires an independently observed branch_ref")
        if strict and boundary=="branch-present-without-pr":raise SnapshotError("remote branch exists without an open pull request; this is not an initial publication")
        return {"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"branch":v["branch"],"initial_boundary":boundary,"pull_request":{"number":None,"state":"absent","head_sha":None,"last_published_sha":None,"last_published_at":None,"feedback":None},"actions":{"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None},"captured_at":v["captured_at"]}
    p=pulls[0]
    if v["branch"]["head_sha"] is not None and v["branch"]["head_sha"]!=p["head_sha"]:raise SnapshotError("branch head does not match PR head")
    if "branch_ref" in v and v["branch_ref"]["object_sha"]!=p["head_sha"]:
        raise SnapshotError("an open pull request exists but its branch ref was not observed" if not v["branch_ref"]["observed"] else "observed branch ref disagrees with the pull request head")
    c=select(v["check_runs"],check_name,p["head_sha"]);feedback=None
    if c is None:actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":None}
    elif billing(c):actions={"circuit":"billing-open","observed_at":c["completed_at"],"blocker":"billing-or-spending-limit","latest_check":None}
    else:
        actions={"circuit":"closed","observed_at":None,"blocker":None,"latest_check":{"head_sha":c["head_sha"],"conclusion":c["conclusion"],"completed_at":c["completed_at"],"check_run_id":c["id"],"check_suite_id":c["check_suite_id"],"workflow_run_id":c["workflow_run_id"],"workflow_id":c["workflow_id"],"job_id":c["job_id"],"app_id":c["app_id"]}}
        if c["conclusion"] in ACTIONABLE:feedback={"id":f"check-run:{c['id']}","kind":"ci","head_sha":c["head_sha"],"observed_at":c["completed_at"],"consumed_by_sha":None}
    return {"schema":SNAPSHOT_SCHEMA,"repository":v["repository"],"branch":v["branch"],"initial_boundary":"not-initial","pull_request":{"number":p["number"],"state":"draft" if p["draft"] else "ready","head_sha":p["head_sha"],"last_published_sha":p["head_sha"],"last_published_at":p["updated_at"],"feedback":feedback},"actions":actions,"captured_at":v["captured_at"]}
def atomic(path:Path,v:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);payload=json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,prefix=f".{path.name}.",delete=False) as h:h.write(payload);tmp=Path(h.name)
    tmp.replace(path)
def _json_stdout(entry:dict[str,Any],label:str)->Any:
    if entry["exit"]!=0:raise CaptureError(f"gh api failed for {label}: {entry['stderr'].strip() or entry['stdout'].strip()}")
    try:return json.loads(entry["stdout"])
    except json.JSONDecodeError as e:raise CaptureError(f"gh api returned non-JSON: {label}") from e

def _gh_identity(timeout:int)->dict[str,str]:
    invoked=next((value for value in GH_CANDIDATES if Path(value).is_file() and os.access(value,os.X_OK)),None)
    if invoked is None:raise CaptureError(f"gh absent from admitted absolute paths: {', '.join(GH_CANDIDATES)}")
    resolved=str(Path(invoked).resolve(strict=True));digest=hashlib.sha256(Path(resolved).read_bytes()).hexdigest()
    try:r=subprocess.run([resolved,"--version"],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=False)
    except subprocess.TimeoutExpired as e:raise CaptureError("admitted gh identity check timed out") from e
    version=r.stdout.splitlines()[0] if r.returncode==0 and r.stdout.splitlines() else ""
    if not version.startswith("gh version "):raise CaptureError("admitted gh executable did not report a canonical version")
    return {"invoked_path":invoked,"resolved_path":resolved,"sha256":digest,"version":version}

def _capture_entry(gh_path:str,endpoint:str,timeout:int,paginated:bool=False)->dict[str,Any]:
    argv=[gh_path,"api",*(["--paginate","--slurp"] if paginated else []),endpoint]
    try:r=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=False)
    except FileNotFoundError as e:raise CaptureError(f"admitted gh absent: {gh_path}") from e
    except subprocess.TimeoutExpired as e:raise CaptureError(f"gh api timed out: {endpoint}") from e
    return {"argv":argv,"exit":r.returncode,"stdout":r.stdout,"stdout_sha256":hashlib.sha256(r.stdout.encode()).hexdigest(),"stderr":r.stderr,"stderr_sha256":hashlib.sha256(r.stderr.encode()).hexdigest()}

def _validated_captures(raw:dict[str,Any])->list[dict[str,Any]]:
    exact(raw,{"schema","producer","gh_executable","repository","branch","check_name","workflow","captured_at","captures"},"transport")
    if raw["schema"]!=TRANSPORT_SCHEMA or raw["producer"]!="github_actions_snapshot.py":raise SnapshotError("unsupported Actions transport producer")
    identity=raw["gh_executable"]
    if not isinstance(identity,dict):raise SnapshotError("transport gh_executable must be object")
    exact(identity,{"invoked_path","resolved_path","sha256","version"},"transport gh_executable")
    invoked=text(identity["invoked_path"],"gh invoked_path");resolved=text(identity["resolved_path"],"gh resolved_path")
    if invoked not in GH_CANDIDATES or not resolved.startswith("/") or not SHA256_RE.fullmatch(text(identity["sha256"],"gh sha256")) or not text(identity["version"],"gh version").startswith("gh version "):raise SnapshotError("transport gh executable identity is not admitted")
    repo=text(raw["repository"],"transport.repository")
    if not REPO_RE.fullmatch(repo):raise SnapshotError("transport repository must be owner/name")
    text(raw["branch"],"transport.branch");text(raw["check_name"],"transport.check_name");workflow_path(raw["workflow"],"transport.workflow");timestamp(raw["captured_at"],"transport.captured_at")
    entries=raw["captures"]
    if not isinstance(entries,list) or not entries:raise SnapshotError("transport captures must be non-empty array")
    for i,entry in enumerate(entries):
        if not isinstance(entry,dict):raise SnapshotError(f"transport captures[{i}] must be object")
        exact(entry,{"argv","exit","stdout","stdout_sha256","stderr","stderr_sha256"},f"transport captures[{i}]")
        argv=entry["argv"]
        if not isinstance(argv,list) or len(argv) not in {3,5} or not all(isinstance(x,str) and x for x in argv) or argv[:2] != [resolved, "api"]:raise SnapshotError(f"transport captures[{i}] argv is not exact resolved admitted gh api argv")
        if not isinstance(entry["exit"],int) or isinstance(entry["exit"],bool):raise SnapshotError(f"transport captures[{i}] exit is invalid")
        for stream in ("stdout","stderr"):
            value=entry[stream];digest=entry[f"{stream}_sha256"]
            if not isinstance(value,str) or not isinstance(digest,str) or hashlib.sha256(value.encode()).hexdigest()!=digest:raise SnapshotError(f"transport captures[{i}] {stream} digest mismatch")
    return entries

def _check_identity(raw:dict[str,Any],repo:str)->tuple[int,int,int,int]:
    details=raw.get("details_url")
    if not isinstance(details,str):raise SnapshotError("check run lacks GitHub Actions job URL")
    match=re.fullmatch(rf"https://github\.com/{re.escape(repo)}/actions/runs/([1-9][0-9]*)/job/([1-9][0-9]*)",details)
    if match is None:raise SnapshotError("check run does not bind exact Actions run/job identities")
    app=raw.get("app");suite=raw.get("check_suite")
    if not isinstance(app,dict) or app.get("slug")!="github-actions" or not isinstance(app.get("id"),int) or isinstance(app.get("id"),bool) or app["id"]<=0:raise SnapshotError("check run is not owned by the GitHub Actions app")
    if not isinstance(suite,dict) or not isinstance(suite.get("id"),int) or isinstance(suite.get("id"),bool) or suite["id"]<=0:raise SnapshotError("check run lacks check-suite identity")
    return int(match.group(1)),int(match.group(2)),app["id"],suite["id"]

def _workflow_identity(raw:Any,expected_path:str)->int:
    if not isinstance(raw,dict):raise SnapshotError("workflow response malformed")
    workflow_id=raw.get("id")
    if not isinstance(workflow_id,int) or isinstance(workflow_id,bool) or workflow_id<=0:raise SnapshotError("workflow response lacks a positive id")
    if raw.get("path")!=expected_path:raise SnapshotError("workflow response path does not match policy")
    return workflow_id

def _for_workflow(checks:list[dict[str,Any]],workflow_id:int)->list[dict[str,Any]]:
    return [value for value in checks if value["workflow_id"]==workflow_id]

def observation_from_transport(raw:dict[str,Any])->dict[str,Any]:
    entries=_validated_captures(raw);repo=raw["repository"];branch_name=raw["branch"];check_name=raw["check_name"];workflow=raw["workflow"];owner=repo.split('/',1)[0]
    expected_repo=f"repos/{repo}"
    if entries[0]["argv"]!=[entries[0]["argv"][0],"api",expected_repo]:raise SnapshotError("transport repository argv mismatch")
    r=_json_stdout(entries[0],expected_repo)
    if not isinstance(r,dict):raise SnapshotError("repository response malformed")
    rv={"full_name":r.get("full_name"),"repository_id":r.get("id"),"owner_login":(r.get("owner") or {}).get("login"),"private":r.get("private")};repository(rv)
    workflow_endpoint=f"repos/{repo}/actions/workflows/{quote(workflow,safe='')}"
    if len(entries)<2 or entries[1]["argv"]!=[entries[1]["argv"][0],"api",workflow_endpoint]:raise SnapshotError("transport workflow argv mismatch")
    workflow_id=_workflow_identity(_json_stdout(entries[1],workflow_endpoint),workflow)
    pulls_endpoint=f"repos/{repo}/pulls?state=open&head={owner}:{branch_name}&per_page=100"
    if len(entries)<3 or entries[2]["argv"]!=[entries[2]["argv"][0],"api","--paginate","--slurp",pulls_endpoint]:raise SnapshotError("transport PR argv mismatch")
    pages=_json_stdout(entries[2],pulls_endpoint)
    if not isinstance(pages,list) or any(not isinstance(page,list) for page in pages):raise SnapshotError("PR pagination response malformed")
    ps=[item for page in pages for item in page]
    if any(not isinstance(x,dict) for x in ps):raise SnapshotError("PR response malformed")
    pulls=[{"number":x.get("number"),"draft":x.get("draft"),"head_sha":(x.get("head") or {}).get("sha"),"updated_at":x.get("updated_at")} for x in ps]
    if len(pulls)>1:raise SnapshotError("branch has multiple open pull requests")
    checks=[];head=None;branch_ref_value=None;index=3
    if pulls:
        head=sha(pulls[0]["head_sha"],"live PR head");checks_endpoint=f"repos/{repo}/commits/{head}/check-runs?per_page=100"
        if len(entries)<=index or entries[index]["argv"]!=[entries[index]["argv"][0],"api","--paginate","--slurp",checks_endpoint]:raise SnapshotError("transport check-runs argv mismatch")
        check_pages=_json_stdout(entries[index],checks_endpoint);index+=1
        if not isinstance(check_pages,list) or any(not isinstance(page,dict) or not isinstance(page.get("check_runs"),list) for page in check_pages):raise SnapshotError("check-runs pagination response malformed")
        selected=[x for page in check_pages for x in page["check_runs"] if isinstance(x,dict) and x.get("name")==check_name]
        for x in selected:
            run_id,job_id,app_id,suite_id=_check_identity(x,repo)
            run_endpoint=f"repos/{repo}/actions/runs/{run_id}"
            if len(entries)<=index or entries[index]["argv"]!=[entries[0]["argv"][0],"api",run_endpoint]:raise SnapshotError("transport workflow-run argv mismatch")
            run=_json_stdout(entries[index],run_endpoint);index+=1
            if not isinstance(run,dict) or run.get("id")!=run_id or run.get("head_sha")!=head or not isinstance(run.get("workflow_id"),int) or isinstance(run.get("workflow_id"),bool) or run["workflow_id"]<=0:raise SnapshotError("workflow run identity/head mismatch")
            endpoint=f"repos/{repo}/check-runs/{x.get('id')}/annotations?per_page=100"
            if len(entries)<=index or entries[index]["argv"]!=[entries[index]["argv"][0],"api","--paginate","--slurp",endpoint]:raise SnapshotError("transport annotations argv mismatch")
            annotation_pages=_json_stdout(entries[index],endpoint);index+=1
            if not isinstance(annotation_pages,list) or any(not isinstance(page,list) for page in annotation_pages):raise SnapshotError("annotations pagination response malformed")
            anns=[item for page in annotation_pages for item in page]
            checks.append({"id":x.get("id"),"name":x.get("name"),"head_sha":x.get("head_sha"),"status":x.get("status"),"conclusion":x.get("conclusion"),"completed_at":x.get("completed_at"),"annotations":[{"message":a.get("message")} for a in anns if isinstance(a,dict)],"app_id":app_id,"app_slug":"github-actions","check_suite_id":suite_id,"workflow_run_id":run_id,"workflow_id":run["workflow_id"],"job_id":job_id})
        checks=_for_workflow(checks,workflow_id)
    endpoint=f"repos/{repo}/git/ref/heads/{quote(branch_name,safe='')}"
    if len(entries)>index:
        if entries[index]["argv"]!=[entries[index]["argv"][0],"api",endpoint]:raise SnapshotError("transport branch-ref argv mismatch")
        entry=entries[index];index+=1
        if entry["exit"]==0:
            ref=_json_stdout(entry,endpoint)
            if not isinstance(ref,dict) or not isinstance(ref.get("object"),dict):raise SnapshotError("branch ref response malformed")
            ref_head=sha(ref["object"].get("sha"),"remote branch head")
            if not pulls:head=ref_head
            branch_ref_value={"queried_ref":f"refs/heads/{branch_name}","observed":True,"object_sha":ref_head}
        elif "404" in entry["stderr"] or "Not Found" in entry["stderr"]:
            branch_ref_value={"queried_ref":f"refs/heads/{branch_name}","observed":False,"object_sha":None}
        else:raise CaptureError(f"gh api failed for {endpoint}")
    elif not pulls:
        raise SnapshotError("transport branch-ref capture is missing")
    if index!=len(entries):raise SnapshotError("transport contains unconsumed provider calls")
    result={"schema":OBSERVATION_SCHEMA,"repository":rv,"branch":{"name":branch_name,"head_sha":head},"pull_requests":pulls,"check_runs":checks,"captured_at":timestamp(raw["captured_at"],"transport.captured_at")}
    if branch_ref_value is not None:result["branch_ref"]=branch_ref_value
    return result

def capture_transport(repo:str,branch_name:str,check_name:str,workflow:str,timeout:int)->dict[str,Any]:
    if not REPO_RE.fullmatch(repo):raise CaptureError("repository must be owner/name")
    if not branch_name or branch_name.startswith('-') or '\n' in branch_name:raise CaptureError("unsafe branch")
    workflow=workflow_path(workflow);gh_identity=_gh_identity(timeout);gh_path=gh_identity["resolved_path"];captures=[]
    def call(endpoint:str,paginated:bool=False)->Any:
        entry=_capture_entry(gh_path,endpoint,timeout,paginated);captures.append(entry);return _json_stdout(entry,endpoint)
    r=call(f"repos/{repo}");owner=repo.split('/',1)[0]
    if not isinstance(r,dict):raise CaptureError("repository response malformed")
    rv={"full_name":r.get("full_name"),"repository_id":r.get("id"),"owner_login":(r.get("owner") or {}).get("login"),"private":r.get("private")};repository(rv)
    workflow_endpoint=f"repos/{repo}/actions/workflows/{quote(workflow,safe='')}"
    _workflow_identity(call(workflow_endpoint),workflow)
    pull_pages=call(f"repos/{repo}/pulls?state=open&head={owner}:{branch_name}&per_page=100",True)
    if not isinstance(pull_pages,list) or any(not isinstance(page,list) for page in pull_pages):raise SnapshotError("branch PR pagination is malformed")
    ps=[item for page in pull_pages for item in page]
    if len(ps)>1 or any(not isinstance(item,dict) for item in ps):raise SnapshotError("branch has multiple or malformed open pull requests")
    if ps:
        head=sha((ps[0].get("head") or {}).get("sha"),"live PR head");check_pages=call(f"repos/{repo}/commits/{head}/check-runs?per_page=100",True)
        if not isinstance(check_pages,list) or any(not isinstance(page,dict) or not isinstance(page.get("check_runs"),list) for page in check_pages):raise CaptureError("check-runs pagination response malformed")
        for page in check_pages:
            for x in page["check_runs"]:
                if isinstance(x,dict) and x.get("name")==check_name:
                    run_id,_,_,_=_check_identity(x,repo)
                    call(f"repos/{repo}/actions/runs/{run_id}")
                    call(f"repos/{repo}/check-runs/{x.get('id')}/annotations?per_page=100",True)
    captures.append(_capture_entry(gh_path,f"repos/{repo}/git/ref/heads/{quote(branch_name,safe='')}",timeout))
    return {"schema":TRANSPORT_SCHEMA,"producer":"github_actions_snapshot.py","gh_executable":gh_identity,"repository":repo,"branch":branch_name,"check_name":check_name,"workflow":workflow,"captured_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"captures":captures}

def capture(repo:str,branch_name:str,check_name:str,workflow:str,timeout:int)->dict[str,Any]:
    return observation_from_transport(capture_transport(repo,branch_name,check_name,workflow,timeout))
def fixture()->dict[str,Any]:
    h="1"*40
    return {"schema":OBSERVATION_SCHEMA,"repository":{"full_name":"ed3c/skills-shared","repository_id":1326262274,"owner_login":"ed3c","private":True},"branch":{"name":"feature","head_sha":h},"pull_requests":[{"number":42,"draft":False,"head_sha":h,"updated_at":"2026-08-12T05:00:00Z"}],"check_runs":[{"id":9001,"name":"contract","head_sha":h,"status":"completed","conclusion":"failure","completed_at":"2026-08-12T05:01:00Z","annotations":[{"message":"repository test failed"}],"app_id":15368,"app_slug":"github-actions","check_suite_id":8001,"workflow_run_id":7001,"workflow_id":6001,"job_id":5001}],"captured_at":"2026-08-12T05:02:00Z"}
def selftest()->None:
    if build(fixture(),"contract")["pull_request"]["feedback"]["id"]!="check-run:9001":raise SnapshotError("actionable check lost")
    agree=fixture();agree["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"1"*40}
    if build(agree,"contract",strict=True)["initial_boundary"]!="not-initial":raise SnapshotError("an agreeing PR branch ref was not admitted")
    disagree=fixture();disagree["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"9"*40}
    try:build(disagree,"contract",strict=True)
    except SnapshotError:pass
    else:raise SnapshotError("a PR whose independently observed ref disagrees with its head was admitted")
    missing=fixture()
    try:build(missing,"contract",strict=True)
    except SnapshotError:pass
    else:raise SnapshotError("strict mode admitted a PR without an independently observed branch ref")
    absent=fixture();absent["branch"]["head_sha"]=None;absent["pull_requests"]=[];absent["check_runs"]=[]
    if build(absent,"contract")["initial_boundary"]!="unproven":raise SnapshotError("unproved initial boundary was guessed")
    absent["branch_ref"]={"queried_ref":"refs/heads/feature","observed":False,"object_sha":None}
    if build(absent,"contract",strict=True)["initial_boundary"]!="trusted-initial":raise SnapshotError("independently absent branch was not admitted as initial")
    orphan=fixture();orphan["pull_requests"]=[];orphan["check_runs"]=[];orphan["branch_ref"]={"queried_ref":"refs/heads/feature","observed":True,"object_sha":"1"*40}
    if build(orphan,"contract")["initial_boundary"]!="branch-present-without-pr":raise SnapshotError("orphan branch was collapsed into initial publication")
    try:build(orphan,"contract",strict=True)
    except SnapshotError:pass
    else:raise SnapshotError("strict mode admitted an orphan branch")
    b=fixture();b["check_runs"][0]["annotations"]=[{"message":"The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"}]
    if build(b,"contract")["actions"]["circuit"]!="billing-open":raise SnapshotError("billing collapsed")
    mixed=fixture();mixed["check_runs"].append(dict(mixed["check_runs"][0],id=9002,workflow_id=6002,job_id=5002))
    mixed["check_runs"]=_for_workflow(mixed["check_runs"],6001)
    if build(mixed,"contract")["pull_request"]["feedback"]["id"]!="check-run:9001":raise SnapshotError("workflow-bound check selection lost the required check")
    try:_workflow_identity({"id":6001,"path":".github/workflows/other.yml"},".github/workflows/verify.yml")
    except SnapshotError:pass
    else:raise SnapshotError("a workflow response for another path was admitted")
    cases=[];m=fixture();m["pull_requests"].append(dict(m["pull_requests"][0],number=43));cases.append(m);p=fixture();p["repository"]["private"]=False;cases.append(p);s=fixture();s["check_runs"][0]["head_sha"]="2"*40;cases.append(s);a=fixture();a["check_runs"][0]["annotations"]=[{}];cases.append(a);i=fixture();i["check_runs"][0].update({"status":"in_progress","conclusion":None,"completed_at":None});cases.append(i);d=fixture();d["check_runs"].append(dict(d["check_runs"][0],id=9002,job_id=5002));cases.append(d);foreign=fixture();foreign["check_runs"][0]["app_slug"]="other";cases.append(foreign)
    for x in cases:
        try:build(x,"contract")
        except SnapshotError:pass
        else:raise SnapshotError("negative observation passed")
    print("SELFTEST GREEN: trusted GitHub publication snapshots; branch absence proved independently")
def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true");subs=p.add_subparsers(dest="cmd");r=subs.add_parser("replay");r.add_argument("--observation",type=Path,required=True);r.add_argument("--check-name",required=True);r.add_argument("--output",type=Path,required=True);r.add_argument("--strict",action="store_true");t=subs.add_parser("replay-transport");t.add_argument("--transport",type=Path,required=True);t.add_argument("--observation-output",type=Path,required=True);t.add_argument("--output",type=Path,required=True);t.add_argument("--strict",action="store_true");c=subs.add_parser("capture");c.add_argument("--repository",required=True);c.add_argument("--branch",required=True);c.add_argument("--check-name",required=True);c.add_argument("--workflow",required=True);c.add_argument("--timeout-seconds",type=int,default=30);c.add_argument("--transport-output",type=Path,required=True);c.add_argument("--observation-output",type=Path);c.add_argument("--output",type=Path,required=True);c.add_argument("--strict",action="store_true");a=p.parse_args(argv)
    if a.selftest:
        try:selftest();return 0
        except Exception as e:print(f"SELFTEST RED: {e}",file=sys.stderr);return 1
    try:
        if a.cmd=="replay":v=build(load(a.observation,"observation"),a.check_name,strict=a.strict);atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        if a.cmd=="replay-transport":
            raw=load(a.transport,"transport");o=observation_from_transport(raw);v=build(o,raw["check_name"],strict=a.strict);atomic(a.observation_output.resolve(),o);atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        if a.cmd=="capture":
            if a.timeout_seconds<1:raise CaptureError("timeout must be positive")
            raw=capture_transport(a.repository,a.branch,a.check_name,a.workflow,a.timeout_seconds);o=observation_from_transport(raw);v=build(o,a.check_name,strict=a.strict)
            atomic(a.transport_output.resolve(),raw)
            if a.observation_output:atomic(a.observation_output.resolve(),o)
            atomic(a.output.resolve(),v);print(f"WROTE {a.output.resolve()}");return 0
        p.error("replay, capture, or --selftest required")
    except SnapshotError as e:print(f"BLOCK snapshot-state: {e}",file=sys.stderr);return 2
    except (CaptureError,OSError) as e:print(f"FATAL snapshot-capture: {e}",file=sys.stderr);return 64
if __name__=="__main__":raise SystemExit(main())
