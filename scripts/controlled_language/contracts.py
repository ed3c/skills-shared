from __future__ import annotations

from typing import Any

from .common import EVIDENCE, POLICY, SAFETY, digest, has_text, is_digest, reasoning_fields


def validate_standard_pack(pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if pack.get("schema_version") != "controlled-language-standard-pack-reference/v1":
        errors.append("invalid standard-pack schema_version")
    source = pack.get("source", {})
    if not is_digest(source.get("artifact_digest")):
        errors.append("standard-pack source digest is invalid")
    if not is_digest(pack.get("ruleset_digest")):
        errors.append("standard-pack ruleset digest is invalid")
    license_policy = pack.get("license_policy", {})
    if pack.get("content_mode") == "VENDORED" and license_policy.get("redistribution_allowed") is not True:
        errors.append("non-redistributable standard pack cannot use VENDORED content_mode")
    legal = license_policy.get("human_legal_review")
    if legal == "ADMITTED":
        if not has_text(license_policy.get("approval_receipt_ref")) or not is_digest(
            license_policy.get("approval_receipt_digest")
        ):
            errors.append("admitted legal review requires exact approval receipt")
    elif license_policy.get("approval_receipt_ref") is not None or license_policy.get("approval_receipt_digest") is not None:
        errors.append("non-admitted legal review cannot carry approval receipt")
    terms = pack.get("technical_terminology_policy", {})
    if terms.get("technical_name_human_admit") is not True:
        errors.append("technical names must remain Human Admit")
    if terms.get("technical_verb_human_admit") is not True:
        errors.append("technical verbs must remain Human Admit")
    if pack.get("compliance_claim_policy") != "HUMAN_ADMIT_REQUIRED":
        errors.append("official compliance claims must remain HUMAN_ADMIT_REQUIRED")
    return errors + reasoning_fields(pack)


def validate_termbase_entry(term: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if term.get("schema_version") != "controlled-language-termbase-entry/v1":
        errors.append("invalid termbase schema_version")
    if term.get("append_only") is not True:
        errors.append("termbase entry must be append_only")
    if not term.get("source_refs"):
        errors.append("termbase entry requires source_refs")
    for ref in term.get("source_refs", []):
        if not is_digest(ref.get("artifact_digest")) or not has_text(ref.get("locator")):
            errors.append("termbase source_ref is not exact")
    state = term.get("decision_state")
    review = term.get("human_review", {})
    if state == "ADMITTED":
        if term.get("approved_for_use") is not True:
            errors.append("ADMITTED term must be approved_for_use")
        if review.get("state") != "ADMITTED":
            errors.append("ADMITTED term requires Human review state ADMITTED")
        if not has_text(review.get("approval_receipt_ref")) or not is_digest(review.get("approval_receipt_digest")):
            errors.append("ADMITTED term requires exact Human receipt")
        if term.get("term_type") == "TECHNICAL_VERB" and term.get("replacement_assessment") != "NO_APPROVED_GENERAL_VERB":
            errors.append("ADMITTED technical verb requires NO_APPROVED_GENERAL_VERB assessment")
    elif term.get("approved_for_use") is True:
        errors.append(f"{state} term cannot be approved_for_use")
    if state == "SUPERSEDED" and not has_text(term.get("superseded_by")):
        errors.append("SUPERSEDED term requires superseded_by")
    return errors + reasoning_fields(term)


def validate_request(
    request: dict[str, Any],
    pack: dict[str, Any] | None = None,
    pack_raw: bytes | None = None,
    terms: dict[str, tuple[dict[str, Any], bytes]] | None = None,
) -> list[str]:
    errors: list[str] = []
    if request.get("schema_version") != "controlled-language-request/v1":
        errors.append("invalid request schema_version")
    subject = request.get("subject_identity", {})
    if not is_digest(subject.get("artifact_digest")) or not has_text(subject.get("locator")):
        errors.append("request subject identity is not exact")
    item = request.get("input", {})
    if item.get("mode") == "INLINE":
        text = item.get("text")
        if not has_text(text) or item.get("content_digest") != digest(text.encode()):
            errors.append("INLINE request digest does not match exact text bytes")
    elif item.get("mode") == "SOURCE_REF":
        if not has_text(item.get("source_ref")) or not is_digest(item.get("content_digest")):
            errors.append("SOURCE_REF request is not exact")
    else:
        errors.append("request input mode is invalid")
    if item.get("content_digest") != subject.get("artifact_digest"):
        errors.append("request subject does not match input digest")

    profile = request.get("profile_reference", {})
    if pack is not None and pack_raw is not None:
        if profile.get("pack_id") != pack.get("pack_id") or profile.get("edition") != pack.get("edition"):
            errors.append("request profile identity does not match standard pack")
        if profile.get("artifact_digest") != digest(pack_raw):
            errors.append("request profile digest does not match exact standard-pack bytes")

    referenced: set[str] = set()
    for ref in request.get("termbase_references", []):
        term_id = ref.get("term_id")
        if term_id in referenced:
            errors.append(f"duplicate termbase reference {term_id}")
        referenced.add(term_id)
        if terms is not None:
            loaded = terms.get(term_id)
            if loaded is None:
                errors.append(f"request references unavailable termbase entry {term_id}")
            elif ref.get("artifact_digest") != digest(loaded[1]):
                errors.append(f"request termbase digest mismatch for {term_id}")
    if not referenced:
        errors.append("request requires at least one termbase reference")

    privacy = request.get("privacy", {})
    classification = privacy.get("classification")
    lane = privacy.get("execution_lane")
    network = privacy.get("allow_network")
    approval = privacy.get("human_external_processing_approval")
    if lane == "LOCAL_ONLY" and network is not False:
        errors.append("LOCAL_ONLY execution must disable network")
    if classification == "RESTRICTED" and (lane != "LOCAL_ONLY" or network is not False):
        errors.append("RESTRICTED text must remain LOCAL_ONLY with network disabled")
    if lane == "EXTERNAL_APPROVED" and approval != "ADMITTED":
        errors.append("external processing requires Human approval")

    requested = request.get("requested_evidence_classes", [])
    if len(requested) != len(set(requested)) or not set(requested).issubset(EVIDENCE):
        errors.append("requested evidence classes are invalid or duplicated")
    if "DETERMINISTIC" not in requested:
        errors.append("request must include DETERMINISTIC evidence")
    if request.get("document_class") in SAFETY and "HUMAN" not in requested:
        errors.append("WARNING and CAUTION requests must include HUMAN evidence")

    repair = request.get("repair_policy", {})
    max_attempts = repair.get("max_attempts")
    if not isinstance(max_attempts, int) or not 0 <= max_attempts <= 3:
        errors.append("repair max_attempts must be in [0,3]")
    if repair.get("no_improvement_action") != "STOP":
        errors.append("repair no_improvement_action must be STOP")
    if request.get("completion_policy") != POLICY:
        errors.append("request completion policy weakens repository laws")
    return errors + reasoning_fields(request)


def validate_violation(violation: dict[str, Any], request: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if violation.get("schema_version") != "controlled-language-violation/v1":
        errors.append("invalid violation schema_version")
    span = violation.get("source_span", {})
    if not is_digest(span.get("artifact_digest")) or not is_digest(span.get("found_text_digest")):
        errors.append("violation source span is not exact")
    start, end = span.get("start"), span.get("end")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
        errors.append("violation span must satisfy 0 <= start <= end")
    if request is not None:
        if violation.get("request_id") != request.get("request_id"):
            errors.append("violation request_id mismatch")
        observed = {"artifact_digest": span.get("artifact_digest"), "locator": span.get("locator")}
        if observed != request.get("subject_identity"):
            errors.append("violation source does not bind request subject")
    if violation.get("status") == "WAIVED":
        waiver = violation.get("waiver") or {}
        if not has_text(waiver.get("human_receipt_ref")) or not is_digest(waiver.get("human_receipt_digest")):
            errors.append("WAIVED violation requires exact Human receipt")
    elif violation.get("waiver") is not None:
        errors.append("non-WAIVED violation cannot carry waiver")
    return errors + reasoning_fields(violation)
