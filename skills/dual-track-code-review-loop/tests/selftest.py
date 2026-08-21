#!/usr/bin/env python3
"""Replay the DTCR C0 contract and its planted refusal controls.

This suite is deterministic and repository-local. It proves only that the
committed C0 schemas/examples/refusal controls behave as declared on these bytes.
It does not prove provider adapters, runtime behavior, legal clearance, user
value, merge, release, or production readiness.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    print("DTCR-C0-HARNESS: jsonschema==4.26.0 is required", file=sys.stderr)
    raise SystemExit(64) from exc

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "dual-track-code-review-loop"
SCHEMA_DIR = SKILL / "references" / "schemas"
DISPOSITION_FILE = SKILL / "references" / "source-disposition" / "refused-claims.json"
CASES_FILE = SKILL / "cases.json"

PRIVATE_LOCATOR_PATTERNS = (
    re.compile(r"https?://docs\.google\.com/", re.I),
    re.compile(r"https?://drive\.google\.com/", re.I),
    re.compile(r"(?<![A-Za-z0-9_])/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"(?<![A-Za-z0-9_])/home/[A-Za-z0-9._-]+/"),
)
TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


class HarnessError(RuntimeError):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"unreadable JSON {path.relative_to(ROOT)}: {exc}") from exc


def schema_id(schema: dict[str, Any]) -> str:
    try:
        return schema["properties"]["schema"]["const"]
    except (KeyError, TypeError) as exc:
        raise HarnessError(f"{schema.get('$id', '<unknown>')}: missing properties.schema.const") from exc


def errors(schema: dict[str, Any], instance: Any) -> list[str]:
    return [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in Draft202012Validator(schema).iter_errors(instance)
    ]


def parse_guard_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for match in TOKEN_RE.finditer(path.strip()):
        key, index = match.groups()
        tokens.append(int(index) if index is not None else key)
    if not tokens:
        raise HarnessError(f"empty guard path: {path!r}")
    return tokens


def neutralize_guard(schema: dict[str, Any], guard_path: str) -> None:
    """Disable one named schema guard without changing the planted instance."""
    tokens = parse_guard_path(guard_path)
    # `not.pattern` is one compound guard. Removing only `pattern` leaves
    # `not: {}`, which rejects every value and is not a meaningful knockout.
    if len(tokens) >= 2 and tokens[-1] == "pattern" and tokens[-2] == "not":
        tokens = tokens[:-1]

    node: Any = schema
    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(node, list) or token >= len(node):
                raise HarnessError(f"guard path does not resolve: {guard_path}")
            node = node[token]
        else:
            if not isinstance(node, dict) or token not in node:
                raise HarnessError(f"guard path does not resolve: {guard_path}")
            node = node[token]

    terminal = tokens[-1]
    if isinstance(terminal, int):
        if not isinstance(node, list) or terminal >= len(node):
            raise HarnessError(f"guard path does not resolve: {guard_path}")
        del node[terminal]
    else:
        if not isinstance(node, dict) or terminal not in node:
            raise HarnessError(f"guard path does not resolve: {guard_path}")
        del node[terminal]


def guard_paths(refused_by: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\s+and\s+", refused_by) if part.strip()]
    if not parts:
        raise HarnessError(f"refused_by has no guard: {refused_by!r}")
    return parts


def collect() -> tuple[
    dict[str, dict[str, Any]],
    list[tuple[str, dict[str, Any], dict[str, Any], str]],
    list[tuple[str, dict[str, Any], dict[str, Any], str]],
]:
    schemas: dict[str, dict[str, Any]] = {}
    positive: list[tuple[str, dict[str, Any], dict[str, Any], str]] = []
    controls: list[tuple[str, dict[str, Any], dict[str, Any], str]] = []

    files = sorted(SCHEMA_DIR.glob("*.schema.json"))
    if not files:
        raise HarnessError("no DTCR schemas found")

    for path in files:
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        sid = schema_id(schema)
        if sid in schemas:
            raise HarnessError(f"duplicate schema identity {sid}")
        schemas[sid] = schema

        for index, instance in enumerate(schema.get("examples") or []):
            positive.append((f"{path.name}#examples[{index}]", schema, instance, sid))

        positive_ref = schema.get("x-positive-instance")
        if positive_ref:
            resolved = (path.parent / positive_ref).resolve()
            try:
                resolved.relative_to(SKILL.resolve())
            except ValueError as exc:
                raise HarnessError(f"x-positive-instance escapes Skill: {positive_ref}") from exc
            positive.append((f"{path.name}#x-positive-instance", schema, load(resolved), sid))

        for control in schema.get("x-refusal-controls") or []:
            controls.append((control["case_id"], schema, control["instance"], control["refused_by"]))

    disposition = load(DISPOSITION_FILE)
    for row in disposition.get("dispositions") or []:
        control = row.get("negative_control") or {}
        sid = control.get("schema_id")
        if sid not in schemas:
            raise HarnessError(f"{row.get('disposition_id')}: unknown target schema {sid!r}")
        controls.append((control["case_id"], schemas[sid], control["instance"], control["refused_by"]))

    return schemas, positive, controls


def check_public_locator_leaks() -> None:
    """Refuse resolved private Google/home locators in the portable C0 tree."""
    problems: list[str] = []
    for path in sorted(SKILL.rglob("*")):
        if not path.is_file() or "tests" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PRIVATE_LOCATOR_PATTERNS:
            if pattern.search(text):
                problems.append(f"{path.relative_to(ROOT)} matches {pattern.pattern}")
    if problems:
        raise HarnessError("private locator leak(s): " + "; ".join(problems))


def main() -> int:
    cases = load(CASES_FILE)
    expected = cases["expected_denominator"]
    schemas, positive, controls = collect()

    if len(schemas) != expected["schemas"]:
        raise HarnessError(f"schema denominator drift: expected {expected['schemas']}, got {len(schemas)}")
    if len(positive) != expected["positive_instances"]:
        raise HarnessError(
            f"positive denominator drift: expected {expected['positive_instances']}, got {len(positive)}"
        )
    if len(controls) != expected["refusal_controls"]:
        raise HarnessError(
            f"control denominator drift: expected {expected['refusal_controls']}, got {len(controls)}"
        )

    for label, schema, instance, sid in positive:
        failures = errors(schema, instance)
        if failures:
            raise HarnessError(f"positive {label} for {sid} is RED: {failures[:3]}")

    seen: set[str] = set()
    refused = 0
    discriminating = 0
    for case_id, schema, instance, refused_by in controls:
        if case_id in seen:
            raise HarnessError(f"duplicate refusal case id: {case_id}")
        seen.add(case_id)

        before = errors(schema, instance)
        if not before:
            raise HarnessError(f"{case_id}: planted defect is not refused")
        refused += 1

        weakened = copy.deepcopy(schema)
        for guard in guard_paths(refused_by):
            neutralize_guard(weakened, guard)
        Draft202012Validator.check_schema(weakened)
        after = errors(weakened, instance)
        if after:
            raise HarnessError(
                f"{case_id}: own-guard knockout did not discriminate; refused_by={refused_by!r}; "
                f"remaining={after[:3]}"
            )
        discriminating += 1

    if refused != expected["refusal_controls"]:
        raise HarnessError(f"refusal count mismatch: {refused}")
    if discriminating != expected["knockout_discriminating"]:
        raise HarnessError(
            f"knockout denominator mismatch: expected {expected['knockout_discriminating']}, got {discriminating}"
        )

    check_public_locator_leaks()
    print(
        "DTCR C0 harness: PASS "
        f"schemas={len(schemas)} positives={len(positive)} "
        f"refusals={refused} knockouts={discriminating} private_locator_scan=PASS"
    )
    print(
        "Evidence ceiling: deterministic C0 schema/control replay only; "
        "provider/runtime/user/legal/merge/release/production NOT established."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as exc:
        print(f"DTCR C0 harness: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
