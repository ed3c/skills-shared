#!/usr/bin/env python3
"""Bounded reversible GitHub Issue Dependencies live canary."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

VIS = {"PUBLIC", "PRIVATE", "INTERNAL"}
API_VERSION = "2026-03-10"


class ContractError(ValueError):
    pass


def validate_plan(d: dict[str, Any]) -> None:
    req = {
        "repo",
        "repo_visibility",
        "default_branch",
        "blocker_issue",
        "blocked_issue",
        "canary_label",
        "expected_before_blocked_by",
    }
    if set(d) != req:
        raise ContractError("plan fields invalid")
    if not isinstance(d["repo"], str) or d["repo"].count("/") != 1:
        raise ContractError("repo must be owner/name")
    if (
        d["repo_visibility"] not in VIS
        or not isinstance(d["default_branch"], str)
        or not d["default_branch"].strip()
    ):
        raise ContractError("repo metadata invalid")
    for field in ("blocker_issue", "blocked_issue"):
        if (
            not isinstance(d[field], int)
            or isinstance(d[field], bool)
            or d[field] <= 0
        ):
            raise ContractError(f"{field} invalid")
    if d["blocker_issue"] == d["blocked_issue"]:
        raise ContractError("self canary forbidden")
    if not isinstance(d["canary_label"], str) or not d["canary_label"].strip():
        raise ContractError("canary_label required")
    before = d["expected_before_blocked_by"]
    if (
        not isinstance(before, list)
        or not all(
            isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in before
        )
        or len(set(before)) != len(before)
    ):
        raise ContractError("expected_before invalid")
    if d["blocker_issue"] in before:
        raise ContractError("canary edge already present")


def _run(argv: list[str]) -> str:
    proc = subprocess.run(argv, text=True, capture_output=True)
    if proc.returncode:
        raise ContractError(
            f"command failed ({proc.returncode}): {' '.join(argv)}: "
            f"{proc.stderr.strip()}"
        )
    return proc.stdout


def _labels(value: Any) -> set[str]:
    if not isinstance(value, list):
        raise ContractError("labels malformed")
    out: set[str] = set()
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ContractError("label malformed")
        out.add(row["name"])
    return out


def _api_header() -> str:
    return f"X-GitHub-Api-Version: {API_VERSION}"


def _rest_issue_id(d: dict[str, Any], issue_number: int) -> int:
    raw = _run(
        [
            "gh",
            "api",
            f"repos/{d['repo']}/issues/{issue_number}",
            "-H",
            _api_header(),
            "--jq",
            ".id",
        ]
    ).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ContractError("issue REST id malformed") from exc
    if value <= 0:
        raise ContractError("issue REST id malformed")
    return value


def preflight(d: dict[str, Any]) -> dict[str, Any]:
    validate_plan(d)
    repo = json.loads(
        _run(
            [
                "gh",
                "repo",
                "view",
                d["repo"],
                "--json",
                "nameWithOwner,visibility,defaultBranchRef",
            ]
        )
    )
    ref = repo.get("defaultBranchRef")
    branch = ref.get("name") if isinstance(ref, dict) else None
    if (
        repo.get("nameWithOwner") != d["repo"]
        or str(repo.get("visibility", "")).upper() != d["repo_visibility"]
        or branch != d["default_branch"]
    ):
        raise ContractError("repository preflight drift")

    issues: dict[str, Any] = {}
    for field in ("blocker_issue", "blocked_issue"):
        number = d[field]
        issue = json.loads(
            _run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(number),
                    "--repo",
                    d["repo"],
                    "--json",
                    "number,state,labels",
                ]
            )
        )
        if issue.get("number") != number or str(issue.get("state", "")).upper() != "OPEN":
            raise ContractError(f"canary issue identity/state drift: {number}")
        labels = _labels(issue.get("labels"))
        if d["canary_label"] not in labels:
            raise ContractError(f"issue {number} lacks canary ownership label")
        issues[str(number)] = {"state": "OPEN", "labels": sorted(labels)}
    return {
        "repository": {
            "nameWithOwner": d["repo"],
            "visibility": d["repo_visibility"],
            "default_branch": d["default_branch"],
        },
        "issues": issues,
    }


def read_blocked_by(d: dict[str, Any]) -> list[int]:
    endpoint = (
        f"repos/{d['repo']}/issues/{d['blocked_issue']}"
        "/dependencies/blocked_by?per_page=100"
    )
    pages = json.loads(
        _run(
            [
                "gh",
                "api",
                endpoint,
                "--paginate",
                "--slurp",
                "-H",
                _api_header(),
            ]
        )
    )
    if not isinstance(pages, list):
        raise ContractError("blockedBy pages malformed")

    expected_repo_url = f"https://api.github.com/repos/{d['repo']}"
    values: list[int] = []
    for page in pages:
        if not isinstance(page, list):
            raise ContractError("blockedBy page malformed")
        for row in page:
            if not isinstance(row, dict):
                raise ContractError("blockedBy malformed")
            number = row.get("number")
            if (
                not isinstance(number, int)
                or isinstance(number, bool)
                or number <= 0
            ):
                raise ContractError("blockedBy malformed")
            if row.get("repository_url") != expected_repo_url:
                raise ContractError("cross-repository blockedBy forbidden for canary fixture")
            values.append(number)

    if len(set(values)) != len(values):
        raise ContractError("blockedBy duplicate")
    return sorted(values)


def _add_blocked_by(d: dict[str, Any], blocker_rest_id: int) -> None:
    endpoint = (
        f"repos/{d['repo']}/issues/{d['blocked_issue']}/dependencies/blocked_by"
    )
    _run(
        [
            "gh",
            "api",
            endpoint,
            "--method",
            "POST",
            "-H",
            _api_header(),
            "-F",
            f"issue_id={blocker_rest_id}",
            "--silent",
        ]
    )


def _remove_blocked_by(d: dict[str, Any], blocker_rest_id: int) -> None:
    endpoint = (
        f"repos/{d['repo']}/issues/{d['blocked_issue']}"
        f"/dependencies/blocked_by/{blocker_rest_id}"
    )
    _run(
        [
            "gh",
            "api",
            endpoint,
            "--method",
            "DELETE",
            "-H",
            _api_header(),
            "--silent",
        ]
    )


def static_receipt(d: dict[str, Any]) -> dict[str, Any]:
    validate_plan(d)
    return {
        "schema_version": 1,
        "repo": d["repo"],
        "blocker_issue": d["blocker_issue"],
        "blocked_issue": d["blocked_issue"],
        "canary_label": d["canary_label"],
        "expected_before_blocked_by": sorted(d["expected_before_blocked_by"]),
        "execution": "NOT_EXERCISED",
        "evidence_ceiling": "STATIC_CANARY_PLAN_ONLY",
    }


def execute(d: dict[str, Any]) -> dict[str, Any]:
    validate_plan(d)
    preflight_before = preflight(d)
    before = read_blocked_by(d)
    expected = sorted(d["expected_before_blocked_by"])
    if before != expected:
        raise ContractError(f"unexpected pre-canary denominator: {before}")

    blocker = d["blocker_issue"]
    blocked = d["blocked_issue"]
    blocker_rest_id = _rest_issue_id(d, blocker)
    added = False
    error: Exception | None = None
    applied: list[int] | None = None
    preflight_after: dict[str, Any] | None = None
    cleanup: list[int] | None = None

    try:
        _add_blocked_by(d, blocker_rest_id)
        added = True
        applied = read_blocked_by(d)
        if applied != sorted([*expected, blocker]):
            raise ContractError(f"applied readback mismatch: {applied}")
        preflight_after = preflight(d)
        if preflight_after != preflight_before:
            raise ContractError("preflight changed during canary")
    except Exception as exc:
        error = exc
    finally:
        if added:
            try:
                _remove_blocked_by(d, blocker_rest_id)
                cleanup = read_blocked_by(d)
                if cleanup != expected:
                    raise ContractError(
                        f"cleanup did not restore denominator: {cleanup}"
                    )
            except Exception as cleanup_error:
                raise ContractError(
                    "canary cleanup failed after remote mutation: "
                    f"{cleanup_error}"
                ) from cleanup_error

    if error is not None:
        raise error
    return {
        "schema_version": 1,
        "repo": d["repo"],
        "blocker_issue": blocker,
        "blocked_issue": blocked,
        "canary_label": d["canary_label"],
        "preflight": preflight_after,
        "before": {"blockedBy": before},
        "applied": {"blockedBy": applied},
        "cleanup": {"blockedBy": cleanup},
        "execution": "EXERCISED",
        "canary_state": "LIVE_GITHUB_DEPENDENCY_CANARY_PASS",
        "semantic_authority": False,
        "evidence_ceiling": "REMOTE_CANARY_EDGE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.loads(Path(args.plan).read_text())
    receipt = execute(data) if args.execute else static_receipt(data)
    output = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
