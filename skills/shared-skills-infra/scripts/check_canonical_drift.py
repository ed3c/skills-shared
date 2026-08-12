#!/usr/bin/env python3
"""Report what landed in canonical while you were not looking.

Canonical is what every project symlinks to, so anything written here is live
everywhere the moment it hits the disk -- before any PR exists, and without
passing any of the four merge-authority layers, all of which guard the PR path
instead. On 2026-08-07 a concurrent session wrote 3692 lines into this checkout,
committed straight to main and pushed, and nothing reported it (issue #18).

This does not prevent that; with a shell you can always write a file. It makes
the state visible, which is the only property a gate can honestly offer here:

    check_canonical_drift.py --since <sha>   what landed since you last looked
    check_canonical_drift.py                 unpushed / behind / dirty right now

Deliberately standalone. It is not wired into `check`, because a tool whose
absence takes out the governance gate costs more than the class of problem it
catches -- the lesson the dead-assertion linter taught on the day it shipped.

Exit: 0 nothing moved, 1 canonical moved or is dirty, 3 cannot tell (no remote,
no network, not a repo) -- which must never read as clean.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CANNOT_TELL = 3


def git(*args: str, repo: Path) -> tuple[int, str]:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    return done.returncode, done.stdout.strip()


def report(repo: Path, since: str | None, fetch: bool) -> int:
    code, _ = git("rev-parse", "--is-inside-work-tree", repo=repo)
    if code != 0:
        print(f"CANNOT-TELL {repo} is not a git checkout", file=sys.stderr)
        return CANNOT_TELL

    findings: list[str] = []

    if since:
        code, log = git(
            "log", "--format=%h %an <%ae> %ad %s", "--date=format:%H:%M:%S",
            f"{since}..HEAD", repo=repo,
        )
        if code != 0:
            print(f"CANNOT-TELL {since} is not a commit in {repo}", file=sys.stderr)
            return CANNOT_TELL
        if log:
            lines = log.splitlines()
            findings.append(
                f"MOVED canonical advanced since {since}: {len(lines)} commit(s)"
            )
            findings.extend(f"      {line}" for line in lines)

    if fetch:
        code, _ = git("fetch", "--quiet", "origin", repo=repo)
        if code != 0:
            # Offline is not clean. Say so and keep whatever else was found.
            findings.append("CANNOT-TELL could not fetch origin; remote state unknown")

    code, ahead = git("log", "--format=%h %an %s", "origin/main..HEAD", repo=repo)
    if code != 0:
        print("CANNOT-TELL no origin/main to compare against", file=sys.stderr)
        return CANNOT_TELL
    if ahead:
        lines = ahead.splitlines()
        findings.append(f"UNPUSHED {len(lines)} commit(s) here are not on origin:")
        findings.extend(f"      {line}" for line in lines)

    _, behind = git("log", "--format=%h %an %s", "HEAD..origin/main", repo=repo)
    if behind:
        lines = behind.splitlines()
        findings.append(
            f"BEHIND {len(lines)} origin commit(s) this checkout does not have:"
        )
        findings.extend(f"      {line}" for line in lines)

    _, dirty = git("status", "--porcelain", repo=repo)
    if dirty:
        lines = dirty.splitlines()
        findings.append(f"DIRTY {len(lines)} uncommitted path(s):")
        findings.extend(f"      {line}" for line in lines[:10])

    if any(line.startswith("CANNOT-TELL") for line in findings):
        for line in findings:
            print(line, file=sys.stderr)
        return CANNOT_TELL
    if findings:
        for line in findings:
            print(line, file=sys.stderr)
        return 1
    print(f"PASS canonical unchanged ({repo})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--since", help="the sha you last looked at")
    parser.add_argument(
        "--no-fetch", action="store_true",
        help="compare against the remote ref already on disk, without network",
    )
    args = parser.parse_args(argv)
    return report(args.repo.expanduser(), args.since, not args.no_fetch)


if __name__ == "__main__":
    raise SystemExit(main())
