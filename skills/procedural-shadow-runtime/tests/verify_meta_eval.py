#!/usr/bin/env python3
"""Positive, semantic-mutation, and input-error controls for meta Eval v2."""
from __future__ import annotations
import copy,json,subprocess,sys,tempfile
from pathlib import Path
from typing import Callable
from fixture_factory import meta
ROOT=Path(__file__).resolve().parents[1];CHECKER=ROOT/"scripts"/"check_meta_abstraction_eval.py"
def run(p:Path):return subprocess.run([sys.executable,"-S",str(CHECKER),str(p)],text=True,capture_output=True,check=False)
def write(d:Path,n:str,x:dict)->Path:p=d/f"{n}.json";p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");return p
def expect(p:Path,c:int,n:str)->None:
 r=run(p)
 if r.returncode!=c:raise AssertionError(f"{n}: expected {c}, got {r.returncode}\n{r.stdout}\n{r.stderr}")
def main()->int:
 valid=meta()
 mutations:list[tuple[str,Callable[[dict],None]]]=[("safety-violation",lambda d:d["controls"].__setitem__("safety_violations",1)),("unresolved-must",lambda d:(d["grounding"].__setitem__("must_terminal",11),d["grounding"].__setitem__("unresolved_must",1))),("negative-control-absent",lambda d:d["controls"].__setitem__("negative_control_executed",False)),("held-out-absent",lambda d:d["generalization"].__setitem__("held_out_family_count",0)),("counterfactual-incomplete",lambda d:(d["generalization"]["conditions_exercised"].remove("METADATA_ONLY"),d["generalization"]["condition_success_rates"].pop("METADATA_ONLY"))),("l5-without-production-closure",lambda d:(d["candidate"].__setitem__("current_level","L4"),d["candidate"].__setitem__("target_level","L5"))),("accuracy-regression",lambda d:d["regression"]["candidate"].__setitem__("accuracy",.97)),("token-regression",lambda d:d["regression"]["candidate"].__setitem__("avg_tokens",1450.0)),("latency-regression",lambda d:d["regression"]["candidate"].__setitem__("p95_latency_ms",6000.0)),("schema-regression",lambda d:d["regression"]["candidate"].__setitem__("schema_failure_rate",.002)),("raw-private-reasoning",lambda d:d["controls"].__setitem__("raw_private_reasoning",True)),("candidate-private-reasoning",lambda d:d["candidate"].__setitem__("raw_private_reasoning",True)),("capability-widening",lambda d:d["controls"].__setitem__("unauthorized_capability_widening",True)),("private-data-egress",lambda d:d["controls"].__setitem__("private_data_egress",True)),("hidden-cot-claim",lambda d:d["controls"].__setitem__("model_weights_or_hidden_cot_claimed",True)),("shadow-write-authority",lambda d:d["controls"].__setitem__("shadow_workers_read_only",False)),("human-authority-removed",lambda d:d["controls"].__setitem__("human_promotion_authority",False)),("rights-review-missing",lambda d:d["controls"].__setitem__("source_rights_reviewed",False)),("declared-score-tamper",lambda d:d["promotion"].__setitem__("declared_raw_meta_score",99.0)),("level-skip",lambda d:d["candidate"].__setitem__("current_level","L2")),("duplicate-condition",lambda d:d["generalization"]["conditions_exercised"].append("NO_SKILL")),("source-digest-missing",lambda d:d["candidate"]["source_anchors"][0].pop("content_sha256")),("trace-incomplete",lambda d:d["regression"]["feedback"].__setitem__("trace_completeness",.80)),("architecture-freeform",lambda d:d.__setitem__("architecture",{"control_flow_state":5})),("architecture-score-tamper",lambda d:d["architecture"]["declared"].__setitem__("effective_score",99.0)),("architecture-rubric-tamper",lambda d:d["architecture"]["rubric"].__setitem__("content_sha256","d"*64)),("architecture-subject-mismatch",lambda d:d["architecture"]["subject"].__setitem__("current_sha","2"*40)),("architecture-unexercised",lambda d:(d["architecture"]["criteria"][0].__setitem__("status","NOT_EXERCISED"),d["architecture"]["criteria"][0].__setitem__("evidence",[])))]
 with tempfile.TemporaryDirectory(prefix="meta-eval-controls-") as t:
  dd=Path(t);expect(write(dd,"valid",valid),0,"positive")
  for n,m in mutations:x=copy.deepcopy(valid);m(x);expect(write(dd,n,x),2,n)
  bad=dd/"malformed.json";bad.write_text("{not-json");expect(bad,64,"malformed");expect(dd/"absent.json",64,"absent")
 print(f"META ABSTRACTION EVAL V2 GREEN: positive=1 mutations_refused={len(mutations)} input_errors=2");return 0
if __name__=="__main__":raise SystemExit(main())
