#!/usr/bin/env python3
"""Validate one admitted Forgejo issue-state request and its live readback."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import build_opener, HTTPRedirectHandler, Request


REQUEST_SCHEMA = "forgejo-terminal-issue-state-request@v2"
OBSERVATION_SCHEMA = "forgejo-issue-state-observation@v1"
RECEIPT_SCHEMA = "forgejo-issue-state-readback-receipt@v1"
LOOPBACK_FORGES = {"http://localhost:3000", "http://127.0.0.1:3000"}
STATES = {"open", "closed"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MAX_TRANSITION_SECONDS = 300
GITHUB_ISSUE_URL_RE = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*"
    r"(?=$|[\s<>)\]}'\",.;:!])"
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _object(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{name} fields drift")


def _load(path: Path, name: str) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{name} must be a regular file")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot parse {name}: {error}") from error
    return _object(value, name)


def _canonical(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _positive_integer(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _state(value: object, name: str) -> str:
    if not isinstance(value, str) or value not in STATES:
        raise ValueError(f"{name} must be open or closed")
    return value


def _timestamp(value: object, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{name} must include a UTC offset")
    return timestamp


def _github_locator(value: object, kind: str) -> tuple[str, int]:
    if not isinstance(value, str):
        raise ValueError(f"GitHub {kind} URL must be a string")
    parsed = urlparse(value)
    parts = parsed.path.strip("/").split("/")
    noun = "issues" if kind == "issue" else "pull"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or parsed.query
        or parsed.fragment
        or len(parts) != 4
        or parts[2] != noun
    ):
        raise ValueError(f"GitHub {kind} URL is invalid")
    try:
        number = int(parts[3])
    except ValueError as error:
        raise ValueError(f"GitHub {kind} number is invalid") from error
    if number <= 0:
        raise ValueError(f"GitHub {kind} number is invalid")
    return "/".join(parts[:2]), number


def validate_request(value: Mapping[str, object]) -> dict[str, object]:
    _exact_keys(
        value,
        {
            "schema_version", "forge_url", "repository", "issue_number",
            "action", "expected_state", "desired_state", "idempotency_marker",
            "source_receipt", "admission", "maturity_effect",
        },
        "request",
    )
    if value["schema_version"] != REQUEST_SCHEMA:
        raise ValueError("request schema_version is invalid")
    if value["forge_url"] not in LOOPBACK_FORGES:
        raise ValueError("forge_url must be the allowlisted local Forgejo")
    repository = value["repository"]
    if not isinstance(repository, str) or REPOSITORY_RE.fullmatch(repository) is None:
        raise ValueError("repository is invalid")
    issue_number = _positive_integer(value["issue_number"], "issue_number")
    if value["action"] != "set-state":
        raise ValueError("action must be set-state")
    expected_state = _state(value["expected_state"], "expected_state")
    desired_state = _state(value["desired_state"], "desired_state")
    if expected_state != "open" or desired_state != "closed":
        raise ValueError("terminal issue request must transition open to closed")
    marker = value["idempotency_marker"]
    if not isinstance(marker, str) or len(marker) > 256:
        raise ValueError("idempotency_marker must be one bounded source URL")

    source = _object(value["source_receipt"], "source_receipt")
    _exact_keys(
        source,
        {"kind", "issue_url", "issue_state", "pull_request_url", "merge_sha"},
        "source_receipt",
    )
    if source["kind"] != "github-issue-closure" or source["issue_state"] != "closed":
        raise ValueError("source_receipt must prove a closed GitHub issue")
    issue_repo, _ = _github_locator(source["issue_url"], "issue")
    pull_repo, _ = _github_locator(source["pull_request_url"], "pull request")
    if issue_repo != pull_repo:
        raise ValueError("GitHub issue and pull request repositories differ")
    if marker != source["issue_url"]:
        raise ValueError("idempotency_marker does not bind the source GitHub issue")
    if not isinstance(source["merge_sha"], str) or COMMIT_RE.fullmatch(source["merge_sha"]) is None:
        raise ValueError("source merge_sha must be a full lowercase commit")

    admission = _object(value["admission"], "admission")
    _exact_keys(admission, {"status", "authority", "reason"}, "admission")
    if admission["status"] != "admitted" or admission["authority"] != "user":
        raise ValueError("request lacks explicit user admission")
    reason = admission["reason"]
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise ValueError("admission reason is invalid")
    if value["maturity_effect"] != "tracking-only-no-maturity-change":
        raise ValueError("maturity_effect must preserve the tracking-only boundary")

    return {
        "status": "validated",
        "schema_version": REQUEST_SCHEMA,
        "request_sha256": _digest(value),
        "repository": repository,
        "issue_number": issue_number,
        "expected_state": expected_state,
        "desired_state": desired_state,
        "idempotency_marker": marker,
    }


def _run_json(command: list[str], name: str) -> Mapping[str, object]:
    try:
        completed = subprocess.run(
            command, text=True, capture_output=True, check=False, timeout=15
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"authenticated {name} read timed out") from error
    if completed.returncode != 0:
        raise ValueError(f"authenticated {name} read failed")
    try:
        return _object(json.loads(completed.stdout), name)
    except json.JSONDecodeError as error:
        raise ValueError(f"authenticated {name} read returned invalid JSON") from error


JsonReader = Callable[[list[str], str], Mapping[str, object]]


def validate_source_live(
    value: Mapping[str, object], json_reader: JsonReader = _run_json
) -> dict[str, object]:
    validated = validate_request(value)
    source = _object(value["source_receipt"], "source_receipt")
    repository, issue_number = _github_locator(source["issue_url"], "issue")
    _, pull_number = _github_locator(source["pull_request_url"], "pull request")
    issue = json_reader(
        ["gh", "api", f"repos/{repository}/issues/{issue_number}"], "GitHub issue"
    )
    pull = json_reader(
        ["gh", "api", f"repos/{repository}/pulls/{pull_number}"], "GitHub pull request"
    )
    if issue.get("html_url") != source["issue_url"] or issue.get("state") != "closed":
        raise ValueError("live GitHub issue is not the declared closed source")
    if pull.get("html_url") != source["pull_request_url"] or pull.get("merged_at") is None:
        raise ValueError("live GitHub pull request is not merged")
    if pull.get("merge_commit_sha") != source["merge_sha"]:
        raise ValueError("live GitHub pull request merge SHA mismatch")
    closes = re.compile(
        rf"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{issue_number}\b"
    )
    if closes.search(str(pull.get("body") or "")) is None:
        raise ValueError("merged GitHub pull request does not declare source issue closure")
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    observation = {
        "producer": "gh-cli-authenticated-read",
        "issue_url": source["issue_url"],
        "issue_state": "closed",
        "pull_request_url": source["pull_request_url"],
        "pull_request_state": "merged",
        "merge_sha": source["merge_sha"],
        "observed_at": observed_at,
    }
    stable_source_identity = {
        field: field_value
        for field, field_value in observation.items()
        if field != "observed_at"
    }
    return {
        "status": "source-verified",
        "request_sha256": validated["request_sha256"],
        "source_observation_sha256": _digest(stable_source_identity),
        **observation,
    }


def _credentials(forge_url: str) -> tuple[str, str]:
    parsed = urlparse(forge_url)
    try:
        completed = subprocess.run(
            ["git", "credential", "fill"],
            input=f"protocol={parsed.scheme}\nhost={parsed.netloc}\n\n",
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("Forgejo credential helper timed out") from error
    if completed.returncode != 0:
        raise ValueError("Forgejo credential helper failed")
    fields = dict(
        line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line
    )
    if not fields.get("username") or not fields.get("password"):
        raise ValueError("Forgejo credentials are unavailable")
    return fields["username"], fields["password"]


def _forgejo_issue(value: Mapping[str, object]) -> Mapping[str, object]:
    forge_url = str(value["forge_url"])
    repository = str(value["repository"])
    owner, repo = repository.split("/", 1)
    issue_number = int(value["issue_number"])
    username, password = _credentials(forge_url)
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    url = (
        f"{forge_url}/api/v1/repos/{quote(owner, safe='')}/"
        f"{quote(repo, safe='')}/issues/{issue_number}"
    )
    request = Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with build_opener(_NoRedirect()).open(request, timeout=10) as response:
            if response.geturl() != url:
                raise ValueError("Forgejo issue read crossed an origin boundary")
            return _object(json.load(response), "Forgejo issue")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ValueError("authenticated Forgejo issue read failed") from error


def _forgejo_timeline(value: Mapping[str, object]) -> list[Mapping[str, object]]:
    forge_url = str(value["forge_url"])
    owner, repo = str(value["repository"]).split("/", 1)
    issue_number = int(value["issue_number"])
    username, password = _credentials(forge_url)
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    url = (
        f"{forge_url}/api/v1/repos/{quote(owner, safe='')}/"
        f"{quote(repo, safe='')}/issues/{issue_number}/timeline"
    )
    request = Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with build_opener(_NoRedirect()).open(request, timeout=10) as response:
            if response.geturl() != url:
                raise ValueError("Forgejo timeline read crossed an origin boundary")
            value_json = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ValueError("authenticated Forgejo timeline read failed") from error
    if not isinstance(value_json, list) or not all(
        isinstance(item, dict) for item in value_json
    ):
        raise ValueError("Forgejo timeline must be an event list")
    return value_json


IssueReader = Callable[[Mapping[str, object]], Mapping[str, object]]
TimelineReader = Callable[[Mapping[str, object]], list[Mapping[str, object]]]


def _capture_live(
    value: Mapping[str, object], phase: str, expected_state: str,
    issue_reader: IssueReader,
) -> dict[str, object]:
    validated = validate_request(value)
    issue = issue_reader(value)
    if _positive_integer(issue.get("number"), "live issue number") != validated["issue_number"]:
        raise ValueError("live Forgejo issue number mismatch")
    live_state = _state(issue.get("state"), "live issue state")
    if live_state != expected_state:
        raise ValueError(f"live {phase} state does not match {expected_state}")
    marker = validated["idempotency_marker"]
    live_markers = set(GITHUB_ISSUE_URL_RE.findall(str(issue.get("body") or "")))
    if marker not in live_markers:
        raise ValueError("idempotency marker is absent from the live Forgejo issue")
    return {
        "status": "captured",
        "schema_version": OBSERVATION_SCHEMA,
        "request_sha256": validated["request_sha256"],
        "phase": phase,
        "producer": "forgejo-api-authenticated-read",
        "forge_url": value["forge_url"],
        "repository": value["repository"],
        "issue_number": value["issue_number"],
        "state": live_state,
        "idempotency_marker": marker,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def capture_pre_live(
    value: Mapping[str, object], issue_reader: IssueReader = _forgejo_issue
) -> dict[str, object]:
    validated = validate_request(value)
    return _capture_live(value, "pre", str(validated["expected_state"]), issue_reader)


def _validate_pre(value: Mapping[str, object], pre: Mapping[str, object]) -> dict[str, object]:
    validated = validate_request(value)
    _exact_keys(
        pre,
        {
            "status", "schema_version", "request_sha256", "phase", "producer",
            "forge_url", "repository", "issue_number", "state",
            "idempotency_marker", "observed_at",
        },
        "pre-observation",
    )
    if pre["status"] != "captured" or pre["schema_version"] != OBSERVATION_SCHEMA:
        raise ValueError("pre-observation schema is invalid")
    if pre["phase"] != "pre" or pre["producer"] != "forgejo-api-authenticated-read":
        raise ValueError("pre-observation provenance is invalid")
    digest = pre["request_sha256"]
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        raise ValueError("pre-observation request_sha256 is invalid")
    if digest != validated["request_sha256"]:
        raise ValueError("pre-observation request digest mismatch")
    _positive_integer(pre["issue_number"], "pre-observation issue_number")
    for field in ("forge_url", "repository", "issue_number", "idempotency_marker"):
        if pre[field] != value[field]:
            raise ValueError(f"pre-observation {field} mismatch")
    if _state(pre["state"], "pre-observation state") != validated["expected_state"]:
        raise ValueError("pre-observation state does not match expected_state")
    _timestamp(pre["observed_at"], "pre-observation observed_at")
    return validated


def _closure_event(
    pre: Mapping[str, object], timeline: list[Mapping[str, object]]
) -> tuple[str, str]:
    pre_time = _timestamp(pre["observed_at"], "pre-observation observed_at")
    candidates: list[tuple[datetime, str]] = []
    for event in timeline:
        if event.get("type") != "close":
            continue
        created_at = _timestamp(event.get("created_at"), "closure event created_at")
        delta = (created_at - pre_time).total_seconds()
        user = event.get("user")
        actor = user.get("login") if isinstance(user, dict) else None
        if 0 <= delta <= MAX_TRANSITION_SECONDS and isinstance(actor, str) and actor:
            candidates.append((created_at, actor))
    if len(candidates) != 1:
        raise ValueError("no unique authenticated closure event follows the pre-observation")
    created_at, actor = candidates[0]
    return created_at.isoformat(), actor


def verify_live(
    request: Mapping[str, object], pre: Mapping[str, object],
    issue_reader: IssueReader = _forgejo_issue,
    source_reader: JsonReader = _run_json,
    timeline_reader: TimelineReader = _forgejo_timeline,
) -> dict[str, object]:
    validated = _validate_pre(request, pre)
    source_observation = validate_source_live(request, source_reader)
    closure_created_at, closure_actor = _closure_event(pre, timeline_reader(request))
    post = _capture_live(
        request, "post", str(validated["desired_state"]), issue_reader
    )
    stable_post_identity = {
        field: field_value for field, field_value in post.items()
        if field != "observed_at"
    }
    source = _object(request["source_receipt"], "source_receipt")
    return {
        "status": "verified",
        "schema_version": RECEIPT_SCHEMA,
        "producer": "forgejo-api-authenticated-read",
        "request_sha256": validated["request_sha256"],
        "source_observation_sha256": source_observation["source_observation_sha256"],
        "pre_observation_sha256": _digest(pre),
        "post_observation_sha256": _digest(stable_post_identity),
        "closure_created_at": closure_created_at,
        "closure_actor": closure_actor,
        "repository": request["repository"],
        "issue_number": request["issue_number"],
        "state": post["state"],
        "idempotency_marker": post["idempotency_marker"],
        "observed_at": post["observed_at"],
        "source_merge_sha": source["merge_sha"],
        "maturity_effect": request["maturity_effect"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--request", type=Path, required=True)
    source = subparsers.add_parser("validate-source-live")
    source.add_argument("--request", type=Path, required=True)
    capture = subparsers.add_parser("capture-pre-live")
    capture.add_argument("--request", type=Path, required=True)
    readback = subparsers.add_parser("verify-live")
    readback.add_argument("--request", type=Path, required=True)
    readback.add_argument("--pre-observation", type=Path, required=True)
    args = parser.parse_args()
    try:
        request = _load(args.request, "request")
        if args.command == "validate":
            result = validate_request(request)
        elif args.command == "validate-source-live":
            result = validate_source_live(request)
        elif args.command == "capture-pre-live":
            result = capture_pre_live(request)
        else:
            result = verify_live(request, _load(args.pre_observation, "pre-observation"))
    except (OSError, TypeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
