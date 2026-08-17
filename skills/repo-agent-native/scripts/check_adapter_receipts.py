#!/usr/bin/env python3
"""Validate captured adapter receipts. Zero network, zero provider execution.

`capture_adapter_receipt.py` runs providers. This reads only what that wrote, so
CI and a reviewer can judge a lane on a host where none of the providers exist.
The two never share a code path, because a validator that could re-run the thing
it validates would be able to hide a disagreement between them.

The laws are the ones `EVIDENCE_MODEL.md` and `TOOL_ROUTING.md` already state and
nothing enforced:

  a lane cannot claim an evidence level its read-back does not support
  a provider that did not run cannot carry a run's evidence
  a lane cannot report PASS with no control that would have turned it red
  identity, policy, budget and residue are recorded or the receipt is not one
  no secret-shaped value survives into a durable receipt

Exit codes: 0 pass, 2 receipt failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "repo-agent-native/adapter-receipt/v1"

VALID_STATES = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
                "SKIPPED_BY_POLICY"}
UNEXERCISED_STATES = {"ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}
EVIDENCE_LEVELS = {"A", "A-", "B+", "B", "C", "D"}
# Levels whose own definition in EVIDENCE_MODEL.md contains a read-back clause.
READBACK_LEVELS = {"A", "A-"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*\S{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def require(body: dict[str, Any], key: str, code: str, name: str) -> Any:
    if key not in body:
        refuse(code, f"{name} has no {key}")
    return body[key]


def check_shape(body: Any, name: str) -> None:
    if not isinstance(body, dict):
        refuse("RECEIPT_MALFORMED", f"{name} is not an object")
    if body.get("schema") != SCHEMA:
        refuse("RECEIPT_MALFORMED", f"{name} schema must be {SCHEMA}")
    for section in ("adapter", "subject", "policy", "budgets", "execution",
                    "result", "residue", "controls"):
        if section not in body:
            refuse("RECEIPT_MALFORMED", f"{name} has no {section} section")


def check_subject(body: dict[str, Any], name: str) -> None:
    """A receipt without an exact subject is a claim about no particular tree."""
    subject = body["subject"]
    for field in ("commit_sha", "tree_sha"):
        value = subject.get(field)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            refuse("SUBJECT_UNBOUND",
                   f"{name}: subject.{field} must be a 40-character lowercase SHA")
    if not subject.get("repository"):
        refuse("SUBJECT_UNBOUND", f"{name}: subject.repository is empty")
    dirty = subject.get("dirty_paths")
    if not isinstance(dirty, int):
        refuse("SUBJECT_UNBOUND", f"{name}: subject.dirty_paths must be recorded")
    if dirty > 0 and body["result"].get("state") == "PASS":
        refuse("SUBJECT_UNBOUND",
               f"{name}: {dirty} dirty path(s) at capture, so the receipt does not "
               f"describe the recorded tree")


def check_identity(body: dict[str, Any], name: str) -> None:
    adapter = body["adapter"]
    state = body["result"].get("state")
    if not adapter.get("kind") or not adapter.get("provider"):
        refuse("RECEIPT_MALFORMED", f"{name}: adapter kind and provider are required")
    if state in UNEXERCISED_STATES:
        return
    if not adapter.get("version"):
        refuse("PROVIDER_UNIDENTIFIED", f"{name}: no provider version recorded")
    digest = adapter.get("executable_sha256")
    if digest is not None and not SHA256.fullmatch(str(digest)):
        refuse("PROVIDER_UNIDENTIFIED", f"{name}: executable_sha256 is not a SHA-256")


def check_policy(body: dict[str, Any], name: str) -> None:
    policy = body["policy"]
    for field in ("network", "filesystem", "secrets"):
        if not policy.get(field):
            refuse("POLICY_UNDECLARED", f"{name}: policy.{field} is not declared")
    if policy.get("secrets") != "none":
        refuse("POLICY_UNDECLARED",
               f"{name}: policy.secrets is {policy.get('secrets')!r}; an adapter that "
               f"needs a secret needs a separate admission, not a receipt field")


def check_budgets(body: dict[str, Any], name: str) -> None:
    budgets = body["budgets"]
    for field in ("timeout_seconds", "max_output_bytes"):
        value = budgets.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            refuse("BUDGET_UNBOUNDED", f"{name}: budgets.{field} must be a bounded integer")
    if body["result"].get("state") not in UNEXERCISED_STATES:
        if budgets["timeout_seconds"] <= 0:
            refuse("BUDGET_UNBOUNDED", f"{name}: an executed lane needs a positive timeout")


def check_execution(body: dict[str, Any], name: str) -> None:
    """An unexercised provider cannot carry a run's evidence, and the reverse."""
    execution = body["execution"]
    state = body["result"].get("state")
    if state in UNEXERCISED_STATES:
        if execution.get("terminal_state") not in {"NOT_STARTED", "EXECUTABLE_ABSENT"}:
            refuse("STATE_LAUNDERED",
                   f"{name}: result state {state} with terminal_state "
                   f"{execution.get('terminal_state')!r}; a lane that did not run has no run")
        if execution.get("duration_ms") or execution.get("stdout_bytes"):
            refuse("STATE_LAUNDERED",
                   f"{name}: result state {state} yet the execution records a duration or "
                   f"output")
        return

    if execution.get("terminal_state") != "COMPLETED":
        refuse("STATE_LAUNDERED",
               f"{name}: terminal_state {execution.get('terminal_state')!r} cannot support "
               f"result state {state}")
    if state == "PASS" and execution.get("exit_code") != 0:
        refuse("STATE_LAUNDERED",
               f"{name}: PASS with exit code {execution.get('exit_code')!r}")
    for field in ("stdout_sha256", "stderr_sha256"):
        value = execution.get(field)
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            refuse("RECEIPT_MALFORMED", f"{name}: execution.{field} must be a SHA-256")


def check_evidence(body: dict[str, Any], name: str) -> None:
    """The level a lane claims must be one its read-back actually supports."""
    result = body["result"]
    state = result.get("state")
    if state not in VALID_STATES:
        refuse("RECEIPT_MALFORMED", f"{name}: result.state {state!r} is not an admitted state")

    level = result.get("evidence_level")
    if state in UNEXERCISED_STATES:
        if level is not None:
            refuse("EVIDENCE_LEVEL_OVERCLAIMED",
                   f"{name}: state {state} carries evidence level {level!r}")
        return
    if level not in EVIDENCE_LEVELS:
        refuse("EVIDENCE_LEVEL_OVERCLAIMED",
               f"{name}: evidence_level {level!r} is not in the admitted set")

    readback = result.get("source_readback")
    if not isinstance(readback, dict):
        refuse("READBACK_MISSING", f"{name}: result.source_readback is required")
    for field in ("required", "performed", "confirmed"):
        if field not in readback:
            refuse("READBACK_MISSING", f"{name}: source_readback.{field} is required")

    confirmed = readback["confirmed"]
    performed = readback["performed"]
    if confirmed > performed:
        refuse("READBACK_MISSING",
               f"{name}: {confirmed} confirmed of {performed} performed read-backs")

    if level in READBACK_LEVELS and state == "PASS":
        if not readback["required"]:
            refuse("EVIDENCE_LEVEL_OVERCLAIMED",
                   f"{name}: level {level} requires source read-back by definition, but "
                   f"the receipt declares it optional")
        if confirmed < 1:
            refuse("EVIDENCE_LEVEL_OVERCLAIMED",
                   f"{name}: level {level} claimed with no confirmed read-back")
    if level == "B+" and result.get("result_count", 0) > 0 and not readback["required"]:
        refuse("EVIDENCE_LEVEL_OVERCLAIMED",
               f"{name}: an indexed-candidate lane must require read-back before any hit "
               f"is promoted")


def check_controls(body: dict[str, Any], name: str) -> None:
    """A PASS with no control that could have turned it red is an unproven PASS."""
    controls = body["controls"]
    state = body["result"].get("state")
    if state in UNEXERCISED_STATES:
        return
    if not isinstance(controls, list) or not controls:
        refuse("CONTROL_MISSING",
               f"{name}: state {state} with no control; a lane that cannot be shown to "
               f"fail has not been shown to work")
    for index, control in enumerate(controls):
        if not isinstance(control, dict) or not control.get("id"):
            refuse("CONTROL_MISSING", f"{name}: controls[{index}] has no id")
        if "observed" not in control:
            refuse("CONTROL_MISSING",
                   f"{name}: control {control.get('id')!r} records no observation")
    if state == "PASS" and not any(c.get("observed") == "RED" for c in controls):
        refuse("CONTROL_MISSING",
               f"{name}: PASS with no control observed RED; every control agreed with the "
               f"result it was meant to challenge")


def check_residue(body: dict[str, Any], name: str) -> None:
    residue = body["residue"]
    if "paths" not in residue or "cleaned" not in residue:
        refuse("RESIDUE_UNDECLARED", f"{name}: residue.paths and residue.cleaned are required")
    if not isinstance(residue["paths"], list):
        refuse("RESIDUE_UNDECLARED", f"{name}: residue.paths must be a list")
    if residue["paths"] and residue["cleaned"] is True:
        refuse("RESIDUE_UNDECLARED",
               f"{name}: residue is declared cleaned while paths remain listed")


def check_secrets(body: Any, name: str, path: str = "") -> None:
    if isinstance(body, dict):
        for key, value in body.items():
            check_secrets(value, name, f"{path}.{key}")
    elif isinstance(body, list):
        for index, value in enumerate(body):
            check_secrets(value, name, f"{path}[{index}]")
    elif isinstance(body, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(body):
                refuse("SECRET_IN_RECEIPT", f"{name}: secret-shaped value at {path}")


CHECKS = (check_subject, check_identity, check_policy, check_budgets,
          check_execution, check_evidence, check_controls, check_residue)


def validate_one(body: Any, name: str) -> None:
    check_shape(body, name)
    check_secrets(body, name)
    for check in CHECKS:
        check(body, name)


def validate_set(receipts: dict[str, Any]) -> None:
    if not receipts:
        refuse("RECEIPT_MALFORMED", "no receipts found")
    for name, body in sorted(receipts.items()):
        validate_one(body, name)
    subjects = {body["subject"]["commit_sha"] for body in receipts.values()}
    if len(subjects) > 1:
        refuse("SUBJECT_UNBOUND",
               f"receipts span {len(subjects)} commits; one capture is one subject")


def load_dir(directory: Path) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    for path in sorted(directory.glob("*.receipt.json")):
        receipts[path.name] = json.loads(path.read_text(encoding="utf-8"))
    return receipts


def derive_unexercised(body: dict[str, Any]) -> dict[str, Any]:
    """Turn a copy of an executed receipt into the shape of a lane that did not run.

    Derived here rather than imported from the capture script: the two files
    deliberately share no code path, and a selftest that borrowed the producer's
    idea of an unexercised receipt could not catch the producer disagreeing with
    the law. Every field the unexercised laws read is set explicitly.
    """
    copied = copy.deepcopy(body)
    copied["adapter"].update({"executable": None, "version": None,
                              "executable_sha256": None})
    copied["policy"] = {"network": "none", "filesystem": "none", "secrets": "none",
                        "allowed_argv": []}
    copied["budgets"] = {"timeout_seconds": 0, "max_output_bytes": 0}
    copied["execution"] = {"terminal_state": "NOT_STARTED", "exit_code": None}
    copied["result"] = {"state": "ABSENT", "evidence_level": None, "result_count": 0,
                        "source_readback": {"required": False, "performed": 0,
                                            "confirmed": 0},
                        "detail": "derived by the selftest, never captured"}
    copied["residue"] = {"paths": [], "cleaned": True}
    copied["controls"] = []
    return copied


def selftest(receipts: dict[str, Any]) -> int:
    """Plant one defect per law and require its own refusal."""
    try:
        validate_set(receipts)
    except Refused as failure:
        print(f"SELFTEST RED: committed receipts already refused -- {failure}",
              file=sys.stderr)
        return 2

    committed = len(receipts)
    executed = next((n for n, b in receipts.items()
                     if b["result"]["state"] not in UNEXERCISED_STATES), None)
    if executed is None:
        print("SELFTEST RED: no executed receipt to plant an executed lane's defects on",
              file=sys.stderr)
        return 2

    unexercised = next((n for n, b in receipts.items()
                        if b["result"]["state"] in UNEXERCISED_STATES), None)
    derived = None
    if unexercised is None:
        # A capture in which every lane ran is the goal, not a reason to stop
        # planting. The two laws about a lane that did not run must stay provable
        # on a fully exercised set, or the day the last ABSENT lane is closed is
        # the day those two refusals quietly stop being tested.
        derived = "derived-unexercised.receipt.json"
        receipts = dict(receipts)
        receipts[derived] = derive_unexercised(receipts[executed])
        unexercised = derived
        try:
            validate_set(receipts)
        except Refused as failure:
            print(f"SELFTEST RED: the derived unexercised receipt is itself refused "
                  f"-- {failure}", file=sys.stderr)
            return 2

    def mutated(target: str, fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(receipts)
        fn(copied[target])
        return copied

    controls: list[tuple[str, str, dict[str, Any]]] = [
        ("subject-unbound", "SUBJECT_UNBOUND",
         mutated(executed, lambda b: b["subject"].update({"commit_sha": "deadbeef"}))),
        ("dirty-tree-passes", "SUBJECT_UNBOUND",
         mutated(executed, lambda b: b["subject"].update({"dirty_paths": 3}))),
        ("provider-unidentified", "PROVIDER_UNIDENTIFIED",
         mutated(executed, lambda b: b["adapter"].update({"version": None}))),
        ("policy-undeclared", "POLICY_UNDECLARED",
         mutated(executed, lambda b: b["policy"].pop("network", None))),
        ("secret-admitted", "POLICY_UNDECLARED",
         mutated(executed, lambda b: b["policy"].update({"secrets": "env"}))),
        ("budget-unbounded", "BUDGET_UNBOUNDED",
         mutated(executed, lambda b: b["budgets"].update({"timeout_seconds": 0}))),
        ("absent-lane-carries-a-run", "STATE_LAUNDERED",
         mutated(unexercised, lambda b: b["execution"].update(
             {"terminal_state": "COMPLETED", "duration_ms": 12}))),
        ("pass-on-nonzero-exit", "STATE_LAUNDERED",
         mutated(executed, lambda b: b["execution"].update({"exit_code": 1}))),
        ("absent-lane-claims-a-level", "EVIDENCE_LEVEL_OVERCLAIMED",
         mutated(unexercised, lambda b: b["result"].update({"evidence_level": "A"}))),
        ("readback-dropped", "READBACK_MISSING",
         mutated(executed, lambda b: b["result"].pop("source_readback"))),
        ("controls-removed", "CONTROL_MISSING",
         mutated(executed, lambda b: b.update({"controls": []}))),
        ("no-control-went-red", "CONTROL_MISSING",
         mutated(executed, lambda b: b.update(
             {"controls": [{"id": "agreeable", "observed": "GREEN"}]}))),
        ("residue-undeclared", "RESIDUE_UNDECLARED",
         mutated(executed, lambda b: b["residue"].pop("cleaned"))),
        ("secret-leaked", "SECRET_IN_RECEIPT",
         mutated(executed, lambda b: b["policy"].update(
             {"note": "api_key = " + "A" * 32}))),
    ]

    # Level A claimed without a confirmed read-back, planted on a lane that
    # actually has read-back so the refusal is about the claim, not the shape.
    readback_lane = next((n for n, b in receipts.items()
                          if b["result"].get("evidence_level") in READBACK_LEVELS
                          and b["result"]["state"] == "PASS"), None)
    if readback_lane:
        controls.append((
            "level-a-without-readback", "EVIDENCE_LEVEL_OVERCLAIMED",
            mutated(readback_lane,
                    lambda b: b["result"]["source_readback"].update({"confirmed": 0}))))

    failed = 0
    for name, code, mutation in controls:
        try:
            validate_set(mutation)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                  file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused", file=sys.stderr)
        failed += 1

    if failed:
        return 2
    note = "" if derived is None else (
        " (every committed lane ran, so the unexercised receipt the last two "
        "controls need was derived from an executed one)")
    print(f"SELFTEST GREEN: {committed} committed receipt(s) admitted; "
          f"{len(controls)} planted defects refused{note}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    parser.add_argument("--receipts", type=Path,
                        default=Path(__file__).resolve().parent.parent / "evals" / "receipts")
    args = parser.parse_args(argv)

    if not args.receipts.is_dir():
        print(f"USAGE: {args.receipts} is not a directory", file=sys.stderr)
        return 64
    try:
        receipts = load_dir(args.receipts)
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable receipt: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(receipts)

    try:
        validate_set(receipts)
    except Refused as failure:
        print(f"ADAPTER RECEIPT REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    states: dict[str, int] = {}
    for body in receipts.values():
        state = body["result"]["state"]
        states[state] = states.get(state, 0) + 1
    summary = ", ".join(f"{count} {state}" for state, count in sorted(states.items()))
    subject = next(iter(receipts.values()))["subject"]["commit_sha"][:12]
    print(f"ADAPTER RECEIPTS GREEN: {len(receipts)} lane(s) at {subject} -- {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
