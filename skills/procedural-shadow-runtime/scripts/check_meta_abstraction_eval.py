#!/usr/bin/env python3
"""Deterministic checker for procedural-meta-abstraction-eval/v1."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from meta_eval_common import (
    LEVEL_NAMES, META_WEIGHTS, SCHEMA, ContractError, arr, band, close,
    enum, exact_keys, number, obj, parse, require, text, validate_candidate,
    validate_controls, validate_design, validate_subject,
)
from meta_eval_promotion import ceiling, errors
from meta_eval_scoring import architecture, generalization, grounding, regression


def validate(data: dict[str, Any]) -> dict[str, Any]:
    top = ["schema", "receipt_id", "subject", "candidate", "evaluation_design", "architecture", "grounding", "generalization", "regression", "controls", "promotion"]
    exact_keys(data, top, "$")
    require(data["schema"] == SCHEMA, f"$.schema must equal {SCHEMA}")
    text(data["receipt_id"], "$.receipt_id")
    validate_subject(data)
    current, target = validate_candidate(data)
    design, controls = validate_design(data), validate_controls(data)
    architecture_score = architecture(data)
    grounding_score, grounding_counts = grounding(data)
    generalization_score, generalization_state = generalization(data)
    regression_score, regression_state = regression(data)
    raw = architecture_score * META_WEIGHTS["architecture"] + grounding_score * META_WEIGHTS["grounding"] + generalization_score * META_WEIGHTS["generalization"] + regression_score * META_WEIGHTS["regression"]
    cap, cap_reasons = ceiling(target, grounding_counts, generalization_state, regression_state, controls)
    effective = min(raw, cap)

    promotion = obj(data["promotion"], "$.promotion")
    fields = ["decision", "evidence_state", "declared_raw_meta_score", "declared_effective_meta_score", "declared_score_ceiling", "ceiling_reasons", "reasons"]
    exact_keys(promotion, fields, "$.promotion")
    decision = enum(promotion["decision"], {"ELIGIBLE_FOR_HUMAN_ADMIT", "HOLD", "REJECT"}, "$.promotion.decision")
    state = enum(promotion["evidence_state"], {"PASS", "FAIL", "NOT_EXERCISED"}, "$.promotion.evidence_state")
    close(raw, number(promotion["declared_raw_meta_score"], "$.promotion.declared_raw_meta_score", 0.0, 100.0), "$.promotion.declared_raw_meta_score")
    close(effective, number(promotion["declared_effective_meta_score"], "$.promotion.declared_effective_meta_score", 0.0, 100.0), "$.promotion.declared_effective_meta_score")
    close(cap, number(promotion["declared_score_ceiling"], "$.promotion.declared_score_ceiling", 0.0, 100.0), "$.promotion.declared_score_ceiling")
    declared_caps = [text(item, f"$.promotion.ceiling_reasons[{index}]") for index, item in enumerate(arr(promotion["ceiling_reasons"], "$.promotion.ceiling_reasons"))]
    require(declared_caps == cap_reasons, "ceiling_reasons do not match recomputed reasons")
    reasons = [text(item, f"$.promotion.reasons[{index}]") for index, item in enumerate(arr(promotion["reasons"], "$.promotion.reasons"))]
    failed = errors(target, design, architecture_score, grounding_counts, generalization_state, regression_state, controls, effective)
    if decision == "ELIGIBLE_FOR_HUMAN_ADMIT":
        require(state == "PASS", "eligible decision requires PASS evidence_state")
        require(not failed, "eligibility gates failed: " + "; ".join(failed))
    elif decision == "REJECT":
        require(state == "FAIL", "REJECT requires FAIL evidence_state")
        require(bool(failed), "REJECT requires a failed eligibility gate")
    else:
        require(bool(reasons), "HOLD requires at least one reason")

    return {
        "receipt_id": data["receipt_id"], "current_level": current,
        "target_level": target, "target_name": LEVEL_NAMES[target],
        "architecture_score": round(architecture_score, 4),
        "architecture_band": band(architecture_score),
        "grounding_score": round(grounding_score, 4),
        "generalization_score": round(generalization_score, 4),
        "regression_score": round(regression_score, 4),
        "raw_meta_score": round(raw, 4),
        "effective_meta_score": round(effective, 4),
        "score_ceiling": round(cap, 4), "ceiling_reasons": cap_reasons,
        "decision": decision, "evidence_state": state,
        "human_admit_required": True,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_meta_abstraction_eval.py <receipt.json>", file=sys.stderr)
        return 64
    try:
        data = parse(Path(argv[1]))
    except RuntimeError as exc:
        print(f"INPUT FAIL: {exc}", file=sys.stderr)
        return 64
    try:
        result = validate(data)
    except ContractError as exc:
        print(f"CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
