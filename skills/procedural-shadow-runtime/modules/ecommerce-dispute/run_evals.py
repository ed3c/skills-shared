#!/usr/bin/env python3
"""Deterministic domain Eval runner for the e-commerce dispute adapter protocol."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "ecommerce-dispute-eval-receipt/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class EvalError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise EvalError(message)


def parse_args(argv: list[str]) -> dict[str, str]:
    if len(argv) != 13:
        raise RuntimeError(
            "usage: run_evals.py --adapter PATH --cases PATH --repository OWNER/REPO "
            "--subject-sha SHA40 --subject-digest SHA256 --output PATH"
        )
    expected = ["--adapter", "--cases", "--repository", "--subject-sha", "--subject-digest", "--output"]
    result: dict[str, str] = {}
    for index, flag in enumerate(expected):
        actual = argv[1 + index * 2]
        if actual != flag:
            raise RuntimeError(f"expected {flag}, got {actual}")
        value = argv[2 + index * 2]
        if not value:
            raise RuntimeError(f"{flag} requires a value")
        result[flag[2:].replace("-", "_")] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return data


def load_adapter(path: Path) -> Any:
    try:
        spec = importlib.util.spec_from_file_location("ecommerce_dispute_candidate_adapter", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load adapter spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (OSError, ImportError, SyntaxError) as exc:
        raise RuntimeError(f"cannot import adapter {path}: {exc}") from exc
    if not callable(getattr(module, "run_case", None)):
        raise RuntimeError("adapter must expose run_case(case: dict) -> dict")
    return module


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RuntimeError(f"cannot hash {path}: {exc}") from exc


def resolve_path(value: Any, dotted: str) -> Any:
    current = value
    for segment in dotted.split("."):
        if isinstance(current, list):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError) as exc:
                raise EvalError(f"path {dotted} cannot resolve list index {segment}") from exc
        elif isinstance(current, dict):
            require(segment in current, f"path {dotted} missing key {segment}")
            current = current[segment]
        else:
            raise EvalError(f"path {dotted} crosses non-container at {segment}")
    return current


def check_assertion(result: dict[str, Any], assertion: dict[str, Any]) -> tuple[bool, Any, Any]:
    allowed = {"assertion_id", "path", "operator", "safety", "expected", "expected_path"}
    unknown = set(assertion) - allowed
    require(not unknown, f"assertion has unknown keys: {sorted(unknown)}")
    assertion_id = assertion.get("assertion_id")
    require(isinstance(assertion_id, str) and assertion_id, "assertion_id must be non-empty")
    path = assertion.get("path")
    require(isinstance(path, str) and path, f"{assertion_id}: path must be non-empty")
    operator = assertion.get("operator")
    require(operator in {"eq", "in", "lt", "lte", "contains_all", "same_as"}, f"{assertion_id}: unsupported operator")
    actual = resolve_path(result, path)

    if operator == "same_as":
        expected_path = assertion.get("expected_path")
        require(isinstance(expected_path, str) and expected_path, f"{assertion_id}: expected_path required")
        expected = resolve_path(result, expected_path)
        return actual == expected, actual, expected

    require("expected" in assertion, f"{assertion_id}: expected required")
    expected = assertion["expected"]
    if operator == "eq":
        passed = actual == expected
    elif operator == "in":
        require(isinstance(expected, list), f"{assertion_id}: expected must be a list for in")
        passed = actual in expected
    elif operator == "lt":
        passed = float(actual) < float(expected)
    elif operator == "lte":
        passed = float(actual) <= float(expected)
    else:
        require(isinstance(actual, str) and isinstance(expected, list), f"{assertion_id}: contains_all requires string actual and list expected")
        lowered = actual.lower()
        passed = all(str(item).lower() in lowered for item in expected)
    return passed, actual, expected


def validate_cases(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(data.get("schema") == "ecommerce-dispute-evals/v1", "cases schema mismatch")
    family_id = data.get("family_id")
    require(isinstance(family_id, str) and family_id, "family_id missing")
    constraints = data.get("constraints")
    require(isinstance(constraints, dict), "constraints must be an object")
    required_constraints = {
        "hitl_above_usd",
        "logistics_timeout_ms",
        "max_tokens",
        "max_latency_ms",
        "max_cost_usd",
        "low_confidence_threshold",
    }
    require(set(constraints) == required_constraints, "constraints keys mismatch")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 6, "exactly six canonical cases are required")
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    require(ids == ["EC-01", "EC-02", "EC-03", "EC-04", "EC-05", "EC-06"], "canonical case IDs/order mismatch")
    return cases, constraints


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        adapter_path = Path(args["adapter"]).resolve()
        cases_path = Path(args["cases"]).resolve()
        output_path = Path(args["output"]).resolve()
        repository = args["repository"]
        subject_sha = args["subject_sha"]
        subject_digest = args["subject_digest"]
        if HEX40.fullmatch(subject_sha) is None:
            raise RuntimeError("--subject-sha must be 40 lowercase hex characters")
        if HEX64.fullmatch(subject_digest) is None:
            raise RuntimeError("--subject-digest must be 64 lowercase hex characters")
        cases_data = load_json(cases_path)
        cases, constraints = validate_cases(cases_data)
        adapter = load_adapter(adapter_path)
        adapter_hash = sha256(adapter_path)
        cases_hash = sha256(cases_path)
    except (RuntimeError, EvalError) as exc:
        print(f"INPUT FAIL: {exc}", file=sys.stderr)
        return 64

    case_receipts: list[dict[str, Any]] = []
    safety_failures = 0
    assertion_failures = 0
    try:
        for case in cases:
            case_id = str(case["case_id"])
            result = adapter.run_case(case)
            require(isinstance(result, dict), f"{case_id}: adapter result must be an object")
            trace = resolve_path(result, "trace")
            require(isinstance(trace, dict), f"{case_id}: trace must be an object")
            global_assertions = [
                {
                    "assertion_id": f"{case_id}-TOKEN-BUDGET",
                    "path": "trace.total_tokens",
                    "operator": "lte",
                    "expected": constraints["max_tokens"],
                    "safety": False,
                },
                {
                    "assertion_id": f"{case_id}-LATENCY-BUDGET",
                    "path": "trace.latency_ms",
                    "operator": "lte",
                    "expected": constraints["max_latency_ms"],
                    "safety": False,
                },
                {
                    "assertion_id": f"{case_id}-COST-BUDGET",
                    "path": "trace.cost_usd",
                    "operator": "lte",
                    "expected": constraints["max_cost_usd"],
                    "safety": False,
                },
            ]
            assertions = list(case.get("assertions", [])) + global_assertions
            results: list[dict[str, Any]] = []
            for assertion in assertions:
                passed, actual, expected = check_assertion(result, assertion)
                safety = bool(assertion.get("safety", False))
                if not passed:
                    assertion_failures += 1
                    if safety:
                        safety_failures += 1
                results.append(
                    {
                        "assertion_id": assertion["assertion_id"],
                        "passed": passed,
                        "safety": safety,
                        "actual": actual,
                        "expected": expected,
                    }
                )
            case_receipts.append(
                {
                    "case_id": case_id,
                    "category": case["category"],
                    "passed": all(item["passed"] for item in results),
                    "assertions": results,
                    "trace": trace,
                }
            )
    except Exception as exc:
        print(f"CONTRACT FAIL: adapter execution failed: {exc}", file=sys.stderr)
        return 2

    execution_state = "PASS" if assertion_failures == 0 else "FAIL"
    receipt = {
        "schema": SCHEMA,
        "family_id": cases_data["family_id"],
        "subject": {
            "repository": repository,
            "current_sha": subject_sha,
            "subject_digest": subject_digest,
        },
        "adapter": {
            "path": str(adapter_path),
            "content_sha256": adapter_hash,
        },
        "dataset": {
            "path": str(cases_path),
            "content_sha256": cases_hash,
            "case_count": len(cases),
        },
        "case_receipts": case_receipts,
        "summary": {
            "execution_state": execution_state,
            "assertion_failures": assertion_failures,
            "safety_failures": safety_failures,
            "semantic_judge_state": "NOT_EXERCISED",
        },
    }
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"INPUT FAIL: cannot write {output_path}: {exc}", file=sys.stderr)
        return 64

    if assertion_failures:
        print(f"CONTRACT FAIL: assertions={assertion_failures} safety={safety_failures}", file=sys.stderr)
        return 2
    print(json.dumps(receipt["summary"], sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
