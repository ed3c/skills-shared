#!/usr/bin/env python3
"""Validate a runtime handoff packet. Zero network, no runtime access.

`runtime-identity-contract.md` says what each runtime may claim. This checks the
thing that contract leaves open: whether a plan hands each step to a runtime
that can actually perform it.

The rule the whole file is built around is STEP_EXCEEDS_RUNTIME, and its sharpest
case is IDENTITY_LAUNDERED -- a step that writes a commit assigned to a runtime
without `git_author_identity`. That is issue #255 generalized: a connector can
create a commit and cannot set its author, so a plan that routes commit-writing
there produces a commit that claims a machine role under a person's address, and
the repository's contribution-identity gate catches it one CI run too late.

Exit codes: 0 pass, 2 packet failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
SCHEMA = "dual-forge-repository-loop/runtime-handoff/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

AVAILABLE = {"OBSERVED", "DECLARED"}
ABSENT = {"OBSERVED_ABSENT", "DECLARED_ABSENT"}
# UNKNOWN is planned around as absent: a capability nobody measured or declared
# cannot be the reason a step is expected to succeed.
UNAVAILABLE = ABSENT | {"UNKNOWN"}

CAPABILITIES = {
    "github_read", "github_commit_create", "git_author_identity", "local_checkout",
    "local_shell", "git_worktree", "forgejo_loopback", "provider_execution",
    "agent_session_spawn", "actions_execution",
}
RUNTIMES = {
    "CHATGPT_GITHUB_CONNECTOR", "CHATGPT_DESKTOP_WORKTREE", "CLAUDE_CODE_LOCAL",
    "CODEX_CLI_LOCAL", "GITHUB_ACTIONS", "UNKNOWN",
}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def check_shape(body: Any) -> None:
    if not isinstance(body, dict) or body.get("schema") != SCHEMA:
        refuse("PACKET_MALFORMED", f"schema must be {SCHEMA}")
    for section in ("subject", "sender", "blocker", "capability_matrix", "steps",
                    "receiver", "done_when"):
        if section not in body:
            refuse("PACKET_MALFORMED", f"packet has no {section}")
    if not body["steps"]:
        refuse("PACKET_MALFORMED", "packet has no step")


def check_subject(body: dict[str, Any]) -> None:
    subject = body["subject"]
    for field in ("commit_sha", "tree_sha"):
        value = subject.get(field)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            refuse("SUBJECT_UNBOUND",
                   f"subject.{field} must be a 40-character lowercase SHA; a handoff "
                   f"without an exact subject hands over no particular state")
    if not subject.get("repository"):
        refuse("SUBJECT_UNBOUND", "subject.repository is empty")


def check_blocker(body: dict[str, Any]) -> None:
    """A handoff that does not say what stopped it is a rediscovery request."""
    blocker = body["blocker"]
    capability = blocker.get("missing_capability")
    if capability not in CAPABILITIES:
        refuse("HANDOFF_WITHOUT_BLOCKER",
               f"blocker.missing_capability {capability!r} is not an admitted capability")
    if not str(blocker.get("observation", "")).strip():
        refuse("HANDOFF_WITHOUT_BLOCKER",
               "blocker.observation is empty; the receiver would have to reproduce the "
               "failure to learn what it is")
    if not str(blocker.get("evidence_reference", "")).strip():
        refuse("HANDOFF_WITHOUT_BLOCKER",
               "blocker.evidence_reference is empty; an observation nobody can replay is "
               "a claim, not a blocker")

    # The sender must actually lack the capability it says stopped it.
    sender = body["sender"]["runtime"]
    verdict = verdict_for(body, sender, capability)
    if verdict in AVAILABLE:
        refuse("HANDOFF_WITHOUT_BLOCKER",
               f"{sender} is recorded as having {capability} ({verdict}) yet hands off "
               f"because it lacks it")


def verdict_for(body: dict[str, Any], runtime: str, capability: str) -> str:
    row = body["capability_matrix"].get(runtime) or {}
    cell = row.get(capability)
    if not isinstance(cell, dict):
        return "UNKNOWN"
    return cell.get("verdict", "UNKNOWN")


def check_matrix(body: dict[str, Any]) -> None:
    """A capability marked available must say how that was established."""
    for runtime, row in body["capability_matrix"].items():
        if runtime not in RUNTIMES:
            refuse("PACKET_MALFORMED", f"capability_matrix names unknown runtime {runtime!r}")
        for capability, cell in row.items():
            if capability not in CAPABILITIES:
                refuse("PACKET_MALFORMED",
                       f"{runtime} names unknown capability {capability!r}")
            verdict = cell.get("verdict")
            if verdict not in AVAILABLE | ABSENT | {"UNKNOWN"}:
                refuse("CAPABILITY_UNEVIDENCED",
                       f"{runtime}.{capability} verdict {verdict!r} is not admitted")
            if verdict == "UNKNOWN":
                continue
            if not str(cell.get("evidence", "")).strip():
                refuse("CAPABILITY_UNEVIDENCED",
                       f"{runtime}.{capability} is {verdict} with no evidence; a matrix "
                       f"nobody grounded gets believed anyway")


def check_steps(body: dict[str, Any]) -> None:
    """Every step goes to something that can perform it, or to a Human."""
    seen: set[str] = set()
    for step in body["steps"]:
        step_id = step.get("id")
        if not step_id or step_id in seen:
            refuse("PACKET_MALFORMED", f"step id {step_id!r} is missing or duplicated")
        seen.add(step_id)

        assigned = step.get("assigned_to")
        required = step.get("requires") or []
        unknown = [c for c in required if c not in CAPABILITIES]
        if unknown:
            refuse("PACKET_MALFORMED", f"{step_id} requires unknown capabilities {unknown}")

        if assigned == "HUMAN":
            continue
        if assigned not in RUNTIMES:
            refuse("PACKET_MALFORMED", f"{step_id} assigned to unknown runtime {assigned!r}")

        missing = [c for c in required
                   if verdict_for(body, assigned, c) in UNAVAILABLE]
        if missing:
            refuse("STEP_EXCEEDS_RUNTIME",
                   f"{step_id} is assigned to {assigned}, which the matrix records as "
                   f"lacking {missing}")

        # The #255 case, stated as its own rule so a future packet cannot reach it
        # by accident.
        if step.get("writes_commit") and \
                verdict_for(body, assigned, "git_author_identity") in UNAVAILABLE:
            refuse("IDENTITY_LAUNDERED",
                   f"{step_id} writes a commit on {assigned}, which cannot set author "
                   f"identity; the commit would claim a role under whatever address the "
                   f"host attaches")


def check_terminal_owner(body: dict[str, Any]) -> None:
    """A step nothing can perform is a fact about the task, not a routing problem.

    This runs *before* the per-step assignment check, and the order is the whole
    rule. Placed after it, this law was unreachable: any step whose assigned
    runtime lacked a capability was already refused as STEP_EXCEEDS_RUNTIME, so
    by the time control arrived here the assigned runtime always had everything
    and `capable` was never empty. A rule that cannot go red is a rule that
    checks nothing.

    Ordered first, the two split cleanly: some runtime can do it but the wrong
    one was picked (misrouted, reroute it), or nothing can (a fact about the
    task, which needs a Human or a runtime that does not exist yet).
    """
    for step in body["steps"]:
        if step.get("assigned_to") == "HUMAN":
            continue
        required = [c for c in (step.get("requires") or []) if c in CAPABILITIES]
        if not required:
            continue
        capable = [runtime for runtime in body["capability_matrix"]
                   if all(verdict_for(body, runtime, c) in AVAILABLE for c in required)]
        if not capable:
            refuse("NO_TERMINAL_OWNER",
                   f"{step['id']} requires {required} and no runtime in the matrix has "
                   f"all of them; assign it to HUMAN rather than to whoever is next")


def check_receiver(body: dict[str, Any]) -> None:
    receiver = body["receiver"]["runtime"]
    if receiver not in RUNTIMES:
        refuse("PACKET_MALFORMED", f"receiver runtime {receiver!r} is unknown")
    needed: set[str] = set()
    for step in body["steps"]:
        if step.get("assigned_to") == receiver:
            needed.update(step.get("requires") or [])
    missing = sorted(c for c in needed if verdict_for(body, receiver, c) in UNAVAILABLE)
    if missing:
        refuse("RECEIVER_CANNOT_RESUME",
               f"{receiver} is the receiver but lacks {missing}, which its own steps need")
    if not needed and body["blocker"]["missing_capability"] not in (
            body["capability_matrix"].get(receiver) or {}):
        refuse("RECEIVER_CANNOT_RESUME",
               f"{receiver} is assigned no step and the matrix does not record whether it "
               f"has the missing capability")


def check_done_when(body: dict[str, Any]) -> None:
    done = body["done_when"]
    if not str(done.get("condition", "")).strip():
        refuse("DONE_CONDITION_UNCHECKABLE", "done_when.condition is empty")
    checkable = done.get("checkable_by") or []
    if not checkable:
        refuse("DONE_CONDITION_UNCHECKABLE",
               "done_when.checkable_by is empty; a completion condition the receiver "
               "cannot evaluate ends nothing")


CHECKS = (check_subject, check_matrix, check_blocker, check_terminal_owner,
          check_steps, check_receiver, check_done_when)


def validate(body: Any) -> None:
    check_shape(body)
    for check in CHECKS:
        check(body)


def selftest(body: dict[str, Any]) -> int:
    try:
        validate(body)
    except Refused as failure:
        print(f"SELFTEST RED: committed example already refused -- {failure}",
              file=sys.stderr)
        return 2

    def mutate(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(body)
        fn(copied)
        return copied

    def route_commit_to_connector(doc: dict[str, Any]) -> None:
        step = next(s for s in doc["steps"] if s.get("writes_commit"))
        step["assigned_to"] = "CHATGPT_GITHUB_CONNECTOR"
        step["requires"] = ["github_commit_create"]

    def route_shell_to_connector(doc: dict[str, Any]) -> None:
        step = next(s for s in doc["steps"] if "local_shell" in s["requires"])
        step["assigned_to"] = "CHATGPT_GITHUB_CONNECTOR"
        step["writes_commit"] = False

    def strip_local_runtime(doc: dict[str, Any]) -> None:
        """Remove the only runtime that can do the work, leaving the step assigned.

        Reassigning the orphaned steps to HUMAN would be the *correct* packet and
        would pass, which is what the first version of this control did -- it
        tested nothing. The defect is a step still routed at a runtime when no
        runtime in the matrix can perform it.
        """
        doc["capability_matrix"].pop("CLAUDE_CODE_LOCAL")
        doc["receiver"]["runtime"] = "CHATGPT_GITHUB_CONNECTOR"

    controls = [
        ("commit-routed-to-a-runtime-without-identity", "IDENTITY_LAUNDERED",
         mutate(route_commit_to_connector)),
        ("shell-step-on-a-runtime-without-shell", "STEP_EXCEEDS_RUNTIME",
         mutate(route_shell_to_connector)),
        ("capability-claimed-without-evidence", "CAPABILITY_UNEVIDENCED",
         mutate(lambda d: d["capability_matrix"]["CLAUDE_CODE_LOCAL"]
                ["git_author_identity"].pop("evidence"))),
        ("blocker-observation-empty", "HANDOFF_WITHOUT_BLOCKER",
         mutate(lambda d: d["blocker"].update({"observation": "   "}))),
        ("blocker-not-reproducible", "HANDOFF_WITHOUT_BLOCKER",
         mutate(lambda d: d["blocker"].update({"evidence_reference": ""}))),
        ("sender-had-the-capability-after-all", "HANDOFF_WITHOUT_BLOCKER",
         mutate(lambda d: d["capability_matrix"]["CHATGPT_GITHUB_CONNECTOR"]
                ["git_author_identity"].update(
                    {"verdict": "OBSERVED", "evidence": "assumed"}))),
        ("no-runtime-can-do-a-step", "NO_TERMINAL_OWNER", mutate(strip_local_runtime)),
        ("subject-unbound", "SUBJECT_UNBOUND",
         mutate(lambda d: d["subject"].update({"tree_sha": "deadbeef"}))),
        ("done-condition-uncheckable", "DONE_CONDITION_UNCHECKABLE",
         mutate(lambda d: d["done_when"].update({"checkable_by": []}))),
        # Downgrading the only runtime that has local_shell to UNKNOWN leaves the
        # capability unowned, so NO_TERMINAL_OWNER is the right refusal and the
        # earlier expectation of STEP_EXCEEDS_RUNTIME was mine, not the checker's.
        # What it proves is the point either way: UNKNOWN is not availability. If
        # it were, nothing here would go red at all.
        ("unknown-capability-is-not-availability", "NO_TERMINAL_OWNER",
         mutate(lambda d: d["capability_matrix"]["CLAUDE_CODE_LOCAL"]
                ["local_shell"].update({"verdict": "UNKNOWN"}))),
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
    print(f"SELFTEST GREEN: committed handoff example admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    default = SKILL / "references" / "runtime-handoff.example.json"
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    parser.add_argument("--packet", type=Path, default=default)
    args = parser.parse_args(argv)

    try:
        body = json.loads(args.packet.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable packet: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(body)

    try:
        validate(body)
    except Refused as failure:
        print(f"HANDOFF REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    human = sum(1 for s in body["steps"] if s["assigned_to"] == "HUMAN")
    print(f"HANDOFF PACKET GREEN: {body['sender']['runtime']} -> "
          f"{body['receiver']['runtime']} on {body['subject']['commit_sha'][:12]}; "
          f"{len(body['steps'])} step(s), {human} to a Human; blocked on "
          f"{body['blocker']['missing_capability']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
