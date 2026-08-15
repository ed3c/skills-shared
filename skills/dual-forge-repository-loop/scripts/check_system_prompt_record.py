#!/usr/bin/env python3
"""Validate system-prompt-runtime-receipt/v1 recording claims.

Exit codes:
  0   the receipt supports the recording authority it claims
  2   structurally valid receipt claims authority its evidence does not support
  64  missing, unreadable, malformed, or schema-invalid input
  70  required validator dependency is unavailable

Only a System Prompt whose exact bytes were exercised in a named runtime and
admitted by a replayable verifier may become recorded, projected, or canonical.
A prompt may exist as a candidate before proof; it may not enter an active prompt
registry, instruction projection, or default Agent context because its Markdown is
complete or its static tests pass.

This checker judges internal support: whether the claimed authority follows from
the evidence the receipt itself binds. It does not observe a host, rerun a suite,
or replay a bundle -- those are the lanes whose results the receipt records.
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
        "PROMPT-RECORD-RED validator-unavailable: jsonschema is required; "
        "the checker refuses to skip schema validation",
        file=sys.stderr,
    )
    raise SystemExit(70)

SCHEMA_INVALID = 64
SEMANTIC_FAIL = 2

SCHEMA_NAME = "system-prompt-runtime-receipt.schema.json"

# The recording path, in order. SCOPE_DECIDED forks into exactly one eligibility.
RECORD_SEQUENCE = (
    "AUTHORED",
    "CANDIDATE_BOUND",
    "EVAL_CONTRACT_BOUND",
    "RUNTIME_BOOTSTRAP_PASS",
    "RUNTIME_EXECUTED",
    "EXECUTOR_EVIDENCE_CAPTURED",
    "DETERMINISTIC_VERIFIER_PASS",
    "NEGATIVE_CONTROLS_PASS",
    "RECEIPT_BUNDLE_REPLAY_PASS",
    "SCOPE_DECIDED",
)
ELIGIBILITY_STATES = ("LOCAL_RECORD_ELIGIBLE", "PORTABLE_RECORD_ELIGIBLE")
TAIL_SEQUENCE = ("RELEASE_ADMIT_REQUIRED", "RECORDED", "PROJECTED")
STOP_STATES = {
    "ABSENT",
    "NOT_EXERCISED",
    "STALE_PROMPT",
    "STALE_RUNTIME",
    "SUBJECT_MISMATCH",
    "BOOTSTRAP_FAIL",
    "EXECUTION_FAIL",
    "VERIFIER_FAIL",
    "CONTROL_FAIL",
    "REPLAY_FAIL",
    "REGRESSION",
    "SCOPE_OVERCLAIM",
    "RECEIPT_REVOKED",
    "SUPERSEDED",
    "HUMAN_ADMIT_REQUIRED",
}
AUTHORITY_BY_ELIGIBILITY = {
    "LOCAL_RECORD_ELIGIBLE": "LOCAL_RECORD",
    "PORTABLE_RECORD_ELIGIBLE": "PORTABLE_RECORD",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"PROMPT-RECORD-INVALID absent-input: {path}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"PROMPT-RECORD-INVALID unreadable-input: {path}: {exc}", file=sys.stderr)
        raise SystemExit(SCHEMA_INVALID)


def validate_schema(document: Any, schema: Any) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    return [
        f"schema-invalid at {'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in errors
    ]


def expected_progress(length: int, eligibility: str | None) -> list[str]:
    path = list(RECORD_SEQUENCE)
    if eligibility is not None:
        path.append(eligibility)
        path.extend(TAIL_SEQUENCE)
    return path[:length]


def state_errors(states: list[str]) -> list[str]:
    errors: list[str] = []
    stops = [state for state in states if state in STOP_STATES]
    if len(stops) > 1:
        errors.append(f"multiple-stop-states: {','.join(stops)}")
    if stops and states[-1] not in STOP_STATES:
        errors.append(f"stop-state-not-terminal: {stops[0]} is followed by {states[-1]}")

    progress = [state for state in states if state not in STOP_STATES]
    chosen = [state for state in progress if state in ELIGIBILITY_STATES]
    if len(chosen) > 1:
        errors.append(f"multiple-scope-eligibility: {','.join(chosen)}")
    eligibility = chosen[0] if chosen else None
    expected = expected_progress(len(progress), eligibility)
    if progress != expected:
        errors.append(
            "record-sequence-violation: "
            f"observed={'>'.join(progress) or '-'} expected-prefix={'>'.join(expected) or '-'}"
        )
    if "RECORDED" in states and stops:
        errors.append(f"recorded-while-stopped: {stops[0]} with RECORDED")
    if "PROJECTED" in states and "RECORDED" not in states:
        errors.append("projected-without-record: a candidate is not addressable as active")
    return errors


def semantic_errors(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract = receipt["evaluation_contract"]
    runtime = receipt["runtime"]
    execution = receipt["execution"]
    verification = receipt["verification"]
    promotion = receipt["promotion"]
    states: list[str] = receipt["record_states"]
    stacks: list[str] = receipt.get("observed_stacks", [])

    errors.extend(state_errors(states))
    recorded = "RECORDED" in states

    # Absent controls are not passing controls.
    declared_controls = set(contract["negative_controls"])
    observed_controls = {item["id"] for item in verification["negative_control_results"]}
    if "NEGATIVE_CONTROLS_PASS" in states:
        if not declared_controls:
            errors.append("controls-pass-without-controls: no negative control is declared")
        missing = sorted(declared_controls - observed_controls)
        if missing:
            errors.append("control-result-missing: " + ",".join(missing))
        unowned = sorted(observed_controls - declared_controls)
        if unowned:
            errors.append("control-result-unowned: " + ",".join(unowned))
        survived = sorted(
            item["id"] for item in verification["negative_control_results"] if item["state"] != "KILLED"
        )
        if survived:
            errors.append("negative-control-survived: " + ",".join(survived))

    if "DETERMINISTIC_VERIFIER_PASS" in states and verification["result"] != "PASS":
        errors.append(f"verifier-pass-claimed-without-pass: result={verification['result']}")
    if "RUNTIME_EXECUTED" in states and execution["terminal_state"] != "COMPLETED":
        errors.append(f"execution-claimed-without-completion: {execution['terminal_state']}")
    if "RUNTIME_BOOTSTRAP_PASS" in states and runtime["bootstrap_receipt_digest"] == "ABSENT":
        errors.append("bootstrap-pass-without-receipt: no skill-resolution receipt is bound")

    if execution["ended_at"] < execution["started_at"]:
        errors.append(
            f"execution-window-inverted: ended_at={execution['ended_at']} "
            f"started_at={execution['started_at']}"
        )

    chosen = [state for state in states if state in ELIGIBILITY_STATES]
    if chosen:
        expected_authority = AUTHORITY_BY_ELIGIBILITY[chosen[0]]
        if promotion["authority"] != expected_authority:
            errors.append(
                f"authority-scope-mismatch: {chosen[0]} with authority={promotion['authority']}"
            )
    # Portable authority is a claim about more than one stack. One stack is a
    # local record wearing a portable label.
    if promotion["authority"] == "PORTABLE_RECORD" and len(stacks) < 2:
        errors.append(
            f"portable-authority-single-stack: observed_stacks={len(stacks)}"
        )

    if recorded:
        for required in ("DETERMINISTIC_VERIFIER_PASS", "NEGATIVE_CONTROLS_PASS", "RECEIPT_BUNDLE_REPLAY_PASS"):
            if required not in states:
                errors.append(f"recorded-without-{required.lower().replace('_', '-')}")
        if promotion["release_admit_state"] != "ADMITTED":
            errors.append(
                f"recorded-without-admission: release_admit_state={promotion['release_admit_state']}"
            )
        if promotion["regressions"]:
            errors.append("recorded-with-regressions: " + ",".join(sorted(promotion["regressions"])))
        if verification["unsupported_claims"]:
            errors.append(
                "recorded-with-unsupported-claims: "
                + ",".join(sorted(verification["unsupported_claims"]))
            )
        if promotion["authority"] == "NONE":
            errors.append("recorded-without-authority")
        if runtime["identity"] == "UNKNOWN":
            errors.append("recorded-on-unknown-runtime")

    return errors


def check(receipt_path: Path, schema_root: Path) -> int:
    receipt = load_json(receipt_path)
    schema = load_json(schema_root / SCHEMA_NAME)

    schema_errors = validate_schema(receipt, schema)
    if schema_errors:
        for error in schema_errors:
            print(f"PROMPT-RECORD-INVALID {error}", file=sys.stderr)
        return SCHEMA_INVALID

    errors = semantic_errors(receipt)
    if errors:
        for error in errors:
            print(f"PROMPT-RECORD-RED {error}", file=sys.stderr)
        return SEMANTIC_FAIL

    print(
        "PROMPT-RECORD-GREEN "
        f"prompt={receipt['prompt']['prompt_id']}@{receipt['prompt']['version']} "
        f"digest={receipt['prompt']['content_sha256'][:12]} "
        f"runtime={receipt['runtime']['identity']} "
        f"verifier={receipt['verification']['result']} "
        f"authority={receipt['promotion']['authority']} "
        f"terminal={receipt['record_states'][-1]}"
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
