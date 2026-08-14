#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any, Sequence

SHA40 = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"\d+\.\d+\.\d+")
PROMPT_ENV = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_EDITOR": ":",
    "GIT_SEQUENCE_EDITOR": ":",
    "GCM_INTERACTIVE": "Never",
    "PAGER": "cat",
    "GIT_PAGER": "cat",
    "LC_ALL": "C",
}


def run(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(PROMPT_ENV)
    result = subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n"
            f"stdout:\n{result.stdout[-4000:]}\n"
            f"stderr:\n{result.stderr[-4000:]}"
        )
    return result


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo, check=check)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "skills-shared-git-town-canary/1"},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                target.write_bytes(response.read())
            return
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"download failed: {url}: {last_error}")


def ref_digest(repo_or_bare: Path, *, bare: bool) -> str:
    argv = ["git"]
    if bare:
        argv.append(f"--git-dir={repo_or_bare}")
    argv.extend(["for-each-ref", "--format=%(refname) %(objectname)"])
    result = run(argv, cwd=None if bare else repo_or_bare)
    lines = "\n".join(sorted(line for line in result.stdout.splitlines() if line))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def configure_identity(repo: Path) -> None:
    git(repo, "config", "user.name", "Git Town Canary")
    git(repo, "config", "user.email", "git-town-canary@example.invalid")


def init_fixture(root: Path, name: str) -> tuple[Path, Path]:
    fixture = root / name
    remote = fixture / "remote.git"
    repo = fixture / "repo"
    fixture.mkdir(parents=True)
    run(["git", "init", "--bare", str(remote)])
    run(["git", "init", "--initial-branch=main", str(repo)])
    configure_identity(repo)
    git(repo, "remote", "add", "origin", str(remote))
    return remote, repo


class Canary:
    def __init__(self, git_town: Path) -> None:
        self.git_town = git_town
        self.commands: list[list[str]] = []

    def town(
        self,
        repo: Path,
        *args: str,
        check: bool = True,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(list(args))
        return run(
            [str(self.git_town), *args],
            cwd=repo,
            check=check,
            timeout=timeout,
        )

    def configure(self, repo: Path) -> None:
        self.town(
            repo,
            "config",
            "setup",
            "--main-branch",
            "main",
            "--hosting-platform",
            "none",
            "--non-interactive",
        )

    def positive(self, root: Path) -> dict[str, Any]:
        remote, repo = init_fixture(root, "positive")
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "base.txt")
        git(repo, "commit", "-m", "base")
        main_before = git(repo, "rev-parse", "main").stdout.strip()
        git(repo, "push", "-u", "origin", "main")

        self.configure(repo)
        self.town(repo, "hack", "parent")
        (repo / "parent.txt").write_text("parent-v1\n", encoding="utf-8")
        git(repo, "add", "parent.txt")
        git(repo, "commit", "-m", "parent v1")

        self.town(repo, "hack", "child")
        (repo / "child.txt").write_text("child\n", encoding="utf-8")
        git(repo, "add", "child.txt")
        git(repo, "commit", "-m", "child")
        git(repo, "push", "-u", "origin", "parent", "child")

        git(repo, "switch", "parent")
        with (repo / "parent.txt").open("a", encoding="utf-8") as stream:
            stream.write("parent-v2\n")
        git(repo, "add", "parent.txt")
        git(repo, "commit", "-m", "parent v2")
        git(repo, "push", "origin", "parent")
        git(repo, "switch", "main")

        worker = root / "positive-worker"
        git(repo, "worktree", "add", str(worker), "child")
        configure_identity(worker)

        remote_before = ref_digest(remote, bare=True)
        refs_before = ref_digest(worker, bare=False)
        head_before = git(worker, "rev-parse", "HEAD").stdout.strip()
        dry = self.town(
            worker,
            "sync",
            "--stack",
            "--dry-run",
            "--non-interactive",
            "--no-auto-resolve",
            "--no-push",
            check=False,
        )
        refs_after = ref_digest(worker, bare=False)
        head_after = git(worker, "rev-parse", "HEAD").stdout.strip()

        sync = self.town(
            worker,
            "sync",
            "--stack",
            "--non-interactive",
            "--no-auto-resolve",
            "--no-push",
            check=False,
        )
        ancestor = git(
            worker,
            "merge-base",
            "--is-ancestor",
            "parent",
            "child",
            check=False,
        ).returncode == 0
        remote_after = ref_digest(remote, bare=True)
        clean = git(worker, "status", "--porcelain=v1").stdout.strip() == ""

        return {
            "dry_run_exit": dry.returncode,
            "dry_run_mutated_local_refs": refs_before != refs_after or head_before != head_after,
            "sync_exit": sync.returncode,
            "parent_is_ancestor": ancestor,
            "main_unchanged": git(worker, "rev-parse", "main").stdout.strip() == main_before,
            "remote_refs_unchanged": remote_before == remote_after,
            "worktree_clean_after": clean,
        }

    def conflict(self, root: Path) -> dict[str, Any]:
        remote, repo = init_fixture(root, "conflict")
        (repo / "shared.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "shared.txt")
        git(repo, "commit", "-m", "base")
        main_before = git(repo, "rev-parse", "main").stdout.strip()
        git(repo, "push", "-u", "origin", "main")

        self.configure(repo)
        self.town(repo, "hack", "parent")
        (repo / "parent-anchor.txt").write_text("parent-anchor\n", encoding="utf-8")
        git(repo, "add", "parent-anchor.txt")
        git(repo, "commit", "-m", "parent anchor")

        self.town(repo, "hack", "child")
        (repo / "shared.txt").write_text("child\n", encoding="utf-8")
        git(repo, "add", "shared.txt")
        git(repo, "commit", "-m", "child edits shared line")
        git(repo, "push", "-u", "origin", "parent", "child")

        git(repo, "switch", "parent")
        (repo / "shared.txt").write_text("parent\n", encoding="utf-8")
        git(repo, "add", "shared.txt")
        git(repo, "commit", "-m", "parent edits shared line")
        git(repo, "push", "origin", "parent")
        git(repo, "switch", "main")

        worker = root / "conflict-worker"
        git(repo, "worktree", "add", str(worker), "child")
        configure_identity(worker)
        remote_before = ref_digest(remote, bare=True)

        sync = self.town(
            worker,
            "sync",
            "--stack",
            "--non-interactive",
            "--no-auto-resolve",
            "--no-push",
            check=False,
        )
        remote_after = ref_digest(remote, bare=True)
        unmerged = bool(git(worker, "diff", "--name-only", "--diff-filter=U").stdout.strip())

        suspended = False
        for state in ("rebase-merge", "rebase-apply"):
            raw = git(worker, "rev-parse", "--git-path", state).stdout.strip()
            path = Path(raw)
            if not path.is_absolute():
                path = worker / path
            suspended = suspended or path.is_dir()

        prohibited = {"continue", "skip", "undo", "ship"}
        automatic_recovery = any(
            any(token in prohibited for token in command)
            for command in self.commands
        )
        return {
            "sync_exit": sync.returncode,
            "unmerged_paths_present": unmerged,
            "suspended_rebase_present": suspended,
            "remote_refs_unchanged": remote_before == remote_after,
            "main_unchanged": git(worker, "rev-parse", "main").stdout.strip() == main_before,
            "automatic_semantic_recovery_attempted": automatic_recovery,
        }


def validate_receipt(receipt: dict[str, Any], admission: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(receipt.get("schema_version") == "git-town-live-canary-receipt/v1",
            "invalid receipt schema")
    require(receipt.get("tool_version") == admission["version"],
            "tool version differs from admission")
    require(receipt.get("asset_sha256") == admission["asset"]["sha256"],
            "asset digest differs from admission")
    require(receipt.get("checksums_sha256") == admission["checksums"]["sha256"],
            "checksums digest differs from admission")
    require(receipt.get("license_marker") == admission["license"]["expected_marker"],
            "license marker was not observed")
    require(receipt.get("legal_acceptance") == "HUMAN_ADMIT_REQUIRED",
            "legal acceptance did not remain Human-owned")

    for flag in ("--stack", "--dry-run", "--non-interactive", "--no-auto-resolve", "--no-push"):
        require(flag in receipt.get("observed_sync_flags", []),
                f"required flag missing: {flag}")

    positive = receipt["positive_canary"]
    require(positive["dry_run_exit"] == 0, "positive dry-run failed")
    require(positive["dry_run_mutated_local_refs"] is False,
            "positive dry-run moved local refs")
    require(positive["sync_exit"] == 0, "positive sync failed")
    require(positive["parent_is_ancestor"] is True,
            "positive sync did not restore ancestry")
    require(positive["main_unchanged"] is True, "positive sync changed main")
    require(positive["remote_refs_unchanged"] is True,
            "positive sync changed remote refs")
    require(positive["worktree_clean_after"] is True,
            "positive sync left a dirty worktree")

    conflict = receipt["conflict_canary"]
    require(conflict["sync_exit"] != 0, "planted conflict did not fail")
    require(conflict["unmerged_paths_present"] is True,
            "planted conflict did not preserve unmerged paths")
    require(conflict["suspended_rebase_present"] is True,
            "planted conflict did not preserve suspended rebase state")
    require(conflict["remote_refs_unchanged"] is True,
            "conflict sync changed remote refs")
    require(conflict["main_unchanged"] is True, "conflict sync changed main")
    require(conflict["automatic_semantic_recovery_attempted"] is False,
            "automatic semantic recovery was attempted")

    require(receipt["network_publication"] == "NOT_EXERCISED",
            "network publication lane collapsed")
    require(receipt["merge"] == "HUMAN_ADMIT_REQUIRED",
            "merge did not remain Human-owned")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    if SHA40.fullmatch(args.subject) is None:
        print("subject must be a 40-character lowercase SHA", file=sys.stderr)
        return 64
    admission = json.loads(args.admission.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="git-town-live-canary-") as tmp_raw:
        tmp = Path(tmp_raw)
        downloads = tmp / "downloads"
        downloads.mkdir()
        asset = downloads / admission["asset"]["name"]
        checksums = downloads / "checksums.txt"
        license_file = downloads / "LICENSE"
        download(admission["asset"]["url"], asset)
        download(admission["checksums"]["url"], checksums)
        download(admission["license"]["url"], license_file)

        if sha256(asset) != admission["asset"]["sha256"]:
            raise RuntimeError("release asset checksum mismatch")
        if sha256(checksums) != admission["checksums"]["sha256"]:
            raise RuntimeError("checksums.txt checksum mismatch")
        checksum_entries = {}
        for line in checksums.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) >= 2:
                checksum_entries[fields[-1].lstrip("*")] = fields[0]
        if checksum_entries.get(admission["asset"]["name"]) != admission["asset"]["sha256"]:
            raise RuntimeError("checksums.txt does not bind the selected asset")
        license_text = license_file.read_text(encoding="utf-8")
        if admission["license"]["expected_marker"] not in license_text:
            raise RuntimeError("expected direct license marker is absent")

        extract = tmp / "extract"
        run(["dpkg-deb", "-x", str(asset), str(extract)])
        candidates = [
            path
            for path in extract.rglob("git-town")
            if path.is_file() and os.access(path, os.X_OK)
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one executable, found {len(candidates)}")
        git_town = candidates[0]
        version_output = run([str(git_town), "--version"]).stdout
        match = VERSION.search(version_output)
        if match is None or match.group(0) != admission["version"]:
            raise RuntimeError(f"unexpected Git Town version: {version_output.strip()}")

        sync_help = run([str(git_town), "sync", "--help"]).stdout
        flags = ["--stack", "--dry-run", "--non-interactive", "--no-auto-resolve", "--no-push"]
        missing = [flag for flag in flags if flag not in sync_help]
        if missing:
            raise RuntimeError(f"required sync flags absent: {missing}")

        harness = Canary(git_town)
        fixtures = tmp / "fixtures"
        fixtures.mkdir()
        positive = harness.positive(fixtures)
        conflict = harness.conflict(fixtures)

        receipt = {
            "schema_version": "git-town-live-canary-receipt/v1",
            "subject_sha": args.subject,
            "tool_version": admission["version"],
            "asset_sha256": sha256(asset),
            "checksums_sha256": sha256(checksums),
            "license_sha256": sha256(license_file),
            "license_marker": admission["license"]["expected_marker"],
            "legal_acceptance": admission["license"]["organization_acceptance"],
            "observed_sync_flags": flags,
            "positive_canary": positive,
            "conflict_canary": conflict,
            "network_publication": "NOT_EXERCISED",
            "merge": "HUMAN_ADMIT_REQUIRED",
        }
        errors = validate_receipt(receipt, admission)
        receipt["result"] = "PASS" if not errors else "FAIL"
        receipt["errors"] = errors
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 2

    print(f"PASS Git Town {admission['version']} disposable live canaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
