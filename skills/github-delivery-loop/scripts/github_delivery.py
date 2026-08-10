#!/usr/bin/env python3
"""Validate local delivery artifacts and their GitHub tracking receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from delivery_sync import (
    SyncError,
    _json_bytes,
    build_outputs,
    fetch_github_snapshot,
    write_outputs,
)


class DeliveryError(ValueError):
    """Raised when delivery state cannot be trusted."""


COMMIT_RE = re.compile(r"[0-9a-f]{40}")
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


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


def _github_url(value: Any, field: str, repository: str, kind: str) -> str | None:
    if not isinstance(value, str):
        return f"invalid GitHub URL in {field}: expected string"
    escaped = re.escape(repository)
    patterns = {
        "issue": rf"https://github\.com/{escaped}/issues/[1-9][0-9]*",
        "pull": rf"https://github\.com/{escaped}/pull/[1-9][0-9]*",
        "project": (
            r"https://github\.com/(?:users|orgs)/[A-Za-z0-9_.-]+/projects/[1-9][0-9]*"
        ),
    }
    if re.fullmatch(patterns[kind], value) is None:
        return f"invalid GitHub URL in {field}: {value}"
    return None


def _validate_line(line: dict[str, Any], repo_root: Path) -> list[str]:
    failures: list[str] = []
    line_id = line.get("id")
    repository = line.get("github_repo")
    repository_id = line.get("github_repository_id")
    if not isinstance(line_id, str) or not line_id:
        return ["registry line has no id"]
    if not isinstance(repository, str) or REPO_RE.fullmatch(repository) is None:
        return [f"{line_id}: invalid github_repo"]
    if repository_id is not None and (
        not isinstance(repository_id, str) or not repository_id
    ):
        return [f"{line_id}: invalid github_repository_id"]
    try:
        artifact = repo_root / _relative(
            line.get("artifact_path"), f"{line_id}.artifact_path"
        )
        receipt_path = repo_root / _relative(
            line.get("receipt_path"), f"{line_id}.receipt_path"
        )
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
    except DeliveryError as error:
        return [f"{line_id}: {error}"]

    if receipt.get("schema") != "github-delivery-receipt/v1":
        failures.append(f"{line_id}: invalid receipt schema")
    if receipt.get("line") != line_id:
        failures.append(f"{line_id}: line mismatch")
    receipt_repository = receipt.get("github_repo")
    if (
        not isinstance(receipt_repository, str)
        or REPO_RE.fullmatch(receipt_repository) is None
    ):
        failures.append(f"{line_id}: invalid receipt github_repo")
        receipt_repository = repository
    if repository_id is None and receipt_repository != repository:
        failures.append(f"{line_id}: github_repo mismatch")
    if (
        repository_id is not None
        and receipt.get("github_repository_id") != repository_id
    ):
        failures.append(f"{line_id}: github_repository_id mismatch")
    if COMMIT_RE.fullmatch(str(receipt.get("source_commit", ""))) is None:
        failures.append(f"{line_id}: source_commit must be a full 40-character SHA")
    try:
        datetime.fromisoformat(str(receipt.get("synced_at", "")).replace("Z", "+00:00"))
    except ValueError:
        failures.append(f"{line_id}: synced_at must be ISO-8601")

    url_error = _github_url(
        receipt.get("prd_issue_url"), "prd_issue_url", receipt_repository, "issue"
    )
    if url_error:
        failures.append(f"{line_id}: {url_error}")
    for field, kind in (("issue_urls", "issue"), ("pr_urls", "pull")):
        values = receipt.get(field)
        if not isinstance(values, list):
            failures.append(f"{line_id}: {field} must be a list")
            continue
        for index, value in enumerate(values):
            url_error = _github_url(
                value, f"{field}[{index}]", receipt_repository, kind
            )
            if url_error:
                failures.append(f"{line_id}: {url_error}")
    url_error = _github_url(
        receipt.get("project_url"), "project_url", repository, "project"
    )
    if url_error:
        failures.append(f"{line_id}: {url_error}")

    if not publication_path.is_file():
        failures.append(f"PUBLICATION-MISSING {line_id}: {publication_path}")
        return failures
    try:
        publication = _load_json(publication_path)
    except DeliveryError as error:
        failures.append(f"{line_id}: {error}")
        return failures
    if publication.get("schema") != "github-publication-attestation/v1":
        failures.append(f"{line_id}: invalid publication schema")
    if publication.get("line") != line_id:
        failures.append(f"{line_id}: publication line mismatch")
    publication_repository = publication.get("github_repo")
    if publication_repository != receipt_repository:
        failures.append(f"{line_id}: publication github_repo mismatch")
    if (
        repository_id is not None
        and publication.get("github_repository_id") != repository_id
    ):
        failures.append(f"{line_id}: publication github_repository_id mismatch")
    if publication.get("remote_url") != f"https://github.com/{receipt_repository}":
        failures.append(f"{line_id}: publication remote_url mismatch")
    if publication.get("visibility") not in {"PRIVATE", "PUBLIC"}:
        failures.append(f"{line_id}: publication visibility must be PRIVATE or PUBLIC")
    for field in ("commit", "export_source_commit", "export_tree_sha"):
        if COMMIT_RE.fullmatch(str(publication.get(field, ""))) is None:
            failures.append(f"{line_id}: publication {field} must be a full SHA")
    if (
        not isinstance(publication.get("file_count"), int)
        or publication["file_count"] < 1
    ):
        failures.append(f"{line_id}: publication file_count must be positive")
    if publication.get("history_root") is not True:
        failures.append(f"{line_id}: publication history_root must be true")
    try:
        datetime.fromisoformat(
            str(publication.get("verified_at", "")).replace("Z", "+00:00")
        )
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
        publication.get("visibility") != "PUBLIC"
        or publication.get("license_spdx") != "MIT"
    ):
        failures.append(
            f"{line_id}: public_ready requires PUBLIC visibility and MIT license"
        )
    return failures


def check(registry_path: Path) -> int:
    """Validate every registered line without network access."""
    registry_path = registry_path.resolve()
    try:
        registry = _load_json(registry_path)
        if registry.get("schema") != "github-delivery-registry/v1":
            raise DeliveryError("registry schema must be github-delivery-registry/v1")
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
    if registry.get("schema") != "github-delivery-registry/v1":
        raise DeliveryError("registry schema must be github-delivery-registry/v1")
    lines = registry.get("lines")
    if not isinstance(lines, list):
        raise DeliveryError("registry lines must be a list")
    matching = [
        line for line in lines if isinstance(line, dict) and line.get("id") == line_id
    ]
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
    use_github: bool,
    metrics_path: Path,
    dashboard_path: Path,
    export_source_commit: str,
    export_tree_sha: str,
) -> int:
    """Synchronize one delivery line from a replayable or live GitHub snapshot."""
    try:
        line, repo_root = _sync_line(registry_path, line_id)
        current_receipt = _load_json(
            repo_root / _relative(line["receipt_path"], "receipt_path")
        )
        expected_prd_issue_url = current_receipt.get("prd_issue_url")
        if not isinstance(expected_prd_issue_url, str):
            raise DeliveryError("existing receipt must pin prd_issue_url")
        if snapshot_path is not None:
            snapshot = _load_json(snapshot_path.resolve())
        elif use_github:
            project_url = current_receipt.get("project_url")
            if not isinstance(project_url, str):
                raise DeliveryError(
                    "existing receipt must provide project_url for live sync"
                )
            snapshot = fetch_github_snapshot(line["github_repo"], project_url)
        else:
            raise DeliveryError("sync requires exactly one of --snapshot or --github")
        receipt, publication, metrics, dashboard = build_outputs(
            line=line,
            snapshot=snapshot,
            export_source_commit=export_source_commit,
            export_tree_sha=export_tree_sha,
            repo_root=repo_root,
            expected_prd_issue_url=expected_prd_issue_url,
        )
        receipt_path = repo_root / _relative(line["receipt_path"], "receipt_path")
        publication_path = repo_root / _relative(
            line["publication_path"], "publication_path"
        )
        write_outputs(
            {
                receipt_path: _json_bytes(receipt),
                publication_path: _json_bytes(publication),
                metrics_path.resolve(): _json_bytes(metrics),
                dashboard_path.resolve(): dashboard.encode("utf-8"),
            }
        )
        print(f"SYNCED {line_id} {snapshot['fetched_at']}")
        return 0
    except (DeliveryError, SyncError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser(
        "check", help="run the zero-network receipt gate"
    )
    check_parser.add_argument("--registry", required=True, type=Path)
    sync_parser = commands.add_parser(
        "sync", help="synchronize GitHub live state or replay a saved snapshot"
    )
    sync_parser.add_argument("--registry", required=True, type=Path)
    sync_parser.add_argument("--line", required=True)
    source = sync_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--github", action="store_true")
    source.add_argument("--snapshot", type=Path)
    sync_parser.add_argument("--metrics", required=True, type=Path)
    sync_parser.add_argument("--dashboard", required=True, type=Path)
    sync_parser.add_argument("--export-source-commit", required=True)
    sync_parser.add_argument("--export-tree-sha", required=True)
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
            args.github,
            args.metrics,
            args.dashboard,
            args.export_source_commit,
            args.export_tree_sha,
        )
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
