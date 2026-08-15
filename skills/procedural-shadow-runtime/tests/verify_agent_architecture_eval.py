#!/usr/bin/env python3
"""Positive, Vibe-band, mutation, and input-error controls."""
from __future__ import annotations
import copy,json,subprocess,sys,tempfile
from pathlib import Path
from typing import Callable
from fixture_factory import architecture
ROOT=Path(__file__).resolve().parents[1]; CHECKER=ROOT/"scripts"/"check_agent_architecture_eval.py"
def run(p:Path):return subprocess.run([sys.executable,"-S",str(CHECKER),str(p)],text=True,capture_output=True,check=False)
def write(d:Path,n:str,x:dict)->Path:p=d/f"{n}.json";p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");return p
def expect(p:Path,c:int,n:str)->None:
 r=run(p)
 if r.returncode!=c:raise AssertionError(f"{n}: expected {c}, got {r.returncode}\n{r.stdout}\n{r.stderr}")
def by(xs:list[dict],k:str,v:str)->dict:return next(x for x in xs if x[k]==v)
def main()->int:
 valid=architecture(); vibe=architecture(True)
 def contradiction(d:dict)->None:
  s=by(d["vibe_signals"],"signal_id","VC-TL-02_NON_IDEMPOTENT_WRITE");s["status"]="DETECTED";s["evidence"][0]["polarity"]="PROVES_PRESENT";s["evidence"][0]["mode"]="NEGATIVE_CONTROL"
 def unexercised(d:dict)->None:d["criteria"][0].update(status="NOT_EXERCISED",evidence=[])
 mutations:list[tuple[str,Callable[[dict],None]]]=[("missing-criterion",lambda d:d["criteria"].pop()),("duplicate-criterion",lambda d:d["criteria"].append(copy.deepcopy(d["criteria"][0]))),("unknown-evidence-mode",lambda d:d["criteria"][0]["evidence"][0].__setitem__("mode","PROSE")),("subject-digest-mismatch",lambda d:d["criteria"][0]["evidence"][0].__setitem__("subject_digest","d"*64)),("rubric-digest-tamper",lambda d:d["rubric"].__setitem__("content_sha256","d"*64)),("declared-score-tamper",lambda d:d["declared"].__setitem__("effective_score",99.0)),("positive-vibe-contradiction",contradiction),("verified-without-evidence",lambda d:d["criteria"][0].__setitem__("evidence",[])),("vibe-polarity-mismatch",lambda d:d["vibe_signals"][0]["evidence"][0].__setitem__("polarity","PROVES_PRESENT")),("raw-private-reasoning",lambda d:d["authority"].__setitem__("raw_private_reasoning",True)),("capability-widening",lambda d:d["authority"].__setitem__("capability_widening",True)),("private-data-egress",lambda d:d["authority"].__setitem__("private_data_egress",True)),("rights-review-missing",lambda d:d["authority"].__setitem__("source_rights_reviewed",False)),("human-authority-missing",lambda d:d["authority"].__setitem__("human_review_authority",False)),("unexercised-declared-pass",unexercised),("critical-ceiling-tamper",lambda d:d["declared"].__setitem__("score_ceiling",59.0))]
 with tempfile.TemporaryDirectory(prefix="agent-architecture-controls-") as t:
  d=Path(t); expect(write(d,"valid",valid),0,"positive");expect(write(d,"vibe",vibe),0,"vibe")
  for n,m in mutations:x=copy.deepcopy(valid);m(x);expect(write(d,n,x),2,n)
  bad=d/"malformed.json";bad.write_text("{not-json");expect(bad,64,"malformed");expect(d/"absent.json",64,"absent")
 print(f"AGENT ARCHITECTURE EVAL GREEN: positive=1 vibe_closed=1 mutations_refused={len(mutations)} input_errors=2");return 0
if __name__=="__main__":raise SystemExit(main())
