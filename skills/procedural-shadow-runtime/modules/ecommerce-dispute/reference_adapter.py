#!/usr/bin/env python3
"""Deterministic reference adapter for the e-commerce dispute Eval family.

This is an executable fixture, not a production Agent. The LLM node is represented
by the case's structured mock output; deterministic code owns routing and writes.
"""
from __future__ import annotations

from typing import Any


def _idempotency_key(dispute_id: str, action: str, approved_amount: float) -> str:
    return f"idemp_{dispute_id}_{action}_{int(round(approved_amount * 100))}"


def _run_once(
    payload: dict[str, Any],
    mock: dict[str, Any],
    ledger: dict[str, dict[str, Any]],
    tool_calls: dict[str, int],
) -> dict[str, Any]:
    logistics = mock["logistics"]
    retry_count = 0
    if int(logistics["latency_ms"]) > 5000:
        logistics_status = "API_TIMEOUT"
        delivered = None
        retry_count = 1
    else:
        logistics_status = str(logistics["status"])
        delivered = logistics.get("delivered")

    vision_score = mock.get("vision", {}).get("score")
    decision = mock["llm"]
    action = str(decision["action"])
    approved_amount = float(decision["approved_amount"])
    confidence = float(decision["confidence"])
    reason = str(decision["reason"])

    high_value = float(payload["claimed_amount"]) > 500.0 or approved_amount > 500.0
    low_confidence = confidence < 0.80
    unusable_image = vision_score is not None and float(vision_score) < 0.0
    requires_hitl = (
        high_value
        or logistics_status == "API_TIMEOUT"
        or low_confidence
        or unusable_image
        or action == "escalate_human"
    )
    route = "HITL" if requires_hitl else "EXECUTE"
    execution_status = "pending" if requires_hitl else "failed"
    cache_hit = False
    key = _idempotency_key(str(payload["dispute_id"]), action, approved_amount)

    if not requires_hitl:
        if action == "full_refund":
            if key in ledger:
                cache_hit = True
                execution_status = str(ledger[key]["execution_status"])
            else:
                tool_calls["payment_gateway_refund"] += 1
                execution_status = "approved"
                ledger[key] = {"execution_status": execution_status}
        elif action == "reject":
            tool_calls["send_rejection_notice"] += 1
            execution_status = "rejected"
        elif action == "partial_voucher":
            tool_calls["issue_voucher"] += 1
            execution_status = "approved"

    recommendation = "none"
    if unusable_image or low_confidence:
        recommendation = "request_supplemental_evidence"

    return {
        "final": {
            "action": action,
            "approved_amount": approved_amount,
            "confidence_score": confidence,
            "reason": reason,
            "requires_hitl": requires_hitl,
            "route": route,
            "execution_status": execution_status,
            "idempotency_key": key,
            "cache_hit": cache_hit,
            "logistics_status": logistics_status,
            "logistics_delivered": delivered,
            "fabricated_delivery_state": False,
            "damage_score": vision_score,
            "recommendation": recommendation,
        },
        "trace": {
            "retry_count": retry_count,
            "total_tokens": 900,
            "latency_ms": min(int(logistics["latency_ms"]) + 650, 9000),
            "cost_usd": 0.03,
            "states": [
                "INPUT_SANITIZER_AND_CONTEXT_BUDGET",
                "EVIDENCE_GATHER",
                "STRUCTURED_LLM_ARBITRATION",
                "DETERMINISTIC_GUARDRAIL",
                "HITL_QUEUE" if requires_hitl else "IDEMPOTENT_SAFE_EXECUTION",
                "AUDIT_TRACE",
            ],
        },
    }


def _merge_trace(results: list[dict[str, Any]]) -> dict[str, Any]:
    traces = [item["trace"] for item in results]
    return {
        "retry_count": max(item["retry_count"] for item in traces),
        "total_tokens": max(item["total_tokens"] for item in traces),
        "latency_ms": max(item["latency_ms"] for item in traces),
        "cost_usd": max(item["cost_usd"] for item in traces),
        "states": sorted({state for item in traces for state in item["states"]}),
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Execute one domain case and return the adapter protocol result."""
    ledger: dict[str, dict[str, Any]] = {}
    tool_calls = {
        "payment_gateway_refund": 0,
        "issue_voucher": 0,
        "send_rejection_notice": 0,
    }

    if "variants" in case:
        variants: dict[str, Any] = {}
        runs: list[dict[str, Any]] = []
        for name, variant in case["variants"].items():
            result = _run_once(variant["input"], variant["mock"], ledger, tool_calls)
            variants[name] = result
            runs.append(result)
        return {"variants": variants, "tool_calls": tool_calls, "trace": _merge_trace(runs)}

    attempts = int(case.get("attempts", 1))
    results = [_run_once(case["input"], case["mock"], ledger, tool_calls) for _ in range(attempts)]
    if attempts > 1:
        return {"attempts": results, "tool_calls": tool_calls, "trace": _merge_trace(results)}
    return {**results[0], "tool_calls": tool_calls}
