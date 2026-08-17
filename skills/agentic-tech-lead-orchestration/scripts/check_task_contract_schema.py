#!/usr/bin/env python3
"""Validate the portable Tech Lead task packet against its Draft 2020-12 schema.

This is the shape gate. It is deliberately separate from assert_task_contract.py,
which owns semantic/hard-law assertions. A packet must pass both before Worker
admission. Missing validator/schema is a mechanism error, not a semantic PASS.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "references" / "task-contract.schema.json"
DEFAULT_SELFTEST_CONTRACT = SKILL_ROOT / "references" / "example-stack-contract.json"
MAX_BYTES = 4 * 1024 * 1024


class InputError(ValueError):
    pass


class MechanismError(RuntimeError):
    pass


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise InputError(f"{label} not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise InputError(f"{label} exceeds 4 MiB: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} root must be an object")
    return value


def _validator():
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        raise MechanismError(
            "jsonschema with Draft 2020-12 support is unavailable; install the pinned repository validator"
        ) from exc

    try:
        schema = _read_object(SCHEMA_PATH, "task schema")
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)
    except InputError as exc:
        raise MechanismError(str(exc)) from exc
    except SchemaError as exc:
        raise MechanismError(f"invalid task schema: {exc.message}") from exc


def validate_object(contract: dict[str, Any]) -> list[str]:
    validator = _validator()
    errors = sorted(
        validator.iter_errors(contract),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    rendered: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        rendered.append(f"{path}: {error.message}")
    return rendered


def _selftest() -> list[str]:
    base = _read_object(DEFAULT_SELFTEST_CONTRACT, "selftest contract")
    if validate_object(base):
        return ["positive example did not satisfy task-contract.schema.json"]

    mutations: list[tuple[str, dict[str, Any]]] = []

    extra = copy.deepcopy(base)
    extra["unexpected_runtime_override"] = True
    mutations.append(("root additional property", extra))

    nested = copy.deepcopy(base)
    nested["automation"]["auto_merge"] = True
    mutations.append(("auto_merge authority widening", nested))

    malformed = copy.deepcopy(base)
    malformed["budgets"]["max_workers"] = 0
    mutations.append(("worker budget below schema floor", malformed))

    missing = copy.deepcopy(base)
    del missing["subject"]["base_tree"]
    mutations.append(("missing exact tree subject", missing))

    failures: list[str] = []
    for name, value in mutations:
        if not validate_object(value):
            failures.append(f"mutation survived: {name}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.selftest:
            failures = _selftest()
            if failures:
                for failure in failures:
                    print(f"TASK-SCHEMA-SELFTEST-RED {failure}", file=sys.stderr)
                return 2
            print("TASK-SCHEMA-SELFTEST-GREEN positive + 4 planted schema defects closed")

        if args.contract is None:
            if args.selftest:
                return 0
            raise InputError("--contract is required unless --selftest is used")

        contract = _read_object(args.contract.resolve(), "contract")
        errors = validate_object(contract)
        if errors:
            for error in errors:
                print(f"TASK-SCHEMA-RED {error}", file=sys.stderr)
            return 2
        print(f"TASK-SCHEMA-GREEN schema=agentic-tech-lead/task-contract/v1 contract={args.contract}")
        return 0
    except InputError as exc:
        print(f"TASK-SCHEMA-INPUT-RED {exc}", file=sys.stderr)
        return 64
    except MechanismError as exc:
        print(f"TASK-SCHEMA-MECHANISM-RED {exc}", file=sys.stderr)
        return 70
    except Exception as exc:
        print(f"TASK-SCHEMA-MECHANISM-RED unexpected error: {exc}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
