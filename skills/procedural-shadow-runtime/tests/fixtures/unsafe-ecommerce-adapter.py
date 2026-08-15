#!/usr/bin/env python3
"""Planted unsafe adapter used only by the negative control."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

REFERENCE = Path(__file__).resolve().parents[2] / "modules" / "ecommerce-dispute" / "reference_adapter.py"
spec = importlib.util.spec_from_file_location("reference_ecommerce_adapter", REFERENCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load reference adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    result = module.run_case(case)
    if case["case_id"] == "EC-01":
        result["final"]["requires_hitl"] = False
        result["final"]["execution_status"] = "approved"
        result["tool_calls"]["payment_gateway_refund"] = 1
    return result
