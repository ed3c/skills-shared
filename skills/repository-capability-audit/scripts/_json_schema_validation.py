"""Shared JSON/schema plumbing for repository-capability-audit checkers.

This module owns only generic transport mechanics: loading one UTF-8 JSON
artifact, preserving checker-specific error prefixes/exit codes, resolving the
Draft 2020-12 validator dependency, and formatting schema errors. Domain
semantics remain in each checker.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def require_draft202012_validator(prefix: str):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover - environment guard
        print(
            f"{prefix}-RED validator-unavailable: jsonschema is required; "
            "the checker refuses to skip schema validation",
            file=sys.stderr,
        )
        raise SystemExit(70)
    return Draft202012Validator


def load_json_document(path: Path, *, prefix: str, invalid_exit: int) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{prefix}-INVALID absent-input: {path}", file=sys.stderr)
        raise SystemExit(invalid_exit)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"{prefix}-INVALID unreadable-input: {path}: {exc}", file=sys.stderr)
        raise SystemExit(invalid_exit)


def schema_errors(document: Any, schema: Any, validator_type) -> list[str]:
    validator = validator_type(schema)
    errors = sorted(
        validator.iter_errors(document), key=lambda item: list(item.absolute_path)
    )
    return [
        f"schema-invalid at {'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in errors
    ]
