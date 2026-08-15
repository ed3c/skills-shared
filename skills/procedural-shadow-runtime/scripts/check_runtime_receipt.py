#!/usr/bin/env python3
"""Deterministic semantic checker for procedural-shadow-runtime contracts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TERMINAL = {
    "VERIFIED",
    "SATISFIED_BY_PRIOR_EVIDENCE",
    "NOT_APPLICABLE_WITH_EVIDENCE",
    "BLOCKED",
    "FAILED",
    "WAIVED_WITH_AUTHORIZED_REASON",
}
NON_TERMINAL = {"MENTIONED", "PLANNED", "EXECUTED_PENDING_VERIFICATION"}
FORBIDDEN_KEYS = {
    "chain_of_thought",
    "chain-of-thought",
    "private_reasoning",
    "raw_reasoning",
    "hidden_reasoning",
    "reasoning_trace",
}


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(value, dict):
        raise RuntimeError("top-level JSON must be an object")
    return value


def reject_private_reasoning(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(key.lower() not in FORBIDDEN_KEYS, f"{path}.{key}: private reasoning payloads are forbidden")
            reject_private_reasoning(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_reasoning(child, f"{path}[{index}]")


def require_digest(value: Any, regex: re.Pattern[str], path: str) -> str:
    require(isinstance(value, str) and regex.fullmatch(value) is not None, f"{path}: invalid digest")
    return value


def require_source(source: Any, path: str) -> None:
    require(isinstance(source, dict), f"{path}: source must be object")
    for key in ("repository", "ref", "path", "content_sha256"):
        require(key in source, f"{path}.{key}: missing")
    for key in ("repository", "ref", "path"):
        require(isinstance(source[key], str) and source[key].strip(), f"{path}.{key}: empty")
    require_digest(source["content_sha256"], HEX64, f"{path}.content_sha256")


def validate_capsule(capsule: dict[str, Any], receipt: dict[str, Any] | None = None) -> dict[str, Any]:
    reject_private_reasoning(capsule)
    require(capsule.get("schema") == "procedural-shadow-context-capsule/v1", "$.schema: wrong capsule schema")
    require(isinstance(capsule.get("capsule_id"), str) and capsule["capsule_id"], "$.capsule_id: missing")
    require(isinstance(capsule.get("checkpoint"), str) and capsule["checkpoint"], "$.checkpoint: missing")
    require_digest(capsule.get("context_digest"), HEX64, "$.context_digest")
    require(isinstance(capsule.get("expires_at_checkpoint"), str) and capsule["expires_at_checkpoint"], "$.expires_at_checkpoint: missing")
    authority = capsule.get("authority")
    require(isinstance(authority, dict), "$.authority: missing")
    require(authority.get("shadow_read_only") is True, "$.authority.shadow_read_only must be true")
    require(authority.get("capability_widening") == "DENY", "$.authority.capability_widening must DENY")
    require(authority.get("private_data_egress") == "DENY", "$.authority.private_data_egress must DENY")
    require(authority.get("raw_private_reasoning") == "DENY", "$.authority.raw_private_reasoning must DENY")
    procedures = capsule.get("procedures")
    require(isinstance(procedures, list) and procedures, "$.procedures: non-empty list required")
    seen: set[str] = set()
    for index, proc in enumerate(procedures):
        path = f"$.procedures[{index}]"
        require(isinstance(proc, dict), f"{path}: object required")
        pid = proc.get("procedure_id")
        require(isinstance(pid, str) and pid, f"{path}.procedure_id: missing")
        require(pid not in seen, f"{path}.procedure_id: duplicate")
        seen.add(pid)
        require(proc.get("criticality") in {"must", "should", "may"}, f"{path}.criticality: invalid")
        require_source(proc.get("source"), f"{path}.source")
        require(isinstance(proc.get("expected_observation"), str) and proc["expected_observation"], f"{path}.expected_observation: missing")
        require(proc.get("failure_action") in {"BLOCK", "REPAIR", "ESCALATE"}, f"{path}.failure_action: invalid")
    if receipt is not None:
        subject = receipt.get("subject", {})
        require(capsule["context_digest"] == subject.get("context_digest"), "capsule context digest is stale for receipt subject")
        receipt_checkpoint = receipt.get("checkpoint")
        if receipt_checkpoint is not None:
            require(capsule["expires_at_checkpoint"] == receipt_checkpoint, "capsule expired for receipt checkpoint")
    return {"capsule_id": capsule["capsule_id"], "procedures": len(procedures)}


def validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    reject_private_reasoning(receipt)
    require(receipt.get("schema") == "procedural-shadow-runtime-receipt/v1", "$.schema: wrong receipt schema")
    require(isinstance(receipt.get("receipt_id"), str) and receipt["receipt_id"], "$.receipt_id: missing")
    subject = receipt.get("subject")
    require(isinstance(subject, dict), "$.subject: missing")
    for key in ("repository", "runtime"):
        require(isinstance(subject.get(key), str) and subject[key], f"$.subject.{key}: missing")
    require_digest(subject.get("base_sha"), HEX40, "$.subject.base_sha")
    require_digest(subject.get("current_sha"), HEX40, "$.subject.current_sha")
    require_digest(subject.get("context_digest"), HEX64, "$.subject.context_digest")

    action = receipt.get("action")
    require(isinstance(action, dict), "$.action: missing")
    require(isinstance(action.get("class"), str) and action["class"], "$.action.class: missing")
    require(isinstance(action.get("side_effecting"), bool), "$.action.side_effecting: bool required")
    require_digest(action.get("intent_digest"), HEX64, "$.action.intent_digest")

    procedures = receipt.get("applicable_procedures")
    require(isinstance(procedures, list), "$.applicable_procedures: list required")
    criticality: dict[str, str] = {}
    for index, proc in enumerate(procedures):
        path = f"$.applicable_procedures[{index}]"
        require(isinstance(proc, dict), f"{path}: object required")
        pid = proc.get("procedure_id")
        require(isinstance(pid, str) and pid, f"{path}.procedure_id: missing")
        require(pid not in criticality, f"{path}.procedure_id: duplicate")
        require(proc.get("criticality") in {"must", "should", "may"}, f"{path}.criticality: invalid")
        criticality[pid] = proc["criticality"]
        require_source(proc.get("source"), f"{path}.source")

    assertions = receipt.get("assertions")
    evidence = receipt.get("evidence")
    dispositions = receipt.get("dispositions")
    require(isinstance(assertions, list), "$.assertions: list required")
    require(isinstance(evidence, list), "$.evidence: list required")
    require(isinstance(dispositions, list), "$.dispositions: list required")

    assertions_by_proc: dict[str, list[str]] = {}
    for index, assertion in enumerate(assertions):
        require(isinstance(assertion, dict), f"$.assertions[{index}]: object required")
        pid = assertion.get("procedure_id")
        require(pid in criticality, f"$.assertions[{index}].procedure_id: unknown")
        result = assertion.get("result")
        require(result in {"PASS", "FAIL", "NOT_RUN"}, f"$.assertions[{index}].result: invalid")
        assertions_by_proc.setdefault(pid, []).append(result)

    evidence_by_proc: dict[str, int] = {}
    for index, item in enumerate(evidence):
        require(isinstance(item, dict), f"$.evidence[{index}]: object required")
        pid = item.get("procedure_id")
        require(pid in criticality, f"$.evidence[{index}].procedure_id: unknown")
        require(item.get("exact_subject") is True, f"$.evidence[{index}].exact_subject must be true")
        require_digest(item.get("artifact_sha256"), HEX64, f"$.evidence[{index}].artifact_sha256")
        evidence_by_proc[pid] = evidence_by_proc.get(pid, 0) + 1

    disposition_by_proc: dict[str, dict[str, Any]] = {}
    for index, disposition in enumerate(dispositions):
        require(isinstance(disposition, dict), f"$.dispositions[{index}]: object required")
        pid = disposition.get("procedure_id")
        require(pid in criticality, f"$.dispositions[{index}].procedure_id: unknown")
        require(pid not in disposition_by_proc, f"$.dispositions[{index}].procedure_id: duplicate")
        state = disposition.get("state")
        require(state in TERMINAL | NON_TERMINAL, f"$.dispositions[{index}].state: invalid")
        disposition_by_proc[pid] = disposition

    close_state = receipt.get("close_state")
    require(close_state in {"PASS", "BLOCKED", "FAIL"}, "$.close_state: invalid")
    if close_state == "PASS":
        must_ids = {pid for pid, level in criticality.items() if level == "must"}
        require(must_ids <= disposition_by_proc.keys(), "PASS has missing must dispositions")
        for pid in must_ids:
            disposition = disposition_by_proc[pid]
            state = disposition["state"]
            require(state in TERMINAL, f"PASS has non-terminal must disposition: {pid}")
            require(state not in {"BLOCKED", "FAILED"}, f"PASS cannot contain {state}: {pid}")
            if state == "VERIFIED":
                require(evidence_by_proc.get(pid, 0) > 0, f"VERIFIED must procedure lacks exact-subject evidence: {pid}")
                require("PASS" in assertions_by_proc.get(pid, []), f"VERIFIED must procedure lacks passing assertion: {pid}")
            elif state == "SATISFIED_BY_PRIOR_EVIDENCE":
                require(evidence_by_proc.get(pid, 0) > 0, f"prior-evidence disposition lacks evidence binding: {pid}")
            elif state == "NOT_APPLICABLE_WITH_EVIDENCE":
                require(evidence_by_proc.get(pid, 0) > 0, f"N/A disposition lacks evidence: {pid}")
            elif state == "WAIVED_WITH_AUTHORIZED_REASON":
                require(isinstance(disposition.get("reason"), str) and disposition["reason"].strip(), f"waiver lacks authorized reason: {pid}")
    return {
        "receipt_id": receipt["receipt_id"],
        "close_state": close_state,
        "applicable": len(procedures),
        "must": sum(1 for value in criticality.values() if value == "must"),
    }


def main(argv: list[str]) -> int:
    if len(argv) not in {2, 3}:
        print("usage: check_runtime_receipt.py <receipt.json> [capsule.json]", file=sys.stderr)
        return 64
    try:
        receipt = read_json(Path(argv[1]))
        capsule = read_json(Path(argv[2])) if len(argv) == 3 else None
    except RuntimeError as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 64
    try:
        result = validate_receipt(receipt)
        if capsule is not None:
            result["capsule"] = validate_capsule(capsule, receipt)
    except ContractError as exc:
        print(f"CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
