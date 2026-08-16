#!/usr/bin/env python3
"""Refuse laundering connector observations into local/Forgejo runtime evidence.

This is a classification gate, not a live-runtime probe. It enforces the
private-lineage law that GitHub connector access can describe GitHub-side
observations but cannot satisfy a local Git, worktree, or Forgejo execution
transition.

Exit codes: 0 admitted classification, 2 refused claim, 64 unusable input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "forgejo-private-runtime-evidence-claim/v1"
RUNTIMES = {
    "CHATGPT_GITHUB_CONNECTOR",
    "CHATGPT_DESKTOP_WORKTREE",
    "CLAUDE_CODE_LOCAL",
    "CODEX_CLI_LOCAL",
    "GITHUB_ACTIONS",
}
LANES = {
    "github_read",
    "github_api_mutation",
    "github_actions",
    "local_git",
    "local_worktree",
    "forgejo_loopback",
    "forgejo_issue",
    "forgejo_pr",
    "forgejo_runtime_receipt",
}
LOCAL_OR_FORGEJO = {
    "local_git",
    "local_worktree",
    "forgejo_loopback",
    "forgejo_issue",
    "forgejo_pr",
    "forgejo_runtime_receipt",
}
STATES = {
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
    "HUMAN_ADMIT_REQUIRED",
}
# PASS/FAIL/ABSENT assert that this runtime observed the lane. A connector may
# report that a local lane was not exercised, but it may not manufacture an
# observed local result from provider-side access.
OBSERVED_STATES = {"PASS", "FAIL", "ABSENT"}


class Refused(Exception):
    pass


def validate(body: Any) -> None:
    if not isinstance(body, dict) or body.get("schema") != SCHEMA:
        raise Refused(f"schema must be {SCHEMA}")
    if set(body) != {"schema", "runtime_identity", "evidence_lane", "state", "evidence_reference"}:
        raise Refused("claim fields must be exactly schema, runtime_identity, evidence_lane, state, evidence_reference")

    runtime = body.get("runtime_identity")
    lane = body.get("evidence_lane")
    state = body.get("state")
    evidence = body.get("evidence_reference")
    if runtime not in RUNTIMES:
        raise Refused(f"unknown runtime_identity {runtime!r}")
    if lane not in LANES:
        raise Refused(f"unknown evidence_lane {lane!r}")
    if state not in STATES:
        raise Refused(f"unknown state {state!r}")
    if not isinstance(evidence, str):
        raise Refused("evidence_reference must be a string")

    if runtime == "CHATGPT_GITHUB_CONNECTOR" and lane in LOCAL_OR_FORGEJO and state in OBSERVED_STATES:
        raise Refused(
            f"CONNECTOR_LOCAL_EVIDENCE_LAUNDERED: {runtime} cannot claim {state} for {lane}; "
            "provider access is not local/Forgejo execution evidence"
        )

    # Any observed result needs a replay pointer. Non-execution states may use
    # an empty reference because their purpose is to avoid inventing evidence.
    if state in OBSERVED_STATES and not evidence.strip():
        raise Refused("observed PASS/FAIL/ABSENT state requires evidence_reference")


def selftest() -> int:
    def claim(runtime: str, lane: str, state: str, evidence: str = "receipt:sha256:demo") -> dict[str, str]:
        return {
            "schema": SCHEMA,
            "runtime_identity": runtime,
            "evidence_lane": lane,
            "state": state,
            "evidence_reference": evidence,
        }

    admitted = [
        claim("CHATGPT_GITHUB_CONNECTOR", "github_read", "PASS"),
        claim("CHATGPT_GITHUB_CONNECTOR", "forgejo_loopback", "NOT_EXERCISED", ""),
        claim("CLAUDE_CODE_LOCAL", "forgejo_loopback", "PASS"),
    ]
    for index, body in enumerate(admitted, 1):
        try:
            validate(body)
        except Refused as error:
            print(f"SELFTEST RED admitted[{index}]: {error}", file=sys.stderr)
            return 2

    refused = [
        claim("CHATGPT_GITHUB_CONNECTOR", "local_git", "PASS"),
        claim("CHATGPT_GITHUB_CONNECTOR", "local_worktree", "FAIL"),
        claim("CHATGPT_GITHUB_CONNECTOR", "forgejo_loopback", "ABSENT"),
        claim("CHATGPT_GITHUB_CONNECTOR", "forgejo_issue", "PASS"),
        claim("CHATGPT_GITHUB_CONNECTOR", "forgejo_pr", "PASS"),
        claim("CHATGPT_GITHUB_CONNECTOR", "forgejo_runtime_receipt", "PASS"),
    ]
    for index, body in enumerate(refused, 1):
        try:
            validate(body)
        except Refused as error:
            if "CONNECTOR_LOCAL_EVIDENCE_LAUNDERED" in str(error):
                continue
            print(f"SELFTEST RED refused[{index}] wrong reason: {error}", file=sys.stderr)
            return 2
        print(f"SELFTEST RED refused[{index}] was admitted", file=sys.stderr)
        return 2

    missing_evidence = claim("CLAUDE_CODE_LOCAL", "local_git", "PASS", "")
    try:
        validate(missing_evidence)
    except Refused as error:
        if "evidence_reference" not in str(error):
            print(f"SELFTEST RED missing-evidence wrong reason: {error}", file=sys.stderr)
            return 2
    else:
        print("SELFTEST RED observed state without evidence was admitted", file=sys.stderr)
        return 2

    print("SELFTEST GREEN: connector GitHub evidence stays provider-scoped; six local/Forgejo laundering mutations refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("claim", nargs="?", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.claim is None:
        print("USAGE: claim path required unless --selftest is used", file=sys.stderr)
        return 64
    try:
        body = json.loads(args.claim.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"UNUSABLE: {error}", file=sys.stderr)
        return 64
    try:
        validate(body)
    except Refused as error:
        print(f"RUNTIME EVIDENCE CLASSIFICATION RED: {error}", file=sys.stderr)
        return 2
    print("RUNTIME EVIDENCE CLASSIFICATION GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
