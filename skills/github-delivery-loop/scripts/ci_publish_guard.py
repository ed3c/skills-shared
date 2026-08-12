#!/usr/bin/env python3
"""PreToolUse guard that routes managed GitHub pushes through ci_publish.py."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


POLICY_PATH = Path(".github-delivery/ci-policy.json")


def _command(payload: dict[str, Any]) -> tuple[str, Path]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return "", Path.cwd()
    command = tool_input.get("command", tool_input.get("cmd", ""))
    if not isinstance(command, str):
        return "", Path.cwd()
    cwd_value = tool_input.get("workdir", tool_input.get("cwd", os.getcwd()))
    cwd = Path(cwd_value) if isinstance(cwd_value, str) and cwd_value else Path.cwd()
    return command, cwd


def _repo_root(cwd: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _pushes(command: str, cwd: Path) -> list[tuple[Path, str | None]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token and set(token).issubset({";", "&", "|"}):
            segments.append([])
        else:
            segments[-1].append(token)
    pushes: list[tuple[Path, str | None]] = []
    active_cwd = cwd
    for tokens in segments:
        if len(tokens) == 2 and tokens[0] == "cd":
            candidate = Path(tokens[1])
            active_cwd = candidate if candidate.is_absolute() else active_cwd / candidate
            continue
        if tokens and tokens[0] in {"command", "env"}:
            tokens = tokens[1:]
        if not tokens or Path(tokens[0]).name != "git":
            continue
        index = 1
        command_cwd = active_cwd
        if index + 1 < len(tokens) and tokens[index] == "-C":
            command_cwd = Path(tokens[index + 1])
            index += 2
        if index >= len(tokens) or tokens[index] != "push":
            continue
        index += 1
        while index < len(tokens) and tokens[index].startswith("-"):
            index += 1
        remote = tokens[index] if index < len(tokens) else None
        pushes.append((command_cwd, remote))
    return pushes


def _github_remote(repo_root: Path, remote: str | None) -> bool:
    if remote and ("github.com:" in remote.lower() or "github.com/" in remote.lower()):
        return True
    if remote:
        argv = ["git", "-C", str(repo_root), "remote", "get-url", "--push", remote]
    else:
        branch = subprocess.run(
            ["git", "-C", str(repo_root), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        selected = subprocess.run(
            ["git", "-C", str(repo_root), "config", "--get", f"branch.{branch}.remote"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        argv = ["git", "-C", str(repo_root), "remote", "get-url", "--push", selected or "origin"]
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # An enrolled repository with an unresolvable push destination fails closed.
        return True
    return "github.com" in result.stdout.lower()


def should_block(payload: dict[str, Any]) -> tuple[bool, str]:
    command, cwd = _command(payload)
    pushes = _pushes(command, cwd)
    if not pushes:
        return False, "not-a-git-push"
    for command_cwd, remote in pushes:
        root = _repo_root(command_cwd)
        if root is None or not (root / POLICY_PATH).is_file():
            continue
        if _github_remote(root, remote):
            return True, f"managed GitHub publication in {root} must use ci_publish.py"
    return False, "no-managed-github-push"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"BLOCK ci-publication-guard:malformed-hook-payload:{error}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("BLOCK ci-publication-guard:payload-root-must-be-object", file=sys.stderr)
        return 2
    blocked, reason = should_block(payload)
    if blocked:
        print(f"BLOCK ci-publication-guard:{reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
