#!/usr/bin/env python3
"""Idempotently register the CI publication guard on Codex and Claude hooks."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


class InstallError(ValueError):
    """An existing hook document is malformed or unsafe to modify."""


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"unreadable hook settings {path}: {error}") from error
    if not isinstance(value, dict):
        raise InstallError(f"hook settings root must be an object: {path}")
    return value


def updated(document: dict[str, Any], command: str) -> tuple[dict[str, Any], bool]:
    clone = json.loads(json.dumps(document))
    hooks = clone.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise InstallError("hooks must be an object")
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise InstallError("hooks.PreToolUse must be an array")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        nested = entry.get("hooks")
        if not isinstance(nested, list):
            continue
        if any(isinstance(item, dict) and item.get("command") == command for item in nested):
            return clone, False
    entries.append(
        {
            "matcher": "*",
            "hooks": [{"type": "command", "command": command}],
        }
    )
    return clone, True


def install(path: Path, guard: Path, apply: bool) -> str:
    if not guard.is_file():
        raise InstallError(f"guard script does not exist: {guard}")
    command = shlex.quote(str(guard))
    document = _load(path)
    replacement, changed = updated(document, command)
    if not changed:
        return f"OK {path}"
    if not apply:
        return f"WOULD-INSTALL {path} command={command}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + ".pre-ci-publish-guard.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(replacement, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return f"INSTALLED {path}"


def main() -> int:
    home = Path.home()
    default_guard = home / ".agents/skills/github-delivery-loop/scripts/ci_publish_guard.py"
    parser = argparse.ArgumentParser()
    parser.add_argument("--guard", type=Path, default=default_guard)
    parser.add_argument("--codex-hooks", type=Path, default=home / ".codex/hooks.json")
    parser.add_argument("--claude-settings", type=Path, default=home / ".claude/settings.json")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        print(install(args.codex_hooks, args.guard.resolve(), args.apply))
        print(install(args.claude_settings, args.guard.resolve(), args.apply))
    except InstallError as error:
        print(f"BLOCK install-ci-publish-guard:{error}", file=sys.stderr)
        return 1
    if not args.apply:
        print("DRY-RUN: pass --apply to modify hook settings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
