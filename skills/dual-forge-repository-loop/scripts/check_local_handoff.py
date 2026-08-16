#!/usr/bin/env python3
"""Validate repository-native local handoff manifests.

Exit codes:
  0  contract passes
  2  contract violation
 64  absent/malformed input

The checker proves archive-independence of the declared handoff shape. It does
not prove that a local runtime actually executed the handoff.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".gz", ".7z", ".rar", ".b64")
LOCAL_RUNTIMES = {"CLAUDE_CODE_LOCAL", "CODEX_CLI_LOCAL", "CHATGPT_DESKTOP_WORKTREE"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Invalid(Exception):
    pass


def refuse(msg: str) -> None:
    raise Invalid(msg)


def safe_repo_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        refuse(f"{label}: path must be a non-empty string")
    low = value.lower()
    if "://" in low or low.startswith(("sandbox:", "file:", "conversation:", "attachment:")):
        refuse(f"{label}: opaque/external locator is forbidden: {value}")
    p = Path(value)
    if p.is_absolute() or any(part == ".." for part in p.parts):
        refuse(f"{label}: path must stay inside checkout: {value}")
    if low.endswith(ARCHIVE_SUFFIXES):
        refuse(f"{label}: archive/base64 cannot be a required input: {value}")
    return value


def evaluate(doc: dict[str, Any]) -> None:
    if doc.get("schema") != "repository-native-local-handoff/v1":
        refuse("schema must be repository-native-local-handoff/v1")
    repository = doc.get("repository")
    if not isinstance(repository, str) or "/" not in repository or repository.startswith("/"):
        refuse("repository must be owner/name")

    subject = doc.get("subject")
    if not isinstance(subject, dict) or not SHA40.fullmatch(str(subject.get("commit", ""))):
        refuse("subject.commit must be a 40-character lowercase hex SHA")
    tree = subject.get("tree")
    if tree is not None and not SHA40.fullmatch(str(tree)):
        refuse("subject.tree must be a 40-character lowercase hex SHA when present")

    required = doc.get("required_inputs")
    if not isinstance(required, list) or not required:
        refuse("required_inputs must be a non-empty list")
    seen: set[str] = set()
    for i, item in enumerate(required):
        if not isinstance(item, dict):
            refuse(f"required_inputs[{i}] must be an object")
        path = safe_repo_path(item.get("path"), f"required_inputs[{i}]")
        if path in seen:
            refuse(f"duplicate required input: {path}")
        seen.add(path)
        if item.get("git_tracked") is not True:
            refuse(f"required input must declare git_tracked=true: {path}")
        if not SHA256.fullmatch(str(item.get("sha256", ""))):
            refuse(f"required input must carry exact sha256: {path}")

    entrypoint = safe_repo_path(doc.get("entrypoint"), "entrypoint")
    if entrypoint not in seen:
        refuse("entrypoint must also appear in required_inputs")

    runtime = doc.get("runtime")
    allowed = runtime.get("allowed") if isinstance(runtime, dict) else None
    if not isinstance(allowed, list) or not allowed:
        refuse("runtime.allowed must be a non-empty list")
    unknown = set(allowed) - LOCAL_RUNTIMES
    if unknown:
        refuse(f"runtime.allowed contains non-local runtime(s): {sorted(unknown)}")

    exports = doc.get("optional_exports", [])
    if not isinstance(exports, list):
        refuse("optional_exports must be a list")
    for i, item in enumerate(exports):
        if not isinstance(item, dict):
            refuse(f"optional_exports[{i}] must be an object")
        if item.get("required") is not False:
            refuse(f"optional export must declare required=false at index {i}")

    if doc.get("archive_independence") is not True:
        refuse("archive_independence must be true")


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise SystemExit(64) from e
    except (OSError, json.JSONDecodeError) as e:
        print(f"LOCAL-HANDOFF-INVALID {e}", file=sys.stderr)
        raise SystemExit(64) from e
    if not isinstance(data, dict):
        print("LOCAL-HANDOFF-INVALID top level must be object", file=sys.stderr)
        raise SystemExit(64)
    return data


def selftest() -> None:
    good = {
        "schema": "repository-native-local-handoff/v1",
        "repository": "example/repo",
        "subject": {"commit": "a" * 40, "tree": "b" * 40},
        "required_inputs": [
            {"path": "replay/REPLAY.sh", "git_tracked": True, "sha256": "1" * 64},
            {"path": "replay/contract.json", "git_tracked": True, "sha256": "2" * 64},
        ],
        "entrypoint": "replay/REPLAY.sh",
        "runtime": {"allowed": ["CODEX_CLI_LOCAL", "CLAUDE_CODE_LOCAL"]},
        "optional_exports": [{"path": "exports/replay.zip", "required": False}],
        "archive_independence": True,
    }
    evaluate(good)
    mutations = {
        "zip-required": lambda d: d["required_inputs"].append({"path": "replay.zip", "git_tracked": True, "sha256": "3" * 64}),
        "base64-required": lambda d: d["required_inputs"].append({"path": "part-01.b64", "git_tracked": True, "sha256": "3" * 64}),
        "url-required": lambda d: d["required_inputs"].append({"path": "https://example.invalid/file", "git_tracked": True, "sha256": "3" * 64}),
        "sandbox-required": lambda d: d["required_inputs"].append({"path": "sandbox:/mnt/data/file", "git_tracked": True, "sha256": "3" * 64}),
        "untracked-required": lambda d: d["required_inputs"].append({"path": "replay/live.json", "git_tracked": False, "sha256": "3" * 64}),
        "undigested-required": lambda d: d["required_inputs"].append({"path": "replay/live.json", "git_tracked": True, "sha256": "short"}),
        "entrypoint-not-required": lambda d: d.__setitem__("entrypoint", "replay/other.sh"),
        "archive-required-flag": lambda d: d["optional_exports"][0].__setitem__("required", True),
        "connector-runtime": lambda d: d["runtime"]["allowed"].append("CHATGPT_GITHUB_CONNECTOR"),
        "archive-independence-off": lambda d: d.__setitem__("archive_independence", False),
    }
    killed = 0
    for name, mutate in mutations.items():
        candidate = copy.deepcopy(good)
        mutate(candidate)
        try:
            evaluate(candidate)
        except Invalid:
            killed += 1
        else:
            raise AssertionError(f"mutation survived: {name}")
    print(f"SELFTEST GREEN: {killed}/{len(mutations)} archive/opaque-dependency defects refused")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.manifest:
        return 64
    doc = load(Path(args.manifest))
    try:
        evaluate(doc)
    except Invalid as e:
        print(f"LOCAL-HANDOFF-RED {e}")
        return 2
    print("LOCAL-HANDOFF-GREEN repository-native; archives are optional exports only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
