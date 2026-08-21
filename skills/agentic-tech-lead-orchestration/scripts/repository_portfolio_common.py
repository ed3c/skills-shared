#!/usr/bin/env python3
"""Shared deterministic helpers for repository portfolio control gates."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - deterministic environment failure
    raise SystemExit("jsonschema is required for repository portfolio gates") from exc


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_object(value: dict[str, Any], digest_field: str) -> str:
    clone = dict(value)
    clone.pop(digest_field, None)
    return hashlib.sha256(canonical_json(clone)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(instance: Any, schema_path: Path, store: dict[str, Any] | None = None) -> list[str]:
    schema = load_json(schema_path)
    registry = None
    # Draft202012Validator can resolve local refs through a resolver store in older
    # jsonschema versions. For this subtree, callers validate referenced records
    # separately and use this helper only for self-contained portions.
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))]


def parse_timestamp(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def normalize_lease(path: str) -> str:
    value = path.strip().replace("\\", "/")
    while value.endswith("/**"):
        value = value[:-3]
    while value.endswith("/*"):
        value = value[:-2]
    return value.rstrip("/") or "/"


def leases_overlap(left: str, right: str) -> bool:
    l = normalize_lease(left)
    r = normalize_lease(right)
    if l in {"*", "**", "/"} or r in {"*", "**", "/"}:
        return True
    if "UNKNOWN" in {l.upper(), r.upper()}:
        return True
    return l == r or l.startswith(r + "/") or r.startswith(l + "/")
