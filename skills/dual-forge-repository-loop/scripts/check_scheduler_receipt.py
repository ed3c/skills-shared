#!/usr/bin/env python3
"""Validate a live multi-Worker scheduler receipt. Zero network, zero execution.

`run_worker_scheduler.py` drives real Workers and writes the transition log.
This reads only that log, so a reviewer on a host with no Agent can still judge
whether the run obeyed the lifecycle -- and, more importantly, whether the
scheduler awarded itself anything the contract does not allow.

The rule this exists for is the coverage rule. worker-task.schema.json declares
twenty-one states; a receipt that produced nine of them and said nothing about
the rest reads exactly like a receipt that produced all of them. Every declared
state must appear either in the transition log or in the receipt's own
`declared_not_produced` list, and the checker recomputes both rather than
believing either.

Exit codes: 0 pass, 2 receipt failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "dual-forge-repository-loop/scheduler-run-receipt/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
TIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

DECLARED_STATES = {
    "PLANNED", "ADMITTED", "ASSIGNED", "LEASED", "RUNNING", "CHECKPOINTED",
    "RESULT_READY", "RESULT_VERIFIED", "INTEGRATED", "REJECTED_NOT_DECOMPOSABLE",
    "DUPLICATE_SUPPRESSED", "STALE_ATTEMPT", "LEASE_EXPIRED", "TIMED_OUT",
    "CANCELLED", "STRAGGLER_DETACHED", "FAILED_RETRYABLE", "FAILED_TERMINAL",
    "BLOCKED_AUTHORITY", "BLOCKED_CONFLICT", "SUPERSEDED",
}

TERMINAL = {"INTEGRATED", "STALE_ATTEMPT", "LEASE_EXPIRED", "CANCELLED",
            "STRAGGLER_DETACHED", "FAILED_TERMINAL", "BLOCKED_AUTHORITY",
            "BLOCKED_CONFLICT", "SUPERSEDED", "REJECTED_NOT_DECOMPOSABLE",
            "DUPLICATE_SUPPRESSED"}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def parse_time(value: str, code: str, what: str) -> datetime:
    if not isinstance(value, str) or not TIME.fullmatch(value):
        refuse(code, f"{what} is not an RFC3339 Z timestamp: {value!r}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def check_shape(body: Any) -> None:
    if not isinstance(body, dict) or body.get("schema") != SCHEMA:
        refuse("RECEIPT_MALFORMED", f"schema must be {SCHEMA}")
    for section in ("run_id", "subject", "started_at", "ended_at", "attempts",
                    "transitions", "refusals", "planted", "state_coverage",
                    "declared_non_claims"):
        if section not in body:
            refuse("RECEIPT_MALFORMED", f"receipt has no {section}")
    if not body["transitions"]:
        refuse("RECEIPT_MALFORMED", "receipt records no transition")


def check_identities(body: dict[str, Any]) -> None:
    """Attempt identities are globally unique; a reused one hides a second run."""
    seen: set[str] = set()
    for attempt in body["attempts"]:
        attempt_id = attempt.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            refuse("IDENTITY_NOT_UNIQUE", "an attempt has no attempt_id")
        if attempt_id in seen:
            refuse("IDENTITY_NOT_UNIQUE", f"attempt_id {attempt_id} appears twice")
        seen.add(attempt_id)
        if not attempt.get("task_id"):
            refuse("IDENTITY_NOT_UNIQUE", f"{attempt_id} has no task_id")

    for transition in body["transitions"]:
        if transition.get("attempt_id") not in seen:
            refuse("IDENTITY_NOT_UNIQUE",
                   f"transition {transition.get('sequence')} names unknown attempt "
                   f"{transition.get('attempt_id')!r}")


def check_sequence(body: dict[str, Any]) -> None:
    """The log is ordered, monotonic in time, and no attempt moves after terminal."""
    previous_sequence = 0
    previous_time = parse_time(body["started_at"], "RECEIPT_MALFORMED", "started_at")
    terminated: dict[str, str] = {}

    for transition in body["transitions"]:
        sequence = transition.get("sequence")
        if not isinstance(sequence, int) or sequence != previous_sequence + 1:
            refuse("TRANSITION_LOG_BROKEN",
                   f"sequence {sequence!r} does not follow {previous_sequence}")
        previous_sequence = sequence

        state = transition.get("state")
        if state not in DECLARED_STATES:
            refuse("UNDECLARED_STATE", f"transition {sequence} records state {state!r}")

        moment = parse_time(transition.get("at"), "TRANSITION_LOG_BROKEN",
                            f"transition {sequence}.at")
        if moment < previous_time:
            refuse("TRANSITION_LOG_BROKEN",
                   f"transition {sequence} at {transition['at']} precedes the previous one")
        previous_time = moment

        attempt_id = transition["attempt_id"]
        if attempt_id in terminated:
            refuse("TRANSITION_AFTER_TERMINAL",
                   f"{attempt_id} reached {terminated[attempt_id]} and then moved to "
                   f"{state} at transition {sequence}")
        if state in TERMINAL:
            terminated[attempt_id] = state


def check_verification_precedes_integration(body: dict[str, Any]) -> None:
    """Nothing is integrated that an oracle did not verify first."""
    verified: dict[str, dict[str, Any]] = {}
    for transition in body["transitions"]:
        attempt_id = transition["attempt_id"]
        if transition["state"] == "RESULT_VERIFIED":
            if not transition.get("oracle"):
                refuse("UNVERIFIED_INTEGRATION",
                       f"{attempt_id} recorded RESULT_VERIFIED with no oracle")
            if transition.get("exit_code") != 0:
                refuse("UNVERIFIED_INTEGRATION",
                       f"{attempt_id} recorded RESULT_VERIFIED with exit code "
                       f"{transition.get('exit_code')!r}")
            verified[attempt_id] = transition
        elif transition["state"] == "INTEGRATED":
            if attempt_id not in verified:
                refuse("UNVERIFIED_INTEGRATION",
                       f"{attempt_id} integrated with no preceding RESULT_VERIFIED")
            head = transition.get("head_subject_sha")
            if not isinstance(head, str) or not SHA40.fullmatch(head):
                refuse("UNVERIFIED_INTEGRATION",
                       f"{attempt_id} integrated without a 40-character head sha")


def check_leases(body: dict[str, Any]) -> None:
    """One active writer per branch and per path, replayed over the log."""
    by_id = {a["attempt_id"]: a for a in body["attempts"]}
    branch_holder: dict[str, str] = {}
    path_holder: dict[str, str] = {}

    for transition in body["transitions"]:
        attempt_id = transition["attempt_id"]
        attempt = by_id[attempt_id]
        state = transition["state"]

        if state == "ASSIGNED":
            branch = transition.get("branch") or attempt.get("branch")
            holder = branch_holder.get(branch)
            if holder and holder != attempt_id:
                refuse("LEASE_DOUBLE_HELD",
                       f"branch {branch} assigned to {attempt_id} while {holder} holds it")
            branch_holder[branch] = attempt_id
        elif state == "ADMITTED" and transition.get("base_rebound_to") is None:
            for path in attempt.get("allowed_paths", []):
                holder = path_holder.get(path)
                if holder and holder != attempt_id:
                    refuse("LEASE_DOUBLE_HELD",
                           f"path {path} admitted to {attempt_id} while {holder} holds it")
                path_holder[path] = attempt_id
        elif state in {"INTEGRATED", "CANCELLED", "FAILED_TERMINAL", "SUPERSEDED"}:
            branch = attempt.get("branch")
            if branch_holder.get(branch) == attempt_id:
                branch_holder.pop(branch, None)


def check_lease_expiry(body: dict[str, Any]) -> None:
    """A lease recorded EXPIRED must have an expiry the evaluation actually passed."""
    for transition in body["transitions"]:
        if transition["state"] != "LEASE_EXPIRED":
            continue
        evaluated = transition.get("evaluated_at")
        if not evaluated:
            refuse("LEASE_EXPIRY_UNPROVEN",
                   f"{transition['attempt_id']} recorded LEASE_EXPIRED with no "
                   f"evaluation time; an expiry nothing compared against is a field")
        attempt = next(a for a in body["attempts"]
                       if a["attempt_id"] == transition["attempt_id"])
        expiry = attempt.get("lease", {}).get("expiry")
        if not expiry:
            refuse("LEASE_EXPIRY_UNPROVEN",
                   f"{transition['attempt_id']} has no lease expiry to expire")
        if parse_time(expiry, "LEASE_EXPIRY_UNPROVEN", "lease.expiry") >= parse_time(
                evaluated, "LEASE_EXPIRY_UNPROVEN", "evaluated_at"):
            refuse("LEASE_EXPIRY_UNPROVEN",
                   f"{transition['attempt_id']} expiry {expiry} is not before the "
                   f"evaluation at {evaluated}")


def check_heartbeats(body: dict[str, Any]) -> None:
    for attempt in body["attempts"]:
        sequence = 0
        for beat in attempt.get("heartbeats", []):
            if beat.get("sequence") != sequence + 1:
                refuse("HEARTBEAT_BROKEN",
                       f"{attempt['attempt_id']} heartbeat {beat.get('sequence')!r} does "
                       f"not follow {sequence}")
            sequence = beat["sequence"]
        recorded = attempt.get("lease", {}).get("heartbeat_sequence")
        if attempt.get("heartbeats") and recorded != sequence:
            refuse("HEARTBEAT_BROKEN",
                   f"{attempt['attempt_id']} lease records {recorded} heartbeats and the "
                   f"log has {sequence}")


def check_coverage(body: dict[str, Any]) -> None:
    """Recompute coverage; a state list nobody derives is a state list nobody checked."""
    coverage = body["state_coverage"]
    produced = sorted({t["state"] for t in body["transitions"]})
    if coverage.get("produced") != produced:
        refuse("COVERAGE_MISREPORTED",
               f"state_coverage.produced does not match the transition log; the log "
               f"produced {produced}")
    missing = sorted(DECLARED_STATES - set(produced))
    if coverage.get("declared_not_produced") != missing:
        refuse("COVERAGE_MISREPORTED",
               f"state_coverage.declared_not_produced does not match the contract; the "
               f"unproduced states are {missing}")
    if not body["declared_non_claims"]:
        refuse("COVERAGE_MISREPORTED",
               "a run that measured no throughput advantage must say so; "
               "declared_non_claims is empty")


CHECKS = (check_identities, check_sequence, check_verification_precedes_integration,
          check_leases, check_lease_expiry, check_heartbeats, check_coverage)


def validate(body: Any) -> None:
    check_shape(body)
    for check in CHECKS:
        check(body)


def selftest(body: dict[str, Any]) -> int:
    try:
        validate(body)
    except Refused as failure:
        print(f"SELFTEST RED: committed receipt already refused -- {failure}",
              file=sys.stderr)
        return 2

    def mutate(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(body)
        fn(copied)
        return copied

    def duplicate_attempt(doc: dict[str, Any]) -> None:
        doc["attempts"].append(copy.deepcopy(doc["attempts"][0]))

    def break_sequence(doc: dict[str, Any]) -> None:
        doc["transitions"][3]["sequence"] = 99

    def unknown_state(doc: dict[str, Any]) -> None:
        doc["transitions"][2]["state"] = "MOSTLY_FINE"

    def move_after_terminal(doc: dict[str, Any]) -> None:
        last = doc["transitions"][-1]
        integrated = next(t for t in doc["transitions"] if t["state"] == "INTEGRATED")
        doc["transitions"].append({
            "sequence": last["sequence"] + 1, "attempt_id": integrated["attempt_id"],
            "task_id": integrated["task_id"], "state": "RUNNING", "at": doc["ended_at"]})

    def integrate_unverified(doc: dict[str, Any]) -> None:
        for transition in doc["transitions"]:
            if transition["state"] == "RESULT_VERIFIED":
                transition["state"] = "RESULT_READY"
                break

    def verified_with_failure(doc: dict[str, Any]) -> None:
        for transition in doc["transitions"]:
            if transition["state"] == "RESULT_VERIFIED":
                transition["exit_code"] = 1
                break

    def double_branch(doc: dict[str, Any]) -> None:
        """Two writers on one branch *at the same time*.

        The first version of this control retargeted a later ASSIGNED onto an
        earlier branch and nothing refused it -- correctly, because the earlier
        holder had already integrated and released. Sequential reuse of a branch
        is legal; simultaneous holding is not. So the violation has to be
        injected while the first lease is still held, which means inserting a
        transition rather than editing one.
        """
        index, first = next((i, t) for i, t in enumerate(doc["transitions"])
                            if t["state"] == "ASSIGNED")
        intruder = next(a for a in doc["attempts"]
                        if a["attempt_id"] != first["attempt_id"])
        injected = {"sequence": first["sequence"] + 1,
                    "attempt_id": intruder["attempt_id"],
                    "task_id": intruder["task_id"], "state": "ASSIGNED",
                    "at": first["at"], "branch": first["branch"]}
        doc["transitions"].insert(index + 1, injected)
        for offset, transition in enumerate(doc["transitions"][index + 2:]):
            transition["sequence"] = injected["sequence"] + 1 + offset

    def unproven_expiry(doc: dict[str, Any]) -> None:
        for transition in doc["transitions"]:
            if transition["state"] == "LEASE_EXPIRED":
                transition.pop("evaluated_at", None)
                break

    def skip_heartbeat(doc: dict[str, Any]) -> None:
        for attempt in doc["attempts"]:
            if len(attempt.get("heartbeats", [])) >= 2:
                attempt["heartbeats"][1]["sequence"] = 5
                break

    def hide_missing_states(doc: dict[str, Any]) -> None:
        doc["state_coverage"]["declared_not_produced"] = []

    def inflate_produced(doc: dict[str, Any]) -> None:
        doc["state_coverage"]["produced"] = sorted(DECLARED_STATES)

    def drop_non_claims(doc: dict[str, Any]) -> None:
        doc["declared_non_claims"] = []

    controls = [
        ("duplicate-attempt-id", "IDENTITY_NOT_UNIQUE", mutate(duplicate_attempt)),
        ("sequence-broken", "TRANSITION_LOG_BROKEN", mutate(break_sequence)),
        ("undeclared-state", "UNDECLARED_STATE", mutate(unknown_state)),
        ("move-after-terminal", "TRANSITION_AFTER_TERMINAL", mutate(move_after_terminal)),
        ("integrate-unverified", "UNVERIFIED_INTEGRATION", mutate(integrate_unverified)),
        ("verified-on-failure", "UNVERIFIED_INTEGRATION", mutate(verified_with_failure)),
        ("two-writers-one-branch", "LEASE_DOUBLE_HELD", mutate(double_branch)),
        ("expiry-never-evaluated", "LEASE_EXPIRY_UNPROVEN", mutate(unproven_expiry)),
        ("heartbeat-skipped", "HEARTBEAT_BROKEN", mutate(skip_heartbeat)),
        ("hide-unproduced-states", "COVERAGE_MISREPORTED", mutate(hide_missing_states)),
        ("claim-every-state", "COVERAGE_MISREPORTED", mutate(inflate_produced)),
        ("drop-non-claims", "COVERAGE_MISREPORTED", mutate(drop_non_claims)),
    ]

    failed = 0
    for name, code, doc in controls:
        try:
            validate(doc)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                  file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused",
              file=sys.stderr)
        failed += 1

    if failed:
        return 2
    print(f"SELFTEST GREEN: committed scheduler receipt admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    default = (Path(__file__).resolve().parent.parent / "evals" / "receipts"
               / "scheduler-run.receipt.json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    parser.add_argument("--receipt", type=Path, default=default)
    args = parser.parse_args(argv)

    try:
        body = json.loads(args.receipt.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable receipt: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(body)

    try:
        validate(body)
    except Refused as failure:
        print(f"SCHEDULER RECEIPT REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    produced = body["state_coverage"]["produced"]
    missing = body["state_coverage"]["declared_not_produced"]
    integrated = sum(1 for t in body["transitions"] if t["state"] == "INTEGRATED")
    print(f"SCHEDULER RECEIPT GREEN: {len(body['transitions'])} transitions, "
          f"{integrated} integrated, {len(produced)}/{len(DECLARED_STATES)} declared "
          f"states produced; not produced: {', '.join(missing) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
