#!/usr/bin/env python3
"""Validate the two halves of the Skill bootstrap contract.

Exit codes:
  0   the document is internally consistent for what it declares
  2   structurally valid document declares something it cannot support
  64  missing, unreadable, malformed, or schema-invalid input
  70  required validator dependency is unavailable

Two documents, one contract. `skill-runtime-requirements/v1` is what a Skill needs
stated abstractly; `consumer-skill-binding/v1` is where one repository resolves
those abstractions onto an exact canonical commit and a set of host surfaces. The
document's own `schema` field selects which is being checked.

Neither is a runtime observation. A binding that pins the right commit still does
not prove a surface exists on this machine -- that is what a
skill-resolution-receipt records, and check_skill_bootstrap.py judges.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment guard
    print(
        "SKILL-REQUIREMENTS-RED validator-unavailable: jsonschema is required; "
        "the checker refuses to skip schema validation",
        file=sys.stderr,
    )
    raise SystemExit(70)

sys.path.insert(0, str(Path(__file__).resolve().parent))
# One matrix, not two. A binding that permits an access mode the runtime cannot
# observe is the same defect check_skill_bootstrap.py refuses in a receipt, made
# earlier and in configuration; a second copy here would drift from that one.
from check_skill_bootstrap import RUNTIME_ACCESS_MODES  # noqa: E402

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2

SCHEMA_FILES = {
    "skill-runtime-requirements/v1": "skill-runtime-requirements.schema.json",
    "consumer-skill-binding/v1": "consumer-skill-binding.schema.json",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"SKILL-REQUIREMENTS-INVALID absent-input: {path}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"SKILL-REQUIREMENTS-INVALID unreadable-input: {path}: {exc}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)


def validate_schema(document: Any, schema: Any) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    return [
        f"schema-invalid at {'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in errors
    ]


def requirements_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    network = document["network_policy"]
    if network["mode"] == "ALLOWLIST" and not network["allowed_hosts"]:
        errors.append("allowlist-empty: ALLOWLIST with no host is NONE wearing a permissive label")
    if network["mode"] != "ALLOWLIST" and network["allowed_hosts"]:
        errors.append(
            f"allowlist-ignored: mode={network['mode']} with {len(network['allowed_hosts'])} host(s) listed"
        )
    if network["mode"] == "UNRESTRICTED" and not document["not_exercised_without_substrate"]:
        # Unrestricted egress cannot be supported by fixtures, so a manifest
        # claiming it while declaring nothing unproven is overclaiming.
        errors.append(
            "unrestricted-network-without-boundary: declare what stays NOT_EXERCISED without a real substrate"
        )

    required = set(document["required_capabilities"])
    optional = set(document["optional_capabilities"])
    both = sorted(required & optional)
    if both:
        errors.append("capability-required-and-optional: " + ",".join(both))

    filesystem = document["filesystem"]
    if filesystem["writable_subpaths"] and not filesystem["needs_writable_worktree"]:
        errors.append(
            "writable-subpaths-without-writable-worktree: "
            + ",".join(sorted(filesystem["writable_subpaths"]))
        )
    if document["isolation"]["sandbox"] == "READ_ONLY" and filesystem["needs_writable_worktree"]:
        errors.append("read-only-sandbox-needs-writable-worktree")

    if document["secret_variable_names"] and not document["not_exercised_without_substrate"]:
        # A Skill needing secrets cannot prove its secret-dependent behaviour from
        # committed fixtures; saying so is the difference between a bounded claim
        # and a green run that reads as full support.
        errors.append(
            "secrets-without-boundary: a Skill requiring secrets must declare what "
            "stays NOT_EXERCISED without them"
        )
    return errors


def binding_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for runtime, modes in sorted(document["allowed_access_modes"].items()):
        observable = RUNTIME_ACCESS_MODES.get(runtime, set())
        impossible = sorted(set(modes) - observable)
        if impossible:
            errors.append(
                f"access-mode-not-observable:{runtime}: {','.join(impossible)}"
            )
    if "runtime_env" in document:
        env = document["runtime_env"]
        if env["repository_id"] == document["canonical"]["repository_id"]:
            errors.append(
                "runtime-env-collapsed-into-canonical: the instruction plane and the "
                "execution environment are separate subjects and cannot share one pin"
            )
    names = [skill["name"] for skill in document["selected_skills"]]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append("duplicate-selected-skill: " + ",".join(duplicates))
    return errors


def check(path: Path, schema_root: Path) -> int:
    document = load_json(path)
    if not isinstance(document, dict) or "schema" not in document:
        print(
            f"SKILL-REQUIREMENTS-INVALID unidentified-document: {path} has no schema field",
            file=sys.stderr,
        )
        return SCHEMA_INVALID
    schema_id = document["schema"]
    if schema_id not in SCHEMA_FILES:
        print(
            f"SKILL-REQUIREMENTS-INVALID unknown-schema: {schema_id!r} is not one of "
            + ", ".join(sorted(SCHEMA_FILES)),
            file=sys.stderr,
        )
        return SCHEMA_INVALID

    schema = load_json(schema_root / SCHEMA_FILES[schema_id])
    schema_errors = validate_schema(document, schema)
    if schema_errors:
        for error in schema_errors:
            print(f"SKILL-REQUIREMENTS-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = (
        requirements_errors(document)
        if schema_id == "skill-runtime-requirements/v1"
        else binding_errors(document)
    )
    if errors:
        for error in errors:
            print(f"SKILL-REQUIREMENTS-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    if schema_id == "skill-runtime-requirements/v1":
        print(
            "SKILL-REQUIREMENTS-GREEN "
            f"skill={document['skill_name']} "
            f"runtimes={len(document['supported_runtime_identities'])} "
            f"network={document['network_policy']['mode']} "
            f"sandbox={document['isolation']['sandbox']} "
            f"secrets={len(document['secret_variable_names'])} "
            f"unproven={len(document['not_exercised_without_substrate'])}"
        )
    else:
        print(
            "CONSUMER-BINDING-GREEN "
            f"consumer={document['consumer_repository_id']} "
            f"canonical={document['canonical']['repository_id']}@{document['canonical']['commit_sha'][:12]} "
            f"skills={len(document['selected_skills'])} "
            f"runtimes={len(document['allowed_access_modes'])}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "references",
    )
    args = parser.parse_args(argv)
    return check(args.document, args.schema_root)


if __name__ == "__main__":
    raise SystemExit(main())
