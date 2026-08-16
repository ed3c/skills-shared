#!/usr/bin/env python3
"""Verify exact Forgejo-only Git configuration without contacting the remote."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

from url_policy import is_github, parse

PASS = 0
FAIL = 2
ERROR = 64


def run(repo: Path, *args: str, allow: bool = False) -> tuple[int, str, str]:
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if done.returncode and not allow:
        raise RuntimeError(done.stderr.strip() or done.stdout.strip() or "git failed")
    return done.returncode, done.stdout.strip(), done.stderr.strip()


def config(repo: Path, *args: str, all_values: bool = False) -> list[str] | str:
    flags = ["config", "--local", "--get-all" if all_values else "--get", *args]
    code, out, _ = run(repo, *flags, allow=True)
    if code:
        return [] if all_values else ""
    return out.splitlines() if all_values else out


def common_dir(repo: Path) -> Path:
    _, value, _ = run(repo, "rev-parse", "--git-common-dir")
    path = Path(value)
    return path if path.is_absolute() else (repo / path).resolve()


def hook_dir(repo: Path) -> Path:
    value = str(config(repo, "core.hooksPath"))
    if value:
        path = Path(value)
        return path if path.is_absolute() else (repo / path).resolve()
    _, value, _ = run(repo, "rev-parse", "--git-path", "hooks")
    path = Path(value)
    return path if path.is_absolute() else (repo / path).resolve()


def add(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    args = parser.parse_args()
    try:
        repo = args.repo.resolve()
        _, inside, _ = run(repo, "rev-parse", "--is-inside-work-tree")
        if inside != "true":
            raise RuntimeError("not a Git worktree")
        _, top, _ = run(repo, "rev-parse", "--show-toplevel")
        repo = Path(top).resolve()
        failures: list[str] = []

        classification = str(config(repo, "repository.classification"))
        version = str(config(repo, "repository.localOnlyVersion"))
        allowed_remote = str(config(repo, "repository.localOnlyRemote"))
        allowed_url = str(config(repo, "repository.localOnlyURL"))
        allowed_host = str(config(repo, "repository.localOnlyHost"))
        push_default = str(config(repo, "remote.pushDefault"))
        mode_root = str(config(repo, "repository.localOnlyModeRoot"))
        expected_guard = str(config(repo, "repository.localOnlyGuardSha256"))

        add(failures, classification == "LOCAL_ONLY", "repository.classification must be LOCAL_ONLY")
        add(failures, version == "1", "repository.localOnlyVersion must be 1")
        add(failures, bool(allowed_remote), "admitted remote is absent")
        add(failures, bool(allowed_url), "admitted URL is absent")
        parsed_allowed = parse(allowed_url)
        add(failures, bool(parsed_allowed.host), "admitted URL has no host")
        add(failures, not parsed_allowed.has_http_credentials, "admitted URL embeds credentials")
        add(failures, not is_github(parsed_allowed.host), "admitted URL is a GitHub surface")
        add(failures, not parsed_allowed.relative, "admitted URL must be absolute")
        add(failures, parsed_allowed.host == allowed_host, "admitted URL host differs from local config")
        add(failures, push_default == allowed_remote, "remote.pushDefault differs from admitted remote")
        add(failures, bool(mode_root) and Path(mode_root).is_absolute(), "mode root is not an absolute local path")

        _, remote_text, _ = run(repo, "remote")
        remotes = [line for line in remote_text.splitlines() if line]
        add(failures, remotes == [allowed_remote], "exactly one admitted remote must exist")
        if allowed_remote:
            raw_fetch = list(config(repo, f"remote.{allowed_remote}.url", all_values=True))
            raw_push = list(config(repo, f"remote.{allowed_remote}.pushurl", all_values=True))
            if not raw_push:
                raw_push = raw_fetch
            add(failures, raw_fetch == [allowed_url], "raw fetch URL differs from admitted URL")
            add(failures, raw_push == [allowed_url], "raw push URL differs from admitted URL")
            _, resolved_fetch, _ = run(repo, "remote", "get-url", allowed_remote, allow=True)
            _, resolved_push, _ = run(repo, "remote", "get-url", "--push", allowed_remote, allow=True)
            add(failures, resolved_fetch == allowed_url, "resolved fetch URL was rewritten")
            add(failures, resolved_push == allowed_url, "resolved push URL was rewritten")
            mirror = str(config(repo, f"remote.{allowed_remote}.mirror")).lower()
            add(failures, mirror not in {"true", "yes", "on", "1"}, "mirror remote is forbidden")
            push_specs = list(config(repo, f"remote.{allowed_remote}.push", all_values=True))
            add(
                failures,
                not any("refs/*" in spec or spec.startswith("+refs/") for spec in push_specs),
                "mirror-like push refspec is forbidden",
            )

        code, rewrite_text, _ = run(repo, "config", "--get-regexp", r"^url\..*\.(insteadof|pushinsteadof)$", allow=True)
        add(failures, code != 0 or not rewrite_text, "URL rewrite rules are forbidden")

        _, branches_text, _ = run(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
        for branch in [item for item in branches_text.splitlines() if item]:
            push_remote = str(config(repo, f"branch.{branch}.pushRemote"))
            add(failures, push_remote == allowed_remote, f"branch {branch} lacks exact pushRemote")

        common = common_dir(repo)
        marker = common / "LOCAL_ONLY_CLASSIFICATION"
        add(failures, marker.is_file(), "classification marker is absent")
        alternates = common / "objects" / "info" / "alternates"
        add(failures, not alternates.exists() or alternates.stat().st_size == 0, "alternate object file is forbidden")
        add(failures, not os.environ.get("GIT_ALTERNATE_OBJECT_DIRECTORIES"), "alternate object environment is forbidden")

        hooks = hook_dir(repo)
        dispatcher = hooks / "pre-push"
        guard = hooks / "pre-push.local-only-guard"
        add(failures, dispatcher.is_file() and os.access(dispatcher, os.X_OK), "pre-push dispatcher is absent")
        add(failures, guard.is_file() and os.access(guard, os.X_OK), "private-lineage guard is absent")
        if guard.is_file():
            actual = hashlib.sha256(guard.read_bytes()).hexdigest()
            add(failures, bool(expected_guard) and actual == expected_guard, "guard digest differs from admission")

        gitmodules = repo / ".gitmodules"
        if gitmodules.is_file():
            done = subprocess.run(
                ["git", "config", "-f", str(gitmodules), "--get-regexp", r"^submodule\..*\.url$"],
                text=True,
                capture_output=True,
                check=False,
            )
            for line in done.stdout.splitlines():
                _, _, value = line.partition(" ")
                item = parse(value)
                add(failures, not item.has_http_credentials, "submodule URL embeds credentials")
                add(failures, not is_github(item.host), "GitHub submodule is forbidden")
                add(
                    failures,
                    item.relative or item.host == allowed_host,
                    "submodule host differs from admitted Forgejo host",
                )

        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        if failures:
            print(f"FORGEJO-ONLY RED failures={len(failures)}", file=sys.stderr)
            return FAIL
        print(f"FORGEJO-ONLY GREEN remote={allowed_remote} host={allowed_host}")
        return PASS
    except (OSError, RuntimeError) as error:
        print(f"FORGEJO-ONLY ERROR: {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    raise SystemExit(main())
