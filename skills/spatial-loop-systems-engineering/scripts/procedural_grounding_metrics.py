"""Proof-mode, weighted coverage, and four-condition attribution checks."""
from __future__ import annotations
from typing import Any
from procedural_grounding_common import *  # noqa: F403


def validate_proofs_and_metrics(data: dict[str, Any], atoms: list[dict[str, Any]], observations: list[dict[str, Any]], source_by_id: dict[str, dict[str, Any]], obligations: list[dict[str, Any]], obligations_by_proc: dict[str, list[dict[str, Any]]], evidence_state: str) -> tuple[dict[str, Any], list[str]]:
    strongest = {atom["procedure_id"]: strongest_state(observations, atom["procedure_id"]) for atom in atoms}
    critical_unproven: list[str] = []
    for atom in atoms:
        proc_id = atom["procedure_id"]
        state = strongest[proc_id]
        if atom["required_now"] and atom["criticality"] == "CRITICAL":
            source = source_by_id[atom["source_id"]]
            require(source["license_state"] == "ADMITTED", f"critical required atom {proc_id} uses an unadmitted source")
            require(source["trust_state"] == "REVIEWED", f"critical required atom {proc_id} uses an unreviewed source")
            require(source["scripts_state"] in {"NONE", "REVIEWED"}, f"critical required atom {proc_id} uses unreviewed or denied scripts")
            require(source["dynamic_context_state"] in {"NONE", "REVIEWED"}, f"critical required atom {proc_id} uses denied dynamic context")
            if not proof_satisfied(atom, state):
                critical_unproven.append(proc_id)
        if atom["required_now"] and atom["proof_mode"] == "EXTERNAL_OR_HUMAN" and evidence_state == "PASS":
            fail(f"required EXTERNAL_OR_HUMAN atom {proc_id} cannot be promoted to PASS by this checker")
        if atom["required_now"] and atom["criticality"] == "CRITICAL" and atom["novelty"] in {"SKILL_SPECIFIC", "ENVIRONMENT_SPECIFIC", "UNKNOWN"}:
            satisfied = [item for item in obligations_by_proc[proc_id] if item["status"] == "SATISFIED"]
            require(bool(satisfied), f"critical novel atom {proc_id} requires a satisfied assertion/probe obligation")
            refs = {obs["evidence_ref"] for obs in observations if obs["procedure_id"] == proc_id}
            require(any(item["evidence_ref"] in refs for item in satisfied), f"critical novel atom {proc_id} has an obligation receipt not bound to its observation evidence")
    total = sum(atom["weight"] for atom in atoms)
    mentioned = sum(atom["weight"] for atom in atoms if strongest[atom["procedure_id"]] in MENTIONED_STATES)
    harness = sum(atom["weight"] for atom in atoms if strongest[atom["procedure_id"]] in HARNESS_STATES)
    executed = sum(atom["weight"] for atom in atoms if strongest[atom["procedure_id"]] in EXECUTION_STATES)
    evidenced = sum(atom["weight"] for atom in atoms if strongest[atom["procedure_id"]] in EVIDENCE_STATES)
    computed = {
        "atom_count": len(atoms), "total_weight": total, "mentioned_weight": mentioned,
        "harness_encoded_weight": harness, "executed_weight": executed, "evidence_weight": evidenced,
        "critical_unproven": sorted(critical_unproven),
        "mention_coverage": round(mentioned / total, 6), "harness_coverage": round(harness / total, 6),
        "execution_coverage": round(executed / total, 6), "evidence_coverage": round(evidenced / total, 6),
    }
    declared = require_dict(data["declared_metrics"], "$.declared_metrics")
    require_keys(declared, computed.keys(), "$.declared_metrics")
    for key in ("atom_count", "total_weight", "mentioned_weight", "harness_encoded_weight", "executed_weight", "evidence_weight"):
        require_int(declared[key], f"$.declared_metrics.{key}", minimum=0)
        require(declared[key] == computed[key], f"$.declared_metrics.{key} does not match the recomputed value")
    raw_critical = require_list(declared["critical_unproven"], "$.declared_metrics.critical_unproven")
    normalized = [require_id(item, "procedure", f"$.declared_metrics.critical_unproven[{index}]") for index, item in enumerate(raw_critical)]
    require(sorted(normalized) == computed["critical_unproven"], "$.declared_metrics.critical_unproven does not match")
    for key in ("mention_coverage", "harness_coverage", "execution_coverage", "evidence_coverage"):
        value = require_number(declared[key], f"$.declared_metrics.{key}", minimum=0, maximum=1)
        require(approx_equal(value, computed[key]), f"$.declared_metrics.{key} does not match the recomputed value")
    if evidence_state == "PASS":
        require(not critical_unproven, f"PASS is forbidden while critical atoms remain unproven: {', '.join(critical_unproven)}")
        unresolved = [item["obligation_id"] for item in obligations if item["status"] != "SATISFIED"]
        require(not unresolved, f"PASS is forbidden while obligations remain unresolved: {', '.join(unresolved)}")
    return computed, critical_unproven


def validate_attribution(data: dict[str, Any]) -> str:
    item = require_dict(data["attribution"], "$.attribution")
    fields = ["state", "conditions", "trials_per_condition", "condition_scores", "skill_lift", "grounding_lift", "receipt_refs"]
    require_keys(item, fields, "$.attribution")
    state = require_enum(item["state"], {"PASS", "NOT_EXERCISED"}, "$.attribution.state")
    conditions = require_list(item["conditions"], "$.attribution.conditions")
    require(conditions == ATTRIBUTION_CONDITIONS, "$.attribution.conditions must preserve the four clean-context conditions in order")
    require_int(item["trials_per_condition"], "$.attribution.trials_per_condition", minimum=1)
    refs = require_list(item["receipt_refs"], "$.attribution.receipt_refs")
    if state == "NOT_EXERCISED":
        require(item["condition_scores"] is None, "NOT_EXERCISED attribution cannot publish condition scores")
        require(item["skill_lift"] is None and item["grounding_lift"] is None, "NOT_EXERCISED attribution cannot publish lift")
        require(not refs, "NOT_EXERCISED attribution cannot cite execution receipts")
    else:
        scores = require_dict(item["condition_scores"], "$.attribution.condition_scores")
        require(set(scores) == set(ATTRIBUTION_CONDITIONS), "$.attribution.condition_scores must contain exactly the four conditions")
        numeric = {key: require_number(scores[key], f"$.attribution.condition_scores.{key}", minimum=0, maximum=1) for key in ATTRIBUTION_CONDITIONS}
        skill_lift = require_number(item["skill_lift"], "$.attribution.skill_lift", minimum=-1, maximum=1)
        grounding_lift = require_number(item["grounding_lift"], "$.attribution.grounding_lift", minimum=-1, maximum=1)
        require(approx_equal(skill_lift, numeric["FULL_SKILL"] - numeric["NO_SKILL"]), "$.attribution.skill_lift is not recomputed from paired conditions")
        require(approx_equal(grounding_lift, numeric["FULL_SKILL_PLUS_GROUNDING"] - numeric["FULL_SKILL"]), "$.attribution.grounding_lift is not recomputed from paired conditions")
        require(len(refs) >= 4, "PASS attribution requires execution receipts for all conditions")
        for index, ref in enumerate(refs):
            require_str(ref, f"$.attribution.receipt_refs[{index}]")
    return state
