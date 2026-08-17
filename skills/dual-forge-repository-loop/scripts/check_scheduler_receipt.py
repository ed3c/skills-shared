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

The budget ledger is read the same way. Its absence is its own state,
BUDGET_UNMEASURED, because the committed canary ran before the ledger existed:
that run's spend was never measured, which is a different claim from having
spent nothing, and neither the receipt nor this checker may turn one into the
other after the fact. When a ledger is present every number in it is recomputed
from the attempts, and an attempt that passed a cap has to be terminal and
unleased -- over budget and still running is a budget nothing enforced.

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

# A receipt written before the budget ledger existed carries no ledger at all.
# That is its own state and is reported as such: the run happened, its spend was
# never measured, and no later edit may hand it numbers it did not record.
BUDGET_UNMEASURED = "BUDGET_UNMEASURED"
BUDGET_LEDGERED = "BUDGET_LEDGERED"
LEDGER_FIELDS = ("dimensions", "attempt_limits", "global_limits", "attempts",
                 "totals", "unobserved_dimensions", "global_over_budget")


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


def last_states(body: dict[str, Any]) -> dict[str, str]:
    """The state each attempt was left in, read off the log rather than the attempt."""
    final: dict[str, str] = {}
    for transition in body["transitions"]:
        final[transition["attempt_id"]] = transition["state"]
    return final


def check_leases_released_at_close(body: dict[str, Any]) -> None:
    """Nothing still holds a lease when the run ends.

    A run that closes over a live lease has left a writer nobody will reclaim
    from, and the next scheduler cannot tell that lease from one being used.
    """
    active = sorted(attempt["attempt_id"] for attempt in body["attempts"]
                    if (attempt.get("lease") or {}).get("status") == "ACTIVE")
    if active:
        refuse("LEASE_ACTIVE_AT_CLOSE",
               f"{', '.join(active)} still hold an ACTIVE lease at {body['ended_at']}")


def budget_state(body: dict[str, Any]) -> str:
    ledger = body.get("budget_ledger")
    if ledger is None:
        return BUDGET_UNMEASURED
    if not isinstance(ledger, dict):
        refuse("BUDGET_LEDGER_MALFORMED", "budget_ledger is not an object")
    return BUDGET_LEDGERED


def check_budget_ledger(body: dict[str, Any]) -> None:
    """Reconcile every attempt's spend against the caps the receipt itself declares.

    Three things have to hold together. Each attempt's declared overrun must be
    the one recomputed from its own spend, so the ledger cannot report a clean
    run it did not have. An attempt that did exceed a cap must be terminal and
    unleased, because a Worker over budget and still running is a budget nothing
    enforces. And a dimension declared unobserved must carry no spend, because a
    ledger allowed to record unknowns as zero reconciles every time.
    """
    if budget_state(body) == BUDGET_UNMEASURED:
        if body.get("budgets_reconciled"):
            refuse("BUDGET_UNMEASURED_BUT_CLAIMED",
                   "the receipt claims reconciled budgets and carries no budget_ledger; "
                   "a run that recorded no spend cannot be reconciled afterwards")
        return

    ledger = body["budget_ledger"]
    for field in LEDGER_FIELDS:
        if field not in ledger:
            refuse("BUDGET_LEDGER_MALFORMED", f"budget_ledger has no {field}")
    dimensions = ledger["dimensions"]
    if not dimensions:
        refuse("BUDGET_LEDGER_MALFORMED", "budget_ledger measures no dimension")

    entries: dict[str, Any] = {}
    for entry in ledger["attempts"]:
        attempt_id = entry.get("attempt_id")
        if attempt_id in entries:
            refuse("BUDGET_LEDGER_MALFORMED", f"{attempt_id} is charged twice")
        entries[attempt_id] = entry
    known = {attempt["attempt_id"] for attempt in body["attempts"]}
    missing = sorted(known - set(entries))
    strangers = sorted(set(entries) - known)
    if missing or strangers:
        refuse("BUDGET_LEDGER_INCOMPLETE",
               f"unledgered attempts {missing}, ledgered strangers {strangers}")

    final = last_states(body)
    totals = {dimension: 0.0 for dimension in dimensions}
    unobserved: set[str] = set()
    for attempt in body["attempts"]:
        attempt_id = attempt["attempt_id"]
        entry = entries[attempt_id]
        spend = entry.get("spend")
        observed = entry.get("observed")
        if not isinstance(spend, dict) or not isinstance(observed, list):
            refuse("BUDGET_LEDGER_MALFORMED", f"{attempt_id} has no spend and observed")
        for dimension in dimensions:
            if dimension not in spend:
                refuse("BUDGET_LEDGER_MALFORMED",
                       f"{attempt_id} records no {dimension}")
            if dimension not in observed:
                unobserved.add(dimension)
                if spend[dimension]:
                    refuse("BUDGET_LEDGER_MALFORMED",
                           f"{attempt_id} charges {spend[dimension]} {dimension} while "
                           f"declaring that dimension unobserved; a number nobody "
                           f"measured is not a spend")
            totals[dimension] += spend[dimension]

        derived = sorted(d for d in dimensions if d in observed
                         and spend[d] > ledger["attempt_limits"][d])
        if entry.get("over_budget") != derived:
            refuse("BUDGET_NOT_RECONCILED",
                   f"{attempt_id} declares over_budget {entry.get('over_budget')} while "
                   f"its own spend exceeds {derived}")
        if derived:
            state = final.get(attempt_id)
            if state not in TERMINAL:
                refuse("BUDGET_OVERRUN_UNENFORCED",
                       f"{attempt_id} exceeded {derived} and its last state is {state}, "
                       f"which is not terminal")
            if (attempt.get("lease") or {}).get("status") == "ACTIVE":
                refuse("BUDGET_OVERRUN_UNENFORCED",
                       f"{attempt_id} exceeded {derived} and still holds an ACTIVE lease")

    for dimension in dimensions:
        declared = ledger["totals"].get(dimension)
        if not isinstance(declared, (int, float)) or abs(declared - totals[dimension]) > 1e-6:
            refuse("BUDGET_NOT_RECONCILED",
                   f"totals.{dimension} is {declared} against {round(totals[dimension], 3)} "
                   f"summed from the ledger")
    if ledger["unobserved_dimensions"] != sorted(unobserved):
        refuse("BUDGET_NOT_RECONCILED",
               f"unobserved_dimensions is {ledger['unobserved_dimensions']} against "
               f"{sorted(unobserved)} derived from the attempts")

    global_over = sorted(d for d in dimensions if d not in unobserved
                         and totals[d] > ledger["global_limits"][d])
    if ledger["global_over_budget"] != global_over:
        refuse("BUDGET_NOT_RECONCILED",
               f"global_over_budget is {ledger['global_over_budget']} against "
               f"{global_over} derived from the totals")
    if global_over:
        refuse("BUDGET_OVERRUN_UNENFORCED",
               f"the run as a whole passed {global_over}; a global cap that stopped "
               f"nothing is a number in a receipt")


CHECKS = (check_identities, check_sequence, check_verification_precedes_integration,
          check_leases, check_lease_expiry, check_heartbeats, check_coverage,
          check_leases_released_at_close, check_budget_ledger)


def validate(body: Any) -> None:
    check_shape(body)
    for check in CHECKS:
        check(body)


def synthesize_ledger(body: dict[str, Any]) -> dict[str, Any]:
    """Give the ledger controls a base, derived from the receipt they are planted in.

    The committed receipt was produced before the ledger existed, so there is no
    ledger in it to plant a defect in. Editing it to add one would rewrite an
    executed run's evidence, which is the one thing this file must never do.
    So the base is built here, in memory, from what the receipt does record --
    each Worker's own measured duration -- and validated before anything is
    planted in it. Every other dimension is left unobserved rather than filled
    with zeros, which is also what a real run does when the Agent's output will
    not parse.
    """
    copied = copy.deepcopy(body)

    # The overrun control needs an attempt that is still live. A clean run leaves
    # none, so one is added here rather than the control being skipped on the
    # shapes it matters most for. PLANNED appears in every receipt, so adding it
    # moves no coverage number.
    final = last_states(copied)
    if all(final.get(a["attempt_id"]) in TERMINAL for a in copied["attempts"]):
        seed = copied["attempts"][0]
        live = copy.deepcopy(seed)
        live["attempt_id"] = f"{seed['attempt_id']}-selftest-live"
        live["logical_id"] = f"{seed.get('logical_id')}-selftest-live"
        live["lease"] = {"status": "RELEASED", "expiry": None, "heartbeat_sequence": 0}
        live["heartbeats"] = []
        copied["attempts"].append(live)
        copied["transitions"].append({
            "sequence": copied["transitions"][-1]["sequence"] + 1,
            "attempt_id": live["attempt_id"], "task_id": live["task_id"],
            "state": "PLANNED", "at": copied["ended_at"]})

    by_logical = {attempt.get("logical_id"): attempt["attempt_id"]
                  for attempt in copied["attempts"]}
    measured = {by_logical[logical]: round(result.get("duration_ms", 0) / 1000, 3)
                for logical, result in (copied.get("results") or {}).items()
                if logical in by_logical}

    entries = [{"attempt_id": attempt["attempt_id"],
                "spend": {"turns": 0, "tokens": 0, "cost_usd": 0.0,
                          "wall_clock_seconds": measured.get(attempt["attempt_id"], 0)},
                "observed": ["wall_clock_seconds"],
                "over_budget": []}
               for attempt in copied["attempts"]]
    copied["budget_ledger"] = {
        "dimensions": ["cost_usd", "tokens", "turns", "wall_clock_seconds"],
        # The fixture's own caps. The checker never assumes any producer's policy;
        # it reconciles against whatever caps the receipt in front of it declares.
        "attempt_limits": {"turns": 40, "tokens": 120000, "wall_clock_seconds": 900,
                           "cost_usd": 2.0},
        "global_limits": {"turns": 200, "tokens": 600000, "wall_clock_seconds": 3600,
                          "cost_usd": 6.0},
        "attempts": entries,
        "totals": {"cost_usd": 0.0, "tokens": 0, "turns": 0,
                   "wall_clock_seconds": round(sum(measured.values()), 3)},
        "unobserved_dimensions": ["cost_usd", "tokens", "turns"],
        "global_over_budget": [],
    }
    return copied


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
        # Any terminal state will do. Reaching for INTEGRATED specifically made
        # this control crash on a receipt whose Workers all failed their oracle,
        # which is a shape a real run produces.
        last = doc["transitions"][-1]
        finished = next(t for t in doc["transitions"] if t["state"] in TERMINAL)
        doc["transitions"].append({
            "sequence": last["sequence"] + 1, "attempt_id": finished["attempt_id"],
            "task_id": finished["task_id"], "state": "RUNNING", "at": doc["ended_at"]})

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

    ledgered = synthesize_ledger(body)
    try:
        validate(ledgered)
    except Refused as failure:
        print(f"SELFTEST RED: the synthesized ledger base is already refused, so "
              f"nothing planted in it would prove anything -- {failure}", file=sys.stderr)
        return 2

    def with_ledger(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(ledgered)
        fn(copied)
        return copied

    def entry_of(doc: dict[str, Any], attempt_id: str) -> dict[str, Any]:
        return next(e for e in doc["budget_ledger"]["attempts"]
                    if e["attempt_id"] == attempt_id)

    def live_attempt(doc: dict[str, Any]) -> str:
        final = last_states(doc)
        return next(a["attempt_id"] for a in doc["attempts"]
                    if final.get(a["attempt_id"]) not in TERMINAL)

    def overrun_still_active(doc: dict[str, Any]) -> None:
        """The issue's own control: a Worker over budget that nothing stopped."""
        attempt_id = live_attempt(doc)
        entry = entry_of(doc, attempt_id)
        limit = doc["budget_ledger"]["attempt_limits"]["tokens"]
        entry["spend"]["tokens"] = limit + 1
        entry["observed"] = sorted(set(entry["observed"]) | {"tokens"})
        entry["over_budget"] = ["tokens"]
        doc["budget_ledger"]["totals"]["tokens"] += limit + 1

    def overrun_hidden(doc: dict[str, Any]) -> None:
        overrun_still_active(doc)
        entry_of(doc, live_attempt(doc))["over_budget"] = []

    def inflate_totals(doc: dict[str, Any]) -> None:
        doc["budget_ledger"]["totals"]["wall_clock_seconds"] += 5

    def drop_ledger_entry(doc: dict[str, Any]) -> None:
        doc["budget_ledger"]["attempts"].pop(0)

    def charge_unobserved(doc: dict[str, Any]) -> None:
        entry = doc["budget_ledger"]["attempts"][0]
        entry["spend"]["tokens"] = 5
        doc["budget_ledger"]["totals"]["tokens"] += 5

    def truncate_ledger(doc: dict[str, Any]) -> None:
        doc["budget_ledger"].pop("totals")

    def blow_global_cap(doc: dict[str, Any]) -> None:
        # Charge a terminal attempt enough to pass the global cap without passing
        # its own, so the only thing left unenforced is the global one.
        ledger = doc["budget_ledger"]
        entry = ledger["attempts"][0]
        entry["spend"]["wall_clock_seconds"] += 10
        entry["observed"] = sorted(set(entry["observed"]) | {"wall_clock_seconds"})
        ledger["totals"]["wall_clock_seconds"] += 10
        ledger["global_limits"]["wall_clock_seconds"] = 1
        ledger["global_over_budget"] = ["wall_clock_seconds"]

    def claim_without_ledger(doc: dict[str, Any]) -> None:
        # Strip whatever ledger the receipt has: this control is about a run that
        # measured nothing claiming it reconciled, and it must plant that state
        # rather than assume the receipt already happens to be in it.
        doc.pop("budget_ledger", None)
        doc["budgets_reconciled"] = True

    def hold_lease_at_close(doc: dict[str, Any]) -> None:
        doc["attempts"][0]["lease"]["status"] = "ACTIVE"

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
        ("lease-active-at-close", "LEASE_ACTIVE_AT_CLOSE", mutate(hold_lease_at_close)),
        ("budget-claimed-without-ledger", "BUDGET_UNMEASURED_BUT_CLAIMED",
         mutate(claim_without_ledger)),
        ("budget-overrun-still-active", "BUDGET_OVERRUN_UNENFORCED",
         with_ledger(overrun_still_active)),
        ("budget-overrun-hidden", "BUDGET_NOT_RECONCILED", with_ledger(overrun_hidden)),
        ("budget-totals-inflated", "BUDGET_NOT_RECONCILED", with_ledger(inflate_totals)),
        ("budget-attempt-unledgered", "BUDGET_LEDGER_INCOMPLETE",
         with_ledger(drop_ledger_entry)),
        ("budget-unobserved-but-charged", "BUDGET_LEDGER_MALFORMED",
         with_ledger(charge_unobserved)),
        ("budget-ledger-truncated", "BUDGET_LEDGER_MALFORMED",
         with_ledger(truncate_ledger)),
        ("budget-global-cap-blown", "BUDGET_OVERRUN_UNENFORCED",
         with_ledger(blow_global_cap)),
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
    state = budget_state(body)
    if state == BUDGET_UNMEASURED:
        budget = ("budget BUDGET_UNMEASURED: this run predates the ledger and recorded "
                  "no spend, which is not the same as having spent nothing")
    else:
        ledger = body["budget_ledger"]
        budget = (f"budget reconciled over {len(ledger['attempts'])} attempts, "
                  f"unobserved {', '.join(ledger['unobserved_dimensions']) or 'none'}")
    print(f"SCHEDULER RECEIPT GREEN: {len(body['transitions'])} transitions, "
          f"{integrated} integrated, {len(produced)}/{len(DECLARED_STATES)} declared "
          f"states produced; not produced: {', '.join(missing) or 'none'}; {budget}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
