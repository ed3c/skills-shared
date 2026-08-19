#!/usr/bin/env python3
"""Fail-closed semantic gate for repository-entropy-audit/v1 packets."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment,misc]

OK, CONTRACT, USAGE, MECHANISM = 0, 2, 64, 70
ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "references" / "entropy-audit.schema.json"
EXAMPLE = ROOT / "references" / "example-audit.json"
CHANGE = {"REMOVE", "COLLAPSE", "DEMOTE"}
PROTECTED = {"TRUST_BOUNDARY", "ACCESSIBILITY", "DATA_LOSS_GUARD", "RESOURCE_QUIESCENCE"}
REQUIRED_CHECKS = {"dynamic_reachability", "trust_safety", "history_rationale", "ownership_model"}
PROOF_OK = {"PASS", "NOT_APPLICABLE"}


class InputError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{path} must contain an object")
    return value


def load_validator(path: Path = SCHEMA) -> Draft202012Validator:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required; contract validity cannot be guessed")
    schema = load_json(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimeError(f"invalid Draft 2020-12 schema: {exc}") from exc
    return Draft202012Validator(schema)


def fmt(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def schema_errors(doc: dict[str, Any], validator: Draft202012Validator) -> list[str]:
    return [
        f"{fmt(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]


def safe_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def net_reduction(candidate: dict[str, Any]) -> tuple[int, int]:
    value = candidate["reduction"]
    removed = sum(len(value[key]) for key in (
        "concepts_removed", "contracts_removed", "states_removed", "dependencies_removed"
    ))
    return removed, len(value["concepts_added"])


def semantic_errors(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    add = errors.append
    subject = doc["subject"]
    if subject["dirty"]:
        add("subject.dirty must be false; bind an immutable clean subject")

    boundaries: dict[str, dict[str, Any]] = {}
    for i, boundary in enumerate(doc["contract_boundaries"]):
        ident = boundary["id"]
        if ident in boundaries:
            add(f"contract_boundaries[{i}].id duplicates {ident}")
        boundaries[ident] = boundary

    candidates: dict[str, dict[str, Any]] = {}
    for i, candidate in enumerate(doc["candidates"]):
        ident = candidate["id"]
        if ident in candidates:
            add(f"candidates[{i}].id duplicates {ident}")
        candidates[ident] = candidate
        for target in candidate["targets"]:
            if not safe_path(target):
                add(f"candidate {ident} target {target!r} must be a safe repository-relative path")

        unknown = sorted(set(candidate["boundary_ids"]) - set(boundaries))
        if unknown:
            add(f"candidate {ident} references unknown boundaries: {', '.join(unknown)}")
            bound: list[dict[str, Any]] = []
        else:
            bound = [boundaries[item] for item in candidate["boundary_ids"]]

        action = candidate["action"]
        if action in CHANGE:
            consumers = candidate["consumers"]
            if consumers["production"]:
                add(f"candidate {ident} changes a surface with production consumers")
            if consumers["ambiguous"]:
                add(f"candidate {ident} changes a surface with ambiguous consumers")
            if candidate["confidence"] != "HIGH":
                add(f"candidate {ident} change action requires HIGH confidence")
            if candidate["capability_effect"] != "NONE_OBSERVABLE":
                add(f"candidate {ident} change action requires capability_effect=NONE_OBSERVABLE")

            checks = candidate["checks"]
            for name, state in checks.items():
                if state not in PROOF_OK:
                    add(f"candidate {ident} check {name}={state} cannot admit a change")
            for name in REQUIRED_CHECKS:
                if checks[name] != "PASS":
                    add(f"candidate {ident} required check {name} must be PASS")

            blocked = [
                item["id"] for item in bound
                if item["kind"] in PROTECTED
                or item["mutation_policy"] in {"PROTECTED", "HUMAN_DECISION"}
            ]
            if blocked:
                add(f"candidate {ident} attempts automatic change across protected/Human boundaries: " + ", ".join(blocked))

            removed, added = net_reduction(candidate)
            if removed == 0:
                add(f"candidate {ident} removes no concept, contract, state, or dependency")
            if removed <= added:
                add(f"candidate {ident} is not conceptually net-negative: removed={removed}, added={added}")

        if action == "ESCALATE_PRODUCT_DECISION" and candidate["capability_effect"] == "NONE_OBSERVABLE":
            add(f"candidate {ident} escalation must declare an observable or unknown capability effect")

    selected = doc["selected_candidate_ids"]
    unknown = sorted(set(selected) - set(candidates))
    if unknown:
        add(f"selected_candidate_ids reference unknown candidates: {', '.join(unknown)}")
    if doc["mode"] == "AUDIT" and selected:
        add("AUDIT mode cannot select candidates for mutation")
    chosen = [candidates[item] for item in selected if item in candidates]
    changes = [item for item in chosen if item["action"] in CHANGE]
    escalations = [item for item in chosen if item["action"] == "ESCALATE_PRODUCT_DECISION"]

    shadow = doc["shadow_review"]
    if shadow["subject_commit"] != subject["commit"]:
        add("shadow_review.subject_commit must match subject.commit")
    if not shadow["independent"]:
        add("shadow_review.independent must be true")
    if shadow["writes_target"]:
        add("shadow_review.writes_target must be false; Shadow is not a second writer")

    delivery = doc["delivery"]
    if delivery["required"]:
        if delivery["state"] not in {"ASSERTED", "BLOCKED"}:
            add("delivery.required=true requires state ASSERTED or BLOCKED")
        for key in ("task_dag_digest", "stack_index", "convergence_owner"):
            if delivery[key] is None or delivery[key] == "":
                add(f"delivery.required=true requires {key}")
        if delivery["stack_index"] and not safe_path(delivery["stack_index"]):
            add("delivery.stack_index must be a safe repository-relative path")
    else:
        if delivery["state"] != "NOT_APPLICABLE":
            add("delivery.required=false requires state=NOT_APPLICABLE")
        if any(delivery[key] is not None for key in ("task_dag_digest", "stack_index", "convergence_owner")):
            add("delivery.required=false requires null DAG, Stack and convergence fields")

    handoff = doc["local_handoff"]
    if handoff["required"]:
        if not handoff["queue_subject"]:
            add("local_handoff.required=true requires queue_subject")
        elif not safe_path(handoff["queue_subject"]):
            add("local_handoff.queue_subject must be a safe repository-relative path")
        if not handoff["reason"].strip():
            add("local_handoff.required=true requires a reason")
    elif handoff["queue_subject"] is not None:
        add("local_handoff.required=false requires queue_subject=null")

    verdict, mode, verify = doc["verdict"], doc["mode"], doc["verification"]
    if mode == "AUDIT" and verdict not in {"AUDIT_COMPLETE", "BLOCKED", "HUMAN_ADMIT_REQUIRED"}:
        add(f"AUDIT mode cannot emit verdict {verdict}")

    if verdict in {"IMPLEMENTATION_ELIGIBLE", "IMPLEMENTATION_VERIFIED"}:
        if mode != "APPLY":
            add(f"{verdict} requires APPLY mode")
        if not changes:
            add(f"{verdict} requires at least one selected change candidate")
        if escalations:
            add(f"{verdict} cannot include a selected product-decision escalation")
        if shadow["verdict"] != "ELIGIBLE_FOR_IMPLEMENTATION":
            add(f"{verdict} requires shadow_review.verdict=ELIGIBLE_FOR_IMPLEMENTATION")
        if not delivery["required"] or delivery["state"] != "ASSERTED":
            add(f"{verdict} requires an ASSERTED delivery DAG/Stack contract")

    if verdict == "IMPLEMENTATION_ELIGIBLE" and verify["decisive"] == verify["global_objective"] == "PASS":
        add("IMPLEMENTATION_ELIGIBLE has verified evidence; use IMPLEMENTATION_VERIFIED")

    if verdict == "IMPLEMENTATION_VERIFIED":
        for name in ("decisive", "narrow", "residue_search", "global_objective"):
            if verify[name] != "PASS":
                add(f"IMPLEMENTATION_VERIFIED requires verification.{name}=PASS")
        if verify["broad"] not in PROOF_OK:
            add("IMPLEMENTATION_VERIFIED requires verification.broad PASS or NOT_APPLICABLE")
        if not verify["commands"]:
            add("IMPLEMENTATION_VERIFIED requires recorded verification commands")
        if not verify["evidence"]:
            add("IMPLEMENTATION_VERIFIED requires verification evidence")

    if verdict == "HUMAN_ADMIT_REQUIRED" and shadow["verdict"] != "HUMAN_ADMIT_REQUIRED" and not escalations:
        add("HUMAN_ADMIT_REQUIRED needs Shadow Human verdict or selected product-decision escalation")
    if verdict == "AUDIT_COMPLETE" and mode == "APPLY" and changes:
        add("APPLY mode with selected changes cannot terminate at AUDIT_COMPLETE")
    return errors


def validate_document(doc: dict[str, Any], *, validator: Draft202012Validator | None = None) -> list[str]:
    validator = validator or load_validator()
    errors = schema_errors(doc, validator)
    return errors or semantic_errors(doc)


def run_selftest() -> list[str]:
    validator, base, errors = load_validator(), load_json(EXAMPLE), []
    cases: list[tuple[str, dict[str, Any]]] = []
    for name, mutate in (
        ("dirty subject", lambda d: d["subject"].__setitem__("dirty", True)),
        ("production consumer", lambda d: d["candidates"][0]["consumers"].__setitem__("production", copy.deepcopy(d["candidates"][0]["consumers"]["non_production"]))),
        ("protected boundary", lambda d: d["candidates"][0].__setitem__("boundary_ids", ["BOUNDARY_RESOURCE_STOP"])),
        ("Shadow writer", lambda d: d["shadow_review"].__setitem__("writes_target", True)),
        ("false verified verdict", lambda d: d["verification"].__setitem__("decisive", "NOT_EXERCISED")),
    ):
        doc = copy.deepcopy(base)
        mutate(doc)
        cases.append((name, doc))
    if validate_document(base, validator=validator):
        errors.append("positive example did not pass")
    for name, doc in cases:
        if not validate_document(doc, validator=validator):
            errors.append(f"mutation survived: {name}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", type=Path)
    group.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        validator = load_validator()
        if args.selftest:
            errors, subject = run_selftest(), "selftest"
        else:
            doc = load_json(args.audit)
            errors = validate_document(doc, validator=validator)
            value = doc.get("subject", {})
            subject = f"{value.get('repository', 'unknown')}@{value.get('commit', 'unknown')}"
    except InputError as exc:
        print(f"ENTROPY-AUDIT-USAGE {exc}", file=sys.stderr)
        return USAGE
    except RuntimeError as exc:
        print(f"ENTROPY-AUDIT-MECHANISM {exc}", file=sys.stderr)
        return MECHANISM
    if errors:
        for error in errors:
            print(f"ENTROPY-AUDIT-RED {error}", file=sys.stderr)
        return CONTRACT
    print(f"ENTROPY-AUDIT-GREEN subject={subject}")
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
