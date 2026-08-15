#!/usr/bin/env python3
"""Produce exact-HEAD local verification evidence for GitHub publication admission.

Zero-network. Commands are repository-owned argv arrays, never shell strings.
Exit: 0 PASS, 2 executed-but-red, 64 malformed/dirty/unavailable.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, threading, time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

CONTRACT_SCHEMA="github-delivery-local-verification-contract/v1"
RECEIPT_SCHEMA="github-delivery-local-verification/v1"
EVIDENCE_SCHEMA="github-delivery-local-verification-evidence/v1"
SHA_RE=re.compile(r"^[0-9a-f]{40}$"); DIGEST_RE=re.compile(r"^[0-9a-f]{64}$")
ID_RE=re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MACHINE=(re.compile(r"^/Users/"),re.compile(r"^/home/"),re.compile(r"^[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]"),re.compile(r"^~/"))
SAFE_ENV={"HOME","LANG","LC_ALL","LC_CTYPE","PATH","PYTHONPATH","TEMP","TMP","TMPDIR","TZ"}
FIXED_ENV={"GCM_INTERACTIVE":"Never","GIT_EDITOR":":","GIT_PAGER":"cat","GIT_SEQUENCE_EDITOR":":","GIT_TERMINAL_PROMPT":"0","PAGER":"cat"}

class VerificationError(ValueError): pass

def canonical(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def sha(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def now()->str:return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def exact(v:dict[str,Any], fields:set[str], label:str)->None:
    if set(v)!=fields: raise VerificationError(f"{label} fields drifted: missing={sorted(fields-set(v))} extra={sorted(set(v)-fields)}")
def load(path:Path,label:str)->dict[str,Any]:
    try:v=json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:raise VerificationError(f"missing {label}: {path}") from e
    except (OSError,UnicodeDecodeError,json.JSONDecodeError) as e:raise VerificationError(f"unreadable {label}: {path}: {e}") from e
    if not isinstance(v,dict):raise VerificationError(f"{label} root must be an object")
    return v
def positive_int(v:Any,label:str,minimum:int=1)->int:
    if not isinstance(v,int) or isinstance(v,bool) or v<minimum:raise VerificationError(f"{label} must be integer >= {minimum}")
    return v
def unsafe(s:str)->bool:return any(p.search(s) for p in MACHINE)
def norm_cwd(v:Any,label:str)->str:
    if not isinstance(v,str) or not v:raise VerificationError(f"{label} must be non-empty")
    p=PurePosixPath(v)
    if unsafe(v) or p.is_absolute() or ".." in p.parts:raise VerificationError(f"{label} must be safe repository-relative path")
    return "." if p.as_posix() in {"","."} else p.as_posix()
def argv(v:Any,label:str)->list[str]:
    if not isinstance(v,list) or not v or any(not isinstance(x,str) or not x for x in v):raise VerificationError(f"{label} must be non-empty argv array")
    out=list(v)
    for i,x in enumerate(out):
        if any(c in x for c in ("\x00","\n","\r")) or unsafe(x) or x.startswith(("/","~/")):raise VerificationError(f"{label}[{i}] contains unsafe host/control data")
    if out[0] in {"sh","bash","zsh","fish"} and len(out)>1 and out[1] in {"-c","-lc"}:raise VerificationError(f"{label} may not execute shell strings")
    return out
def validate_contract(v:dict[str,Any], repo_id:int)->dict[str,Any]:
    exact(v,{"schema","repository_id","inherit_env","commands"},"contract")
    if v["schema"]!=CONTRACT_SCHEMA:raise VerificationError(f"contract.schema must be {CONTRACT_SCHEMA}")
    if positive_int(v["repository_id"],"contract.repository_id")!=repo_id:raise VerificationError("repository identity mismatch")
    inherit=v["inherit_env"]
    if not isinstance(inherit,list) or any(not isinstance(x,str) or not x for x in inherit) or len(inherit)!=len(set(inherit)):raise VerificationError("inherit_env must be unique string list")
    bad=sorted(set(inherit)-SAFE_ENV)
    if bad:raise VerificationError(f"unadmitted inherited env names: {bad}")
    raw=v["commands"]
    if not isinstance(raw,list) or not raw:raise VerificationError("commands must be non-empty")
    seen=set(); commands=[]
    for i,item in enumerate(raw):
        label=f"commands[{i}]"
        if not isinstance(item,dict):raise VerificationError(f"{label} must be object")
        exact(item,{"id","argv","cwd","timeout_seconds","max_output_bytes"},label)
        cid=item["id"]
        if not isinstance(cid,str) or not ID_RE.fullmatch(cid) or cid in seen:raise VerificationError(f"invalid/duplicate command id: {cid!r}")
        seen.add(cid); commands.append({"id":cid,"argv":argv(item["argv"],f"{label}.argv"),"cwd":norm_cwd(item["cwd"],f"{label}.cwd"),"timeout_seconds":positive_int(item["timeout_seconds"],f"{label}.timeout_seconds"),"max_output_bytes":positive_int(item["max_output_bytes"],f"{label}.max_output_bytes",256)})
    return {"schema":CONTRACT_SCHEMA,"repository_id":repo_id,"inherit_env":sorted(inherit),"commands":commands}
def git(root:Path,*args:str)->str:
    r=subprocess.run(["git","-C",str(root),*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**FIXED_ENV,"PATH":os.environ.get("PATH","")})
    if r.returncode:raise VerificationError(f"git {' '.join(args)} failed: {(r.stderr.strip() or r.stdout.strip())}")
    return r.stdout.strip()
def subject(root:Path)->tuple[str,str]:
    head=git(root,"rev-parse","HEAD"); tree=git(root,"rev-parse","HEAD^{tree}")
    if not SHA_RE.fullmatch(head) or not SHA_RE.fullmatch(tree):raise VerificationError("Git returned non-exact object ID")
    dirty=git(root,"status","--porcelain=v1","--untracked-files=all")
    if dirty:raise VerificationError(f"working tree is dirty: {dirty.splitlines()[0]}")
    return head,tree
def environment(names:list[str])->dict[str,str]:
    out=dict(FIXED_ENV)
    for n in names:
        if n in os.environ:out[n]=os.environ[n]
    out.setdefault("PATH",os.defpath); return out

class Capture:
    def __init__(self,stream:BinaryIO,limit:int):self.stream=stream;self.limit=limit;self.total=0;self.digest=hashlib.sha256();self.error=None
    def run(self)->None:
        try:
            while True:
                chunk=self.stream.read(65536)
                if not chunk:return
                self.total+=len(chunk);self.digest.update(chunk)
        except BaseException as e:self.error=e

def run_command(root:Path,c:dict[str,Any],env:dict[str,str])->dict[str,Any]:
    cwd=(root/c["cwd"]).resolve()
    try:cwd.relative_to(root)
    except ValueError as e:raise VerificationError(f"cwd escapes repository: {c['cwd']}") from e
    if not cwd.is_dir():raise VerificationError(f"cwd absent: {c['cwd']}")
    start=time.monotonic(); started=now()
    try:p=subprocess.Popen(c["argv"],cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False,start_new_session=True)
    except OSError as e:return {"id":c["id"],"argv":c["argv"],"cwd":c["cwd"],"timeout_seconds":c["timeout_seconds"],"max_output_bytes":c["max_output_bytes"],"started_at":started,"duration_ms":int((time.monotonic()-start)*1000),"exit":None,"timed_out":False,"spawn_error":str(e),"stdout_bytes":0,"stderr_bytes":0,"stdout_sha256":sha(b""),"stderr_sha256":sha(b""),"stdout_truncated":False,"stderr_truncated":False}
    assert p.stdout and p.stderr
    a=Capture(p.stdout,c["max_output_bytes"]);b=Capture(p.stderr,c["max_output_bytes"]);ta=threading.Thread(target=a.run,daemon=True);tb=threading.Thread(target=b.run,daemon=True);ta.start();tb.start();timed=False
    try:code=p.wait(timeout=c["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed=True
        try:os.killpg(p.pid,15)
        except (ProcessLookupError,PermissionError):p.terminate()
        try:code=p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,9)
            except (ProcessLookupError,PermissionError):p.kill()
            code=p.wait()
    ta.join(2);tb.join(2)
    p.stdout.close();p.stderr.close()
    if ta.is_alive() or tb.is_alive() or a.error or b.error:raise VerificationError(f"stream capture failed: {c['id']}")
    return {"id":c["id"],"argv":c["argv"],"cwd":c["cwd"],"timeout_seconds":c["timeout_seconds"],"max_output_bytes":c["max_output_bytes"],"started_at":started,"duration_ms":int((time.monotonic()-start)*1000),"exit":code,"timed_out":timed,"spawn_error":None,"stdout_bytes":a.total,"stderr_bytes":b.total,"stdout_sha256":a.digest.hexdigest(),"stderr_sha256":b.digest.hexdigest(),"stdout_truncated":a.total>c["max_output_bytes"],"stderr_truncated":b.total>c["max_output_bytes"]}
def atomic(path:Path,v:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);payload=json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,prefix=f".{path.name}.",delete=False) as h:h.write(payload);tmp=Path(h.name)
    tmp.replace(path)
def build(root:Path,contract:dict[str,Any],repo_id:int)->tuple[dict[str,Any],dict[str,Any],int]:
    # Normalize here, not at each call site: run_command compares an already
    # resolved cwd against this root, so an unresolved root makes every
    # containment check fail on any path reached through a symlink (/tmp on
    # macOS) or given relatively. Callers must not have to remember.
    root=root.resolve()
    cfg=validate_contract(contract,repo_id);head,tree=subject(root);stamp=now();results=[run_command(root,c,environment(cfg["inherit_env"])) for c in cfg["commands"]]
    status="PASS" if all(r["exit"]==0 and not r["timed_out"] and r["spawn_error"] is None and not r["stdout_truncated"] and not r["stderr_truncated"] for r in results) else "FAIL"
    evidence={"schema":EVIDENCE_SCHEMA,"repository_id":repo_id,"head_sha":head,"tree_sha":tree,"contract_sha256":sha(canonical(cfg)),"verified_at":stamp,"clean_subject":True,"commands":results,"status":status};evidence["content_sha256"]=sha(canonical(evidence));digest=sha(canonical(evidence))
    receipt={"schema":RECEIPT_SCHEMA,"repository_id":repo_id,"head_sha":head,"status":status,"verified_at":stamp,"evidence_sha256":digest,"commands":[c["id"] for c in cfg["commands"]]}
    return receipt,evidence,0 if status=="PASS" else 2
def verify(root:Path,contract:Path,repo_id:int,receipt:Path,evidence:Path)->int:
    r,e,code=build(root,load(contract,"verification contract"),repo_id);atomic(evidence.resolve(),e);atomic(receipt.resolve(),r);print(f"{r['status']} local-verification head={r['head_sha']} evidence={r['evidence_sha256'][:12]}");return code

def fixture(argv:list[str])->dict[str,Any]:return {"schema":CONTRACT_SCHEMA,"repository_id":1326262274,"inherit_env":["PATH"],"commands":[{"id":"fixture","argv":argv,"cwd":".","timeout_seconds":2,"max_output_bytes":4096}]}
def selftest()->None:
    with tempfile.TemporaryDirectory(prefix="local-verify.") as t:
        root=Path(t)/"repo";root.mkdir();subprocess.run(["git","init","-q",str(root)],check=True);subprocess.run(["git","-C",str(root),"config","user.name","fixture"],check=True);subprocess.run(["git","-C",str(root),"config","user.email","fixture@example.invalid"],check=True);(root/"x.txt").write_text("x\n");subprocess.run(["git","-C",str(root),"add","x.txt"],check=True);subprocess.run(["git","-C",str(root),"commit","-qm","x"],check=True)
        if build(root,fixture(["python3","-c","print('ok')"]),1326262274)[2]!=0:raise VerificationError("positive failed")
        if build(root,fixture(["python3","-c","raise SystemExit(7)"]),1326262274)[2]!=2:raise VerificationError("nonzero passed")
        c=fixture(["python3","-c","import time;time.sleep(2)"]);c["commands"][0]["timeout_seconds"]=1
        if build(root,c,1326262274)[2]!=2:raise VerificationError("timeout passed")
        if build(root,fixture(["python3","-c","print('x'*5000)"]),1326262274)[2]!=2:raise VerificationError("overflow passed")
        (root/"dirty").write_text("x")
        try:build(root,fixture(["python3","-c","pass"]),1326262274)
        except VerificationError:pass
        else:raise VerificationError("dirty passed")
        (root/"dirty").unlink()
        for bad in ({**fixture(["python3","-c","pass"]),"inherit_env":["GITHUB_TOKEN"]},fixture(["/usr/bin/python3","-c","pass"]),{**fixture(["python3","-c","pass"]),"commands":[]}):
            try:validate_contract(bad,1326262274)
            except VerificationError:pass
            else:raise VerificationError("unsafe contract passed")
        try:validate_contract(fixture(["python3","-c","pass"]),999)
        except VerificationError:pass
        else:raise VerificationError("identity mismatch passed")
        # A root reached relatively must verify identically. Guards the shape of
        # the containment check itself, not just this fixture's absolute path.
        cwd0=Path.cwd()
        try:
            os.chdir(root.parent)
            if build(Path("repo"),fixture(["python3","-c","print('ok')"]),1326262274)[2]!=0:raise VerificationError("relative root failed")
        finally:os.chdir(cwd0)
        # ...and normalizing the root must not stop a real escape being refused.
        # Two independent guards, so two controls: norm_cwd rejects an escaping
        # string, and run_command rejects a path that only escapes once
        # resolved. A literal ".." exercises the first and would pass with the
        # second deleted, so the symlink case is what pins containment.
        lit=fixture(["python3","-c","pass"]);lit["commands"][0]["cwd"]=".."
        try:build(root,lit,1326262274)
        except VerificationError:pass
        else:raise VerificationError("literal cwd escape passed")
        # Committed, or the escape would be refused as a dirty subject and this
        # control would pass without ever reaching the containment check.
        (root/"out").symlink_to(root.parent);subprocess.run(["git","-C",str(root),"add","out"],check=True);subprocess.run(["git","-C",str(root),"commit","-qm","out"],check=True)
        esc=fixture(["python3","-c","pass"]);esc["commands"][0]["cwd"]="out"
        try:build(root,esc,1326262274)
        except VerificationError:pass
        else:raise VerificationError("symlink cwd escape passed")
    print("SELFTEST GREEN: exact-HEAD local verification")
def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true");s=p.add_subparsers(dest="cmd");v=s.add_parser("verify");v.add_argument("--repo-root",type=Path,required=True);v.add_argument("--contract",type=Path,required=True);v.add_argument("--repository-id",type=int,required=True);v.add_argument("--receipt",type=Path,required=True);v.add_argument("--evidence",type=Path,required=True);a=p.parse_args(argv)
    if a.selftest:
        try:selftest();return 0
        except Exception as e:print(f"SELFTEST RED: {e}",file=sys.stderr);return 1
    if a.cmd!="verify":p.error("verify or --selftest required")
    try:return verify(a.repo_root,a.contract,a.repository_id,a.receipt,a.evidence)
    except VerificationError as e:print(f"FATAL local-verification: {e}",file=sys.stderr);return 64
    except OSError as e:print(f"FATAL local-verification I/O: {e}",file=sys.stderr);return 64
if __name__=="__main__":raise SystemExit(main())
