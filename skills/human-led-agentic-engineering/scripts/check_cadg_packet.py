#!/usr/bin/env python3
"""Zero-network CADG v1 semantic checker.

A green result proves only packet/receipt contract consistency for supplied
bytes. It never proves live Agent/Shadow execution, Human admission, merge,
release, or production behavior.
"""
from __future__ import annotations

import argparse, copy, hashlib, json, re, sys
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,127}$")
MUTABLE = {"main", "master", "latest", "HEAD", "origin/main", "origin/master"}
FORBIDDEN = {"api_key", "access_token", "bearer_token", "client_secret", "password", "private_key",
             "chain_of_thought", "hidden_reasoning", "private_reasoning", "reasoning_trace", "scratchpad",
             "original_reasoning"}
LANE_STATE = {"STATIC":"STATIC_VERIFIED", "DETERMINISTIC":"DETERMINISTIC_VERIFIED",
              "LOCAL_RUNTIME":"LOCAL_VERIFIED", "PRIVATE":"PRIVATE_VERIFIED",
              "LIVE_PHYSICAL":"LIVE_VERIFIED", "HUMAN_ADMIT":"HUMAN_ADMITTED",
              "DELIVERY":"DELIVERED", "RELEASE":"RELEASED", "PRODUCTION":"PRODUCTION_VERIFIED"}
EDGE = {"CONTEXT_SUPPORTS_ASSUMPTION":("context","assumption"),
        "ASSUMPTION_SUPPORTS_DECISION":("assumption","decision"),
        "ASSUMPTION_CHALLENGES_DECISION":("assumption","decision"),
        "DECISION_CAUSES_DELTA":("decision","delta"), "DELTA_IMPLEMENTED_BY_PR":("delta","pr"),
        "PR_VERIFIED_BY_EVIDENCE":("pr","evidence"),
        "EVIDENCE_DISPOSITIONS_ASSUMPTION":("evidence","assumption")}


def digest(v: Any) -> str:
    b = json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(b).hexdigest()


def obj(v: Any) -> dict[str, Any]: return v if isinstance(v, dict) else {}
def arr(v: Any) -> list[Any]: return v if isinstance(v, list) else []

def index(v: Any, label: str, red: list[tuple[str,str]]) -> dict[str,dict[str,Any]]:
    out = {}
    for n, raw in enumerate(arr(v)):
        x = obj(raw); key = x.get("id")
        if not isinstance(key, str) or not ID.fullmatch(key): red.append(("CADG017", f"{label}[{n}] missing stable id")); continue
        if key in out: red.append(("CADG017", f"duplicate node {key}"))
        out[key] = x
    return out


def exact_subject(s: Any, fields: tuple[str,...], label: str, red: list[tuple[str,str]]) -> bool:
    x = obj(s); ok = isinstance(x.get("repository"), str) and len(x["repository"].strip()) >= 3
    for f in fields:
        v = x.get(f)
        if not isinstance(v, str) or v in MUTABLE or not HEX40.fullmatch(v): ok = False
    if not ok: red.append(("CADG001", f"{label} is not an immutable exact subject"))
    return ok


def same_receipt_subject(a: Any, b: Any) -> bool:
    a,b=obj(a),obj(b)
    return all(a.get(k)==b.get(k) for k in ("repository","base_commit","base_tree","head_commit","head_tree"))


def scan_private(v: Any, red: list[tuple[str,str]], path: str="$") -> None:
    if isinstance(v, dict):
        for k,x in v.items():
            if str(k).casefold() in FORBIDDEN: red.append(("CADG012", f"forbidden field {path}.{k}"))
            scan_private(x, red, f"{path}.{k}")
    elif isinstance(v, list):
        for i,x in enumerate(v): scan_private(x, red, f"{path}[{i}]")
    elif isinstance(v, str):
        low=v.casefold()
        if re.search(r"(?:^|[\s`'\"])(?:/Users/|/home/|[A-Za-z]:\\Users\\)", v): red.append(("CADG012", f"machine path at {path}"))
        if "this is the original private reasoning" in low or "original chain of thought" in low:
            red.append(("CADG011", f"historical packet overclaims original reasoning at {path}"))


def material(delta: dict[str,Any]) -> bool:
    return (any(obj(x).get("change") in {"ADDED","CHANGED","REMOVED"} for k in ("state_changes","ports") for x in arr(delta.get(k)))
            or any(obj(x).get("change") in {"ADDED","WIDENED"} for x in arr(delta.get("effects")))
            or any(obj(x).get("change")=="WIDENED" for x in arr(delta.get("authorities"))))


def validate_packet(p: Any) -> list[tuple[str,str]]:
    r: list[tuple[str,str]]=[]
    if not isinstance(p, dict): return [("CADG001","packet root must be object")]
    scan_private(p,r)
    if p.get("schema")!="cadg-packet/v1": r.append(("CADG001","wrong packet schema"))
    s=obj(p.get("subject")); exact_subject(s,("base_commit","base_tree","analyzed_commit","analyzed_tree"),"packet subject",r)
    if "head_commit" in s or "head_tree" in s: r.append(("CADG019","persisted packet embeds self-referential final head/tree"))
    bind=obj(s.get("binding")); mode=p.get("mode"); stage=p.get("stage"); c=obj(p.get("context"))
    if not DIGEST.fullmatch(str(bind.get("code_manifest_digest",""))): r.append(("CADG001","missing code-manifest digest"))
    if mode=="FORWARD_PROVENANCE":
        if stage not in {"PLAN","PR_TEMPLATE"} or c.get("kind")!="OBSERVED_CONTEXT": r.append(("CADG002","forward mode/context mismatch"))
        if bind.get("kind")!="CODE_MANIFEST" or ".agents/cadg/**" not in arr(bind.get("excluded_paths")):
            r.append(("CADG019","forward packet lacks CADG-excluding code manifest"))
    elif mode=="RECONSTRUCTED_HISTORY":
        if stage!="HISTORY_RECONSTRUCTED" or c.get("kind")!="RECONSTRUCTED_CONTEXT" or not isinstance(p.get("historical_target"),dict):
            r.append(("CADG002","history mode/context mismatch"))
        if bind.get("kind")!="EXACT_GIT_SUBJECT" or arr(bind.get("excluded_paths")):
            r.append(("CADG019","history packet is not one exact Git subject"))
    else: r.append(("CADG002","unknown mode"))
    if c.get("bound_commit")!=s.get("analyzed_commit") or c.get("bound_tree")!=s.get("analyzed_tree") or not DIGEST.fullmatch(str(c.get("manifest_digest",""))):
        r.append(("CADG013","context stale for analyzed subject"))
    sources=index(c.get("sources"),"context.sources",r)
    if not sources or (mode=="FORWARD_PROVENANCE" and not any(x.get("provenance")=="OBSERVED" for x in sources.values())):
        r.append(("CADG005","decision lacks observed context"))

    dlt=obj(p.get("delta")); mat=obj(p.get("materiality"))
    if material(dlt) and mat.get("class")!="MATERIAL" or mat.get("class")=="MATERIAL" and not arr(mat.get("trigger_reasons")):
        r.append(("CADG018","material change bypassed material lane"))
    assumptions=index(p.get("assumptions"),"assumptions",r); unknowns=index(p.get("unknowns"),"unknowns",r)
    inv=index(p.get("invariants"),"invariants",r); ev=index(p.get("evidence"),"evidence",r); req=index(p.get("evidence_requirements"),"requirements",r)
    for aid,a in assumptions.items():
        if not str(a.get("falsifier","")).strip(): r.append(("CADG004",f"{aid} lacks falsifier"))
        if not set(arr(a.get("basis_context_ids"))) or not set(arr(a.get("basis_context_ids"))).issubset(sources): r.append(("CADG017",f"{aid} has unknown basis"))
        if a.get("blocking") is True and a.get("state") not in {"CONFIRMED","HUMAN_ADMITTED"}: r.append(("CADG003",f"blocking {aid} unresolved"))
        if a.get("state")=="HUMAN_ADMITTED" and not str(a.get("human_admission_ref","")).strip(): r.append(("CADG003",f"{aid} lacks Human admission"))
        if not set(arr(a.get("evidence_ids"))).issubset(ev): r.append(("CADG017",f"{aid} references unknown evidence"))
    for uid,u in unknowns.items():
        if u.get("blocking") is True: r.append(("CADG003",f"blocking unknown {uid}"))

    dec=obj(p.get("decision")); did=dec.get("id")
    if c.get("id") not in arr(dec.get("context_ids")): r.append(("CADG005","decision omits packet context"))
    chosen=set(arr(dec.get("assumption_ids"))); blocking={k for k,v in assumptions.items() if v.get("blocking") is True}
    if not blocking.issubset(chosen) or any(assumptions.get(k,{}).get("state")=="FALSIFIED" for k in chosen): r.append(("CADG006","decision assumption disposition invalid"))
    if not chosen.issubset(assumptions) or not set(arr(dec.get("invariant_ids"))).issubset(inv): r.append(("CADG017","decision references unknown node"))
    alts=index(dec.get("alternatives"),"alternatives",r); sel=dec.get("selected_alternative_id")
    if sel not in alts or [k for k,v in alts.items() if v.get("disposition")=="SELECTED"]!=[sel]: r.append(("CADG006","decision must select exactly one alternative"))
    if dec.get("design_material") is True and not str(dec.get("human_admission_ref","")).strip(): r.append(("CADG009","material design lacks Human admission"))
    if dlt.get("decision_id")!=did or not did: r.append(("CADG007","delta not caused by decision"))
    for x in arr(dlt.get("state_changes")):
        writers=arr(obj(x).get("canonical_writers"))
        if len(writers)>1 or len(writers)!=len(set(map(str,writers))): r.append(("CADG008",f"state {obj(x).get('state_id')} has multiple writers"))
    for kind,key in (("effects","effect"),("authorities","authority")):
        for x in arr(dlt.get(kind)):
            x=obj(x)
            if x.get("change")=="WIDENED" and not str(x.get("human_admission_ref","")).strip(): r.append(("CADG009",f"{key} widened without admission"))

    analyzed={"repository":s.get("repository"),"base_commit":s.get("base_commit"),"base_tree":s.get("base_tree"),
              "head_commit":s.get("analyzed_commit"),"head_tree":s.get("analyzed_tree")}
    passed=set(); rel: dict[str,set[str]]={}
    nodes=set(sources)|set(assumptions)|set(unknowns)|set(inv)|set(ev)|{x for x in (c.get("id"),did,dlt.get("id")) if isinstance(x,str)}
    pr=obj(p.get("pr"));
    if isinstance(pr.get("id"),str): nodes.add(pr["id"])
    for eid,e in ev.items():
        q=req.get(str(e.get("requirement_id")),{})
        if not q: r.append(("CADG017",f"{eid} unknown requirement"))
        if q and e.get("lane")!=q.get("lane"): r.append(("CADG010",f"{eid} lane mismatch"))
        expected=LANE_STATE.get(str(e.get("lane")))
        if e.get("asserted_state")!=expected: r.append(("CADG016" if e.get("asserted_state") in {"HUMAN_ADMITTED","DELIVERED","RELEASED","PRODUCTION_VERIFIED"} else "CADG010",f"{eid} promoted evidence"))
        if not same_receipt_subject(e.get("subject"),analyzed): r.append(("CADG014",f"{eid} wrong analyzed subject"))
        if e.get("target_id") not in nodes: r.append(("CADG017",f"{eid} unknown target"))
        if e.get("result")=="PASS":
            passed.add(e.get("requirement_id")); rel.setdefault(str(e.get("target_id")),set()).add(str(e.get("relation")))
    if stage!="PLAN":
        for qid,q in req.items():
            if q.get("required") is True and qid not in passed: r.append(("CADG010",f"required lane {qid} unclosed"))
    for aid,a in assumptions.items():
        x=rel.get(aid,set()); st=a.get("state")
        if st=="CONFIRMED" and "CONFIRMS" not in x: r.append(("CADG003",f"{aid} lacks confirming evidence"))
        if st=="FALSIFIED" and "FALSIFIES" not in x or st=="STALE" and "EXPIRES" not in x or {"CONFIRMS","FALSIFIES"}.issubset(x): r.append(("CADG006",f"{aid} evidence disposition invalid"))

    if stage=="PR_TEMPLATE":
        if not pr or pr.get("repository")!=s.get("repository") or pr.get("base_commit")!=s.get("base_commit"): r.append(("CADG014","PR template mismatch"))
    rb=obj(p.get("rollback"))
    if not HEX40.fullmatch(str(rb.get("commit",""))) or not HEX40.fullmatch(str(rb.get("tree",""))) or not str(rb.get("procedure","")).strip() or not str(rb.get("cleanup","")).strip(): r.append(("CADG015","rollback missing/mutable"))
    if mode=="FORWARD_PROVENANCE" and rb.get("commit")==s.get("analyzed_commit"): r.append(("CADG015","rollback equals candidate"))

    typ={**{k:"assumption" for k in assumptions}, **{k:"evidence" for k in ev}}
    for k,t in ((c.get("id"),"context"),(did,"decision"),(dlt.get("id"),"delta"),(pr.get("id"),"pr")):
        if isinstance(k,str): typ[k]=t
    edges=set()
    for n,x in enumerate(arr(p.get("causal_edges"))):
        x=obj(x); a,b,k=x.get("from"),x.get("to"),x.get("kind")
        if a not in typ or b not in typ or k not in EDGE or (typ[a],typ[b])!=EDGE.get(k): r.append(("CADG017",f"bad causal edge {n}"))
        else: edges.add((a,b,k))
    for aid in assumptions:
        if (c.get("id"),aid,"CONTEXT_SUPPORTS_ASSUMPTION") not in edges: r.append(("CADG017",f"context does not support {aid}"))
    if (did,dlt.get("id"),"DECISION_CAUSES_DELTA") not in edges: r.append(("CADG017","decision-delta edge absent"))
    if stage=="PR_TEMPLATE" and (dlt.get("id"),pr.get("id"),"DELTA_IMPLEMENTED_BY_PR") not in edges: r.append(("CADG017","delta-PR edge absent"))
    return r


def validate_receipt(x: Any, p: dict[str,Any]) -> list[tuple[str,str]]:
    r=[]
    if not isinstance(x,dict): return [("CADG001","receipt root must be object")]
    scan_private(x,r)
    if x.get("schema")!="cadg-admission-receipt/v1": r.append(("CADG001","wrong receipt schema"))
    if x.get("packet_id")!=p.get("packet_id") or x.get("packet_digest")!=digest(p): r.append(("CADG014","receipt packet mismatch"))
    rs=obj(x.get("subject")); exact_subject(rs,("base_commit","base_tree","head_commit","head_tree"),"receipt subject",r)
    ps=obj(p.get("subject")); bind=obj(ps.get("binding"))
    if rs.get("repository")!=ps.get("repository") or rs.get("base_commit")!=ps.get("base_commit") or rs.get("base_tree")!=ps.get("base_tree"): r.append(("CADG014","receipt repo/base mismatch"))
    if x.get("code_manifest_digest")!=bind.get("code_manifest_digest"): r.append(("CADG013","receipt code manifest stale"))
    if obj(x.get("validator")).get("exit_code")!=0 and x.get("cadg")=="PASS" or x.get("cadg")=="PASS" and arr(x.get("refusal_ids")): r.append(("CADG016","invalid result promoted to CADG PASS"))
    if x.get("evidence_ceiling")!=p.get("evidence_ceiling"): r.append(("CADG010","receipt ceiling mismatch"))
    if x.get("shadow")!="NOT_EXERCISED":
        sh=obj(x.get("shadow_evidence"))
        if not same_receipt_subject(sh.get("subject"),rs): r.append(("CADG014","Shadow wrong PR subject"))
        if sh.get("builder_identity")==sh.get("reviewer_identity"): r.append(("CADG016","Builder self-review promoted to Shadow"))
        if not DIGEST.fullmatch(str(sh.get("receipt_digest",""))): r.append(("CADG010","Shadow receipt absent"))
    if x.get("human")=="HUMAN_ADMITTED" and not str(x.get("human_admission_ref","")).strip(): r.append(("CADG009","Human admission ref absent"))
    return r


def load(p: Path) -> Any: return json.loads(p.read_text(encoding="utf-8"))

def selftest(root: Path) -> list[str]:
    e=root/"examples"/"cadg"; f=load(e/"positive-forward-material-change.json"); h=load(e/"positive-reconstructed-history.json"); q=load(e/"positive-admission-receipt.json")
    failures=[]
    for name,p in (("forward",f),("history",h)):
        if z:=validate_packet(p): failures.append(f"positive {name}: {[c for c,_ in z]}")
    if z:=validate_receipt(q,f): failures.append(f"positive receipt: {[c for c,_ in z]}")
    muts=[]
    def m(code,label,fn,base=f):
        p=copy.deepcopy(base); fn(p); muts.append((code,label,p))
    m("CADG001","mutable",lambda p:p["subject"].__setitem__("base_commit","main")); m("CADG002","mode",lambda p:p["context"].__setitem__("kind","RECONSTRUCTED_CONTEXT")); m("CADG003","blocking",lambda p:p["assumptions"][0].__setitem__("state","UNVERIFIED")); m("CADG004","falsifier",lambda p:p["assumptions"][0].__setitem__("falsifier","")); m("CADG005","context",lambda p:p["decision"].__setitem__("context_ids",[])); m("CADG006","assumption",lambda p:p["decision"].__setitem__("assumption_ids",[])); m("CADG007","delta",lambda p:p["delta"].__setitem__("decision_id","DEC_UNKNOWN")); m("CADG008","writers",lambda p:p["delta"]["state_changes"][0].__setitem__("canonical_writers",["A","B"])); m("CADG009","authority",lambda p:p["delta"]["authorities"][0].update({"change":"WIDENED","human_admission_ref":""})); m("CADG010","lane",lambda p:p["evidence"][0].__setitem__("lane","STATIC")); m("CADG011","original",lambda p:p["context"]["sources"][2].__setitem__("notes","This is the original private reasoning."),h); m("CADG012","private",lambda p:p.__setitem__("chain_of_thought","secret")); m("CADG013","stale",lambda p:p["context"].__setitem__("bound_commit","e"*40)); m("CADG014","pr",lambda p:p["pr"].__setitem__("base_commit","e"*40)); m("CADG015","rollback",lambda p:p["rollback"].__setitem__("commit",p["subject"]["analyzed_commit"])); m("CADG016","release",lambda p:p["evidence"][0].__setitem__("asserted_state","RELEASED")); m("CADG017","edge",lambda p:p["causal_edges"][0].__setitem__("from","CTX_UNKNOWN")); m("CADG018","bypass",lambda p:p["materiality"].__setitem__("class","ROUTINE")); m("CADG019","selfref",lambda p:p["subject"].__setitem__("head_commit","e"*40))
    for code,label,p in muts:
        got={c for c,_ in validate_packet(p)}
        if code not in got: failures.append(f"mutation {label}: expected {code}, got {sorted(got)}")
    bad=copy.deepcopy(q); bad["shadow_evidence"]["reviewer_identity"]=bad["shadow_evidence"]["builder_identity"]
    if "CADG016" not in {c for c,_ in validate_receipt(bad,f)}: failures.append("receipt self-review mutation")
    return failures


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--packet",type=Path); ap.add_argument("--receipt",type=Path); ap.add_argument("--selftest",action="store_true"); ap.add_argument("--owner-root",type=Path,default=Path(__file__).resolve().parents[1]); a=ap.parse_args()
    if not a.selftest and a.packet is None: ap.error("--packet required unless --selftest")
    try:
        if a.selftest:
            bad=selftest(a.owner_root.resolve())
            for x in bad: print("CADG-SELFTEST-RED",x)
            if bad: return 2
            print("CADG-SELFTEST-GREEN positives=3 mutations=20"); return 0
        p=load(a.packet); red=validate_packet(p)
        if a.receipt: red += validate_receipt(load(a.receipt),p)
        for code,msg in red: print("CADG-RED",code,msg)
        if red: return 2
        print("CADG-GREEN deterministic-contract-only live=NOT_EXERCISED merge=HUMAN_ADMIT_REQUIRED"); return 0
    except (OSError,UnicodeError,json.JSONDecodeError) as e: print("CADG-INVALID",e,file=sys.stderr); return 64
    except Exception as e: print("CADG-CHECKER-ERROR",e,file=sys.stderr); return 70

if __name__=="__main__": raise SystemExit(main())
