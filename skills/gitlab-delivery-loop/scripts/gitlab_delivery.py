#!/usr/bin/env python3
"""Validate local delivery artifacts and their GitLab tracking receipts.

Zero network in `check`. Every schema and field name is `gitlab-*` so GitHub
state cannot pass through this gate by accident -- see modules/github-vs-gitlab.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from gitlab_sync import (
    HOST_RE,
    PROJECT_RE,
    PUBLICATION_SCHEMA,
    RECEIPT_SCHEMA,
    SHA_RE,
    SyncError,
    _json_bytes,
    build_outputs,
    fetch_gitlab_snapshot,
    reject_github_shape,
    write_outputs,
)


class DeliveryError(ValueError):
    """Raised when delivery state cannot be trusted."""


REGISTRY_SCHEMA = "gitlab-delivery-registry/v1"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DeliveryError(f"unreadable JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise DeliveryError(f"JSON root must be an object: {path}")
    return value


def _relative(raw: Any, field: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise DeliveryError(f"{field} must be a non-empty relative path")
    value = PurePosixPath(raw)
    if value.is_absolute() or ".." in value.parts:
        raise DeliveryError(f"unsafe path in {field}: {raw}")
    return Path(*value.parts)


def _gitlab_url(value: Any, field: str, host: str, project: str, kind: str) -> str | None:
    """Validate a GitLab web URL for this exact host and project path.

    GitLab puts a `/-/` separator between the project path and the resource,
    which is what keeps nested group paths unambiguous. Issues additionally
    resolve under `/-/work_items/N`: that is the form the live API returns in
    `web_url` for migrated issues, so rejecting it would reject real GitLab URLs.
    """
    if not isinstance(value, str):
        return f"invalid GitLab URL in {field}: expected string"
    if "github.com" in value:
        return (
            f"cross-forge URL in {field}: {value} -- this is the GitLab skill, "
            "use github-delivery-loop for GitHub state"
        )
    base = f"https://{re.escape(host)}/{re.escape(project)}"
    patterns = {
        "issue": rf"{base}/-/(?:issues|work_items)/[1-9][0-9]*",
        "merge_request": rf"{base}/-/merge_requests/[1-9][0-9]*",
        "board": rf"{base}/-/boards/[1-9][0-9]*",
    }
    if re.fullmatch(patterns[kind], value) is None:
        return f"invalid GitLab URL in {field}: {value}"
    return None


def _validate_line(line: dict[str, Any], repo_root: Path) -> list[str]:
    failures: list[str] = []
    line_id = line.get("id")
    if not isinstance(line_id, str) or not line_id:
        return ["registry line has no id"]
    try:
        reject_github_shape(line, f"registry line {line_id}")
    except SyncError as error:
        return [f"{line_id}: {error}"]

    host = line.get("gitlab_host")
    project = line.get("gitlab_project")
    project_id = line.get("gitlab_project_id")
    if not isinstance(host, str) or HOST_RE.fullmatch(host) is None:
        return [f"{line_id}: invalid gitlab_host"]
    if not isinstance(project, str) or PROJECT_RE.fullmatch(project) is None:
        return [f"{line_id}: gitlab_project must be a namespaced path (group[/subgroup]/project)"]
    if not isinstance(project_id, int) or isinstance(project_id, bool) or project_id < 1:
        return [f"{line_id}: gitlab_project_id must be a positive integer"]

    try:
        artifact = repo_root / _relative(line.get("artifact_path"), f"{line_id}.artifact_path")
        receipt_path = repo_root / _relative(line.get("receipt_path"), f"{line_id}.receipt_path")
        publication_path = repo_root / _relative(
            line.get("publication_path"), f"{line_id}.publication_path"
        )
    except DeliveryError as error:
        return [str(error)]
    if not artifact.exists():
        return [f"UNMATERIALIZED {line_id}: artifact does not exist: {artifact}"]
    if not receipt_path.is_file():
        return [f"RECEIPT-MISSING {line_id}: {receipt_path}"]
    try:
        receipt = _load_json(receipt_path)
        reject_github_shape(receipt, f"receipt {line_id}")
    except (DeliveryError, SyncError) as error:
        return [f"{line_id}: {error}"]

    if receipt.get("schema") != RECEIPT_SCHEMA:
        failures.append(f"{line_id}: invalid receipt schema (want {RECEIPT_SCHEMA})")
    if receipt.get("line") != line_id:
        failures.append(f"{line_id}: line mismatch")
    if receipt.get("gitlab_host") != host:
        failures.append(f"{line_id}: receipt gitlab_host mismatch")
    receipt_project = receipt.get("gitlab_project")
    if not isinstance(receipt_project, str) or PROJECT_RE.fullmatch(receipt_project) is None:
        failures.append(f"{line_id}: invalid receipt gitlab_project")
        receipt_project = project
    if receipt.get("gitlab_project_id") != project_id:
        failures.append(f"{line_id}: gitlab_project_id mismatch")
    if SHA_RE.fullmatch(str(receipt.get("source_commit", ""))) is None:
        failures.append(f"{line_id}: source_commit must be a full 40-character SHA")
    try:
        datetime.fromisoformat(str(receipt.get("synced_at", "")).replace("Z", "+00:00"))
    except ValueError:
        failures.append(f"{line_id}: synced_at must be ISO-8601")

    url_error = _gitlab_url(
        receipt.get("prd_issue_url"), "prd_issue_url", host, receipt_project, "issue"
    )
    if url_error:
        failures.append(f"{line_id}: {url_error}")
    for field, kind in (("issue_urls", "issue"), ("mr_urls", "merge_request")):
        values = receipt.get(field)
        if not isinstance(values, list):
            failures.append(f"{line_id}: {field} must be a list")
            continue
        for index, value in enumerate(values):
            url_error = _gitlab_url(value, f"{field}[{index}]", host, receipt_project, kind)
            if url_error:
                failures.append(f"{line_id}: {url_error}")
    url_error = _gitlab_url(receipt.get("board_url"), "board_url", host, receipt_project, "board")
    if url_error:
        failures.append(f"{line_id}: {url_error}")

    if not publication_path.is_file():
        failures.append(f"PUBLICATION-MISSING {line_id}: {publication_path}")
        return failures
    try:
        publication = _load_json(publication_path)
        reject_github_shape(publication, f"publication {line_id}")
    except (DeliveryError, SyncError) as error:
        failures.append(f"{line_id}: {error}")
        return failures

    if publication.get("schema") != PUBLICATION_SCHEMA:
        failures.append(f"{line_id}: invalid publication schema (want {PUBLICATION_SCHEMA})")
    if publication.get("line") != line_id:
        failures.append(f"{line_id}: publication line mismatch")
    if publication.get("gitlab_host") != host:
        failures.append(f"{line_id}: publication gitlab_host mismatch")
    if publication.get("gitlab_project") != receipt_project:
        failures.append(f"{line_id}: publication gitlab_project mismatch")
    if publication.get("gitlab_project_id") != project_id:
        failures.append(f"{line_id}: publication gitlab_project_id mismatch")
    if publication.get("remote_url") != f"https://{host}/{receipt_project}":
        failures.append(f"{line_id}: publication remote_url mismatch")
    # GitLab has three visibilities. `internal` is neither public nor private:
    # folding it into either is how a repo visible to every signed-in user on the
    # instance gets attested as private.
    if publication.get("visibility") not in {"private", "internal", "public"}:
        failures.append(f"{line_id}: publication visibility must be private, internal or public")
    for field in ("commit", "export_source_commit", "export_tree_sha"):
        if SHA_RE.fullmatch(str(publication.get(field, ""))) is None:
            failures.append(f"{line_id}: publication {field} must be a full SHA")
    remote_tree = publication.get("remote_head_tree_sha")
    if remote_tree is not None and SHA_RE.fullmatch(str(remote_tree)) is None:
        failures.append(f"{line_id}: publication remote_head_tree_sha must be a full SHA or null")
    if not isinstance(publication.get("file_count"), int) or publication["file_count"] < 1:
        failures.append(f"{line_id}: publication file_count must be positive")
    if publication.get("history_root") is not True:
        failures.append(f"{line_id}: publication history_root must be true")
    try:
        datetime.fromisoformat(str(publication.get("verified_at", "")).replace("Z", "+00:00"))
    except ValueError:
        failures.append(f"{line_id}: publication verified_at must be ISO-8601")
    blockers = publication.get("blockers")
    if not isinstance(blockers, list) or any(
        not isinstance(item, str) or not item for item in blockers
    ):
        failures.append(f"{line_id}: publication blockers must be a string list")
    elif publication.get("public_ready") is True and blockers:
        failures.append(f"{line_id}: public_ready publication cannot have blockers")
    elif publication.get("public_ready") is False and not blockers:
        failures.append(f"{line_id}: non-ready publication must name blockers")
    elif publication.get("public_ready") not in {True, False}:
        failures.append(f"{line_id}: publication public_ready must be boolean")
    if publication.get("public_ready") is True and (
        publication.get("visibility") != "public"
        or publication.get("license_key") != "mit"
        or publication.get("remote_head_tree_sha") != publication.get("export_tree_sha")
    ):
        failures.append(
            f"{line_id}: public_ready requires public visibility, an MIT license, and a "
            "remote head tree equal to the verified export tree"
        )
    return failures


def check(registry_path: Path) -> int:
    """Validate every registered line without network access."""
    registry_path = registry_path.resolve()
    try:
        registry = _load_json(registry_path)
        schema = registry.get("schema")
        if schema != REGISTRY_SCHEMA:
            if isinstance(schema, str) and schema.startswith("github-"):
                raise DeliveryError(
                    f"registry schema is {schema} -- that is GitHub state; run "
                    "github-delivery-loop's github_delivery.py against it"
                )
            raise DeliveryError(f"registry schema must be {REGISTRY_SCHEMA}")
        lines = registry.get("lines")
        if not isinstance(lines, list) or not lines:
            raise DeliveryError("registry lines must be a non-empty list")
        repo_root_raw = registry.get("repo_root")
        if not isinstance(repo_root_raw, str) or not repo_root_raw:
            raise DeliveryError("registry repo_root must be a non-empty string")
        repo_root = (registry_path.parent / repo_root_raw).resolve()
        failures: list[str] = []
        seen: set[str] = set()
        for raw_line in lines:
            if not isinstance(raw_line, dict):
                failures.append("registry line must be an object")
                continue
            line_id = raw_line.get("id")
            if line_id in seen:
                failures.append(f"duplicate line id: {line_id}")
                continue
            seen.add(line_id)
            line_failures = _validate_line(raw_line, repo_root)
            if line_failures:
                failures.extend(line_failures)
            else:
                print(f"PASS {line_id}")
        if failures:
            for failure in failures:
                print(f"FAIL {failure}", file=sys.stderr)
            return 1
        return 0
    except DeliveryError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


def _sync_line(registry_path: Path, line_id: str) -> tuple[dict[str, Any], Path]:
    registry_path = registry_path.resolve()
    registry = _load_json(registry_path)
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise DeliveryError(f"registry schema must be {REGISTRY_SCHEMA}")
    lines = registry.get("lines")
    if not isinstance(lines, list):
        raise DeliveryError("registry lines must be a list")
    matching = [line for line in lines if isinstance(line, dict) and line.get("id") == line_id]
    if len(matching) != 1:
        raise DeliveryError(f"registry line must exist exactly once: {line_id}")
    repo_root_raw = registry.get("repo_root")
    if not isinstance(repo_root_raw, str) or not repo_root_raw:
        raise DeliveryError("registry repo_root must be a non-empty string")
    repo_root = (registry_path.parent / repo_root_raw).resolve()
    line = matching[0]
    for field in ("receipt_path", "publication_path"):
        _relative(line.get(field), f"{line_id}.{field}")
    return line, repo_root


def sync(
    registry_path: Path,
    line_id: str,
    snapshot_path: Path | None,
    use_gitlab: bool,
    metrics_path: Path,
    dashboard_path: Path,
    export_source_commit: str,
    export_tree_sha: str,
    export_repo: Path | None,
) -> int:
    """Synchronize one delivery line from a replayable or live GitLab snapshot."""
    try:
        line, repo_root = _sync_line(registry_path, line_id)
        if snapshot_path is not None:
            snapshot = _load_json(snapshot_path.resolve())
        elif use_gitlab:
            current_receipt = _load_json(
                repo_root / _relative(line["receipt_path"], "receipt_path")
            )
            board_url = current_receipt.get("board_url")
            if not isinstance(board_url, str):
                raise DeliveryError("existing receipt must provide board_url for live sync")
            snapshot = fetch_gitlab_snapshot(line["gitlab_host"], line["gitlab_project"], board_url)
        else:
            raise DeliveryError("sync requires exactly one of --snapshot or --gitlab")
        receipt, publication, metrics, dashboard = build_outputs(
            line=line,
            snapshot=snapshot,
            export_source_commit=export_source_commit,
            export_tree_sha=export_tree_sha,
            export_repo=(export_repo or repo_root).resolve(),
        )
        receipt_path = repo_root / _relative(line["receipt_path"], "receipt_path")
        publication_path = repo_root / _relative(line["publication_path"], "publication_path")
        write_outputs(
            {
                receipt_path: _json_bytes(receipt),
                publication_path: _json_bytes(publication),
                metrics_path.resolve(): _json_bytes(metrics),
                dashboard_path.resolve(): dashboard.encode("utf-8"),
            }
        )
        print(f"SYNCED {line_id} {snapshot['fetched_at']}")
        for blocker in publication["blockers"]:
            print(f"  BLOCKER {blocker}")
        return 0
    except (DeliveryError, SyncError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check", help="run the zero-network receipt gate")
    check_parser.add_argument("--registry", required=True, type=Path)
    sync_parser = commands.add_parser(
        "sync", help="synchronize GitLab live state or replay a saved snapshot"
    )
    sync_parser.add_argument("--registry", required=True, type=Path)
    sync_parser.add_argument("--line", required=True)
    source = sync_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--gitlab", action="store_true")
    source.add_argument("--snapshot", type=Path)
    sync_parser.add_argument("--metrics", required=True, type=Path)
    sync_parser.add_argument("--dashboard", required=True, type=Path)
    sync_parser.add_argument("--export-source-commit", required=True)
    sync_parser.add_argument("--export-tree-sha", required=True)
    sync_parser.add_argument(
        "--export-repo",
        type=Path,
        help="local clone that was pushed; GitLab publishes no root tree sha, so the "
        "remote head's tree is resolved here. Defaults to the registry repo_root.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "check":
        return check(args.registry)
    if args.command == "sync":
        return sync(
            args.registry,
            args.line,
            args.snapshot,
            args.gitlab,
            args.metrics,
            args.dashboard,
            args.export_source_commit,
            args.export_tree_sha,
            args.export_repo,
        )
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
