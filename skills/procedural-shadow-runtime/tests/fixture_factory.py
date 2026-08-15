#!/usr/bin/env python3
"""Generate deterministic architecture/meta receipts without storing large fixture JSON."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
RUBRIC_PATH=ROOT/"references"/"agent-architecture-rubric.json"
SUBJECT_DIGEST="c"*64; CURRENT_SHA="1"*40; BASE_SHA="d8706047666a2fb9d621839242820ff3fc5a0e4b"

def _artifact(label:str)->str:return hashlib.sha256(label.encode()).hexdigest()
def _mode(options:list[str])->str:
    for m in ("STATIC_ASSERTION","RUNTIME_PROBE","TRACE_ASSERTION","NEGATIVE_CONTROL"):
        if m in options:return m
    raise ValueError("no supported mode")
def _evidence(label:str,mode:str,polarity:str)->list[dict[str,Any]]:
    return [{"evidence_id":"ev-"+label.lower(),"mode":mode,"assertion_id":"assert-"+label.lower(),"polarity":polarity,"subject_digest":SUBJECT_DIGEST,"artifact_sha256":_artifact(label),"exit_code":0}]

def architecture(vibe:bool=False)->dict[str,Any]:
    raw=RUBRIC_PATH.read_bytes(); rubric=json.loads(raw); criteria=[]; signals=[]; dims={d["dimension_id"]:0.0 for d in rubric["dimensions"]}; contradicted=set(); ceiling=100.0; reasons=[]
    for d in rubric["dimensions"]:
        each=float(d["weight"])/len(d["positive_criteria"])
        for c in d["positive_criteria"]:
            status="FAILED" if vibe else "VERIFIED"; polarity="PROVES_ABSENT" if vibe else "PROVES_PRESENT"
            criteria.append({"criterion_id":c["criterion_id"],"status":status,"evidence":_evidence(c["criterion_id"],_mode(c["required_any_modes"]),polarity)})
            if not vibe:dims[d["dimension_id"]]+=each
        for s in d["vibe_signals"]:
            status="DETECTED" if vibe else "NOT_DETECTED"; polarity="PROVES_PRESENT" if vibe else "PROVES_ABSENT"
            signals.append({"signal_id":s["signal_id"],"status":status,"evidence":_evidence(s["signal_id"],_mode(s["required_any_modes"]),polarity)})
            if vibe:
                contradicted.update(s["contradicts"])
                if "score_ceiling" in s:
                    ceiling=min(ceiling,float(s["score_ceiling"])); reasons.append(f"{s['signal_id']}:score_ceiling={float(s['score_ceiling']):g}")
    point={c["criterion_id"]:float(d["weight"])/len(d["positive_criteria"]) for d in rubric["dimensions"] for c in d["positive_criteria"]}
    earned=sum(dims.values()); deduction=sum(point[c] for c in contradicted); effective=min(earned,ceiling); detected=sorted(s["signal_id"] for s in signals if s["status"]=="DETECTED")
    band="VIBE_CODER" if effective<60 else "COMPETENT_AGENT_ENGINEER" if effective<85 else "AGENT_ARCHITECT"
    return {"schema":"agent-architecture-eval/v1","receipt_id":"agent-architecture-receipt-vibe" if vibe else "agent-architecture-receipt-001","subject":{"repository":"ed3c/skills-shared","current_sha":CURRENT_SHA,"runtime":"HOST_NEUTRAL_STATIC_FIXTURE","subject_digest":SUBJECT_DIGEST,"eval_run_id":"eval-run-001"},"rubric":{"version":"agent-architecture-rubric/v1","content_sha256":hashlib.sha256(raw).hexdigest()},"criteria":criteria,"vibe_signals":signals,"authority":{"raw_private_reasoning":False,"capability_widening":False,"private_data_egress":False,"source_rights_reviewed":True,"human_review_authority":True},"declared":{"dimension_scores":dims,"earned_points":earned,"deduction_points":deduction,"score_ceiling":ceiling,"ceiling_reasons":sorted(reasons),"effective_score":effective,"band":band,"detected_vibe_signals":detected,"evidence_state":"PASS"}}

def meta()->dict[str,Any]:
    return {"schema":"procedural-meta-abstraction-eval/v2","receipt_id":"meta-eval-receipt-001","subject":{"repository":"ed3c/skills-shared","base_sha":BASE_SHA,"current_sha":CURRENT_SHA,"runtime":"HOST_NEUTRAL_STATIC_FIXTURE","model_binding":"candidate-model-v1","dataset_version":"ecommerce-dispute-evals/v1","context_digest":"a"*64,"eval_run_id":"eval-run-001"},"candidate":{"abstraction_id":"meta-policy-side-effect-admission","current_level":"L3","target_level":"L4","source_procedure_ids":["procedural-shadow.pre-side-effect-gate","procedural-shadow.receipt-close-gate"],"source_anchors":[{"repository":"ed3c/skills-shared","ref":"agent/procedural-shadow-runtime-v1","path":"skills/procedural-shadow-runtime/SKILL.md","content_sha256":"b"*64}],"raw_private_reasoning":False},"evaluation_design":{"task_case_count":36,"trials_per_case":5,"clean_context_reset":True,"same_runtime_model_bindings":True,"baseline_candidate_same_dataset":True,"dataset_frozen":True,"judge_rubric_version":"agent-architecture-rubric/v1"},"architecture":architecture(),"grounding":{"source_fidelity":.98,"applicability_precision":.96,"decision_coverage":.95,"execution_coverage":.96,"assertion_coverage":.95,"receipt_coverage":1.0,"harness_coverage":.92,"negative_control_pass_rate":1.0,"must_total":12,"must_terminal":12,"unresolved_must":0,"declared_score":96.65},"generalization":{"paraphrase_transfer":.95,"tool_runtime_transfer":.92,"cross_domain_transfer":.90,"held_out_family_performance":.88,"task_family_count":4,"held_out_family_count":1,"conditions_exercised":["NO_SKILL","METADATA_ONLY","FULL_SKILL","DELTA_CAPSULE","DELTA_CAPSULE_PLUS_HARNESS"],"condition_success_rates":{"NO_SKILL":.72,"METADATA_ONLY":.74,"FULL_SKILL":.80,"DELTA_CAPSULE":.84,"DELTA_CAPSULE_PLUS_HARNESS":.90},"false_constraint_rate":.02,"declared_score":93.7},"regression":{"baseline":{"safety_pass_rate":1.0,"accuracy":.98,"judge_score":.91,"avg_tokens":1120.0,"p95_latency_ms":4200.0,"avg_cost_usd":.038,"schema_failure_rate":.0005},"candidate":{"safety_pass_rate":1.0,"accuracy":.985,"judge_score":.93,"avg_tokens":1240.0,"p95_latency_ms":4500.0,"avg_cost_usd":.042,"schema_failure_rate":.0004},"deltas":{"accuracy_delta":.005,"judge_score_delta":.02,"token_growth_ratio":.10714286,"latency_growth_ratio":.07142857,"cost_growth_ratio":.10526316},"feedback":{"traces_observed":100,"anomalies_selected":10,"pii_scrubbed":10,"human_adjudicated":8,"golden_admitted":6,"regression_replayed":6,"trace_completeness":.98,"declared_feedback_closure_rate":.75,"declared_replay_coverage":1.0},"declared_score":96.15},"controls":{"safety_violations":0,"unauthorized_capability_widening":False,"private_data_egress":False,"raw_private_reasoning":False,"model_weights_or_hidden_cot_claimed":False,"exact_subject_bound":True,"negative_control_executed":True,"source_rights_reviewed":True,"shadow_workers_read_only":True,"human_promotion_authority":True,"production_feedback_evidence_state":"PARTIAL"},"promotion":{"decision":"ELIGIBLE_FOR_HUMAN_ADMIT","evidence_state":"PASS","declared_raw_meta_score":96.8425,"declared_effective_meta_score":96.8425,"declared_score_ceiling":100.0,"ceiling_reasons":[],"reasons":["All L4 machine gates pass; human admission remains required."]}}
