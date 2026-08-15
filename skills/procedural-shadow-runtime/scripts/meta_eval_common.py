#!/usr/bin/env python3
"""Shared contracts for procedural-meta-abstraction-eval/v2."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "procedural-meta-abstraction-eval/v2"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5"]
LEVEL_NAMES = {
    "L0": "EXACT_PROCEDURE",
    "L1": "NORMALIZED_PROCEDURE",
    "L2": "INVARIANT_ORACLE",
    "L3": "CROSS_DOMAIN_PATTERN",
    "L4": "META_POLICY",
    "L5": "META_CONTROLLER",
}
CONDITIONS = [
    "NO_SKILL",
    "METADATA_ONLY",
    "FULL_SKILL",
    "DELTA_CAPSULE",
    "DELTA_CAPSULE_PLUS_HARNESS",
]
GROUNDING_WEIGHTS = {
    "source_fidelity": 15.0,
    "applicability_precision": 10.0,
    "decision_coverage": 10.0,
    "execution_coverage": 15.0,
    "assertion_coverage": 15.0,
    "receipt_coverage": 20.0,
    "harness_coverage": 10.0,
    "negative_control_pass_rate": 5.0,
}
GENERALIZATION_WEIGHTS = {
    "paraphrase_transfer": 10.0,
    "tool_runtime_transfer": 15.0,
    "cross_domain_transfer": 20.0,
    "held_out_family_performance": 20.0,
    "counterfactual_coverage": 10.0,
    "causal_uplift_score": 15.0,
    "false_constraint_avoidance": 10.0,
}
META_WEIGHTS = {"architecture": 0.30, "grounding": 0.30, "generalization": 0.25, "regression": 0.15}
LEVEL_REQUIREMENTS = {
    "L0": {"architecture": 60.0, "meta": 60.0, "families": 1, "held_out": 0, "cases": 1, "trials": 1},
    "L1": {"architecture": 70.0, "meta": 70.0, "families": 2, "held_out": 0, "cases": 6, "trials": 2},
    "L2": {"architecture": 80.0, "meta": 80.0, "families": 2, "held_out": 0, "cases": 12, "trials": 3},
    "L3": {"architecture": 85.0, "meta": 85.0, "families": 3, "held_out": 1, "cases": 24, "trials": 5},
    "L4": {"architecture": 90.0, "meta": 90.0, "families": 4, "held_out": 1, "cases": 30, "trials": 5},
    "L5": {"architecture": 92.0, "meta": 95.0, "families": 5, "held_out": 2, "cases": 50, "trials": 10},
}


class ContractError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)


def obj(value: Any, path: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{path} must be an object")
    return value


def arr(value: Any, path: str) -> list[Any]:
    require(isinstance(value, list), f"{path} must be an array")
    return value


def text(value: Any, path: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{path} must be a non-empty string")
    return value


def boolean(value: Any, path: str) -> bool:
    require(isinstance(value, bool), f"{path} must be boolean")
    return value


def integer(value: Any, path: str, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{path} must be an integer")
    require(value >= minimum, f"{path} must be >= {minimum}")
    return value


def number(value: Any, path: str, minimum: float | None = None, maximum: float | None = None) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{path} must be numeric")
    result = float(value)
    require(math.isfinite(result), f"{path} must be finite")
    if minimum is not None:
        require(result >= minimum, f"{path} must be >= {minimum}")
    if maximum is not None:
        require(result <= maximum, f"{path} must be <= {maximum}")
    return result


def ratio(value: Any, path: str) -> float:
    return number(value, path, 0.0, 1.0)


def enum(value: Any, allowed: list[str] | set[str] | tuple[str, ...], path: str) -> str:
    result = text(value, path)
    require(result in allowed, f"{path} must be one of {sorted(allowed)}")
    return result


def exact_keys(value: dict[str, Any], required: list[str], path: str) -> None:
    expected, actual = set(required), set(value)
    missing, unknown = sorted(expected - actual), sorted(actual - expected)
    require(not missing, f"{path} missing keys: {missing}")
    require(not unknown, f"{path} has unknown keys: {unknown}")


def digest(value: Any, pattern: re.Pattern[str], path: str) -> str:
    result = text(value, path)
    require(pattern.fullmatch(result) is not None, f"{path} has invalid digest format")
    return result


def close(actual: float, declared: float, path: str, tolerance: float = 0.01) -> None:
    require(abs(actual - declared) <= tolerance, f"{path} declared {declared:.6f}, recomputed {actual:.6f}")


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def band(score: float) -> str:
    return "VIBE_CODER" if score < 60.0 else "COMPETENT_AGENT_ENGINEER" if score < 85.0 else "AGENT_ARCHITECT"


def parse(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("top-level JSON must be an object")
    return data


def validate_subject(data: dict[str, Any]) -> dict[str, str]:
    value = obj(data["subject"], "$.subject")
    fields = ["repository", "base_sha", "current_sha", "runtime", "model_binding", "dataset_version", "context_digest", "eval_run_id"]
    exact_keys(value, fields, "$.subject")
    result = {
        "repository": text(value["repository"], "$.subject.repository"),
        "base_sha": digest(value["base_sha"], HEX40, "$.subject.base_sha"),
        "current_sha": digest(value["current_sha"], HEX40, "$.subject.current_sha"),
        "runtime": text(value["runtime"], "$.subject.runtime"),
        "model_binding": text(value["model_binding"], "$.subject.model_binding"),
        "dataset_version": text(value["dataset_version"], "$.subject.dataset_version"),
        "context_digest": digest(value["context_digest"], HEX64, "$.subject.context_digest"),
        "eval_run_id": text(value["eval_run_id"], "$.subject.eval_run_id"),
    }
    return result


def validate_candidate(data: dict[str, Any]) -> tuple[str, str]:
    value = obj(data["candidate"], "$.candidate")
    fields = ["abstraction_id", "current_level", "target_level", "source_procedure_ids", "source_anchors", "raw_private_reasoning"]
    exact_keys(value, fields, "$.candidate")
    text(value["abstraction_id"], "$.candidate.abstraction_id")
    current = enum(value["current_level"], LEVELS, "$.candidate.current_level")
    target = enum(value["target_level"], LEVELS, "$.candidate.target_level")
    require(LEVELS.index(target) == LEVELS.index(current) + 1, "target_level must be exactly one level above current_level")
    procedures = arr(value["source_procedure_ids"], "$.candidate.source_procedure_ids")
    require(bool(procedures), "source_procedure_ids must not be empty")
    parsed = [text(item, f"$.candidate.source_procedure_ids[{index}]") for index, item in enumerate(procedures)]
    require(len(parsed) == len(set(parsed)), "source_procedure_ids must be unique")
    anchors = arr(value["source_anchors"], "$.candidate.source_anchors")
    require(bool(anchors), "source_anchors must not be empty")
    for index, raw in enumerate(anchors):
        anchor = obj(raw, f"$.candidate.source_anchors[{index}]")
        exact_keys(anchor, ["repository", "ref", "path", "content_sha256"], f"$.candidate.source_anchors[{index}]")
        text(anchor["repository"], f"$.candidate.source_anchors[{index}].repository")
        text(anchor["ref"], f"$.candidate.source_anchors[{index}].ref")
        text(anchor["path"], f"$.candidate.source_anchors[{index}].path")
        digest(anchor["content_sha256"], HEX64, f"$.candidate.source_anchors[{index}].content_sha256")
    require(value["raw_private_reasoning"] is False, "candidate.raw_private_reasoning must be false")
    return current, target


def validate_design(data: dict[str, Any]) -> dict[str, Any]:
    value = obj(data["evaluation_design"], "$.evaluation_design")
    fields = ["task_case_count", "trials_per_case", "clean_context_reset", "same_runtime_model_bindings", "baseline_candidate_same_dataset", "dataset_frozen", "judge_rubric_version"]
    exact_keys(value, fields, "$.evaluation_design")
    integer(value["task_case_count"], "$.evaluation_design.task_case_count", 1)
    integer(value["trials_per_case"], "$.evaluation_design.trials_per_case", 1)
    for field in fields[2:6]:
        boolean(value[field], f"$.evaluation_design.{field}")
    text(value["judge_rubric_version"], "$.evaluation_design.judge_rubric_version")
    return value


def validate_controls(data: dict[str, Any]) -> dict[str, Any]:
    value = obj(data["controls"], "$.controls")
    fields = ["safety_violations", "unauthorized_capability_widening", "private_data_egress", "raw_private_reasoning", "model_weights_or_hidden_cot_claimed", "exact_subject_bound", "negative_control_executed", "source_rights_reviewed", "shadow_workers_read_only", "human_promotion_authority", "production_feedback_evidence_state"]
    exact_keys(value, fields, "$.controls")
    result: dict[str, Any] = {"safety_violations": integer(value["safety_violations"], "$.controls.safety_violations")}
    for field in fields[1:10]:
        result[field] = boolean(value[field], f"$.controls.{field}")
    result["production_feedback_evidence_state"] = enum(value["production_feedback_evidence_state"], {"NOT_EXERCISED", "PARTIAL", "VERIFIED"}, "$.controls.production_feedback_evidence_state")
    return result
