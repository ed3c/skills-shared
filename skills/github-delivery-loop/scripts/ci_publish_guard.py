#!/usr/bin/env python3
"""PreToolUse guard that routes managed GitHub pushes through ci_publish.py."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


POLICY_PATH = Path(".github-delivery/ci-policy.json")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
ENV_OPTIONS_WITH_VALUE = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}
PUSH_OPTIONS_WITH_VALUE = {"--receive-pack", "--exec", "--repo", "--push-option", "-o"}
GIT_OPTIONS_WITH_VALUE = {"-c", "--config-env", "--git-dir", "--work-tree", "--namespace"}


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


def _repo_root(
    cwd: Path, git_options: list[str] | None = None, git_environment: dict[str, str] | None = None
) -> Path | None:
    options = git_options or []
    environment_overrides = git_environment or {}
    selected_git_dir = _selected_git_dir(cwd, options, environment_overrides)
    if selected_git_dir is not None:
        root = _root_from_git_dir(selected_git_dir)
        if root is not None:
            return root
    selected_work_tree = _selected_path(
        cwd, options, environment_overrides, "--work-tree", "GIT_WORK_TREE"
    )
    if selected_work_tree is not None:
        return selected_work_tree
    environment = os.environ.copy()
    environment.update(environment_overrides)
    result = subprocess.run(
        ["git", "-C", str(cwd), *options, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _selected_git_dir(cwd: Path, options: list[str], environment: dict[str, str]) -> Path | None:
    return _selected_path(cwd, options, environment, "--git-dir", "GIT_DIR")


def _selected_path(
    cwd: Path,
    options: list[str],
    environment: dict[str, str],
    option_name: str,
    environment_name: str,
) -> Path | None:
    value = environment.get(environment_name)
    index = 0
    while index < len(options):
        token = options[index]
        if token == option_name and index + 1 < len(options):
            value = options[index + 1]
            index += 2
            continue
        if token.startswith(option_name + "="):
            value = token.split("=", 1)[1]
        index += 1
    if not value:
        return None
    selected = Path(value)
    return (selected if selected.is_absolute() else cwd / selected).resolve()


def _root_from_git_dir(selected: Path) -> Path | None:
    if selected.name == ".git":
        return selected.parent
    marker = selected / "gitdir"
    if marker.is_file():
        try:
            worktree_dot_git = Path(marker.read_text(encoding="utf-8").strip())
        except OSError:
            return None
        return worktree_dot_git.parent
    return None


def _git_command_context(
    tokens: list[str], cwd: Path
) -> tuple[Path, list[str], int] | None:
    """Return the effective cwd, global Git options, and subcommand index."""
    command_cwd = cwd
    options: list[str] = []
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token == "-C":
            if index + 1 >= len(tokens):
                return None
            candidate = Path(tokens[index + 1])
            command_cwd = candidate if candidate.is_absolute() else command_cwd / candidate
            index += 2
            continue
        if token.startswith("-C") and token != "-C":
            candidate = Path(token[2:])
            command_cwd = candidate if candidate.is_absolute() else command_cwd / candidate
            index += 1
            continue
        if token in GIT_OPTIONS_WITH_VALUE:
            if index + 1 >= len(tokens):
                return None
            options.extend(tokens[index : index + 2])
            index += 2
            continue
        if any(token.startswith(option + "=") for option in GIT_OPTIONS_WITH_VALUE):
            options.append(token)
            index += 1
            continue
        if token.startswith("-"):
            options.append(token)
            index += 1
            continue
        break
    if index >= len(tokens):
        return None
    return command_cwd, options, index


def _expand_git_alias(
    tokens: list[str], cwd: Path, environment: dict[str, str]
) -> list[str]:
    """Expand the effective Git alias with the same repo/config context, bounded."""
    expanded = list(tokens)
    for _ in range(5):
        context = _git_command_context(expanded, cwd)
        if context is None:
            return expanded
        command_cwd, options, command_index = context
        command_name = expanded[command_index]
        if command_name == "push":
            return expanded
        root = _repo_root(command_cwd, options, environment)
        if root is None:
            return expanded
        alias_value = _config(root, options, environment, f"alias.{command_name}")
        if not alias_value:
            return expanded
        arguments = expanded[command_index + 1 :]
        try:
            alias_tokens = shlex.split(
                alias_value[1:] if alias_value.startswith("!") else alias_value
            )
        except ValueError:
            return expanded
        if alias_value.startswith("!"):
            if alias_tokens and Path(alias_tokens[0]).name == "git":
                expanded = alias_tokens + arguments
                cwd = root
                continue
            # Arbitrary shell aliases cannot be modelled safely. If they name a
            # push, represent it as a push in the enrolled repository so the
            # policy fails closed.
            if "push" in alias_tokens:
                return ["git", "-C", str(root), "push", *arguments]
            return expanded
        expanded[command_index : command_index + 1] = alias_tokens
    return expanded


def _pushes(command: str, cwd: Path) -> list[tuple[Path, str | None, list[str], dict[str, str]]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token and set(token).issubset({";", "&", "|"}):
            segments.append([])
        else:
            segments[-1].append(token)
    pushes: list[tuple[Path, str | None, list[str], dict[str, str]]] = []
    active_cwd = cwd
    for tokens in segments:
        git_environment: dict[str, str] = {}
        if len(tokens) in {2, 3} and tokens[0] == "cd" and (
            len(tokens) == 2 or tokens[1] == "--"
        ):
            candidate = Path(tokens[-1])
            active_cwd = candidate if candidate.is_absolute() else active_cwd / candidate
            continue
        while tokens:
            executable = Path(tokens[0]).name
            if executable == "command":
                tokens = tokens[1:]
                while tokens and tokens[0].startswith("-"):
                    tokens = tokens[1:]
                continue
            if executable == "env":
                tokens = tokens[1:]
                while tokens:
                    token = tokens[0]
                    if token == "--":
                        tokens = tokens[1:]
                        break
                    if ASSIGNMENT.fullmatch(token):
                        key, value = token.split("=", 1)
                        git_environment[key] = value
                        tokens = tokens[1:]
                        continue
                    if token in {"-i", "--ignore-environment", "-0", "--null"}:
                        tokens = tokens[1:]
                        continue
                    if token in ENV_OPTIONS_WITH_VALUE:
                        if token in {"-S", "--split-string"} and len(tokens) >= 2:
                            try:
                                tokens = shlex.split(tokens[1]) + tokens[2:]
                            except ValueError:
                                tokens = []
                            break
                        if token in {"-C", "--chdir"} and len(tokens) >= 2:
                            candidate = Path(tokens[1])
                            active_cwd = (
                                candidate if candidate.is_absolute() else active_cwd / candidate
                            )
                        tokens = tokens[2:] if len(tokens) >= 2 else []
                        continue
                    if token.startswith("--split-string="):
                        try:
                            tokens = shlex.split(token.split("=", 1)[1]) + tokens[1:]
                        except ValueError:
                            tokens = []
                        break
                    if token.startswith("--chdir="):
                        candidate = Path(token.split("=", 1)[1])
                        active_cwd = candidate if candidate.is_absolute() else active_cwd / candidate
                        tokens = tokens[1:]
                        continue
                    if token.startswith("-S") and token != "-S":
                        try:
                            tokens = shlex.split(token[2:]) + tokens[1:]
                        except ValueError:
                            tokens = []
                        break
                    if any(token.startswith(option + "=") for option in ENV_OPTIONS_WITH_VALUE):
                        tokens = tokens[1:]
                        continue
                    break
                continue
            if ASSIGNMENT.fullmatch(tokens[0]):
                key, value = tokens[0].split("=", 1)
                git_environment[key] = value
                tokens = tokens[1:]
                continue
            break
        if tokens and Path(tokens[0]).name in {"sh", "bash", "zsh"}:
            if len(tokens) >= 3 and tokens[1] == "-c":
                pushes.extend(_pushes(tokens[2], active_cwd))
            continue
        if not tokens or Path(tokens[0]).name != "git":
            continue
        tokens = _expand_git_alias(tokens, active_cwd, git_environment)
        try:
            push_index = tokens.index("push", 1)
        except ValueError:
            continue
        command_cwd = active_cwd
        index = 1
        git_options: list[str] = []
        while index < push_index:
            if tokens[index] == "-C" and index + 1 < push_index:
                candidate = Path(tokens[index + 1])
                command_cwd = candidate if candidate.is_absolute() else command_cwd / candidate
                index += 2
            else:
                git_options.append(tokens[index])
                index += 1
        index = push_index + 1
        while index < len(tokens):
            token = tokens[index]
            if token == "--":
                index += 1
                break
            if token in PUSH_OPTIONS_WITH_VALUE:
                index += 2
                continue
            if token.startswith("-"):
                index += 1
                continue
            break
        remote = tokens[index] if index < len(tokens) else None
        pushes.append((command_cwd, remote, git_options, git_environment))
    return pushes


def _git_with_context(
    repo_root: Path, options: list[str], environment: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.update(environment)
    return subprocess.run(
        ["git", "-C", str(repo_root), *options, *args],
        capture_output=True, text=True, check=False, env=merged,
    )


def _config(
    repo_root: Path, options: list[str], environment: dict[str, str], key: str
) -> str:
    return _git_with_context(repo_root, options, environment, "config", "--get", key).stdout.strip()


def _github_remote(
    repo_root: Path,
    remote: str | None,
    git_options: list[str],
    git_environment: dict[str, str],
) -> bool:
    if remote and ("github.com:" in remote.lower() or "github.com/" in remote.lower()):
        return True
    if remote:
        selected = remote
    else:
        branch = _git_with_context(
            repo_root, git_options, git_environment, "branch", "--show-current"
        ).stdout.strip()
        selected = (
            _config(repo_root, git_options, git_environment, f"branch.{branch}.pushRemote")
            or _config(repo_root, git_options, git_environment, "remote.pushDefault")
            or _config(repo_root, git_options, git_environment, f"branch.{branch}.remote")
        )
        if not selected:
            remotes = _git_with_context(
                repo_root, git_options, git_environment, "remote"
            ).stdout.splitlines()
            selected = "origin" if "origin" in remotes else (remotes[0] if len(remotes) == 1 else "")
    result = _git_with_context(
        repo_root, git_options, git_environment,
        "remote", "get-url", "--push", "--all", selected,
    )
    if result.returncode != 0:
        # An enrolled repository with an unresolvable push destination fails closed.
        return True
    urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not urls:
        return True
    return any("github.com" in url.lower() for url in urls)


def should_block(payload: dict[str, Any]) -> tuple[bool, str]:
    command, cwd = _command(payload)
    pushes = _pushes(command, cwd)
    if not pushes:
        return False, "not-a-git-push"
    for command_cwd, remote, git_options, git_environment in pushes:
        root = _repo_root(command_cwd, git_options, git_environment)
        if root is None or not (root / POLICY_PATH).is_file():
            continue
        if _github_remote(root, remote, git_options, git_environment):
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
