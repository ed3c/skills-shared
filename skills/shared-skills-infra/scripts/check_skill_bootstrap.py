#!/usr/bin/env python3
"""Validate skill-resolution-receipt/v1 bootstrap receipts.

Exit codes:
  0   the receipt admits task execution on the exact submitted subject
  2   structurally valid receipt violates a bootstrap invariant
  64  missing, unreadable, malformed, or schema-invalid input
  70  required validator dependency is unavailable

A System Prompt cannot grant filesystem or process authority, so an instruction
to "load these Skills" establishes nothing about which bytes were resolved,
through which host surface, or whether the environment was prepared. This checker
validates a receipt that records those facts. It does not itself observe a host:
it refuses receipts whose claims are internally impossible for the named runtime,
and admits ones that are consistent. Live host observation is a separate lane.
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
        "SKILL-BOOTSTRAP-RED validator-unavailable: jsonschema is required; "
        "the checker refuses to skip schema validation",
        file=sys.stderr,
    )
    raise SystemExit(70)

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2

SCHEMA_NAME = "skill-resolution-receipt.schema.json"

# The admission path, in order. A receipt may stop early, but it may not skip.
ADMISSION_SEQUENCE = (
    "RUNTIME_BOUND",
    "REPOSITORY_POLICY_BOUND",
    "SKILL_REQUIREMENTS_DISCOVERED",
    "MINIMAL_SKILL_SET_RESOLVED",
    "CANONICAL_SKILL_SUBJECTS_BOUND",
    "SKILL_SURFACES_AVAILABLE",
    "SKILL_RUNTIME_REQUIREMENTS_BOUND",
    "RUNTIME_ENV_CLOSURE_BOUND",
    "ENVIRONMENT_PLAN_RENDERED",
    "ENVIRONMENT_PREPARED",
    "CAPABILITY_PROBES_PASS",
    "TASK_EXECUTION_ADMITTED",
)
BLOCKED_STATES = {
    "SKILL_ROUTE_ABSENT",
    "SKILL_SUBJECT_STALE",
    "SKILL_SHADOWED",
    "SKILL_SURFACE_ABSENT",
    "PRIVATE_SOURCE_NOT_ADMITTED",
    "RUNTIME_REQUIREMENTS_ABSENT",
    "RUNTIME_ENV_BINDING_ABSENT",
    "ENVIRONMENT_NOT_PREPARED",
    "CAPABILITY_NOT_EXERCISED",
    "HOST_MUTATION_NOT_ADMITTED",
    "SECRET_BOUNDARY_BLOCKED",
}
ADMITTED = "TASK_EXECUTION_ADMITTED"

LOCAL_RUNTIMES = {"CLAUDE_CODE_LOCAL", "CODEX_CLI_LOCAL", "CHATGPT_DESKTOP_WORKTREE"}
# Which access modes each runtime can actually observe. A connector read proves
# Skill bytes and nothing about a filesystem; Actions consumes a pinned bundle
# rather than a user surface that does not exist on a runner.
RUNTIME_ACCESS_MODES = {
    "CHATGPT_GITHUB_CONNECTOR": {"CONNECTOR_EXACT_COMMIT_READ_ONLY", "ABSENT"},
    "GITHUB_ACTIONS": {"GITHUB_ACTIONS_PINNED_BUNDLE", "IMMUTABLE_RELEASE_BUNDLE", "ABSENT"},
    "CLAUDE_CODE_LOCAL": {
        "LOCAL_CANONICAL_USER_SURFACE",
        "PROJECT_CANONICAL_PROJECTION",
        "IMMUTABLE_RELEASE_BUNDLE",
        "ABSENT",
    },
    "CODEX_CLI_LOCAL": {
        "LOCAL_CANONICAL_USER_SURFACE",
        "PROJECT_CANONICAL_PROJECTION",
        "IMMUTABLE_RELEASE_BUNDLE",
        "ABSENT",
    },
    "CHATGPT_DESKTOP_WORKTREE": {
        "LOCAL_CANONICAL_USER_SURFACE",
        "PROJECT_CANONICAL_PROJECTION",
        "IMMUTABLE_RELEASE_BUNDLE",
        "ABSENT",
    },
    "UNKNOWN": {"ABSENT"},
}
# Modes that only prove readable bytes. They cannot carry an execution claim.
REASONING_ONLY_MODES = {"CONNECTOR_EXACT_COMMIT_READ_ONLY", "ABSENT"}
SURFACE_READBACK_REQUIRED = {"LOCAL_CANONICAL_USER_SURFACE", "PROJECT_CANONICAL_PROJECTION"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"SKILL-BOOTSTRAP-INVALID absent-input: {path}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"SKILL-BOOTSTRAP-INVALID unreadable-input: {path}: {exc}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)


def validate_schema(document: Any, schema: Any) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    return [
        f"schema-invalid at {'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in errors
    ]


def state_errors(states: list[str]) -> list[str]:
    """The trace must be a prefix of the admission path, optionally ending blocked."""
    errors: list[str] = []
    blocked = [state for state in states if state in BLOCKED_STATES]
    if len(blocked) > 1:
        errors.append(f"multiple-blocked-states: {','.join(blocked)}")
    if blocked and states[-1] not in BLOCKED_STATES:
        errors.append(f"blocked-state-not-terminal: {blocked[0]} is followed by {states[-1]}")
    progress = [state for state in states if state not in BLOCKED_STATES]
    expected = list(ADMISSION_SEQUENCE[: len(progress)])
    if progress != expected:
        errors.append(
            "bootstrap-sequence-violation: "
            f"observed={'>'.join(progress) or '-'} expected-prefix={'>'.join(expected) or '-'}"
        )
    if blocked and ADMITTED in states:
        errors.append(f"admitted-while-blocked: {blocked[0]} with {ADMITTED}")
    return errors


def semantic_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runtime = receipt["runtime_identity"]
    consumer = receipt["consumer"]
    canonical = receipt["canonical"]
    skills: list[dict[str, Any]] = receipt["selected_skills"]
    shadowing = receipt["shadowing_scan"]
    environment = receipt["environment"]
    states: list[str] = receipt["bootstrap_states"]

    errors.extend(state_errors(states))
    admitted = ADMITTED in states
    allowed_modes = RUNTIME_ACCESS_MODES[runtime]
    selected_names = {skill["name"] for skill in skills}

    for skill in skills:
        mode = skill["access_mode"]
        if mode not in allowed_modes:
            errors.append(
                f"access-mode-not-observable:{skill['name']}: {runtime} cannot observe {mode}"
            )
        if mode in SURFACE_READBACK_REQUIRED and skill["surface_readback_state"] != "VERIFIED":
            # A symlink or forwarder that was never read back is a plan, not a surface.
            errors.append(
                f"surface-readback-missing:{skill['name']}: {mode} requires VERIFIED readback, "
                f"got {skill['surface_readback_state']}"
            )
        if mode == "ABSENT" and admitted:
            errors.append(f"absent-skill-admitted:{skill['name']}: ABSENT is not PASS")
        # Minimal triggered closure: every declared dependency must itself be in
        # the selected set, or the set is not closed and the Agent is running on
        # a Skill whose prerequisites were never resolved.
        missing = sorted(set(skill["transitive_dependencies"]) - selected_names)
        if missing:
            errors.append(
                f"dependency-closure-open:{skill['name']}: unresolved={','.join(missing)}"
            )
        if skill["selection_reason"] == "DECLARED_DEPENDENCY" and not any(
            skill["name"] in other["transitive_dependencies"] for other in skills
        ):
            errors.append(
                f"orphan-dependency-selection:{skill['name']}: selected as a declared "
                "dependency but no selected Skill declares it"
            )

    if admitted:
        if shadowing["state"] != "CLEAN":
            # Both hosts prefer a project-local copy, so a shadowed name means the
            # canonical body silently did not run.
            errors.append(f"shadowed-or-unscanned-admission: shadowing_scan={shadowing['state']}")
        if runtime == "UNKNOWN":
            errors.append("unknown-runtime-admitted: UNKNOWN fails closed before execution")
        reasoning_only = sorted(
            skill["name"] for skill in skills if skill["access_mode"] in REASONING_ONLY_MODES
        )
        if reasoning_only:
            # Readable bytes are not an executable Skill, a prepared worktree, or
            # a runnable environment.
            errors.append(
                "execution-claim-on-reasoning-only-access: " + ",".join(reasoning_only)
            )
        if environment["state"] == "NOT_PREPARED":
            errors.append("admitted-without-prepared-environment")
        if environment["absent_secret_names"]:
            errors.append(
                "admitted-with-absent-secrets: "
                + ",".join(sorted(environment["absent_secret_names"]))
            )
        failed_probes = sorted(
            probe["id"] for probe in environment["capability_probes"] if probe["state"] != "PASS"
        )
        if failed_probes:
            errors.append("capability-probe-not-pass: " + ",".join(failed_probes))
        if environment["state"] == "PREPARED" and not environment["capability_probes"]:
            errors.append("prepared-without-probe: preparation claimed with no probe exercised")

    if shadowing["state"] == "CLEAN" and shadowing["findings"]:
        errors.append(
            "shadowing-scan-contradiction: state=CLEAN with "
            f"{len(shadowing['findings'])} finding(s)"
        )
    if shadowing["state"] == "SHADOWED" and not shadowing["findings"]:
        errors.append("shadowing-scan-unsupported: state=SHADOWED with no finding")

    if canonical["visibility"] == "PRIVATE" and consumer["visibility"] == "PUBLIC":
        # A public consumer may not reach a private canonical repository through a
        # new credential; it needs a reviewed immutable bundle or a preinstalled
        # local surface.
        offending = sorted(
            skill["name"]
            for skill in skills
            if skill["access_mode"]
            not in {"IMMUTABLE_RELEASE_BUNDLE", "LOCAL_CANONICAL_USER_SURFACE", "ABSENT"}
        )
        if offending:
            errors.append(
                "public-consumer-private-import: " + ",".join(offending)
            )

    absent_requirements = sorted(
        skill["name"] for skill in skills if skill["runtime_requirements_digest"] == "ABSENT"
    )
    if admitted and absent_requirements:
        errors.append("runtime-requirements-absent: " + ",".join(absent_requirements))

    unresolved = sorted(set(environment["absent_secret_names"]) - set(environment["required_secret_names"]))
    if unresolved:
        errors.append("absent-secret-not-required: " + ",".join(unresolved))

    return errors


def check(receipt_path: Path, schema_root: Path) -> int:
    receipt = load_json(receipt_path)
    schema = load_json(schema_root / SCHEMA_NAME)

    schema_errors = validate_schema(receipt, schema)
    if schema_errors:
        for error in schema_errors:
            print(f"SKILL-BOOTSTRAP-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = semantic_errors(receipt)
    if errors:
        for error in errors:
            print(f"SKILL-BOOTSTRAP-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    terminal = receipt["bootstrap_states"][-1]
    print(
        "SKILL-BOOTSTRAP-GREEN "
        f"consumer={receipt['consumer']['repository_id']} "
        f"runtime={receipt['runtime_identity']} "
        f"canonical={receipt['canonical']['repository_id']}@{receipt['canonical']['commit_sha'][:12]} "
        f"skills={len(receipt['selected_skills'])} "
        f"shadowing={receipt['shadowing_scan']['state']} "
        f"environment={receipt['environment']['state']} "
        f"terminal={terminal}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "references",
    )
    args = parser.parse_args(argv)
    return check(args.receipt, args.schema_root)


if __name__ == "__main__":
    raise SystemExit(main())
