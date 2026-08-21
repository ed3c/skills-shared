#!/usr/bin/env python3
"""Deterministic verifier for the DTCR D1-C provider-neutral fact contract.

The checker validates schema shape, positive examples, planted schema refusals,
own-guard knockout discrimination, and cross-field semantic invariants that JSON
Schema cannot express without provider-specific code. It executes no provider.
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
    print("DTCR-D1C: jsonschema==4.26.0 is required", file=sys.stderr)
    raise SystemExit(64) from exc

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "contract-cases.json"
TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


class ContractError(RuntimeError):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read {path.name}: {exc}") from exc


def schema_id(schema: dict[str, Any]) -> str:
    try:
        return schema["properties"]["schema"]["const"]
    except (KeyError, TypeError) as exc:
        raise ContractError(f"{schema.get('$id', '<unknown>')}: missing schema const") from exc


def validation_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    return [
        f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(instance)
    ]


def parse_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for match in TOKEN_RE.finditer(path.strip()):
        key, index = match.groups()
        tokens.append(int(index) if index is not None else key)
    if not tokens:
        raise ContractError(f"empty path: {path!r}")
    return tokens


def resolve_parent(root: Any, path: str) -> tuple[Any, str | int]:
    tokens = parse_path(path)
    node = root
    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(node, list) or token >= len(node):
                raise ContractError(f"path does not resolve: {path}")
            node = node[token]
        else:
            if not isinstance(node, dict) or token not in node:
                raise ContractError(f"path does not resolve: {path}")
            node = node[token]
    return node, tokens[-1]


def neutralize_guard(schema: dict[str, Any], path: str) -> None:
    tokens = parse_path(path)
    # `not.pattern` is a single logical guard. Removing only the inner pattern
    # creates `not: {}`, which rejects everything and is not a real knockout.
    if len(tokens) >= 2 and tokens[-1] == "pattern" and tokens[-2] == "not":
        tokens = tokens[:-1]
        path = ".".join(str(token) for token in tokens)
    node, terminal = resolve_parent(schema, path)
    if isinstance(terminal, int):
        if not isinstance(node, list) or terminal >= len(node):
            raise ContractError(f"guard path does not resolve: {path}")
        del node[terminal]
    else:
        if not isinstance(node, dict) or terminal not in node:
            raise ContractError(f"guard path does not resolve: {path}")
        del node[terminal]


def guard_paths(value: str) -> list[str]:
    paths = [part.strip() for part in re.split(r"\s+and\s+", value) if part.strip()]
    if not paths:
        raise ContractError(f"refused_by has no guard: {value!r}")
    return paths


def patch(instance: Any, path: str, value: Any) -> None:
    node, terminal = resolve_parent(instance, path)
    if isinstance(terminal, int):
        if not isinstance(node, list) or terminal >= len(node):
            raise ContractError(f"patch path does not resolve: {path}")
        node[terminal] = copy.deepcopy(value)
    else:
        if not isinstance(node, dict) or terminal not in node:
            raise ContractError(f"patch path does not resolve: {path}")
        node[terminal] = copy.deepcopy(value)


def semantic_refusal(instance: dict[str, Any]) -> str | None:
    sid = instance.get("schema")
    if sid == "dtcr/provider-observation/v1":
        coverage = instance["coverage"]
        if coverage["processed"] > coverage["denominator"]:
            return "PROCESSED_EXCEEDS_DENOMINATOR"
        if (
            coverage["completeness"] == "EXACT_FOR_DECLARED_DENOMINATOR"
            and coverage["processed"] != coverage["denominator"]
        ):
            return "EXACT_COVERAGE_COUNT_MISMATCH"
        return None

    if sid == "dtcr/fact-plane-receipt/v1":
        failed = False
        for check in instance["checks"]:
            if check["state"] == "PASS" and check["exit_code"] != 0:
                return "PASS_WITH_NONZERO_EXIT"
            if check["state"] == "FAIL":
                failed = True
        if instance["evidence_state"] == "PASS" and failed:
            return "PASS_RECEIPT_WITH_FAILED_CHECK"
        return None

    if sid == "dtcr/fact-bundle/v1":
        blast = instance.get("blast_radius")
        if blast is None:
            return None
        rank = {
            "NOT_APPLICABLE": 0,
            "UNKNOWN": 1,
            "PARTIAL": 2,
            "EXACT_FOR_DECLARED_DENOMINATOR": 3,
        }
        aggregate = instance["aggregate_coverage"]["completeness"]
        blast_level = blast["coverage"]["completeness"]
        if rank[blast_level] > rank[aggregate]:
            return "BLAST_RADIUS_EXCEEDS_BUNDLE_COVERAGE"
        return None

    return None


def main() -> int:
    contract_cases = load(CASES)
    expected = contract_cases["expected"]

    schemas: dict[str, dict[str, Any]] = {}
    positives: dict[str, dict[str, Any]] = {}
    controls: list[tuple[str, dict[str, Any], dict[str, Any], str]] = []

    for path in sorted(ROOT.glob("*.schema.json")):
        schema = load(path)
        Draft202012Validator.check_schema(schema)
        sid = schema_id(schema)
        if sid in schemas:
            raise ContractError(f"duplicate schema identity: {sid}")
        schemas[sid] = schema
        examples = schema.get("examples") or []
        if len(examples) != 1:
            raise ContractError(f"{path.name}: expected exactly one positive example, got {len(examples)}")
        positives[sid] = examples[0]
        for control in schema.get("x-refusal-controls") or []:
            controls.append((control["case_id"], schema, control["instance"], control["refused_by"]))

    if len(schemas) != expected["schema_files"]:
        raise ContractError(f"schema denominator drift: expected {expected['schema_files']}, got {len(schemas)}")
    if len(positives) != expected["positive_examples"]:
        raise ContractError(f"positive denominator drift: expected {expected['positive_examples']}, got {len(positives)}")
    if len(controls) != expected["schema_refusal_controls"]:
        raise ContractError(f"refusal denominator drift: expected {expected['schema_refusal_controls']}, got {len(controls)}")

    for sid, instance in positives.items():
        failures = validation_errors(schemas[sid], instance)
        if failures:
            raise ContractError(f"positive {sid} is RED: {failures[:3]}")
        semantic = semantic_refusal(instance)
        if semantic:
            raise ContractError(f"positive {sid} violates semantic invariant: {semantic}")

    seen: set[str] = set()
    refused = 0
    knockouts = 0
    for case_id, schema, instance, refused_by in controls:
        if case_id in seen:
            raise ContractError(f"duplicate refusal case: {case_id}")
        seen.add(case_id)
        before = validation_errors(schema, instance)
        if not before:
            raise ContractError(f"{case_id}: planted defect is not refused")
        refused += 1

        weakened = copy.deepcopy(schema)
        for guard in guard_paths(refused_by):
            neutralize_guard(weakened, guard)
        Draft202012Validator.check_schema(weakened)
        after = validation_errors(weakened, instance)
        if after:
            raise ContractError(
                f"{case_id}: own-guard knockout did not discriminate; refused_by={refused_by!r}; remaining={after[:3]}"
            )
        knockouts += 1

    semantic_count = 0
    for mutation in contract_cases["semantic_mutations"]:
        sid = mutation["target_schema"]
        if sid not in positives:
            raise ContractError(f"{mutation['id']}: unknown target schema {sid}")
        instance = copy.deepcopy(positives[sid])
        for change in mutation["patches"]:
            patch(instance, change["path"], change["value"])
        failures = validation_errors(schemas[sid], instance)
        if failures:
            raise ContractError(
                f"{mutation['id']}: intended semantic mutation is schema-invalid before its named invariant: {failures[:3]}"
            )
        actual = semantic_refusal(instance)
        if actual != mutation["refusal"]:
            raise ContractError(
                f"{mutation['id']}: expected semantic refusal {mutation['refusal']}, got {actual!r}"
            )
        semantic_count += 1

    if semantic_count != expected["semantic_mutations"]:
        raise ContractError(
            f"semantic mutation denominator drift: expected {expected['semantic_mutations']}, got {semantic_count}"
        )

    print(
        "DTCR D1-C contract: PASS "
        f"schemas={len(schemas)} positives={len(positives)} "
        f"schema_refusals={refused} knockouts={knockouts} semantic_mutations={semantic_count}"
    )
    print(
        "Evidence ceiling: provider-neutral contract only; provider execution, semantic completeness, "
        "task correctness, refactor correctness, merge/release/production NOT established."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"DTCR D1-C contract: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
