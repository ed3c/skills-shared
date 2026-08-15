#!/usr/bin/env python3
"""Capture exhaustive dual-forge inventories and replay typed reconciliation.

The capture lane writes only raw provider transport. The replay lane derives
the complete provider inventory and checks that a typed observation classifies
every captured open PR and issue exactly once.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from capture_origin_ref import CaptureError, LOOPBACK_FORGES, credentials, forgejo_json


SCHEMA = "dual-forge-reconciliation-transport/v2"
OBSERVATION_SCHEMA = "dual-forge-reconciliation-observation/v2"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
GH_CANDIDATES = (
    "/opt/homebrew/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh",
    "/home/linuxbrew/.linuxbrew/bin/gh",
)


def atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def record(argv: list[str], exit_code: int, stdout: str, stderr: str = "") -> dict[str, Any]:
    return {
        "argv": argv,
        "exit": exit_code,
        "stdout": stdout,
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr": stderr,
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
    }


def gh_identity(timeout: int) -> dict[str, str]:
    invoked = next(
        (path for path in GH_CANDIDATES if Path(path).is_file() and os.access(path, os.X_OK)),
        None,
    )
    if invoked is None:
        raise CaptureError(f"gh absent from admitted absolute paths: {', '.join(GH_CANDIDATES)}")
    resolved = str(Path(invoked).resolve(strict=True))
    try:
        result = subprocess.run(
            [resolved, "--version"], stdin=subprocess.DEVNULL, capture_output=True,
            text=True, check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise CaptureError("admitted gh identity check timed out") from exc
    lines = result.stdout.splitlines()
    if result.returncode != 0 or not lines or not lines[0].startswith("gh version "):
        raise CaptureError("admitted gh executable did not report a canonical version")
    return {
        "invoked_path": invoked,
        "resolved_path": resolved,
        "sha256": hashlib.sha256(Path(resolved).read_bytes()).hexdigest(),
        "version": lines[0],
    }


def gh_capture(gh_path: str, argv: list[str], timeout: int) -> dict[str, Any]:
    actual = [gh_path, *argv]
    try:
        result = subprocess.run(
            actual, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CaptureError(f"GitHub capture unavailable: {' '.join(actual)}") from exc
    entry = record(actual, result.returncode, result.stdout, result.stderr)
    if result.returncode != 0:
        raise CaptureError(f"GitHub capture failed: {result.stderr.strip()}")
    return entry


def forgejo_capture(forge_url: str, endpoint: str, auth: str) -> dict[str, Any]:
    _, stdout = forgejo_json(forge_url, endpoint, auth)
    return record(["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"], 0, stdout)


def capture(
    github_repository: str,
    forgejo_repository: str,
    default_branch: str,
    forge_url: str,
    timeout: int,
) -> dict[str, Any]:
    if REPOSITORY.fullmatch(github_repository) is None or REPOSITORY.fullmatch(forgejo_repository) is None:
        raise CaptureError("repositories must be OWNER/REPOSITORY")
    if forge_url not in LOOPBACK_FORGES:
        raise CaptureError("Forgejo URL must be the allowlisted loopback forge")
    identity = gh_identity(timeout)
    gh_path = identity["resolved_path"]
    captures = [
        gh_capture(gh_path, ["api", f"repos/{github_repository}"], timeout),
        gh_capture(
            gh_path,
            ["api", "--paginate", "--slurp", f"repos/{github_repository}/pulls?state=open&per_page=100"],
            timeout,
        ),
        gh_capture(
            gh_path,
            ["api", "--paginate", "--slurp", f"repos/{github_repository}/issues?state=open&per_page=100"],
            timeout,
        ),
    ]
    username, password = credentials(forge_url)
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    owner, name = forgejo_repository.split("/", 1)
    root = f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    captures.append(forgejo_capture(forge_url, root, auth))
    for resource, query in (
        ("pulls", "state=open"),
        ("issues", "state=open&type=issues"),
    ):
        page = 1
        while True:
            endpoint = f"{root}/{resource}?{query}&limit=50&page={page}"
            entry = forgejo_capture(forge_url, endpoint, auth)
            captures.append(entry)
            payload = json.loads(entry["stdout"])
            if not isinstance(payload, list):
                raise CaptureError(f"Forgejo {resource} response is malformed")
            if len(payload) < 50:
                break
            page += 1
    return {
        "schema": SCHEMA,
        "producer": "capture_reconciliation.py",
        "gh_executable": identity,
        "github_repository": github_repository,
        "forgejo_repository": forgejo_repository,
        "default_branch": default_branch,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "captures": captures,
    }


def parse_entry(entry: Any, expected_argv: list[str] | None, label: str) -> Any:
    if not isinstance(entry, dict) or set(entry) != {
        "argv", "exit", "stdout", "stdout_sha256", "stderr", "stderr_sha256",
    }:
        raise ValueError(f"{label} transport fields drifted")
    argv = entry["argv"]
    if not isinstance(argv, list) or not all(isinstance(value, str) for value in argv):
        raise ValueError(f"{label} argv is malformed")
    if expected_argv is not None and argv != expected_argv:
        raise ValueError(f"{label} argv mismatch")
    if entry["exit"] != 0:
        raise ValueError(f"{label} provider call did not exit zero")
    for stream in ("stdout", "stderr"):
        value = entry[stream]
        if not isinstance(value, str) or hashlib.sha256(value.encode()).hexdigest() != entry[f"{stream}_sha256"]:
            raise ValueError(f"{label} {stream} digest mismatch")
    try:
        return json.loads(entry["stdout"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} stdout is not JSON") from exc


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _provider_inventory(transport: dict[str, Any]) -> dict[str, Any]:
    if set(transport) != {
        "schema", "producer", "gh_executable", "github_repository", "forgejo_repository",
        "default_branch", "captured_at", "captures",
    }:
        raise ValueError("reconciliation transport fields drifted")
    if transport["schema"] != SCHEMA or transport["producer"] != "capture_reconciliation.py":
        raise ValueError("unsupported reconciliation transport producer")
    github_repository = transport["github_repository"]
    forgejo_repository = transport["forgejo_repository"]
    branch = transport["default_branch"]
    captures = transport["captures"]
    identity = transport["gh_executable"]
    if not isinstance(identity, dict) or set(identity) != {
        "invoked_path", "resolved_path", "sha256", "version",
    }:
        raise ValueError("reconciliation gh executable identity fields drifted")
    admitted_path = identity.get("invoked_path")
    gh_path = identity.get("resolved_path")
    if (
        admitted_path not in GH_CANDIDATES
        or not isinstance(gh_path, str)
        or not gh_path.startswith("/")
        or not isinstance(identity.get("sha256"), str)
        or SHA256.fullmatch(identity["sha256"]) is None
        or not isinstance(identity.get("version"), str)
        or not identity["version"].startswith("gh version ")
    ):
        raise ValueError("reconciliation gh executable identity is not admitted")
    if not isinstance(captures, list) or len(captures) < 6:
        raise ValueError("reconciliation transport is incomplete")
    github_repo = parse_entry(captures[0], [gh_path, "api", f"repos/{github_repository}"], "GitHub repository")
    github_pr_pages = parse_entry(
        captures[1],
        [gh_path, "api", "--paginate", "--slurp", f"repos/{github_repository}/pulls?state=open&per_page=100"],
        "GitHub open PRs",
    )
    github_issue_pages = parse_entry(
        captures[2],
        [gh_path, "api", "--paginate", "--slurp", f"repos/{github_repository}/issues?state=open&per_page=100"],
        "GitHub open issues",
    )
    forgejo_repo = parse_entry(
        captures[3],
        ["forgejo-api-authenticated-read", f"/api/v1/repos/{forgejo_repository}"],
        "Forgejo repository",
    )
    if not isinstance(github_repo, dict) or github_repo.get("full_name") != github_repository or github_repo.get("default_branch") != branch:
        raise ValueError("GitHub repository identity mismatch")
    if not isinstance(forgejo_repo, dict) or forgejo_repo.get("full_name") != forgejo_repository or forgejo_repo.get("default_branch") != branch:
        raise ValueError("Forgejo repository identity mismatch")
    if not isinstance(github_pr_pages, list) or any(not isinstance(page, list) for page in github_pr_pages):
        raise ValueError("GitHub PR pagination transport is malformed")
    if not isinstance(github_issue_pages, list) or any(not isinstance(page, list) for page in github_issue_pages):
        raise ValueError("GitHub issue pagination transport is malformed")
    github_prs = [item for page in github_pr_pages for item in page]
    github_issues = [item for page in github_issue_pages for item in page if isinstance(item, dict) and "pull_request" not in item]
    index = 4
    forgejo_prs: list[Any] = []
    page = 1
    pr_terminal_page = False
    while index < len(captures):
        expected = f"/api/v1/repos/{forgejo_repository}/pulls?state=open&limit=50&page={page}"
        if captures[index].get("argv") != ["forgejo-api-authenticated-read", expected]:
            break
        payload = parse_entry(captures[index], ["forgejo-api-authenticated-read", expected], f"Forgejo PR page {page}")
        if not isinstance(payload, list):
            raise ValueError("Forgejo PR page is malformed")
        forgejo_prs.extend(payload);index += 1
        if len(payload) < 50:
            pr_terminal_page = True
            break
        page += 1
    if not pr_terminal_page:
        raise ValueError("Forgejo PR pagination lacks a terminal short page")
    forgejo_issues: list[Any] = []
    page = 1
    issue_terminal_page = False
    while index < len(captures):
        expected = f"/api/v1/repos/{forgejo_repository}/issues?state=open&type=issues&limit=50&page={page}"
        payload = parse_entry(captures[index], ["forgejo-api-authenticated-read", expected], f"Forgejo issue page {page}")
        if not isinstance(payload, list):
            raise ValueError("Forgejo issue page is malformed")
        forgejo_issues.extend(payload);index += 1
        if len(payload) < 50:
            issue_terminal_page = True
            break
        page += 1
    if not issue_terminal_page:
        raise ValueError("Forgejo issue pagination lacks a terminal short page")
    if index != len(captures):
        raise ValueError("reconciliation transport contains unconsumed provider calls")
    return {
        "repository_ids": {
            "github": _positive_int(github_repo.get("id"), "GitHub repository ID"),
            "forgejo": _positive_int(forgejo_repo.get("id"), "Forgejo repository ID"),
        },
        "github_prs": github_prs,
        "forgejo_prs": forgejo_prs,
        "github_issues": github_issues,
        "forgejo_issues": forgejo_issues,
        "captured_at": transport["captured_at"],
    }


def verify_observation(transport: dict[str, Any], observation: dict[str, Any]) -> None:
    inventory = _provider_inventory(transport)
    if observation.get("schema") != OBSERVATION_SCHEMA:
        raise ValueError("reconciliation observation schema is unsupported")
    if observation.get("repository") != transport["github_repository"] or observation.get("forgejo_repository") != transport["forgejo_repository"]:
        raise ValueError("reconciliation repository identities differ from transport")
    if observation.get("repository_ids") != inventory["repository_ids"] or observation.get("captured_at") != inventory["captured_at"]:
        raise ValueError("reconciliation repository IDs/time do not derive from transport")

    def pr_key(raw: Any, forge: str) -> tuple[str, int, str, str, bool]:
        if not isinstance(raw, dict):
            raise ValueError(f"{forge} PR transport item is malformed")
        number = _positive_int(raw.get("number"), f"{forge} PR number")
        head = raw.get("head") or {};base = raw.get("base") or {};draft = raw.get("draft")
        if not isinstance(head, dict) or SHA40.fullmatch(str(head.get("sha"))) is None or not isinstance(base, dict) or not isinstance(base.get("ref"), str) or not base.get("ref") or not isinstance(draft, bool):
            raise ValueError(f"{forge} PR transport identity is malformed")
        return forge, number, head["sha"], base["ref"], draft

    def claimed_pr_key(item: Any, forge: str) -> tuple[str, int, str, str, bool]:
        if not isinstance(item, dict):
            raise ValueError(f"{forge} reconciliation PR item is malformed")
        return forge, _positive_int(item.get("number"), f"{forge} PR number"), item.get("head_sha"), item.get("base_branch"), item.get("wip")

    expected_prs = {
        *(pr_key(item, "github") for item in inventory["github_prs"]),
        *(pr_key(item, "forgejo") for item in inventory["forgejo_prs"]),
    }
    claimed_prs = {
        *(claimed_pr_key(item, "github") for item in observation.get("github_open_prs", [])),
        *(claimed_pr_key(item, "forgejo") for item in observation.get("forgejo_open_prs", [])),
    }
    if claimed_prs != expected_prs or len(claimed_prs) != len(observation.get("github_open_prs", [])) + len(observation.get("forgejo_open_prs", [])):
        raise ValueError("reconciliation open PR inventory is not exhaustive")
    expected_issues = {
        *( ("github", _positive_int(item.get("number"), "GitHub issue number")) for item in inventory["github_issues"] if isinstance(item, dict)),
        *( ("forgejo", _positive_int(item.get("number"), "Forgejo issue number")) for item in inventory["forgejo_issues"] if isinstance(item, dict)),
    }
    claimed_issues = {(item.get("forge"), item.get("number")) for item in observation.get("open_issues", []) if isinstance(item, dict)}
    if claimed_issues != expected_issues or len(claimed_issues) != len(observation.get("open_issues", [])):
        raise ValueError("reconciliation open issue inventory is not exhaustive")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--github-repository", required=True)
    capture_parser.add_argument("--forgejo-repository", required=True)
    capture_parser.add_argument("--default-branch", required=True)
    capture_parser.add_argument("--forge-url", default="http://localhost:3000")
    capture_parser.add_argument("--timeout-seconds", type=int, default=30)
    capture_parser.add_argument("--output", type=Path, required=True)
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--transport", type=Path, required=True)
    replay_parser.add_argument("--observation", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            value = capture(
                args.github_repository, args.forgejo_repository, args.default_branch,
                args.forge_url, args.timeout_seconds,
            )
            atomic(args.output.resolve(), value)
            print(f"WROTE {args.output.resolve()}")
        else:
            transport = json.loads(args.transport.read_text(encoding="utf-8"))
            observation = json.loads(args.observation.read_text(encoding="utf-8"))
            verify_observation(transport, observation)
            print("PASS reconciliation transport replay")
    except (CaptureError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL reconciliation capture/replay: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
