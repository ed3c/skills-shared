#!/usr/bin/env python3
"""Strict GitHub publication snapshot with independent remote-ref proof.

The v1 snapshot producer proves PR/check/billing state. This wrapper additionally
proves whether `refs/heads/<branch>` exists before representing an `initial-pr`
boundary. It is read-only and never pushes, reruns, transitions, merges, changes
billing, or changes permissions.

Exit codes: 0 written, 2 contradictory/unsafe GitHub state, 64 API/I/O failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.parse import quote

import github_actions_snapshot as v1

REF_RE = re.compile(r"^refs/heads/(.+)$")


class RefError(v1.SnapshotError):
    pass


def safe_branch(value: str) -> str:
    if (
        not value
        or value.startswith("-")
        or any(character in value for character in ("\x00", "\n", "\r"))
        or value.startswith("/")
        or value.endswith("/")
        or "//" in value
        or value in {".", ".."}
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise RefError("branch name is unsafe")
    return value


def parse_ref(value: Any, branch: str) -> str:
    if not isinstance(value, dict):
        raise RefError("remote Git ref response must be an object")
    if set(value) != {"ref", "node_id", "url", "object"}:
        raise RefError("remote Git ref response fields drifted")
    expected = f"refs/heads/{branch}"
    if value["ref"] != expected:
        raise RefError(f"remote Git ref does not match exact branch: {value.get('ref')!r}")
    object_value = value["object"]
    if not isinstance(object_value, dict):
        raise RefError("remote Git ref object must be an object")
    if set(object_value) != {"sha", "type", "url"}:
        raise RefError("remote Git ref object fields drifted")
    if object_value["type"] != "commit":
        raise RefError("remote branch ref must point to a commit")
    return v1.sha(object_value["sha"], "remote branch ref SHA")


def exact_remote_ref(
    repository: str,
    branch: str,
    gh: str,
    timeout: int,
) -> str | None:
    branch = safe_branch(branch)
    endpoint = f"repos/{repository}/git/ref/heads/{quote(branch, safe='')}"
    try:
        result = subprocess.run(
            [gh, "api", endpoint],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise v1.CaptureError(f"gh executable is absent: {gh}") from exc
    except subprocess.TimeoutExpired as exc:
        raise v1.CaptureError(f"gh api timed out: {endpoint}") from exc
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        if re.search(r"(?:HTTP\s*)?404\b", message, flags=re.IGNORECASE):
            return None
        raise v1.CaptureError(f"gh api failed for {endpoint}: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise v1.CaptureError(f"gh api returned non-JSON for {endpoint}") from exc
    return parse_ref(payload, branch)


def strict_build(observation: dict[str, Any], check_name: str) -> dict[str, Any]:
    normalized = v1.observation(observation)
    pulls = normalized["pull_requests"]
    branch_head = normalized["branch"]["head_sha"]
    if len(pulls) > 1:
        raise RefError("branch has multiple open pull requests")
    if not pulls:
        if branch_head is not None:
            raise RefError("remote branch exists without an open PR")
    else:
        if branch_head is None:
            raise RefError("open PR exists but exact remote branch ref is absent")
        if pulls[0]["head_sha"] != branch_head:
            raise RefError("open PR head differs from exact remote branch ref")
    return v1.build(observation, check_name)


def capture_observation(
    repository: str,
    branch: str,
    check_name: str,
    gh: str,
    timeout: int,
) -> dict[str, Any]:
    branch = safe_branch(branch)
    observation = v1.capture(repository, branch, check_name, gh, timeout)
    observation["branch"]["head_sha"] = exact_remote_ref(
        repository,
        branch,
        gh,
        timeout,
    )
    strict_build(observation, check_name)
    return observation


def fixture_ref(branch: str, head: str) -> dict[str, Any]:
    return {
        "ref": f"refs/heads/{branch}",
        "node_id": "fixture-node",
        "url": "https://api.github.invalid/ref",
        "object": {
            "sha": head,
            "type": "commit",
            "url": "https://api.github.invalid/commit",
        },
    }


def selftest() -> None:
    observation = v1.fixture()
    strict_build(observation, "contract")
    head = observation["branch"]["head_sha"]
    if parse_ref(fixture_ref("feature", head), "feature") != head:
        raise RefError("exact ref parser changed the object ID")

    absent = v1.fixture()
    absent["branch"]["head_sha"] = None
    absent["pull_requests"] = []
    absent["check_runs"] = []
    if strict_build(absent, "contract")["pull_request"]["state"] != "absent":
        raise RefError("true remote absence did not produce initial boundary")

    branch_only = json.loads(json.dumps(absent))
    branch_only["branch"]["head_sha"] = "1" * 40
    missing_ref = v1.fixture()
    missing_ref["branch"]["head_sha"] = None
    mismatch = v1.fixture()
    mismatch["branch"]["head_sha"] = "2" * 40
    malformed_ref = fixture_ref("feature", "1" * 40)
    malformed_ref["object"]["sha"] = "short"

    for name, value in (
        ("branch-only", branch_only),
        ("pr-without-ref", missing_ref),
        ("pr-ref-mismatch", mismatch),
    ):
        try:
            strict_build(value, "contract")
        except RefError:
            pass
        else:
            raise RefError(f"negative control unexpectedly passed: {name}")
    try:
        parse_ref(malformed_ref, "feature")
    except RefError:
        pass
    else:
        raise RefError("malformed remote object ID unexpectedly passed")
    for unsafe in ("", "-feature", "feature//child", "feature/../child", "/feature"):
        try:
            safe_branch(unsafe)
        except RefError:
            pass
        else:
            raise RefError(f"unsafe branch unexpectedly passed: {unsafe!r}")

    billing = v1.fixture()
    billing["check_runs"][0]["annotations"] = [
        {
            "message": "The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings"
        }
    ]
    result = strict_build(billing, "contract")
    if result["actions"]["circuit"] != "billing-open" or result["actions"]["latest_check"] is not None:
        raise RefError("strict ref proof collapsed billing state")
    print("SELFTEST GREEN: exact remote-ref publication boundary")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="github_actions_snapshot_strict.py")
    parser.add_argument("--selftest", action="store_true")
    subs = parser.add_subparsers(dest="command")
    replay = subs.add_parser("replay")
    replay.add_argument("--observation", type=Path, required=True)
    replay.add_argument("--check-name", required=True)
    replay.add_argument("--output", type=Path, required=True)
    capture = subs.add_parser("capture")
    capture.add_argument("--repository", required=True)
    capture.add_argument("--branch", required=True)
    capture.add_argument("--check-name", required=True)
    capture.add_argument("--gh", default="gh")
    capture.add_argument("--timeout-seconds", type=int, default=30)
    capture.add_argument("--observation-output", type=Path)
    capture.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.selftest:
        if args.command is not None:
            parser.error("--selftest cannot be combined with a command")
        try:
            selftest()
            return 0
        except (v1.SnapshotError, v1.CaptureError, OSError) as exc:
            print(f"SELFTEST RED: {exc}", file=sys.stderr)
            return 1

    try:
        if args.command == "replay":
            observation = v1.load(args.observation, "GitHub observation")
            snapshot = strict_build(observation, args.check_name)
            v1.atomic(args.output.resolve(), snapshot)
            print(f"WROTE {args.output.resolve()}")
            return 0
        if args.command == "capture":
            if args.timeout_seconds < 1:
                raise v1.CaptureError("timeout-seconds must be positive")
            observation = capture_observation(
                args.repository,
                args.branch,
                args.check_name,
                args.gh,
                args.timeout_seconds,
            )
            snapshot = strict_build(observation, args.check_name)
            if args.observation_output is not None:
                v1.atomic(args.observation_output.resolve(), observation)
            v1.atomic(args.output.resolve(), snapshot)
            print(f"WROTE {args.output.resolve()}")
            return 0
        parser.error("replay, capture, or --selftest is required")
    except v1.SnapshotError as exc:
        print(f"BLOCK snapshot-state: {exc}", file=sys.stderr)
        return 2
    except (v1.CaptureError, OSError) as exc:
        print(f"FATAL snapshot-capture: {exc}", file=sys.stderr)
        return 64
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
