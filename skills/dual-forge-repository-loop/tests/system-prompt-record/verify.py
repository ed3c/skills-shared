#!/usr/bin/env python3
"""Controls for the System Prompt recording gate.

Positive fixtures cover the shapes that must stay open: a local record, a portable
record backed by more than one stack, and a candidate that honestly stops short of
recording. Planted defects cover the ways a prompt can claim authority its evidence
does not carry.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parent.parent
CHECKER = SKILL_ROOT / "scripts" / "check_system_prompt_record.py"
SCHEMA_ROOT = SKILL_ROOT / "references"
GOOD = TEST_DIR / "fixtures" / "valid-recorded.json"

THROUGH_SCOPE = [
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
]


def run(document: dict) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "receipt.json"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr


def mutate(name: str, document: dict) -> None:
    if name == "skipped-state":
        document["record_states"].remove("NEGATIVE_CONTROLS_PASS")
    elif name == "recorded-without-replay":
        document["record_states"].remove("RECEIPT_BUNDLE_REPLAY_PASS")
    elif name == "projected-without-record":
        document["record_states"] = THROUGH_SCOPE + [
            "LOCAL_RECORD_ELIGIBLE",
            "RELEASE_ADMIT_REQUIRED",
            "PROJECTED",
        ]
    elif name == "recorded-while-stopped":
        document["record_states"].insert(-1, "SUPERSEDED")
    elif name == "stop-not-terminal":
        document["record_states"] = THROUGH_SCOPE[:6] + ["VERIFIER_FAIL", "DETERMINISTIC_VERIFIER_PASS"]
    elif name == "both-eligibilities":
        states = document["record_states"]
        states.insert(states.index("LOCAL_RECORD_ELIGIBLE") + 1, "PORTABLE_RECORD_ELIGIBLE")
    elif name == "verifier-fail-recorded":
        document["verification"]["result"] = "FAIL"
    elif name == "execution-not-completed":
        document["execution"]["terminal_state"] = "TIMED_OUT"
    elif name == "bootstrap-absent":
        document["runtime"]["bootstrap_receipt_digest"] = "ABSENT"
    elif name == "controls-declared-none":
        document["evaluation_contract"]["negative_controls"] = []
        document["verification"]["negative_control_results"] = []
    elif name == "control-result-missing":
        document["verification"]["negative_control_results"].pop()
    elif name == "control-survived":
        document["verification"]["negative_control_results"][0]["state"] = "SURVIVED"
    elif name == "control-unowned":
        document["verification"]["negative_control_results"].append(
            {"id": "control-not-declared", "state": "KILLED"}
        )
    elif name == "authority-scope-mismatch":
        document["promotion"]["authority"] = "PORTABLE_RECORD"
    elif name == "portable-single-stack":
        states = document["record_states"]
        states[states.index("LOCAL_RECORD_ELIGIBLE")] = "PORTABLE_RECORD_ELIGIBLE"
        document["promotion"]["authority"] = "PORTABLE_RECORD"
    elif name == "recorded-without-admission":
        document["promotion"]["release_admit_state"] = "HUMAN_ADMIT_REQUIRED"
    elif name == "recorded-with-regression":
        document["promotion"]["regressions"] = ["case-single-builder now refused"]
    elif name == "recorded-with-unsupported-claim":
        document["verification"]["unsupported_claims"] = ["cross-model generalization"]
    elif name == "recorded-without-authority":
        document["promotion"]["authority"] = "NONE"
    elif name == "recorded-on-unknown-runtime":
        document["runtime"]["identity"] = "UNKNOWN"
    elif name == "inverted-execution-window":
        document["execution"]["ended_at"] = "2026-08-15T08:00:00Z"
    elif name == "unbounded-effect-policy":
        document["runtime"]["effect_policy"] = "ARBITRARY"
    elif name == "prompt-digest-not-sha256":
        document["prompt"]["content_sha256"] = "not-a-digest"
    elif name == "empty-admitted-scope":
        document["promotion"]["admitted_scope"] = []
    else:
        raise AssertionError(f"unknown mutation: {name}")


def main() -> int:
    good = json.loads(GOOD.read_text(encoding="utf-8"))
    failures: list[str] = []

    code, stdout, stderr = run(good)
    if code != 0 or "PROMPT-RECORD-GREEN" not in stdout or stderr:
        failures.append(f"positive local-record fixture: code={code} stdout={stdout!r} stderr={stderr!r}")

    # Portable authority is admitted when more than one stack actually carried it.
    portable = copy.deepcopy(good)
    states = portable["record_states"]
    states[states.index("LOCAL_RECORD_ELIGIBLE")] = "PORTABLE_RECORD_ELIGIBLE"
    portable["promotion"]["authority"] = "PORTABLE_RECORD"
    portable["observed_stacks"] = [
        "codex-cli/fixture-build+fixture-model/1",
        "claude-code/fixture-build+other-model/2",
    ]
    code, stdout, stderr = run(portable)
    if code != 0 or stderr:
        failures.append(f"positive portable-record fixture: code={code} stderr={stderr!r}")

    # A candidate that stops before recording is the honest shape, not a failure:
    # it claims evaluation authority only.
    candidate = copy.deepcopy(good)
    candidate["record_states"] = THROUGH_SCOPE[:6]
    candidate["verification"]["result"] = "NOT_EXERCISED"
    candidate["verification"]["negative_control_results"] = []
    candidate["promotion"]["authority"] = "NONE"
    candidate["promotion"]["release_admit_state"] = "HUMAN_ADMIT_REQUIRED"
    code, stdout, stderr = run(candidate)
    if code != 0 or stderr:
        failures.append(f"positive candidate fixture: code={code} stderr={stderr!r}")

    # A failed candidate is preserved as archive evidence and terminates in its
    # stop state. It must be admitted as an honest record of refusal.
    refused = copy.deepcopy(good)
    refused["record_states"] = THROUGH_SCOPE[:6] + ["VERIFIER_FAIL"]
    refused["verification"]["result"] = "FAIL"
    refused["verification"]["negative_control_results"] = []
    refused["promotion"]["authority"] = "NONE"
    refused["promotion"]["release_admit_state"] = "REFUSED"
    code, stdout, stderr = run(refused)
    if code != 0 or stderr:
        failures.append(f"positive refused-candidate fixture: code={code} stderr={stderr!r}")

    cases = [
        ("skipped-state", 2, "record-sequence-violation"),
        ("recorded-without-replay", 2, "record-sequence-violation"),
        ("projected-without-record", 2, "projected-without-record"),
        ("recorded-while-stopped", 2, "recorded-while-stopped"),
        ("stop-not-terminal", 2, "stop-state-not-terminal"),
        ("both-eligibilities", 2, "multiple-scope-eligibility"),
        ("verifier-fail-recorded", 2, "verifier-pass-claimed-without-pass"),
        ("execution-not-completed", 2, "execution-claimed-without-completion"),
        ("bootstrap-absent", 2, "bootstrap-pass-without-receipt"),
        ("controls-declared-none", 2, "controls-pass-without-controls"),
        ("control-result-missing", 2, "control-result-missing"),
        ("control-survived", 2, "negative-control-survived"),
        ("control-unowned", 2, "control-result-unowned"),
        ("authority-scope-mismatch", 2, "authority-scope-mismatch"),
        ("portable-single-stack", 2, "portable-authority-single-stack"),
        ("recorded-without-admission", 2, "recorded-without-admission"),
        ("recorded-with-regression", 2, "recorded-with-regressions"),
        ("recorded-with-unsupported-claim", 2, "recorded-with-unsupported-claims"),
        ("recorded-without-authority", 2, "recorded-without-authority"),
        ("recorded-on-unknown-runtime", 2, "recorded-on-unknown-runtime"),
        ("inverted-execution-window", 2, "execution-window-inverted"),
        ("unbounded-effect-policy", 64, "schema-invalid"),
        ("prompt-digest-not-sha256", 64, "schema-invalid"),
        ("empty-admitted-scope", 64, "schema-invalid"),
    ]

    for name, expected_code, marker in cases:
        document = copy.deepcopy(good)
        mutate(name, document)
        code, stdout, stderr = run(document)
        if code != expected_code or marker not in stderr:
            failures.append(
                f"{name}: expected code={expected_code} marker={marker!r}; "
                f"got code={code} stdout={stdout!r} stderr={stderr!r}"
            )

    # The committed live receipts must keep passing. They were produced by real
    # hosts against an exact subject; if a later schema or rule change invalidates
    # them, that is a decision to make deliberately, not to discover in a rerun.
    committed = sorted((SKILL_ROOT / "evals" / "receipts").glob("prompt-receipt-*.json"))
    if not committed:
        failures.append("committed live prompt receipts are missing")
    for path in committed:
        process = subprocess.run(
            [sys.executable, str(CHECKER), str(path), "--schema-root", str(SCHEMA_ROOT)],
            text=True, capture_output=True, check=False,
        )
        if process.returncode != 0:
            failures.append(f"committed receipt {path.name}: code={process.returncode} {process.stderr!r}")

    process = subprocess.run(
        [sys.executable, str(CHECKER), str(TEST_DIR / "fixtures" / "absent.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 64 or "absent-input" not in process.stderr:
        failures.append(
            f"absent input: expected 64/absent-input, got {process.returncode} {process.stderr!r}"
        )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(
        "PASS system-prompt-record: local record, portable record on two stacks, "
        f"unproven candidate, and refused candidate fixtures admitted; {len(cases)} planted "
        "sequence, control, scope, admission, regression, and digest defects refused; "
        "absent input stayed distinct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
