from __future__ import annotations

from typing import Any

from .common import (
    EVIDENCE,
    POLICY,
    SAFETY,
    digest,
    has_text,
    is_digest,
    is_portable_path,
    reasoning_fields,
)

PACK_SOURCE_CLASSES = {"SOURCE_PROPOSAL", "OFFICIAL_STANDARD", "PROJECT_POLICY", "FIXTURE"}
PACK_PROFILE_TYPES = {"CONTROLLED_LANGUAGE", "PROJECT_STYLE", "REGULATORY_PROFILE"}
PACK_CONTENT_MODES = {"REFERENCE_ONLY", "RUNTIME_INJECTED", "VENDORED"}
LICENSE_CLASSES = {"PUBLIC", "RESTRICTED", "PROPRIETARY", "UNKNOWN"}
LEGAL_STATES = {"NOT_REQUIRED", "REQUIRED", "ADMITTED"}
TERM_TYPES = {"TECHNICAL_NAME", "TECHNICAL_VERB"}
TERM_STATES = {"CANDIDATE", "VERIFIED", "ADMITTED", "SUPERSEDED", "REVOKED"}
TERM_REVIEW_STATES = {"NOT_REQUESTED", "REQUIRED", "ADMITTED", "REJECTED"}
TERM_POS = {"NOUN", "PROPN", "VERB"}
TERM_EVIDENCE = {"DETERMINISTIC", "SEMANTIC", "HUMAN"}
DOCUMENT_CLASSES = {
    "PROCEDURAL",
    "DESCRIPTIVE",
    "WARNING",
    "CAUTION",
    "AGENT_PLAN",
    "S1000D_XML",
    "DITA_XML",
}
OPERATIONS = {"AUDIT", "REWRITE_CANDIDATE", "AUDIT_AND_REWRITE"}
PRIVACY_CLASSES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
EXECUTION_LANES = {"LOCAL_ONLY", "PRIVATE_ENDPOINT", "EXTERNAL_APPROVED"}
EXTERNAL_APPROVAL_STATES = {"NOT_REQUIRED", "REQUIRED", "ADMITTED"}
REPAIR_CODES = {
    "SPLIT_ACTION",
    "REPLACE_UNAPPROVED_WORD",
    "CLARIFY_REFERENCE",
    "REWRITE_NOUN_CLUSTER",
    "PRESERVE_WARNING_ORDER",
}
VIOLATION_EVIDENCE = EVIDENCE
VIOLATION_SEVERITIES = {"ERROR", "WARNING", "INFO", "HUMAN_REVIEW"}
VIOLATION_STATES = {"OPEN", "REPAIRED", "WAIVED", "BLOCKED"}


def _string_list(value: Any, allowed: set[str] | None = None) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if len(value) != len(set(value)):
        return False
    if not all(has_text(item) for item in value):
        return False
    return allowed is None or set(value).issubset(allowed)


def validate_standard_pack(pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if pack.get("schema_version") != "controlled-language-standard-pack-reference/v1":
        errors.append("invalid standard-pack schema_version")
    for field in ("pack_id", "display_name", "edition"):
        if not has_text(pack.get(field)):
            errors.append(f"standard-pack {field} is required")
    if pack.get("profile_type") not in PACK_PROFILE_TYPES:
        errors.append("standard-pack profile_type is invalid")
    if pack.get("content_mode") not in PACK_CONTENT_MODES:
        errors.append("standard-pack content_mode is invalid")

    source = pack.get("source")
    if not isinstance(source, dict):
        errors.append("standard-pack source must be an object")
        source = {}
    if source.get("classification") not in PACK_SOURCE_CLASSES:
        errors.append("standard-pack source classification is invalid")
    if not has_text(source.get("authority")) or not has_text(source.get("locator")):
        errors.append("standard-pack source authority and locator are required")
    if not is_digest(source.get("artifact_digest")):
        errors.append("standard-pack source digest is invalid")
    if not is_digest(pack.get("ruleset_digest")):
        errors.append("standard-pack ruleset digest is invalid")

    vocabulary = pack.get("approved_vocabulary_ref")
    if vocabulary is not None:
        if not isinstance(vocabulary, dict) or not has_text(vocabulary.get("locator")) or not is_digest(
            vocabulary.get("artifact_digest")
        ):
            errors.append("approved vocabulary reference is not exact")

    license_policy = pack.get("license_policy")
    if not isinstance(license_policy, dict):
        errors.append("standard-pack license_policy must be an object")
        license_policy = {}
    if license_policy.get("classification") not in LICENSE_CLASSES:
        errors.append("standard-pack license classification is invalid")
    if not isinstance(license_policy.get("redistribution_allowed"), bool):
        errors.append("standard-pack redistribution_allowed must be boolean")
    legal = license_policy.get("human_legal_review")
    if legal not in LEGAL_STATES:
        errors.append("standard-pack legal review state is invalid")
    if pack.get("content_mode") == "VENDORED" and license_policy.get("redistribution_allowed") is not True:
        errors.append("non-redistributable standard pack cannot use VENDORED content_mode")
    if legal == "ADMITTED":
        if not has_text(license_policy.get("approval_receipt_ref")) or not is_digest(
            license_policy.get("approval_receipt_digest")
        ):
            errors.append("admitted legal review requires exact approval receipt")
    elif license_policy.get("approval_receipt_ref") is not None or license_policy.get("approval_receipt_digest") is not None:
        errors.append("non-admitted legal review cannot carry approval receipt")

    terms = pack.get("technical_terminology_policy")
    if not isinstance(terms, dict):
        errors.append("standard-pack technical_terminology_policy must be an object")
        terms = {}
    if not isinstance(terms.get("project_termbase_required"), bool):
        errors.append("project_termbase_required must be boolean")
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
    if not has_text(term.get("term_id")) or not term["term_id"].startswith("TERM-"):
        errors.append("termbase term_id must start with TERM-")
    for field in ("project_scope", "term", "definition"):
        if not has_text(term.get(field)):
            errors.append(f"termbase {field} is required")
    term_type = term.get("term_type")
    if term_type not in TERM_TYPES:
        errors.append("termbase term_type is invalid")
    positions = term.get("allowed_parts_of_speech")
    if not _string_list(positions, TERM_POS):
        errors.append("termbase allowed_parts_of_speech is invalid")
    elif term_type == "TECHNICAL_NAME" and not set(positions).issubset({"NOUN", "PROPN"}):
        errors.append("technical names can use only NOUN or PROPN")
    elif term_type == "TECHNICAL_VERB" and set(positions) != {"VERB"}:
        errors.append("technical verbs must use only VERB")
    if term.get("append_only") is not True:
        errors.append("termbase entry must be append_only")

    refs = term.get("source_refs")
    if not isinstance(refs, list) or not refs:
        errors.append("termbase entry requires source_refs")
        refs = []
    for ref in refs:
        if not isinstance(ref, dict):
            errors.append("termbase source_ref must be an object")
            continue
        if (
            not is_digest(ref.get("artifact_digest"))
            or not has_text(ref.get("locator"))
            or ref.get("evidence_class") not in TERM_EVIDENCE
        ):
            errors.append("termbase source_ref is not exact")

    state = term.get("decision_state")
    if state not in TERM_STATES:
        errors.append("termbase decision_state is invalid")
    if not isinstance(term.get("approved_for_use"), bool):
        errors.append("termbase approved_for_use must be boolean")
    if term.get("replacement_assessment") not in {
        "NOT_APPLICABLE",
        "NOT_EVALUATED",
        "NO_APPROVED_GENERAL_VERB",
        "REPLACEMENT_AVAILABLE",
    }:
        errors.append("termbase replacement_assessment is invalid")

    review = term.get("human_review")
    if not isinstance(review, dict):
        errors.append("termbase human_review must be an object")
        review = {}
    if review.get("state") not in TERM_REVIEW_STATES:
        errors.append("termbase Human review state is invalid")

    if state == "ADMITTED":
        if term.get("approved_for_use") is not True:
            errors.append("ADMITTED term must be approved_for_use")
        if review.get("state") != "ADMITTED":
            errors.append("ADMITTED term requires Human review state ADMITTED")
        if not has_text(review.get("approval_receipt_ref")) or not is_digest(review.get("approval_receipt_digest")):
            errors.append("ADMITTED term requires exact Human receipt")
        if term_type == "TECHNICAL_VERB" and term.get("replacement_assessment") != "NO_APPROVED_GENERAL_VERB":
            errors.append("ADMITTED technical verb requires NO_APPROVED_GENERAL_VERB assessment")
    elif term.get("approved_for_use") is True:
        errors.append(f"{state} term cannot be approved_for_use")
    if state in {"SUPERSEDED", "REVOKED"} and term.get("approved_for_use") is True:
        errors.append(f"{state} term cannot remain approved_for_use")

    supersedes = term.get("supersedes")
    if not isinstance(supersedes, list) or len(supersedes) != len(set(supersedes)) or not all(
        has_text(item) for item in supersedes
    ):
        errors.append("termbase supersedes must be a unique string array")
    if state == "SUPERSEDED" and not has_text(term.get("superseded_by")):
        errors.append("SUPERSEDED term requires superseded_by")
    elif state != "SUPERSEDED" and term.get("superseded_by") is not None:
        errors.append("only SUPERSEDED term can declare superseded_by")
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
    if not has_text(request.get("request_id")):
        errors.append("request_id is required")
    if request.get("document_class") not in DOCUMENT_CLASSES:
        errors.append("request document_class is invalid")
    if request.get("operation") not in OPERATIONS:
        errors.append("request operation is invalid")

    subject = request.get("subject_identity")
    if not isinstance(subject, dict):
        errors.append("request subject_identity must be an object")
        subject = {}
    if not is_digest(subject.get("artifact_digest")) or not has_text(subject.get("locator")):
        errors.append("request subject identity is not exact")

    item = request.get("input")
    if not isinstance(item, dict):
        errors.append("request input must be an object")
        item = {}
    if item.get("mode") == "INLINE":
        text = item.get("text")
        if not has_text(text) or item.get("content_digest") != digest(text.encode()):
            errors.append("INLINE request digest does not match exact text bytes")
    elif item.get("mode") == "SOURCE_REF":
        if not is_portable_path(item.get("source_ref")) or not is_digest(item.get("content_digest")):
            errors.append("SOURCE_REF request is not exact or portable")
    else:
        errors.append("request input mode is invalid")
    if item.get("content_digest") != subject.get("artifact_digest"):
        errors.append("request subject does not match input digest")

    profile = request.get("profile_reference")
    if not isinstance(profile, dict):
        errors.append("request profile_reference must be an object")
        profile = {}
    if not is_portable_path(profile.get("path")):
        errors.append("request profile path must be repository-relative")
    if not has_text(profile.get("pack_id")) or not has_text(profile.get("edition")) or not is_digest(
        profile.get("artifact_digest")
    ):
        errors.append("request profile reference is incomplete")
    if pack is not None and pack_raw is not None:
        if profile.get("pack_id") != pack.get("pack_id") or profile.get("edition") != pack.get("edition"):
            errors.append("request profile identity does not match standard pack")
        if profile.get("artifact_digest") != digest(pack_raw):
            errors.append("request profile digest does not match exact standard-pack bytes")

    term_refs = request.get("termbase_references")
    if not isinstance(term_refs, list) or not term_refs:
        errors.append("request requires at least one termbase reference")
        term_refs = []
    referenced: set[str] = set()
    for ref in term_refs:
        if not isinstance(ref, dict):
            errors.append("request termbase reference must be an object")
            continue
        term_id = ref.get("term_id")
        if not has_text(term_id):
            errors.append("request termbase term_id is required")
            continue
        if not is_portable_path(ref.get("path")) or not is_digest(ref.get("artifact_digest")):
            errors.append(f"request termbase reference {term_id} is not exact or portable")
        if term_id in referenced:
            errors.append(f"duplicate termbase reference {term_id}")
        referenced.add(term_id)
        if terms is not None:
            loaded = terms.get(term_id)
            if loaded is None:
                errors.append(f"request references unavailable termbase entry {term_id}")
            elif ref.get("artifact_digest") != digest(loaded[1]):
                errors.append(f"request termbase digest mismatch for {term_id}")

    privacy = request.get("privacy")
    if not isinstance(privacy, dict):
        errors.append("request privacy must be an object")
        privacy = {}
    classification = privacy.get("classification")
    lane = privacy.get("execution_lane")
    network = privacy.get("allow_network")
    approval = privacy.get("human_external_processing_approval")
    if classification not in PRIVACY_CLASSES:
        errors.append("request privacy classification is invalid")
    if lane not in EXECUTION_LANES:
        errors.append("request execution lane is invalid")
    if not isinstance(network, bool):
        errors.append("request allow_network must be boolean")
    if approval not in EXTERNAL_APPROVAL_STATES:
        errors.append("request external-processing approval state is invalid")
    if lane == "LOCAL_ONLY" and network is not False:
        errors.append("LOCAL_ONLY execution must disable network")
    if classification == "RESTRICTED" and (lane != "LOCAL_ONLY" or network is not False):
        errors.append("RESTRICTED text must remain LOCAL_ONLY with network disabled")
    if lane == "EXTERNAL_APPROVED" and approval != "ADMITTED":
        errors.append("external processing requires Human approval")

    requested = request.get("requested_evidence_classes")
    if not _string_list(requested, EVIDENCE):
        errors.append("requested evidence classes are invalid or duplicated")
        requested = []
    if "DETERMINISTIC" not in requested:
        errors.append("request must include DETERMINISTIC evidence")
    if request.get("document_class") in SAFETY and "HUMAN" not in requested:
        errors.append("WARNING and CAUTION requests must include HUMAN evidence")

    repair = request.get("repair_policy")
    if not isinstance(repair, dict):
        errors.append("request repair_policy must be an object")
        repair = {}
    max_attempts = repair.get("max_attempts")
    if not isinstance(max_attempts, int) or not 0 <= max_attempts <= 3:
        errors.append("repair max_attempts must be in [0,3]")
    codes = repair.get("allowed_repair_codes")
    if not isinstance(codes, list) or len(codes) != len(set(codes)) or not set(codes).issubset(REPAIR_CODES):
        errors.append("repair allowed_repair_codes are invalid or duplicated")
    if repair.get("no_improvement_action") != "STOP":
        errors.append("repair no_improvement_action must be STOP")
    if request.get("completion_policy") != POLICY:
        errors.append("request completion policy weakens repository laws")
    return errors + reasoning_fields(request)


def validate_violation(violation: dict[str, Any], request: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if violation.get("schema_version") != "controlled-language-violation/v1":
        errors.append("invalid violation schema_version")
    if not has_text(violation.get("violation_id")) or not violation["violation_id"].startswith("V-"):
        errors.append("violation_id must start with V-")
    if not has_text(violation.get("constraint_id")) or not violation["constraint_id"].startswith("C-"):
        errors.append("violation constraint_id must start with C-")
    if not has_text(violation.get("intent_id")) or not violation["intent_id"].startswith("MI-"):
        errors.append("violation intent_id must start with MI-")
    if violation.get("evidence_class") not in VIOLATION_EVIDENCE:
        errors.append("violation evidence_class is invalid")
    if violation.get("severity") not in VIOLATION_SEVERITIES:
        errors.append("violation severity is invalid")
    if violation.get("status") not in VIOLATION_STATES:
        errors.append("violation status is invalid")
    if not has_text(violation.get("message")):
        errors.append("violation message is required")

    span = violation.get("source_span")
    if not isinstance(span, dict):
        errors.append("violation source_span must be an object")
        span = {}
    if (
        not is_digest(span.get("artifact_digest"))
        or not is_digest(span.get("found_text_digest"))
        or not has_text(span.get("locator"))
    ):
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
        item = request.get("input", {})
        if item.get("mode") == "INLINE" and isinstance(start, int) and isinstance(end, int):
            text = item.get("text", "")
            if end > len(text):
                errors.append("violation span exceeds INLINE input length")
            elif span.get("found_text_digest") != digest(text[start:end].encode()):
                errors.append("violation found_text_digest does not match exact INLINE span")

    status = violation.get("status")
    if status == "WAIVED":
        waiver = violation.get("waiver") or {}
        if not has_text(waiver.get("human_receipt_ref")) or not is_digest(waiver.get("human_receipt_digest")):
            errors.append("WAIVED violation requires exact Human receipt")
        if not has_text(waiver.get("reason")):
            errors.append("WAIVED violation requires reason")
    elif violation.get("waiver") is not None:
        errors.append("non-WAIVED violation cannot carry waiver")
    if status == "REPAIRED" and not has_text(violation.get("candidate_rewrite")):
        errors.append("REPAIRED violation requires candidate_rewrite")
    return errors + reasoning_fields(violation)
