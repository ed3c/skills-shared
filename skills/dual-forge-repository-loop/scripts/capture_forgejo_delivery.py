#!/usr/bin/env python3
"""Capture and replay Forgejo issue/merged-PR/local-main delivery receipts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from capture_origin_ref import CaptureError, LOOPBACK_FORGES, credentials, forgejo_json


SCHEMA = "dual-forge-delivery-transport/v4"
OBSERVATION_SCHEMA = "dual-forge-delivery-observation/v5"
CREATION_SCHEMA = "dual-forge-worktree-creation-transport/v1"
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ISSUE_CONTEXT_MARKERS = (
    "## Objective", "## Invariants", "## Acceptance", "## Verification", "## Rollback",
)
RECOVERY_BLOCK = re.compile(
    r"<!--\s*three-strike-recovery\s*(\{.*?\})\s*-->", re.DOTALL,
)
THREAD_URL = re.compile(
    r"^https://chatgpt\.com/(?:g/[A-Za-z0-9_-]+/)?c/[0-9a-fA-F-]{32,64}$",
)
CLOSES = re.compile(r"(?im)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#([1-9][0-9]*)\b")


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


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def recovery_blocks(body: str) -> list[dict[str, Any]]:
    values = []
    for match in RECOVERY_BLOCK.finditer(body):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError("three-strike recovery block is not valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("three-strike recovery block must be an object")
        values.append(value)
    return values


def capture_artifact(url: str, forge_url: str, auth: str) -> dict[str, Any]:
    parsed = urlparse(url)
    base = urlparse(forge_url)
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc) or not parsed.path.startswith("/attachments/"):
        raise CaptureError("Desktop screenshot must be a loopback Forgejo attachment URL")
    request = Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with urlopen(request, timeout=15) as response:
            data = response.read(10 * 1024 * 1024 + 1)
            media_type = response.headers.get_content_type()
            status = response.status
    except OSError as exc:
        raise CaptureError(f"Desktop screenshot capture failed: {url}") from exc
    if status != 200 or len(data) > 10 * 1024 * 1024:
        raise CaptureError("Desktop screenshot attachment is unavailable or too large")
    return {
        "url": url, "status": status, "media_type": media_type,
        "body_base64": base64.b64encode(data).decode(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def recovery_branch(desktop_receipt_sha256: str, issue_number: int, base_sha: str) -> str:
    if SHA256.fullmatch(desktop_receipt_sha256 or "") is None or issue_number <= 0 or SHA40.fullmatch(base_sha or "") is None:
        raise CaptureError("recovery worktree causality inputs are malformed")
    nonce = hashlib.sha256(
        f"{desktop_receipt_sha256}\0{issue_number}\0{base_sha}".encode()
    ).hexdigest()[:16]
    return f"recovery/issue-{issue_number}-{nonce}"


def normalized_record(
    argv: list[str], result: subprocess.CompletedProcess[str], replacements: dict[str, str]
) -> dict[str, Any]:
    stdout, stderr = result.stdout, result.stderr
    for actual, token in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        stdout = stdout.replace(actual, token)
        stderr = stderr.replace(actual, token)
    return record(argv, result.returncode, stdout, stderr)


def materialize(
    repo_root: Path,
    worktree: Path,
    issue_number: int,
    base_sha: str,
    desktop_receipt_sha256: str,
    desktop_response_started_at: str,
) -> dict[str, Any]:
    root = repo_root.resolve();target = worktree.resolve()
    if root == target or target.exists():
        raise CaptureError("recovery worktree target must be a fresh path outside the main working tree")
    response_time = timestamp(desktop_response_started_at, "Desktop response_started_at")
    branch = recovery_branch(desktop_receipt_sha256, issue_number, base_sha)
    reason = f"desktop-recovery:{desktop_receipt_sha256[:16]}"
    pre_argv = ["git", "-C", str(root), "worktree", "list", "--porcelain"]
    pre = subprocess.run(pre_argv, capture_output=True, text=True, check=False, timeout=15)
    if pre.returncode != 0 or str(target) in pre.stdout or f"branch refs/heads/{branch}" in pre.stdout:
        raise CaptureError("recovery worktree path or causal branch existed before materialization")
    add_args = ["worktree", "add", "--lock", "--reason", reason, "-b", branch, str(target), base_sha]
    add = subprocess.run(["git", "-C", str(root), *add_args], capture_output=True, text=True, check=False, timeout=60)
    if add.returncode != 0:
        raise CaptureError("trusted recovery worktree materialization failed")
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if timestamp(created_at, "recovery worktree created_at") <= response_time:
        raise CaptureError("recovery worktree materialization did not follow the Desktop response")
    replacements = {str(root): "<repo-root>", str(target): "<worktree>"}
    return {
        "schema": CREATION_SCHEMA,
        "producer": "capture_forgejo_delivery.py:materialize",
        "issue_number": issue_number,
        "desktop_receipt_sha256": desktop_receipt_sha256,
        "desktop_response_started_at": desktop_response_started_at,
        "base_sha": base_sha,
        "branch": branch,
        "lock_reason": reason,
        "created_at": created_at,
        "captures": [
            normalized_record(
                ["git", "-C", "<repo-root>", "worktree", "list", "--porcelain"],
                pre, replacements,
            ),
            normalized_record(
                ["git", "-C", "<repo-root>", *add_args[:-2], "<worktree>", base_sha],
                add, replacements,
            ),
        ],
    }


def capture(
    forgejo_repository: str,
    default_branch: str,
    issue_numbers: list[int],
    pull_numbers: list[int],
    local_main_sha: str,
    repo_root: Path,
    forge_url: str,
    recovery_issue: int,
    recovery_worktree: Path,
    recovery_base_sha: str,
    recovery_creation: dict[str, Any],
) -> dict[str, Any]:
    if REPOSITORY.fullmatch(forgejo_repository) is None or SHA40.fullmatch(local_main_sha) is None:
        raise CaptureError("Forgejo repository or local-main SHA is malformed")
    if not issue_numbers or not pull_numbers or any(value <= 0 for value in issue_numbers + pull_numbers):
        raise CaptureError("at least one positive issue and merged PR number is required")
    if recovery_issue not in issue_numbers or SHA40.fullmatch(recovery_base_sha) is None:
        raise CaptureError("recovery worktree must bind one captured issue and an exact base SHA")
    if forge_url not in LOOPBACK_FORGES:
        raise CaptureError("Forgejo URL must be the allowlisted loopback forge")
    username, password = credentials(forge_url)
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    owner, name = forgejo_repository.split("/", 1)
    root = f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    captures = []
    artifact_urls: set[str] = set()
    for endpoint in [root]:
        _, stdout = forgejo_json(forge_url, endpoint, auth)
        captures.append(record(["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"], 0, stdout))
    for number in issue_numbers:
        endpoint = f"{root}/issues/{number}"
        _, stdout = forgejo_json(forge_url, endpoint, auth)
        captures.append(record(["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"], 0, stdout))
        page = 1
        while True:
            endpoint = f"{root}/issues/{number}/comments?limit=50&page={page}"
            payload, stdout = forgejo_json(forge_url, endpoint, auth)
            captures.append(record(["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"], 0, stdout))
            if not isinstance(payload, list):
                raise CaptureError(f"Forgejo issue {number} comments are malformed")
            for comment in payload:
                if isinstance(comment, dict) and isinstance(comment.get("body"), str):
                    for packet in recovery_blocks(comment["body"]):
                        desktop = packet.get("desktop_submission")
                        if isinstance(desktop, dict) and isinstance(desktop.get("screenshot_url"), str):
                            artifact_urls.add(desktop["screenshot_url"])
            if len(payload) < 50:
                break
            page += 1
    for number in pull_numbers:
        endpoint = f"{root}/pulls/{number}"
        _, stdout = forgejo_json(forge_url, endpoint, auth)
        captures.append(record(["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"], 0, stdout))
    worktree_path = recovery_worktree.resolve();repo_path = repo_root.resolve()
    if worktree_path == repo_path:
        raise CaptureError("recovery worktree cannot be the main working tree")
    worktree_commands = (
        (["rev-parse", "--show-toplevel", "--is-inside-work-tree", "HEAD"], "identity"),
        (["symbolic-ref", "--short", "HEAD"], "branch"),
        (["merge-base", "--is-ancestor", recovery_base_sha, "HEAD"], "base"),
        (["rev-parse", "--path-format=absolute", "--git-common-dir"], "worktree-common-dir"),
        (["-C", str(repo_path), "rev-parse", "--path-format=absolute", "--git-common-dir"], "repo-common-dir"),
        (["worktree", "list", "--porcelain"], "lease"),
    )
    for arguments, label in worktree_commands:
        argv = ["git", "-C", str(worktree_path), *arguments]
        normalized_argv = ["git", "-C", "<worktree>", *arguments]
        if label == "repo-common-dir":
            argv = ["git", "-C", str(repo_path), "rev-parse", "--path-format=absolute", "--git-common-dir"]
            normalized_argv = ["git", "-C", "<repo-root>", "rev-parse", "--path-format=absolute", "--git-common-dir"]
        result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=15)
        stdout = result.stdout
        if label == "identity":
            lines = stdout.splitlines()
            if lines and Path(lines[0]).resolve() == worktree_path:
                lines[0] = "<worktree>"
                stdout = "\n".join(lines) + ("\n" if result.stdout.endswith("\n") else "")
        elif label in {"worktree-common-dir", "repo-common-dir"}:
            stdout = "<common-git-dir>\n" if result.stdout.strip() else result.stdout
        elif label == "lease":
            normalized = []
            other = 0
            for line in stdout.splitlines():
                if line.startswith("worktree "):
                    path = Path(line.removeprefix("worktree "))
                    if path.resolve() == worktree_path:
                        line = "worktree <worktree>"
                    else:
                        other += 1
                        line = f"worktree <other-worktree-{other}>"
                normalized.append(line)
            stdout = "\n".join(normalized) + ("\n" if result.stdout.endswith("\n") else "")
        captures.append(record(normalized_argv, result.returncode, stdout, result.stderr))
        if result.returncode != 0:
            raise CaptureError(f"recovery worktree {label} capture failed")
    actual_worktree_common = subprocess.run(
        ["git", "-C", str(worktree_path), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, check=True, timeout=15,
    ).stdout.strip()
    actual_repo_common = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, check=True, timeout=15,
    ).stdout.strip()
    if Path(actual_worktree_common).resolve() != Path(actual_repo_common).resolve():
        raise CaptureError("recovery worktree does not belong to the target repository object graph")
    for format_value in ("%H %P", "%T"):
        argv = ["git", "-C", str(repo_root.resolve()), "show", "-s", f"--format={format_value}", local_main_sha]
        result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=15)
        captures.append(record(
            ["git", "-C", "<repo-root>", "show", "-s", f"--format={format_value}", local_main_sha],
            result.returncode, result.stdout, result.stderr,
        ))
        if result.returncode != 0:
            raise CaptureError("local main Git receipt capture failed")
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "producer": "capture_forgejo_delivery.py",
        "forgejo_repository": forgejo_repository,
        "default_branch": default_branch,
        "issue_numbers": issue_numbers,
        "pull_numbers": pull_numbers,
        "local_main_sha": local_main_sha,
        "captured_at": captured_at,
        "recovery_worktree": {
            "issue_number": recovery_issue,
            "base_sha": recovery_base_sha,
            "observed_at": captured_at,
            "lease_kind": "git-branch-lock",
            "creation": recovery_creation,
        },
        "captures": captures,
        "desktop_artifacts": [capture_artifact(url, forge_url, auth) for url in sorted(artifact_urls)],
    }


def parse(entry: Any, argv: list[str], label: str) -> Any:
    if not isinstance(entry, dict) or set(entry) != {
        "argv", "exit", "stdout", "stdout_sha256", "stderr", "stderr_sha256",
    }:
        raise ValueError(f"{label} capture fields drifted")
    if entry["argv"] != argv or entry["exit"] != 0:
        raise ValueError(f"{label} exact argv/exit mismatch")
    for stream in ("stdout", "stderr"):
        value = entry[stream]
        if not isinstance(value, str) or hashlib.sha256(value.encode()).hexdigest() != entry[f"{stream}_sha256"]:
            raise ValueError(f"{label} {stream} digest mismatch")
    try:
        return json.loads(entry["stdout"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} stdout is not JSON") from exc


def validated_artifacts(values: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(values, list):
        raise ValueError("Desktop artifact transport must be an array")
    result = {}
    for index, item in enumerate(values):
        if not isinstance(item, dict) or set(item) != {
            "url", "status", "media_type", "body_base64", "sha256",
        }:
            raise ValueError(f"Desktop artifact[{index}] fields drifted")
        if item["url"] in result or item["status"] != 200 or item["media_type"] not in {"image/png", "image/jpeg"}:
            raise ValueError(f"Desktop artifact[{index}] identity/media is invalid")
        try:
            data = base64.b64decode(item["body_base64"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Desktop artifact[{index}] body is not canonical base64") from exc
        digest = hashlib.sha256(data).hexdigest()
        if digest != item["sha256"] or SHA256.fullmatch(digest) is None:
            raise ValueError(f"Desktop artifact[{index}] digest mismatch")
        if item["media_type"] == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Desktop artifact[{index}] is not a PNG")
        if item["media_type"] == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
            raise ValueError(f"Desktop artifact[{index}] is not a JPEG")
        result[item["url"]] = item
    return result


def validate_recovery(
    packet: dict[str, Any], comment: dict[str, Any], artifacts: dict[str, dict[str, Any]],
) -> tuple[str, str, str, str, int, str, str]:
    if set(packet) != {
        "schema", "attempts", "root_cause_question", "implementation_boundary",
        "desktop_submission",
    } or packet.get("schema") != "three-strike-recovery/v1":
        raise ValueError("three-strike recovery packet fields/schema drifted")
    attempts = packet["attempts"]
    if not isinstance(attempts, list) or len(attempts) != 3:
        raise ValueError("three-strike recovery must contain exactly three attempts")
    attempt_times = []
    for index, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, dict) or set(attempt) != {
            "number", "subject", "error", "error_sha256", "evidence_ref", "occurred_at",
        } or attempt.get("number") != index:
            raise ValueError(f"three-strike attempt {index} fields/order drifted")
        for field in ("subject", "error", "evidence_ref"):
            if not isinstance(attempt[field], str) or len(attempt[field].strip()) < 8:
                raise ValueError(f"three-strike attempt {index} {field} is not diagnostic")
        if hashlib.sha256(attempt["error"].encode()).hexdigest() != attempt["error_sha256"]:
            raise ValueError(f"three-strike attempt {index} error digest mismatch")
        attempt_times.append(timestamp(attempt["occurred_at"], f"attempt {index} occurred_at"))
    if attempt_times != sorted(attempt_times):
        raise ValueError("three-strike attempt timestamps are out of order")
    for field in ("root_cause_question", "implementation_boundary"):
        if not isinstance(packet[field], str) or len(packet[field].strip()) < 20:
            raise ValueError(f"three-strike {field} is not self-contained")
    desktop = packet["desktop_submission"]
    if not isinstance(desktop, dict) or set(desktop) != {
        "schema", "observer", "prompt", "prompt_sha256", "thread_url",
        "submit_invoked_at", "timeline_visible_at", "response_started_at",
        "screenshot_url", "screenshot_sha256", "screenshot_media_type",
    } or desktop.get("schema") != "chatgpt-desktop-submission/v1":
        raise ValueError("Desktop submission receipt fields/schema drifted")
    observer = desktop["observer"]
    user = comment.get("user")
    if not isinstance(observer, dict) or set(observer) != {"login", "id"} or not isinstance(user, dict):
        raise ValueError("Desktop submission observer identity is absent")
    if observer.get("login") != user.get("login") or observer.get("id") != user.get("id"):
        raise ValueError("Desktop submission observer does not match provider comment author")
    if not isinstance(observer.get("login"), str) or not observer["login"] or not isinstance(observer.get("id"), int) or isinstance(observer.get("id"), bool) or observer["id"] <= 0:
        raise ValueError("Desktop submission observer identity is malformed")
    prompt = desktop["prompt"]
    if not isinstance(prompt, str) or len(prompt.strip()) < 80 or hashlib.sha256(prompt.encode()).hexdigest() != desktop["prompt_sha256"]:
        raise ValueError("Desktop submission prompt/digest is incomplete")
    if not isinstance(desktop["thread_url"], str) or THREAD_URL.fullmatch(desktop["thread_url"]) is None:
        raise ValueError("Desktop submission thread URL is not an exact ChatGPT conversation identity")
    event_times = [
        timestamp(desktop[field], f"Desktop {field}")
        for field in ("submit_invoked_at", "timeline_visible_at", "response_started_at")
    ]
    comment_time = timestamp(comment.get("created_at"), "Desktop receipt comment created_at")
    if event_times != sorted(event_times) or event_times[-1] > comment_time or event_times[0] < attempt_times[-1]:
        raise ValueError("Desktop submission event chronology is contradictory")
    artifact = artifacts.get(desktop["screenshot_url"])
    if artifact is None or artifact["sha256"] != desktop["screenshot_sha256"] or artifact["media_type"] != desktop["screenshot_media_type"]:
        raise ValueError("Desktop screenshot artifact is absent or digest/media mismatched")
    return (
        hashlib.sha256(canonical(packet)).hexdigest(),
        hashlib.sha256(canonical(desktop)).hexdigest(), desktop["thread_url"],
        desktop["prompt_sha256"], observer["id"], observer["login"],
        desktop["response_started_at"],
    )


def validate_creation(
    value: Any,
    issue_number: int,
    desktop_receipt_sha256: str,
    desktop_response_started_at: str,
    base_sha: str,
) -> tuple[str, str, str]:
    if not isinstance(value, dict) or set(value) != {
        "schema", "producer", "issue_number", "desktop_receipt_sha256",
        "desktop_response_started_at", "base_sha", "branch", "lock_reason",
        "created_at", "captures",
    } or value.get("schema") != CREATION_SCHEMA or value.get("producer") != "capture_forgejo_delivery.py:materialize":
        raise ValueError("recovery worktree creation transport fields/schema drifted")
    expected_branch = recovery_branch(desktop_receipt_sha256, issue_number, base_sha)
    expected_reason = f"desktop-recovery:{desktop_receipt_sha256[:16]}"
    if (
        value["issue_number"] != issue_number
        or value["desktop_receipt_sha256"] != desktop_receipt_sha256
        or value["desktop_response_started_at"] != desktop_response_started_at
        or value["base_sha"] != base_sha
        or value["branch"] != expected_branch
        or value["lock_reason"] != expected_reason
        or timestamp(value["created_at"], "recovery worktree created_at")
        <= timestamp(desktop_response_started_at, "Desktop response_started_at")
    ):
        raise ValueError("recovery worktree creation causality binding is inconsistent")
    captures = value["captures"]
    expected = (
        ["git", "-C", "<repo-root>", "worktree", "list", "--porcelain"],
        ["git", "-C", "<repo-root>", "worktree", "add", "--lock", "--reason", expected_reason, "-b", expected_branch, "<worktree>", base_sha],
    )
    if not isinstance(captures, list) or len(captures) != 2:
        raise ValueError("recovery worktree creation command inventory drifted")
    for index, (entry, argv) in enumerate(zip(captures, expected, strict=True)):
        if not isinstance(entry, dict) or set(entry) != {"argv", "exit", "stdout", "stdout_sha256", "stderr", "stderr_sha256"} or entry.get("argv") != argv or entry.get("exit") != 0:
            raise ValueError(f"recovery worktree creation command[{index}] argv/exit mismatch")
        for stream in ("stdout", "stderr"):
            payload = entry.get(stream)
            if not isinstance(payload, str) or hashlib.sha256(payload.encode()).hexdigest() != entry.get(f"{stream}_sha256"):
                raise ValueError(f"recovery worktree creation command[{index}] digest mismatch")
    if "<worktree>" in captures[0]["stdout"] or f"branch refs/heads/{expected_branch}" in captures[0]["stdout"]:
        raise ValueError("recovery worktree or causal branch existed before trusted materialization")
    return expected_branch, expected_reason, value["created_at"]


def verify_observation(transport: dict[str, Any], observation: dict[str, Any]) -> None:
    if set(transport) != {
        "schema", "producer", "forgejo_repository", "default_branch", "issue_numbers",
        "pull_numbers", "local_main_sha", "captured_at", "recovery_worktree",
        "captures", "desktop_artifacts",
    }:
        raise ValueError("Forgejo delivery transport fields drifted")
    if transport["schema"] != SCHEMA or transport["producer"] != "capture_forgejo_delivery.py":
        raise ValueError("unsupported Forgejo delivery transport producer")
    repository = transport["forgejo_repository"];branch = transport["default_branch"]
    issues = transport["issue_numbers"];pulls = transport["pull_numbers"];local_main = transport["local_main_sha"]
    captures = transport["captures"]
    artifacts = validated_artifacts(transport["desktop_artifacts"])
    if not isinstance(issues, list) or not isinstance(pulls, list) or len(captures) < 1 + len(issues) * 2 + len(pulls) + 2:
        raise ValueError("Forgejo delivery transport inventory is incomplete")
    root = f"repos/{repository}"
    repo_value = parse(captures[0], ["forgejo-api-authenticated-read", f"/api/v1/{root}"], "Forgejo repository")
    if not isinstance(repo_value, dict) or repo_value.get("full_name") != repository or repo_value.get("default_branch") != branch:
        raise ValueError("Forgejo delivery repository identity mismatch")
    repository_id = repo_value.get("id")
    if not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0:
        raise ValueError("Forgejo delivery repository ID is invalid")
    index = 1;derived_issues=[];desktop_response_by_issue={};desktop_receipt_by_issue={}
    for number in issues:
        value = parse(captures[index], ["forgejo-api-authenticated-read", f"/api/v1/{root}/issues/{number}"], f"Forgejo issue {number}");index += 1
        if not isinstance(value, dict) or value.get("number") != number or value.get("pull_request") not in (None, False):
            raise ValueError(f"Forgejo issue {number} provider identity mismatch")
        title=value.get("title");body=value.get("body")
        if not isinstance(title,str) or not title.strip() or not isinstance(body,str):
            raise ValueError(f"Forgejo issue {number} lacks provider-derived title/body")
        comments=[];page=1;terminal=False
        while index < len(captures):
            endpoint=f"/api/v1/{root}/issues/{number}/comments?limit=50&page={page}"
            if captures[index].get("argv") != ["forgejo-api-authenticated-read", endpoint]:
                break
            payload=parse(captures[index],["forgejo-api-authenticated-read",endpoint],f"Forgejo issue {number} comments page {page}");index+=1
            if not isinstance(payload,list) or any(
                not isinstance(item,dict) or not isinstance(item.get("body"),str)
                or not isinstance(item.get("user"),dict) or not isinstance(item.get("created_at"),str)
                for item in payload
            ):
                raise ValueError(f"Forgejo issue {number} comments are malformed")
            comments.extend(payload)
            if len(payload)<50:
                terminal=True;break
            page+=1
        if not terminal:
            raise ValueError(f"Forgejo issue {number} comments lack a terminal short page")
        joined="\n\n".join(item["body"] for item in comments)
        packets=[(packet,comment) for comment in comments for packet in recovery_blocks(comment["body"])]
        context_state="INCOMPLETE";desktop_state="NOT_EXERCISED"
        recovery_sha=desktop_sha=thread_url=prompt_sha=observer_login=response_started_at=None;observer_id=None
        if packets:
            if len(packets)!=1:
                raise ValueError(f"Forgejo issue {number} must have exactly one structured recovery packet")
            recovery_sha,desktop_sha,thread_url,prompt_sha,observer_id,observer_login,response_started_at=validate_recovery(packets[0][0],packets[0][1],artifacts)
            desktop_response_by_issue[number]=response_started_at
            desktop_receipt_by_issue[number]=desktop_sha
            context_state="PASS" if all(marker in body for marker in ISSUE_CONTEXT_MARKERS) else "INCOMPLETE"
            desktop_state="PASS"
        derived_issues.append((number,value.get("state"),hashlib.sha256(title.encode()).hexdigest(),hashlib.sha256(body.encode()).hexdigest(),hashlib.sha256(joined.encode()).hexdigest(),len(comments),context_state,desktop_state,recovery_sha,desktop_sha,thread_url,prompt_sha,observer_id,observer_login,response_started_at))
    derived_prs=[]
    for number in pulls:
        value = parse(captures[index], ["forgejo-api-authenticated-read", f"/api/v1/{root}/pulls/{number}"], f"Forgejo PR {number}");index += 1
        head=value.get("head") if isinstance(value,dict) else None;base=value.get("base") if isinstance(value,dict) else None
        if not isinstance(value,dict) or value.get("number")!=number or value.get("state")!="closed" or value.get("merged") is not True or not isinstance(head,dict) or not isinstance(base,dict):
            raise ValueError(f"Forgejo PR {number} is not a provider-derived merged PR")
        body=value.get("body");merged_at=value.get("merged_at")
        if not isinstance(body,str) or not isinstance(merged_at,str) or not merged_at:
            raise ValueError(f"Forgejo PR {number} lacks provider-derived body/merged_at")
        closes=sorted({int(match) for match in CLOSES.findall(body)})
        derived_prs.append((number,value["state"],value["merged"],head.get("sha"),value.get("merge_commit_sha"),base.get("ref"),hashlib.sha256(body.encode()).hexdigest(),merged_at,tuple(closes)))
    closed_by_pr={issue for item in derived_prs for issue in item[-1]}
    if not set(issues).issubset(closed_by_pr):
        raise ValueError("Forgejo merged PR bodies do not close every implementation issue")
    worktree_binding=transport["recovery_worktree"]
    if not isinstance(worktree_binding,dict) or set(worktree_binding)!={"issue_number","base_sha","observed_at","lease_kind","creation"}:
        raise ValueError("recovery worktree transport fields drifted")
    recovery_issue=worktree_binding["issue_number"]
    recovery_base=worktree_binding["base_sha"]
    observed_at=worktree_binding["observed_at"]
    if recovery_issue not in issues or recovery_issue not in desktop_response_by_issue or SHA40.fullmatch(recovery_base or "") is None or worktree_binding["lease_kind"]!="git-branch-lock":
        raise ValueError("recovery worktree binding is not an exact recovered issue/base")
    if observed_at!=transport["captured_at"] or timestamp(observed_at,"recovery worktree observed_at")<=timestamp(desktop_response_by_issue[recovery_issue],"Desktop response_started_at"):
        raise ValueError("recovery worktree was not observed after the Desktop response")
    causal_branch,lock_reason,created_at=validate_creation(
        worktree_binding["creation"], recovery_issue,
        desktop_receipt_by_issue[recovery_issue], desktop_response_by_issue[recovery_issue],
        recovery_base,
    )
    worktree_entries=captures[index:index+6];index+=6
    expected_worktree_argv=(
        ["git","-C","<worktree>","rev-parse","--show-toplevel","--is-inside-work-tree","HEAD"],
        ["git","-C","<worktree>","symbolic-ref","--short","HEAD"],
        ["git","-C","<worktree>","merge-base","--is-ancestor",recovery_base,"HEAD"],
        ["git","-C","<worktree>","rev-parse","--path-format=absolute","--git-common-dir"],
        ["git","-C","<repo-root>","rev-parse","--path-format=absolute","--git-common-dir"],
        ["git","-C","<worktree>","worktree","list","--porcelain"],
    )
    if len(worktree_entries)!=6:
        raise ValueError("recovery worktree Git transport is incomplete")
    for entry,expected in zip(worktree_entries,expected_worktree_argv,strict=True):
        if not isinstance(entry,dict) or set(entry)!={"argv","exit","stdout","stdout_sha256","stderr","stderr_sha256"} or entry.get("argv")!=expected or entry.get("exit")!=0:
            raise ValueError("recovery worktree exact Git argv/exit mismatch")
        for stream in ("stdout","stderr"):
            value=entry.get(stream)
            if not isinstance(value,str) or hashlib.sha256(value.encode()).hexdigest()!=entry.get(f"{stream}_sha256"):
                raise ValueError("recovery worktree Git stream digest mismatch")
    identity=worktree_entries[0]["stdout"].splitlines()
    if len(identity)!=3 or identity[0]!="<worktree>" or identity[1]!="true" or SHA40.fullmatch(identity[2]) is None:
        raise ValueError("recovery worktree identity is malformed")
    worktree_head=identity[2]
    worktree_branch=worktree_entries[1]["stdout"].strip()
    if BRANCH.fullmatch(worktree_branch or "") is None or ".." in worktree_branch or worktree_branch==branch or worktree_branch!=causal_branch:
        raise ValueError("recovery worktree branch is empty, unsafe, or default branch")
    if worktree_entries[2]["stdout"] or worktree_entries[2]["stderr"]:
        raise ValueError("recovery worktree base proof emitted unexpected output")
    if worktree_entries[3]["stdout"]!="<common-git-dir>\n" or worktree_entries[4]["stdout"]!="<common-git-dir>\n":
        raise ValueError("recovery worktree and target repository common Git dirs differ")
    lease=worktree_entries[5]["stdout"]
    branch_ref=f"refs/heads/{worktree_branch}"
    target_block=f"worktree <worktree>\nHEAD {worktree_head}\nbranch {branch_ref}\nlocked {lock_reason}"
    if target_block not in lease or lease.splitlines().count(f"branch {branch_ref}")!=1:
        raise ValueError("recovery worktree lacks one exclusive Git branch writer lease")
    matching_prs=[item for item in derived_prs if recovery_issue in item[-1] and item[3]==worktree_head]
    if len(matching_prs)!=1:
        raise ValueError("recovery worktree HEAD is not the unique merged PR closing its issue")
    derived_worktree={"issue_number":recovery_issue,"branch":worktree_branch,"head_sha":worktree_head,"base_sha":recovery_base,"created_at":created_at,"observed_at":observed_at,"creation_receipt_sha256":hashlib.sha256(canonical(worktree_binding["creation"])).hexdigest(),"writer_lease":{"kind":"git-branch-lock","branch_ref":branch_ref,"holders":1,"reason":lock_reason}}
    parents_entry=captures[index];tree_entry=captures[index+1]
    for entry,format_value,label in ((parents_entry,"%H %P","local-main parents"),(tree_entry,"%T","local-main tree")):
        expected=["git","-C","<repo-root>","show","-s",f"--format={format_value}",local_main]
        if entry.get("argv")!=expected or entry.get("exit")!=0:
            raise ValueError(f"{label} exact argv/exit mismatch")
        for stream in ("stdout","stderr"):
            value=entry.get(stream);digest=entry.get(f"{stream}_sha256")
            if not isinstance(value,str) or hashlib.sha256(value.encode()).hexdigest()!=digest:
                raise ValueError(f"{label} {stream} digest mismatch")
    parent_fields=parents_entry["stdout"].strip().split()
    if not parent_fields or parent_fields[0]!=local_main:
        raise ValueError("local-main merge receipt does not name its exact subject")
    tree=tree_entry["stdout"].strip()
    if SHA40.fullmatch(tree) is None:
        raise ValueError("local-main tree receipt is malformed")
    if observation.get("schema")!=OBSERVATION_SCHEMA or observation.get("forgejo_repository")!=repository or observation.get("forgejo_repository_id")!=repository_id or observation.get("default_branch")!=branch or observation.get("captured_at")!=transport["captured_at"]:
        raise ValueError("Forgejo delivery observation metadata does not derive from transport")
    claimed_issues={(item.get("number"),item.get("state"),item.get("title_sha256"),item.get("body_sha256"),item.get("comments_sha256"),item.get("comment_count"),item.get("context_state"),item.get("desktop_submission_state"),item.get("recovery_receipt_sha256"),item.get("desktop_receipt_sha256"),item.get("desktop_thread_url"),item.get("desktop_prompt_sha256"),item.get("desktop_observer_id"),item.get("desktop_observer_login"),item.get("desktop_response_started_at")) for item in observation.get("issues",[]) if isinstance(item,dict)}
    claimed_prs={(item.get("number"),item.get("state"),item.get("merged"),item.get("head_sha"),item.get("merge_commit_sha"),item.get("base_branch"),item.get("body_sha256"),item.get("merged_at"),tuple(item.get("closes_issues",[]))) for item in observation.get("merged_prs",[]) if isinstance(item,dict)}
    if claimed_issues!=set(derived_issues) or len(claimed_issues)!=len(observation.get("issues",[])):
        raise ValueError("Forgejo issue receipt inventory is not exhaustive")
    if claimed_prs!=set(derived_prs) or len(claimed_prs)!=len(observation.get("merged_prs",[])):
        raise ValueError("Forgejo merged-PR receipt inventory is not exhaustive")
    claimed_worktree=observation.get("recovery_worktree")
    if not isinstance(claimed_worktree,dict) or set(claimed_worktree)!={*derived_worktree,"receipt"} or {key:claimed_worktree.get(key) for key in derived_worktree}!=derived_worktree or claimed_worktree.get("receipt")!=f"local-git:worktree@{worktree_head[:7]}":
        raise ValueError("recovery worktree observation does not derive from Git transport")
    local_receipt=observation.get("local_main_merge")
    if not isinstance(local_receipt,dict) or local_receipt.get("sha")!=local_main or local_receipt.get("parents")!=parent_fields[1:] or local_receipt.get("tree_sha")!=tree:
        raise ValueError("local-main merge observation does not derive from Git transport")


def main() -> int:
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest="command",required=True)
    materialize_parser=sub.add_parser("materialize");materialize_parser.add_argument("--repo-root",type=Path,required=True);materialize_parser.add_argument("--worktree",type=Path,required=True);materialize_parser.add_argument("--issue",type=int,required=True);materialize_parser.add_argument("--base-sha",required=True);materialize_parser.add_argument("--desktop-receipt-sha256",required=True);materialize_parser.add_argument("--desktop-response-started-at",required=True);materialize_parser.add_argument("--output",type=Path,required=True)
    capture_parser=sub.add_parser("capture");capture_parser.add_argument("--forgejo-repository",required=True);capture_parser.add_argument("--default-branch",required=True);capture_parser.add_argument("--issue",type=int,action="append",required=True);capture_parser.add_argument("--pull",type=int,action="append",required=True);capture_parser.add_argument("--local-main-sha",required=True);capture_parser.add_argument("--repo-root",type=Path,required=True);capture_parser.add_argument("--recovery-issue",type=int,required=True);capture_parser.add_argument("--recovery-worktree",type=Path,required=True);capture_parser.add_argument("--recovery-base-sha",required=True);capture_parser.add_argument("--recovery-creation",type=Path,required=True);capture_parser.add_argument("--forge-url",default="http://localhost:3000");capture_parser.add_argument("--output",type=Path,required=True)
    replay=sub.add_parser("replay");replay.add_argument("--transport",type=Path,required=True);replay.add_argument("--observation",type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=="materialize":
            value=materialize(args.repo_root,args.worktree,args.issue,args.base_sha,args.desktop_receipt_sha256,args.desktop_response_started_at);atomic(args.output.resolve(),value);print(f"WROTE {args.output.resolve()}")
        elif args.command=="capture":
            creation=json.loads(args.recovery_creation.read_text(encoding="utf-8"));value=capture(args.forgejo_repository,args.default_branch,args.issue,args.pull,args.local_main_sha,args.repo_root,args.forge_url,args.recovery_issue,args.recovery_worktree,args.recovery_base_sha,creation);atomic(args.output.resolve(),value);print(f"WROTE {args.output.resolve()}")
        else:
            transport=json.loads(args.transport.read_text(encoding="utf-8"));observation=json.loads(args.observation.read_text(encoding="utf-8"));verify_observation(transport,observation);print("PASS Forgejo delivery transport replay")
    except (CaptureError,ValueError,OSError,json.JSONDecodeError,subprocess.TimeoutExpired) as exc:
        print(f"FAIL Forgejo delivery capture/replay: {exc}",file=sys.stderr);return 2
    return 0


if __name__=="__main__":raise SystemExit(main())
