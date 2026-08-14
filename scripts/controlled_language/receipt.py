from __future__ import annotations

from typing import Any

from .common import EVIDENCE, RUN_STATES, SAFETY, digest, has_text, is_digest, reasoning_fields


def validate_receipt(
    receipt: dict[str, Any],
    request: dict[str, Any],
    request_raw: bytes,
    pack: dict[str, Any],
    pack_raw: bytes,
    terms: dict[str, tuple[dict[str, Any], bytes]],
) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "controlled-language-receipt/v1":
        errors.append("invalid receipt schema_version")
    req_id = receipt.get("request_identity", {})
    if req_id.get("request_id") != request.get("request_id"):
        errors.append("receipt request_id mismatch")
    if req_id.get("artifact_digest") != digest(request_raw):
        errors.append("receipt request artifact_digest does not match exact request bytes")
    if receipt.get("subject_identity") != request.get("subject_identity"):
        errors.append("receipt subject_identity does not match request subject")
    profile = receipt.get("profile_identity", {})
    if profile.get("pack_id") != pack.get("pack_id") or profile.get("edition") != pack.get("edition"):
        errors.append("receipt profile identity mismatch")
    if profile.get("artifact_digest") != digest(pack_raw):
        errors.append("receipt profile digest mismatch")

    observed = {item.get("term_id"): item.get("artifact_digest") for item in receipt.get("termbase_identities", [])}
    if set(observed) != set(terms):
        errors.append("receipt termbase identity set mismatch")
    for term_id, (_, raw) in terms.items():
        if observed.get(term_id) != digest(raw):
            errors.append(f"receipt termbase digest mismatch for {term_id}")

    final = receipt.get("final_status")
    by_class: dict[str, list[str]] = {key: [] for key in EVIDENCE}
    seen: set[str] = set()
    deterministic_failed = False
    for run in receipt.get("evaluator_runs", []):
        evaluator_id = run.get("evaluator_id")
        if evaluator_id in seen:
            errors.append(f"duplicate evaluator_id {evaluator_id}")
        seen.add(evaluator_id)
        evidence = run.get("evidence_class")
        status = run.get("status")
        if evidence not in EVIDENCE or status not in RUN_STATES:
            errors.append(f"invalid evaluator run {evaluator_id}")
            continue
        by_class[evidence].append(status)
        if evidence == "DETERMINISTIC":
            if status != "PASS" or run.get("exit_code") != 0:
                deterministic_failed = True
        elif run.get("exit_code") is not None:
            errors.append(f"non-deterministic evaluator {evaluator_id} cannot assert exit_code")
        if evidence == "CALIBRATED_HEURISTIC" and not has_text(run.get("calibration_ref")):
            errors.append(f"calibrated evaluator {evaluator_id} requires calibration_ref")
        if evidence == "HUMAN" and status == "PASS" and not has_text(run.get("human_receipt_ref")):
            errors.append(f"Human evaluator {evaluator_id} requires receipt")

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

    violations = receipt.get("violations", {})
    counts = sum(violations.get(name, 0) for name in ("open_count", "blocked_count", "waived_count"))
    if counts != len(violations.get("violation_ids", [])):
        errors.append("violation counts do not match violation_ids")
    if final == "PASS" and (violations.get("open_count", 0) or violations.get("blocked_count", 0)):
        errors.append("open or blocked violations veto final PASS")

    max_attempts = request.get("repair_policy", {}).get("max_attempts", 0)
    allowed = set(request.get("repair_policy", {}).get("allowed_repair_codes", []))
    stopped = False
    for index, attempt in enumerate(receipt.get("repair_history", []), start=1):
        if attempt.get("attempt_index") != index or index > max_attempts:
            errors.append("repair attempt index or budget is invalid")
        if stopped:
            errors.append("repair history continues after STOP")
        if attempt.get("selected_repair") not in allowed:
            errors.append("repair is not allowlisted")
        expected, actual = attempt.get("expected_delta", {}), attempt.get("actual_delta", {})
        if expected.get("metric") != actual.get("metric"):
            errors.append("repair delta metrics do not match")
        if actual.get("improved") is False:
            if attempt.get("decision") != "STOP":
                errors.append("measured no improvement requires STOP")
            stopped = True
        elif attempt.get("decision") in {"STOP", "VERIFIED", "HUMAN_ADMIT_REQUIRED"}:
            stopped = True
    history = receipt.get("repair_history", [])
    if final == "PASS" and history and history[-1]["actual_delta"].get("improved") is not True:
        errors.append("final PASS after repair requires measured improvement")

    human = receipt.get("human_review", {})
    if human.get("state") == "ADMITTED":
        if not has_text(human.get("receipt_ref")) or not is_digest(human.get("receipt_digest")):
            errors.append("ADMITTED Human review requires exact receipt")
    elif human.get("receipt_ref") is not None or human.get("receipt_digest") is not None:
        errors.append("non-admitted Human review cannot carry receipt")
    if request.get("document_class") in SAFETY and final == "PASS" and human.get("state") != "ADMITTED":
        errors.append("WARNING or CAUTION cannot PASS without admitted Human review")

    claim = receipt.get("claim_level")
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
