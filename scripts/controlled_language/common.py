from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

EVIDENCE = {"DETERMINISTIC", "CALIBRATED_HEURISTIC", "SEMANTIC", "HUMAN"}
RUN_STATES = {"PASS", "FAIL", "BLOCKED", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}
SAFETY = {"WARNING", "CAUTION"}
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
POLICY = {
    "deterministic_failure_vetoes_advisory": True,
    "stale_evidence_blocks": True,
    "safety_text_requires_human_review": True,
    "official_compliance_requires_human_admit": True,
    "private_chain_of_thought": "FORBIDDEN",
}


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value, raw


def is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_portable_path(value: Any) -> bool:
    if not has_text(value):
        return False
    if value.startswith(("/", "~")) or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and ".." not in parts and "." not in parts


def reasoning_fields(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    forbidden = {"chain_of_thought", "reasoning_trace", "hidden_reasoning"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                errors.append(f"{path}.{key} must not persist private reasoning")
            errors += reasoning_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors += reasoning_fields(child, f"{path}[{index}]")
    return errors


def result(errors: list[str]) -> int:
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 2
    print("PASS controlled-language contract")
    return 0
