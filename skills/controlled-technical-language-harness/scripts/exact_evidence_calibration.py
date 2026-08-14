from __future__ import annotations

from collections import Counter
import re
from typing import Any

from exact_evidence_core import CAL_SCHEMA, PRED_SCHEMA, InputError, SHA, digest


def bool_labels(value: Any, required: list[str], label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != set(required) or not all(isinstance(value[key], bool) for key in required):
        raise InputError(f"{label} must contain exactly the required boolean labels")
    return {key: value[key] for key in required}


def evaluate_calibration(policy: dict[str, Any], policy_raw: bytes, gold: dict[str, Any], gold_raw: bytes,
                         predictions: dict[str, Any], predictions_raw: bytes) -> dict[str, Any]:
    if policy.get("schema_version") != CAL_SCHEMA or predictions.get("schema_version") != PRED_SCHEMA:
        raise InputError("invalid calibration schema_version")
    required = policy.get("required_heuristics")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        raise InputError("required_heuristics must be non-empty and unique")
    gold_id = policy.get("gold_corpus_identity", {})
    if gold_id.get("corpus_id") != gold.get("corpus_id") or gold_id.get("artifact_digest") != digest(gold_raw):
        raise InputError("policy does not bind exact gold corpus")
    if predictions.get("corpus_identity", {}).get("corpus_id") != gold.get("corpus_id") or predictions.get("corpus_identity", {}).get("artifact_digest") != digest(gold_raw):
        raise InputError("predictions do not bind exact gold corpus")
    identity = predictions.get("evaluator_identity", {})
    for key in ("evaluator_id", "version", "model_identity"):
        if not isinstance(identity.get(key), str) or not identity[key]:
            raise InputError(f"prediction evaluator {key} is absent")
    for key in ("implementation_digest", "model_digest"):
        if not isinstance(identity.get(key), str) or not SHA.fullmatch(identity[key]):
            raise InputError(f"prediction evaluator {key} is invalid")
    if re.search(r"(?:^|[-_.])(latest|current|head|rolling|newest)(?:$|[-_.])", identity["model_identity"], re.I):
        raise InputError("prediction model identity is mutable")
    mode = predictions.get("execution_mode")
    if mode not in {"FIXTURE_LABEL_REPLAY", "RECORDED_CLASSIFIER_OUTPUT"}:
        raise InputError("prediction execution_mode is invalid")

    gold_cases, prediction_cases = gold.get("cases"), predictions.get("predictions")
    if not isinstance(gold_cases, list) or not gold_cases or not isinstance(prediction_cases, list) or not prediction_cases:
        raise InputError("gold and predictions must be non-empty")
    gold_map: dict[str, dict[str, bool]] = {}
    for item in gold_cases:
        case_id = item.get("case_id") if isinstance(item, dict) else None
        if not isinstance(case_id, str) or not case_id or case_id in gold_map:
            raise InputError("gold case identities must be unique")
        gold_map[case_id] = bool_labels(item.get("labels"), required, f"gold {case_id}")
    pred_map: dict[str, dict[str, bool]] = {}
    for item in prediction_cases:
        case_id = item.get("case_id") if isinstance(item, dict) else None
        if not isinstance(case_id, str) or not case_id or case_id in pred_map:
            raise InputError("prediction case identities must be unique")
        pred_map[case_id] = bool_labels(item.get("labels"), required, f"prediction {case_id}")
    if set(gold_map) != set(pred_map):
        raise InputError("prediction case set mismatch")

    minimum = policy.get("minimum_cases_per_heuristic")
    if not isinstance(minimum, int) or minimum < 2:
        raise InputError("minimum_cases_per_heuristic must be >= 2")
    metrics: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for heuristic in required:
        pairs = [(gold_map[c][heuristic], pred_map[c][heuristic]) for c in gold_map]
        positives = sum(1 for expected, _ in pairs if expected)
        negatives = len(pairs) - positives
        if positives < minimum or negatives < minimum:
            failures.append(f"{heuristic} lacks positive or negative coverage")
        counts = Counter((expected, observed) for expected, observed in pairs)
        fp, fn = counts[(False, True)], counts[(True, False)]
        fp_rate = fp / negatives if negatives else 1.0
        fn_rate = fn / positives if positives else 1.0
        if fp_rate > policy.get("maximum_false_positive_rate", -1):
            failures.append(f"{heuristic} false-positive rate exceeds ceiling")
        if fn_rate > policy.get("maximum_false_negative_rate", -1):
            failures.append(f"{heuristic} false-negative rate exceeds ceiling")
        metrics[heuristic] = {"cases": len(pairs), "positive": positives, "negative": negatives,
                              "false_positive": fp, "false_negative": fn,
                              "false_positive_rate": fp_rate, "false_negative_rate": fn_rate}
    for boundary in policy.get("required_boundary_cases", []):
        if not isinstance(boundary, dict) or boundary.get("case_id") not in gold_map:
            failures.append("required boundary case is absent")
            continue
        heuristic = boundary.get("heuristic")
        if heuristic not in required or gold_map[boundary["case_id"]][heuristic] != boundary.get("expected"):
            failures.append(f"boundary case {boundary.get('case_id')} is not bound to expected gold label")
        elif pred_map[boundary["case_id"]][heuristic] != boundary.get("expected"):
            failures.append(f"boundary case {boundary.get('case_id')} was classified incorrectly")

    return {
        "schema_version": "controlled-language-corpus-calibration-receipt/v1",
        "evaluator_identity": identity,
        "classifier_state": "NOT_IMPLEMENTED" if mode == "FIXTURE_LABEL_REPLAY" else "EXERCISED",
        "execution_mode": mode,
        "evidence_class": "CALIBRATED_HEURISTIC",
        "admission_effect": "ADVISORY_ONLY",
        "deterministic_promotion": False,
        "policy_digest": digest(policy_raw), "gold_digest": digest(gold_raw),
        "predictions_digest": digest(predictions_raw), "metrics": metrics,
        "failures": failures, "status": "PASS" if not failures else "FAIL",
        "exit_code": 0 if not failures else 2,
    }
