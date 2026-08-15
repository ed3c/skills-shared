from __future__ import annotations

from collections import Counter
from typing import Any

from .common import EVIDENCE, RUN_STATES, SAFETY, digest, has_text, is_digest, reasoning_fields

FINAL_STATES = {"PASS", "FAIL", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}
CLAIM_LEVELS = {
    "MECHANISM_ONLY",
    "PROFILE_CONFORMANCE_CANDIDATE",
    "HUMAN_REVIEWED",
    "OFFICIAL_COMPLIANCE",
}
HUMAN_STATES = {"NOT_REQUIRED", "REQUIRED", "ADMITTED", "REJECTED"}
REPAIR_DECISIONS = {"REPAIR", "STOP", "VERIFIED", "HUMAN_ADMIT_REQUIRED"}
VIOLATION_STATES = {"OPEN", "REPAIRED", "WAIVED", "BLOCKED"}


def validate_receipt(
    receipt: dict[str, Any],
    request: dict[str, Any],
    request_raw: bytes,
    pack: dict[str, Any],
    pack_raw: bytes,
    terms: dict[str, tuple[dict[str, Any], bytes]],
    violations: list[dict[str, Any]] | None = None,
) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "controlled-language-receipt/v1":
        errors.append("invalid receipt schema_version")
    if not has_text(receipt.get("receipt_id")):
        errors.append("receipt_id is required")

    final = receipt.get("final_status")
    if final not in FINAL_STATES:
        errors.append("receipt final_status is invalid")
    claim = receipt.get("claim_level")
    if claim not in CLAIM_LEVELS:
        errors.append("receipt claim_level is invalid")

    req_id = receipt.get("request_identity")
    if not isinstance(req_id, dict):
        errors.append("receipt request_identity must be an object")
        req_id = {}
    if req_id.get("request_id") != request.get("request_id"):
        errors.append("receipt request_id mismatch")
    if req_id.get("artifact_digest") != digest(request_raw):
        errors.append("receipt request artifact_digest does not match exact request bytes")

    if receipt.get("subject_identity") != request.get("subject_identity"):
        errors.append("receipt subject_identity does not match request subject")
    subject_digest = request.get("subject_identity", {}).get("artifact_digest")

    profile = receipt.get("profile_identity")
    if not isinstance(profile, dict):
        errors.append("receipt profile_identity must be an object")
        profile = {}
    if profile.get("pack_id") != pack.get("pack_id") or profile.get("edition") != pack.get("edition"):
        errors.append("receipt profile identity mismatch")
    if profile.get("artifact_digest") != digest(pack_raw):
        errors.append("receipt profile digest mismatch")

    observed: dict[str, str] = {}
    for item in receipt.get("termbase_identities", []):
        if not isinstance(item, dict) or not has_text(item.get("term_id")) or not is_digest(item.get("artifact_digest")):
            errors.append("receipt termbase identity is invalid")
            continue
        term_id = item["term_id"]
        if term_id in observed:
            errors.append(f"duplicate receipt termbase identity {term_id}")
        observed[term_id] = item["artifact_digest"]
    if set(observed) != set(terms):
        errors.append("receipt termbase identity set mismatch")
    for term_id, (_, raw) in terms.items():
        if observed.get(term_id) != digest(raw):
            errors.append(f"receipt termbase digest mismatch for {term_id}")

    runs = receipt.get("evaluator_runs")
    if not isinstance(runs, list) or not runs:
        errors.append("receipt evaluator_runs must be a non-empty list")
        runs = []
    by_class: dict[str, list[str]] = {key: [] for key in EVIDENCE}
    seen: set[str] = set()
    deterministic_failed = False
    for run in runs:
        if not isinstance(run, dict):
            errors.append("receipt evaluator run must be an object")
            continue
        evaluator_id = run.get("evaluator_id")
        if not has_text(evaluator_id) or not has_text(run.get("version")):
            errors.append("evaluator run requires id and version")
            continue
        if evaluator_id in seen:
            errors.append(f"duplicate evaluator_id {evaluator_id}")
        seen.add(evaluator_id)
        evidence = run.get("evidence_class")
        status = run.get("status")
        if evidence not in EVIDENCE or status not in RUN_STATES:
            errors.append(f"invalid evaluator run {evaluator_id}")
            continue
        by_class[evidence].append(status)
        if not is_digest(run.get("input_digest")) or run.get("input_digest") != subject_digest:
            errors.append(f"evaluator {evaluator_id} input_digest does not match exact subject")
        if not is_digest(run.get("output_digest")):
            errors.append(f"evaluator {evaluator_id} output_digest is invalid")
        if evidence == "DETERMINISTIC":
            exit_code = run.get("exit_code")
            if status == "PASS" and exit_code != 0:
                errors.append(f"deterministic evaluator {evaluator_id} PASS requires exit_code 0")
            if status == "FAIL" and (not isinstance(exit_code, int) or exit_code == 0):
                errors.append(f"deterministic evaluator {evaluator_id} FAIL requires nonzero exit_code")
            if status != "PASS" or exit_code != 0:
                deterministic_failed = True
        elif run.get("exit_code") is not None:
            errors.append(f"non-deterministic evaluator {evaluator_id} cannot assert exit_code")
        if evidence == "CALIBRATED_HEURISTIC":
            if not has_text(run.get("calibration_ref")):
                errors.append(f"calibrated evaluator {evaluator_id} requires calibration_ref")
        elif run.get("calibration_ref") is not None:
            errors.append(f"non-calibrated evaluator {evaluator_id} cannot carry calibration_ref")
        if evidence == "HUMAN":
            if status == "PASS" and not has_text(run.get("human_receipt_ref")):
                errors.append(f"Human evaluator {evaluator_id} requires receipt")
        elif run.get("human_receipt_ref") is not None:
            errors.append(f"non-Human evaluator {evaluator_id} cannot carry human_receipt_ref")

    for evidence in request.get("requested_evidence_classes", []):
        states = by_class[evidence]
        if not states:
            errors.append(f"requested evidence class {evidence} has no evaluator run")
        elif final == "PASS" and any(state != "PASS" for state in states):
            errors.append(f"requested evidence class {evidence} is not fully PASS")
    if final == "PASS" and deterministic_failed:
        errors.append("deterministic failure or nonzero exit vetoes final PASS")
    if final == "PASS" and receipt.get("exact_subject_fresh") is not True:
        errors.append("stale or unproven subject cannot receive final PASS")

    summary = receipt.get("violations")
    if not isinstance(summary, dict):
        errors.append("receipt violations must be an object")
        summary = {}
    count_names = ("open_count", "repaired_count", "blocked_count", "waived_count")
    for name in count_names:
        if not isinstance(summary.get(name), int) or summary.get(name, -1) < 0:
            errors.append(f"receipt {name} must be a non-negative integer")
    declared_ids = summary.get("violation_ids")
    if not isinstance(declared_ids, list) or len(declared_ids) != len(set(declared_ids)) or not all(
        has_text(item) for item in declared_ids
    ):
        errors.append("receipt violation_ids must be a unique string array")
        declared_ids = []
    counts = sum(summary.get(name, 0) for name in count_names if isinstance(summary.get(name), int))
    if counts != len(declared_ids):
        errors.append("violation counts do not match violation_ids")

    if violations is not None:
        actual_ids: list[str] = []
        actual_states: list[str] = []
        for violation in violations:
            violation_id = violation.get("violation_id")
            state = violation.get("status")
            if not has_text(violation_id) or state not in VIOLATION_STATES:
                errors.append("loaded violation identity or state is invalid")
                continue
            actual_ids.append(violation_id)
            actual_states.append(state)
        if len(actual_ids) != len(set(actual_ids)):
            errors.append("duplicate loaded violation_id")
        if set(declared_ids) != set(actual_ids):
            errors.append("receipt violation identity set mismatch")
        actual_counts = Counter(actual_states)
        expected_counts = {
            "OPEN": summary.get("open_count"),
            "REPAIRED": summary.get("repaired_count"),
            "BLOCKED": summary.get("blocked_count"),
            "WAIVED": summary.get("waived_count"),
        }
        for state, expected in expected_counts.items():
            if actual_counts[state] != expected:
                errors.append(f"receipt {state} violation count mismatch")

    if final == "PASS" and (summary.get("open_count", 0) or summary.get("blocked_count", 0)):
        errors.append("open or blocked violations veto final PASS")

    max_attempts = request.get("repair_policy", {}).get("max_attempts", 0)
    allowed = set(request.get("repair_policy", {}).get("allowed_repair_codes", []))
    history = receipt.get("repair_history")
    if not isinstance(history, list):
        errors.append("receipt repair_history must be an array")
        history = []
    stopped = False
    for index, attempt in enumerate(history, start=1):
        if not isinstance(attempt, dict):
            errors.append("repair history item must be an object")
            continue
        if attempt.get("attempt_index") != index or index > max_attempts:
            errors.append("repair attempt index or budget is invalid")
        if stopped:
            errors.append("repair history continues after terminal decision")
        failed = attempt.get("failed_constraint_ids")
        if not isinstance(failed, list) or not failed or not all(has_text(item) for item in failed):
            errors.append("repair attempt requires failed_constraint_ids")
        if attempt.get("selected_repair") not in allowed:
            errors.append("repair is not allowlisted")
        expected, actual = attempt.get("expected_delta"), attempt.get("actual_delta")
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            errors.append("repair attempt requires expected and actual delta objects")
            expected, actual = {}, {}
        if not has_text(expected.get("metric")) or expected.get("metric") != actual.get("metric"):
            errors.append("repair delta metrics do not match")
        if not isinstance(expected.get("before"), (int, float)) or not isinstance(expected.get("target"), (int, float)):
            errors.append("repair expected delta values must be numeric")
        if not isinstance(actual.get("after"), (int, float)) or not isinstance(actual.get("improved"), bool):
            errors.append("repair actual delta values are invalid")
        decision = attempt.get("decision")
        if decision not in REPAIR_DECISIONS:
            errors.append("repair decision is invalid")
        if actual.get("improved") is False:
            if decision != "STOP":
                errors.append("measured no improvement requires STOP")
            stopped = True
        elif decision in {"STOP", "VERIFIED", "HUMAN_ADMIT_REQUIRED"}:
            stopped = True
    if final == "PASS" and history:
        if history[-1].get("actual_delta", {}).get("improved") is not True:
            errors.append("final PASS after repair requires measured improvement")
        if history[-1].get("decision") != "VERIFIED":
            errors.append("final PASS after repair requires terminal VERIFIED decision")

    human = receipt.get("human_review")
    if not isinstance(human, dict):
        errors.append("receipt human_review must be an object")
        human = {}
    if human.get("state") not in HUMAN_STATES:
        errors.append("receipt Human review state is invalid")
    if human.get("state") == "ADMITTED":
        if not has_text(human.get("receipt_ref")) or not is_digest(human.get("receipt_digest")):
            errors.append("ADMITTED Human review requires exact receipt")
    elif human.get("receipt_ref") is not None or human.get("receipt_digest") is not None:
        errors.append("non-admitted Human review cannot carry receipt")
    if request.get("document_class") in SAFETY and final == "PASS" and human.get("state") != "ADMITTED":
        errors.append("WARNING or CAUTION cannot PASS without admitted Human review")

    official = receipt.get("official_compliance_receipt")
    if claim == "HUMAN_REVIEWED" and human.get("state") != "ADMITTED":
        errors.append("HUMAN_REVIEWED claim requires admitted Human review")
    if claim == "OFFICIAL_COMPLIANCE":
        if human.get("state") != "ADMITTED":
            errors.append("OFFICIAL_COMPLIANCE requires admitted Human review")
        if not isinstance(official, dict):
            errors.append("OFFICIAL_COMPLIANCE requires official_compliance_receipt")
        elif not has_text(official.get("human_receipt_ref")) or not is_digest(official.get("human_receipt_digest")):
            errors.append("official compliance receipt is not exact")
    elif official is not None:
        errors.append("non-official claim cannot carry official compliance receipt")
    return errors + reasoning_fields(receipt)
