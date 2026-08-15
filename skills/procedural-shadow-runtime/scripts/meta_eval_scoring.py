#!/usr/bin/env python3
"""Score planes for procedural-meta-abstraction-eval/v2."""
from __future__ import annotations

from typing import Any

from agent_architecture_common import ArchitectureContractError, validate_architecture_receipt
from meta_eval_common import (
    CONDITIONS, GENERALIZATION_WEIGHTS, GROUNDING_WEIGHTS,
    ContractError, arr, clamp, close, exact_keys, integer, number, obj, ratio, require,
)


def architecture(data: dict[str, Any]) -> float:
    subject = obj(data["subject"], "$.subject")
    expected_subject = {
        "repository": str(subject["repository"]),
        "current_sha": str(subject["current_sha"]),
        "runtime": str(subject["runtime"]),
        "eval_run_id": str(subject["eval_run_id"]),
    }
    try:
        result = validate_architecture_receipt(data["architecture"], expected_subject=expected_subject)
    except ArchitectureContractError as exc:
        raise ContractError(f"architecture receipt: {exc}") from exc
    require(result["evidence_state"] == "PASS", "architecture receipt must have PASS evidence_state")
    return float(result["effective_score"])


def grounding(data: dict[str, Any]) -> tuple[float, dict[str, int]]:
    value = obj(data["grounding"], "$.grounding")
    exact_keys(value, [*GROUNDING_WEIGHTS, "must_total", "must_terminal", "unresolved_must", "declared_score"], "$.grounding")
    score = sum(ratio(value[field], f"$.grounding.{field}") * weight for field, weight in GROUNDING_WEIGHTS.items())
    total = integer(value["must_total"], "$.grounding.must_total")
    terminal = integer(value["must_terminal"], "$.grounding.must_terminal")
    unresolved = integer(value["unresolved_must"], "$.grounding.unresolved_must")
    require(terminal <= total, "must_terminal cannot exceed must_total")
    require(unresolved == total - terminal, "unresolved_must must equal must_total - must_terminal")
    close(score, number(value["declared_score"], "$.grounding.declared_score", 0.0, 100.0), "$.grounding.declared_score")
    return score, {"must_total": total, "must_terminal": terminal, "unresolved_must": unresolved}


def generalization(data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    value = obj(data["generalization"], "$.generalization")
    fields = ["paraphrase_transfer", "tool_runtime_transfer", "cross_domain_transfer", "held_out_family_performance", "task_family_count", "held_out_family_count", "conditions_exercised", "condition_success_rates", "false_constraint_rate", "declared_score"]
    exact_keys(value, fields, "$.generalization")
    base = {field: ratio(value[field], f"$.generalization.{field}") for field in fields[:4]}
    families = integer(value["task_family_count"], "$.generalization.task_family_count", 1)
    held_out = integer(value["held_out_family_count"], "$.generalization.held_out_family_count")
    require(held_out <= families, "held_out_family_count cannot exceed task_family_count")
    conditions = [str(item) for item in arr(value["conditions_exercised"], "$.generalization.conditions_exercised")]
    require(all(item in CONDITIONS for item in conditions), "conditions_exercised has an unknown condition")
    require(len(conditions) == len(set(conditions)), "conditions_exercised must be unique")
    rates = obj(value["condition_success_rates"], "$.generalization.condition_success_rates")
    require(set(rates) == set(conditions), "condition_success_rates keys must equal conditions_exercised")
    parsed_rates = {key: ratio(raw, f"$.generalization.condition_success_rates.{key}") for key, raw in rates.items()}
    coverage = len(conditions) / len(CONDITIONS)
    uplift = parsed_rates.get("DELTA_CAPSULE_PLUS_HARNESS", 0.0) - parsed_rates.get("NO_SKILL", 0.0)
    uplift_score = clamp(uplift / 0.10) if {"NO_SKILL", "DELTA_CAPSULE_PLUS_HARNESS"}.issubset(parsed_rates) else 0.0
    false_rate = ratio(value["false_constraint_rate"], "$.generalization.false_constraint_rate")
    derived = {**base, "counterfactual_coverage": coverage, "causal_uplift_score": uplift_score, "false_constraint_avoidance": 1.0 - false_rate}
    score = sum(derived[field] * weight for field, weight in GENERALIZATION_WEIGHTS.items())
    close(score, number(value["declared_score"], "$.generalization.declared_score", 0.0, 100.0), "$.generalization.declared_score")
    return score, {"task_family_count": families, "held_out_family_count": held_out, "conditions": conditions, "condition_success_rates": parsed_rates, "counterfactual_coverage": coverage, "raw_uplift": uplift, "causal_uplift_score": uplift_score, "false_constraint_rate": false_rate}


def _metrics(raw: Any, path: str) -> dict[str, float]:
    value = obj(raw, path)
    fields = ["safety_pass_rate", "accuracy", "judge_score", "avg_tokens", "p95_latency_ms", "avg_cost_usd", "schema_failure_rate"]
    exact_keys(value, fields, path)
    return {
        "safety_pass_rate": ratio(value["safety_pass_rate"], f"{path}.safety_pass_rate"),
        "accuracy": ratio(value["accuracy"], f"{path}.accuracy"),
        "judge_score": ratio(value["judge_score"], f"{path}.judge_score"),
        "avg_tokens": number(value["avg_tokens"], f"{path}.avg_tokens", 0.000001),
        "p95_latency_ms": number(value["p95_latency_ms"], f"{path}.p95_latency_ms", 0.000001),
        "avg_cost_usd": number(value["avg_cost_usd"], f"{path}.avg_cost_usd", 0.0),
        "schema_failure_rate": ratio(value["schema_failure_rate"], f"{path}.schema_failure_rate"),
    }


def regression(data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    value = obj(data["regression"], "$.regression")
    exact_keys(value, ["baseline", "candidate", "deltas", "feedback", "declared_score"], "$.regression")
    baseline, candidate = _metrics(value["baseline"], "$.regression.baseline"), _metrics(value["candidate"], "$.regression.candidate")
    computed = {
        "accuracy_delta": candidate["accuracy"] - baseline["accuracy"],
        "judge_score_delta": candidate["judge_score"] - baseline["judge_score"],
        "token_growth_ratio": (candidate["avg_tokens"] - baseline["avg_tokens"]) / baseline["avg_tokens"],
        "latency_growth_ratio": (candidate["p95_latency_ms"] - baseline["p95_latency_ms"]) / baseline["p95_latency_ms"],
        "cost_growth_ratio": (candidate["avg_cost_usd"] - baseline["avg_cost_usd"]) / baseline["avg_cost_usd"] if baseline["avg_cost_usd"] > 0 else 0.0,
    }
    declared = obj(value["deltas"], "$.regression.deltas")
    exact_keys(declared, list(computed), "$.regression.deltas")
    for field, actual in computed.items():
        close(actual, number(declared[field], f"$.regression.deltas.{field}"), f"$.regression.deltas.{field}", 0.0001)
    feedback = obj(value["feedback"], "$.regression.feedback")
    count_fields = ["traces_observed", "anomalies_selected", "pii_scrubbed", "human_adjudicated", "golden_admitted", "regression_replayed"]
    exact_keys(feedback, [*count_fields, "trace_completeness", "declared_feedback_closure_rate", "declared_replay_coverage"], "$.regression.feedback")
    counts = {field: integer(feedback[field], f"$.regression.feedback.{field}") for field in count_fields}
    require(counts["anomalies_selected"] <= counts["traces_observed"], "anomalies_selected cannot exceed traces_observed")
    require(counts["pii_scrubbed"] <= counts["anomalies_selected"], "pii_scrubbed cannot exceed anomalies_selected")
    require(counts["human_adjudicated"] <= counts["pii_scrubbed"], "human_adjudicated cannot exceed pii_scrubbed")
    require(counts["golden_admitted"] <= counts["human_adjudicated"], "golden_admitted cannot exceed human_adjudicated")
    require(counts["regression_replayed"] <= counts["golden_admitted"], "regression_replayed cannot exceed golden_admitted")
    trace = ratio(feedback["trace_completeness"], "$.regression.feedback.trace_completeness")
    closure = counts["golden_admitted"] / counts["human_adjudicated"] if counts["human_adjudicated"] else 0.0
    replay = counts["regression_replayed"] / counts["golden_admitted"] if counts["golden_admitted"] else 0.0
    close(closure, ratio(feedback["declared_feedback_closure_rate"], "$.regression.feedback.declared_feedback_closure_rate"), "$.regression.feedback.declared_feedback_closure_rate", 0.0001)
    close(replay, ratio(feedback["declared_replay_coverage"], "$.regression.feedback.declared_replay_coverage"), "$.regression.feedback.declared_replay_coverage", 0.0001)
    score = (
        candidate["safety_pass_rate"] * 20.0
        + clamp(candidate["accuracy"] / 0.98) * 15.0
        + clamp(candidate["judge_score"] / 0.85) * 10.0
        + (1.0 if candidate["schema_failure_rate"] <= 0.001 else clamp(0.001 / candidate["schema_failure_rate"])) * 10.0
        + clamp(1500.0 / candidate["avg_tokens"]) * 5.0
        + clamp(15000.0 / candidate["p95_latency_ms"]) * 5.0
        + (1.0 if candidate["avg_cost_usd"] <= 0.05 else clamp(0.05 / candidate["avg_cost_usd"])) * 5.0
        + closure * 15.0 + replay * 10.0 + trace * 5.0
    )
    close(score, number(value["declared_score"], "$.regression.declared_score", 0.0, 100.0), "$.regression.declared_score")
    return score, {"baseline": baseline, "candidate": candidate, "deltas": computed, "feedback": {**counts, "trace_completeness": trace}, "feedback_closure": closure, "replay_coverage": replay}
