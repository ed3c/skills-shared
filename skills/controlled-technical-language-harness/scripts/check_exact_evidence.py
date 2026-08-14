#!/usr/bin/env python3
"""CLI and mutation controls for exact CTL evidence binding."""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from exact_evidence_core import (
    CAL_SCHEMA, DET_SCHEMA, PRED_SCHEMA, InputError, digest, evaluate_deterministic, load
)
from exact_evidence_calibration import evaluate_calibration

def selftest() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scripts/controlled_language").mkdir(parents=True)
        # Minimal foundation validators used only to prove composition; the production
        # path imports the admitted repository validators.
        (root / "scripts/controlled_language/__init__.py").write_text("")
        (root / "scripts/controlled_language/contracts.py").write_text(
            "def validate_standard_pack(x): return []\ndef validate_termbase_entry(x): return []\n")
        pack = {"pack_id":"fixture","edition":"0.1","ruleset_digest":""}
        rules = {"rules":[{"id":"R1","lane":"DETERMINISTIC","implementation_state":"IMPLEMENTED","implemented_by":"scripts/check_exact_evidence.py"}]}
        policy = {"profile_identity":{"pack_id":"fixture","edition":"0.1"},
                  "tokenization":{"hyphen_policy":"SPLIT_COMPONENTS","word_pattern":r"[A-Za-z0-9]+"},
                  "sentence_limits":{"PROCEDURAL":3},"forbidden_phrases":[{"text":"etc."}],
                  "implemented_rules":[{"kind":"WORD_LIMIT"}]}
        term = {"term_id":"T1","term":"bleed valve","allowed_parts_of_speech":["NOUN"],
                "decision_state":"ADMITTED","approved_for_use":True}
        for name, obj in (("rules.json",rules),("policy.json",policy),("term.json",term)):
            (root/name).write_text(json.dumps(obj,sort_keys=True)+"\n")
        rules_raw=(root/"rules.json").read_bytes(); pack["ruleset_digest"]=digest(rules_raw)
        (root/"pack.json").write_text(json.dumps(pack,sort_keys=True)+"\n")
        def ref(name): return {"path":name,"artifact_digest":digest((root/name).read_bytes())}
        policy["profile_identity"].update(pack_digest=ref("pack.json")["artifact_digest"],ruleset_digest=ref("rules.json")["artifact_digest"])
        (root/"policy.json").write_text(json.dumps(policy,sort_keys=True)+"\n")
        text="Open bleed valve."
        case={"schema_version":DET_SCHEMA,"profile_pack":ref("pack.json"),"ruleset":ref("rules.json"),"policy":ref("policy.json"),
              "termbase_references":[ref("term.json")],"subject":{"content":text,"artifact_digest":digest(text.encode())},
              "candidate":{"content":text,"artifact_digest":digest(text.encode()),"segments":[{"start":0,"end":len(text),"text_digest":digest(text.encode()),"document_class":"PROCEDURAL"}]},
              "document_class":"PROCEDURAL","technical_terms_used":[{"term_id":"T1","start":5,"end":16,"text_digest":digest(b"bleed valve"),"part_of_speech":"NOUN"}]}
        raw=(json.dumps(case,sort_keys=True)+"\n").encode(); receipt=evaluate_deterministic(root,case,raw)
        if receipt["status"]!="PASS": failures.append(f"canonical deterministic failed: {receipt}")
        mutated=copy.deepcopy(case); mutated["policy"]["artifact_digest"]="sha256:"+"0"*64
        try: evaluate_deterministic(root,mutated,raw); failures.append("stale policy survived")
        except InputError: pass
        mutated=copy.deepcopy(case); mutated["technical_terms_used"][0]["part_of_speech"]="VERB"
        if evaluate_deterministic(root,mutated,raw)["status"]!="FAIL": failures.append("wrong POS survived")
        mutated=copy.deepcopy(case); mutated["candidate"]["segments"][0]["end"]-=1
        covered=mutated["candidate"]["content"][:mutated["candidate"]["segments"][0]["end"]]
        mutated["candidate"]["segments"][0]["text_digest"]=digest(covered.encode())
        if evaluate_deterministic(root,mutated,raw)["status"]!="FAIL": failures.append("uncovered candidate bytes survived")

        xml_source='<procedure><warning id="w1">Hot steam can burn you.</warning><step id="s1">Remove the cap.</step></procedure>'
        xml_case={"schema_version":DET_SCHEMA,"profile_pack":ref("pack.json"),"ruleset":ref("rules.json"),"policy":ref("policy.json"),
                  "termbase_references":[ref("term.json")],"subject":{"content":xml_source,"artifact_digest":digest(xml_source.encode())},
                  "candidate":{"content":xml_source,"artifact_digest":digest(xml_source.encode())},"document_class":"S1000D_XML",
                  "technical_terms_used":[],"xml_preservation":{"id_attribute":"id","protected_nodes":[
                    {"id":"w1","tag":"warning","text_digest":digest(b"Hot steam can burn you.")},
                    {"id":"s1","tag":"step","text_digest":digest(b"Remove the cap.")} ]}}
        xml_raw=(json.dumps(xml_case,sort_keys=True)+"\n").encode()
        if evaluate_deterministic(root,xml_case,xml_raw)["status"]!="PASS": failures.append("canonical XML preservation failed")
        bad_xml=copy.deepcopy(xml_case); bad_xml["candidate"]["content"]='<procedure><step id="s1">Remove the cap.</step></procedure>'
        bad_xml["candidate"]["artifact_digest"]=digest(bad_xml["candidate"]["content"].encode())
        if evaluate_deterministic(root,bad_xml,xml_raw)["status"]!="FAIL": failures.append("removed protected XML node survived")

    heuristics=["IMPERATIVE","PASSIVE","MULTI_ACTION","NOUN_CLUSTER_GT3","AMBIGUOUS_PRONOUN","MEANING_PRESERVED"]
    cases=[]
    for h in heuristics:
        cases += [{"case_id":h+"-p1","labels":{x:x==h for x in heuristics}},
                  {"case_id":h+"-p2","labels":{x:x==h for x in heuristics}},
                  {"case_id":h+"-n1","labels":{x:False for x in heuristics}},
                  {"case_id":h+"-n2","labels":{x:False for x in heuristics}}]
    gold={"corpus_id":"fixture","cases":cases}; gold_raw=(json.dumps(gold,sort_keys=True)+"\n").encode()
    predictions={"schema_version":PRED_SCHEMA,"corpus_identity":{"corpus_id":"fixture","artifact_digest":digest(gold_raw)},
                 "evaluator_identity":{"evaluator_id":"fixture","version":"1.0.0","model_identity":"fixture-v1",
                                       "implementation_digest":"sha256:"+"a"*64,"model_digest":"sha256:"+"b"*64},
                 "execution_mode":"FIXTURE_LABEL_REPLAY","predictions":copy.deepcopy(cases)}
    pred_raw=(json.dumps(predictions,sort_keys=True)+"\n").encode()
    policy={"schema_version":CAL_SCHEMA,"required_heuristics":heuristics,
            "gold_corpus_identity":{"corpus_id":"fixture","artifact_digest":digest(gold_raw)},
            "minimum_cases_per_heuristic":2,"maximum_false_positive_rate":0.0,"maximum_false_negative_rate":0.0,
            "required_boundary_cases":[{"case_id":h+"-p1","heuristic":h,"expected":True} for h in heuristics]}
    policy_raw=(json.dumps(policy,sort_keys=True)+"\n").encode()
    receipt=evaluate_calibration(policy,policy_raw,gold,gold_raw,predictions,pred_raw)
    if receipt["status"]!="PASS" or receipt["classifier_state"]!="NOT_IMPLEMENTED": failures.append("canonical calibration failed")
    bad=copy.deepcopy(predictions); bad["predictions"][0]["labels"][heuristics[0]]=False
    if evaluate_calibration(policy,policy_raw,gold,gold_raw,bad,(json.dumps(bad,sort_keys=True)+"\n").encode())["status"]!="FAIL":
        failures.append("boundary misclassification survived")
    bad=copy.deepcopy(predictions); bad["evaluator_identity"]["model_identity"]="latest"
    try: evaluate_calibration(policy,policy_raw,gold,gold_raw,bad,pred_raw); failures.append("mutable model survived")
    except InputError: pass
    bad=copy.deepcopy(predictions); bad["corpus_identity"]["artifact_digest"]="sha256:"+"0"*64
    try: evaluate_calibration(policy,policy_raw,gold,gold_raw,bad,pred_raw); failures.append("stale gold identity survived")
    except InputError: pass
    bad=copy.deepcopy(predictions); bad["predictions"].pop()
    try: evaluate_calibration(policy,policy_raw,gold,gold_raw,bad,pred_raw); failures.append("incomplete prediction set survived")
    except InputError: pass
    if failures:
        for item in failures: print(f"SELFTEST RED: {item}",file=sys.stderr)
        return 2
    print("SELFTEST GREEN: exact deterministic and corpus calibration evidence stayed bound")
    return 0


def write(path: Path | None, value: dict[str, Any]) -> None:
    payload=json.dumps(value,indent=2,sort_keys=True)+"\n"
    if path: path.write_text(payload)
    else: print(payload,end="")


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    det=sub.add_parser("deterministic"); det.add_argument("--repo-root",type=Path,required=True); det.add_argument("--case",type=Path,required=True); det.add_argument("--receipt",type=Path)
    cal=sub.add_parser("calibration"); cal.add_argument("--policy",type=Path,required=True); cal.add_argument("--gold",type=Path,required=True); cal.add_argument("--predictions",type=Path,required=True); cal.add_argument("--receipt",type=Path)
    sub.add_parser("selftest"); args=parser.parse_args(argv)
    try:
        if args.command=="selftest": return selftest()
        if args.command=="deterministic":
            case,raw=load(args.case); result=evaluate_deterministic(args.repo_root.resolve(),case,raw); write(args.receipt,result); return result["exit_code"]
        policy,policy_raw=load(args.policy); gold,gold_raw=load(args.gold); predictions,pred_raw=load(args.predictions)
        result=evaluate_calibration(policy,policy_raw,gold,gold_raw,predictions,pred_raw); write(args.receipt,result); return result["exit_code"]
    except InputError as exc:
        print(f"INPUT RED: {exc}",file=sys.stderr); return 64
    except Exception as exc:
        print(f"CHECKER RED: {type(exc).__name__}: {exc}",file=sys.stderr); return 70

if __name__=="__main__": raise SystemExit(main())
