#!/usr/bin/env python3
"""Bind CTL deterministic and heuristic evidence to exact artifacts.

Exit 0 = evaluated PASS, 2 = evaluated FAIL, 64 = invalid input,
70 = checker failure. Heuristic calibration is always advisory-only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
DET_SCHEMA = "controlled-language-exact-evidence/v1"
CAL_SCHEMA = "controlled-language-corpus-calibration/v1"
PRED_SCHEMA = "controlled-language-corpus-predictions/v1"
EVALUATOR = "controlled-language-exact-evidence"
VERSION = "1.0.0"

class InputError(Exception):
    pass


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read valid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{path}: root must be an object")
    return value, raw


def exact_path(root: Path, ref: Any, label: str) -> tuple[dict[str, Any], bytes]:
    if not isinstance(ref, dict):
        raise InputError(f"{label} must be an object")
    rel, expected = ref.get("path"), ref.get("artifact_digest")
    if not isinstance(rel, str) or not rel or rel.startswith(("/", "~")) or "\\" in rel:
        raise InputError(f"{label}.path is not portable")
    parts = PurePosixPath(rel).parts
    if "." in parts or ".." in parts or re.match(r"^[A-Za-z]:", rel):
        raise InputError(f"{label}.path is not portable")
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise InputError(f"{label}.artifact_digest is invalid")
    base = root.resolve()
    path = (base / rel).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise InputError(f"{label}.path escapes repository") from exc
    value, raw = load(path)
    if digest(raw) != expected:
        raise InputError(f"{label} digest mismatch")
    return value, raw


def exact_content(item: Any, label: str) -> tuple[str, str]:
    if not isinstance(item, dict) or not isinstance(item.get("content"), str):
        raise InputError(f"{label}.content is required")
    content = item["content"]
    expected = item.get("artifact_digest")
    if not isinstance(expected, str) or digest(content.encode()) != expected:
        raise InputError(f"{label} digest mismatch")
    return content, expected


def exact_span(content: str, item: Any, label: str) -> tuple[int, int, str]:
    if not isinstance(item, dict):
        raise InputError(f"{label} must be an object")
    start, end = item.get("start"), item.get("end")
    if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(content):
        raise InputError(f"{label} has an invalid range")
    text = content[start:end]
    if item.get("text_digest") != digest(text.encode()):
        raise InputError(f"{label} digest mismatch")
    return start, end, text


def word_count(text: str, policy: dict[str, Any]) -> int:
    token = policy.get("tokenization", {})
    if token.get("hyphen_policy") != "SPLIT_COMPONENTS":
        raise InputError("hyphen policy must be SPLIT_COMPONENTS")
    pattern = token.get("word_pattern")
    try:
        return len(re.findall(str(pattern), text))
    except re.error as exc:
        raise InputError(f"invalid word pattern: {exc}") from exc


def xml_nodes(text: str, id_attr: str) -> dict[str, tuple[str, str, int]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise InputError(f"XML is not well formed: {exc}") from exc
    result: dict[str, tuple[str, str, int]] = {}
    for index, node in enumerate(root.iter()):
        identity = node.attrib.get(id_attr)
        if identity:
            if identity in result:
                raise InputError(f"duplicate XML node {identity}")
            text_digest = digest("".join(node.itertext()).strip().encode())
            result[identity] = (node.tag, text_digest, index)
    return result


def foundation_validators(root: Path):
    sys.path.insert(0, str(root / "scripts"))
    try:
        from controlled_language.contracts import validate_standard_pack, validate_termbase_entry
    except Exception as exc:
        raise RuntimeError(f"cannot import foundation validators: {exc}") from exc
    finally:
        sys.path.pop(0)
    return validate_standard_pack, validate_termbase_entry


def evaluate_deterministic(root: Path, case: dict[str, Any], case_raw: bytes) -> dict[str, Any]:
    if case.get("schema_version") != DET_SCHEMA:
        raise InputError("invalid deterministic bundle schema_version")
    validate_pack, validate_term = foundation_validators(root)
    pack, pack_raw = exact_path(root, case.get("profile_pack"), "profile_pack")
    rules, rules_raw = exact_path(root, case.get("ruleset"), "ruleset")
    policy, policy_raw = exact_path(root, case.get("policy"), "policy")
    violations: list[str] = []
    violations.extend(f"pack: {item}" for item in validate_pack(pack))
    if pack.get("ruleset_digest") != digest(rules_raw):
        violations.append("pack does not bind exact ruleset bytes")
    identity = policy.get("profile_identity", {})
    if identity.get("pack_id") != pack.get("pack_id") or identity.get("edition") != pack.get("edition"):
        violations.append("policy profile identity mismatch")
    if identity.get("pack_digest") != digest(pack_raw) or identity.get("ruleset_digest") != digest(rules_raw):
        violations.append("policy profile digest mismatch")
    deterministic_kinds = {"WORD_LIMIT", "FORBIDDEN_PHRASE", "TERMBASE", "XML_PRESERVATION"}
    for rule in policy.get("implemented_rules", []):
        if not isinstance(rule, dict) or rule.get("kind") not in deterministic_kinds:
            violations.append("heuristic or unknown rule entered deterministic policy")
    limits = policy.get("sentence_limits", {})
    if not isinstance(limits, dict) or not limits:
        raise InputError("policy sentence_limits is absent")

    terms: dict[str, dict[str, Any]] = {}
    term_ids: list[dict[str, str]] = []
    for index, ref in enumerate(case.get("termbase_references", [])):
        term, raw = exact_path(root, ref, f"termbase_references[{index}]")
        violations.extend(f"term: {item}" for item in validate_term(term))
        term_id = term.get("term_id")
        if isinstance(term_id, str):
            if term_id in terms:
                violations.append(f"duplicate term identity {term_id}")
            terms[term_id] = term
            term_ids.append({"term_id": term_id, "artifact_digest": digest(raw)})
    if not terms:
        violations.append("exact admitted termbase is absent")

    source, source_digest = exact_content(case.get("subject"), "subject")
    candidate, candidate_digest = exact_content(case.get("candidate"), "candidate")
    doc_class = case.get("document_class")
    segments = case.get("candidate", {}).get("segments")
    if doc_class not in {"S1000D_XML", "DITA_XML"}:
        if not isinstance(segments, list) or not segments:
            raise InputError("non-XML candidate requires segments")
        ranges: list[tuple[int, int]] = []
        for index, segment in enumerate(segments):
            start, end, text = exact_span(candidate, segment, f"candidate.segments[{index}]")
            if segment.get("document_class") != doc_class:
                violations.append(f"segment {index} document class mismatch")
            limit = limits.get(doc_class)
            if not isinstance(limit, int) or limit <= 0:
                violations.append(f"no positive word limit for {doc_class}")
            else:
                observed = word_count(text, policy)
                if observed > limit:
                    violations.append(f"segment {index} has {observed} words; limit is {limit}")
            lowered = text.lower()
            for phrase in policy.get("forbidden_phrases", []):
                if isinstance(phrase, dict) and str(phrase.get("text", "")).lower() in lowered:
                    violations.append(f"forbidden phrase {phrase.get('text')!r}")
            ranges.append((start, end))
        cursor = 0
        for start, end in sorted(ranges):
            if start < cursor:
                violations.append("candidate segments overlap")
            elif candidate[cursor:start].strip():
                violations.append("candidate bytes are uncovered")
            cursor = max(cursor, end)
        if candidate[cursor:].strip():
            violations.append("candidate trailing bytes are uncovered")

        for index, use in enumerate(case.get("technical_terms_used", [])):
            term = terms.get(use.get("term_id") if isinstance(use, dict) else None)
            if term is None:
                violations.append(f"term use {index} is not in exact termbase")
                continue
            _, _, surface = exact_span(candidate, use, f"technical_terms_used[{index}]")
            if surface.lower() != str(term.get("term", "")).lower():
                violations.append(f"term use {index} surface mismatch")
            if use.get("part_of_speech") not in term.get("allowed_parts_of_speech", []):
                violations.append(f"term use {index} POS is not admitted")
            if term.get("decision_state") != "ADMITTED" or term.get("approved_for_use") is not True:
                violations.append(f"term use {index} is not ADMITTED")

    if doc_class in {"S1000D_XML", "DITA_XML"}:
        contract = case.get("xml_preservation")
        if not isinstance(contract, dict):
            raise InputError("XML preservation contract is absent")
        src, cand = xml_nodes(source, contract.get("id_attribute", "id")), xml_nodes(candidate, contract.get("id_attribute", "id"))
        previous = -1
        protected = contract.get("protected_nodes")
        if not isinstance(protected, list) or not protected:
            raise InputError("protected XML nodes are absent")
        for node in protected:
            identity = node.get("id") if isinstance(node, dict) else None
            source_node, candidate_node = src.get(identity), cand.get(identity)
            if source_node is None:
                violations.append(f"protected source node {identity} is absent")
                continue
            if node.get("tag") != source_node[0] or node.get("text_digest") != source_node[1]:
                violations.append(f"protected source node {identity} identity mismatch")
            if candidate_node is None:
                violations.append(f"protected candidate node {identity} was removed")
            elif candidate_node[:2] != source_node[:2]:
                violations.append(f"protected node {identity} tag or text changed")
            elif candidate_node[2] <= previous:
                violations.append(f"protected node {identity} changed order")
            else:
                previous = candidate_node[2]

    return {
        "schema_version": "controlled-language-exact-evidence-receipt/v1",
        "evaluator_identity": {"id": EVALUATOR, "version": VERSION, "evidence_class": "DETERMINISTIC"},
        "case_digest": digest(case_raw),
        "subject_digest": source_digest,
        "candidate_digest": candidate_digest,
        "pack_digest": digest(pack_raw),
        "ruleset_digest": digest(rules_raw),
        "policy_digest": digest(policy_raw),
        "termbase_identities": sorted(term_ids, key=lambda item: item["term_id"]),
        "violations": violations,
        "status": "PASS" if not violations else "FAIL",
        "exit_code": 0 if not violations else 2,
    }
