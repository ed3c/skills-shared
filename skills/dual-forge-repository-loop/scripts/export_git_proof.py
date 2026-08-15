#!/usr/bin/env python3
"""Export a bounded, replayable Git ancestry/tree proof for dual-forge admission."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


SHA40 = re.compile(r"^[0-9a-f]{40}$")
MAX_PROOF_BYTES = 64 * 1024 * 1024
REFS = {
    "github_main": "refs/heads/github-main",
    "forgejo_main": "refs/heads/forgejo-main",
    "local_main": "refs/heads/local-main",
    "candidate": "refs/heads/candidate",
}


class ExportError(ValueError):
    pass


def run(argv: list[str], *, cwd: Path | None = None, payload: bytes | None = None) -> bytes:
    result = subprocess.run(
        argv,
        cwd=cwd,
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).decode(errors="replace").strip()
        raise ExportError(f"command failed ({result.returncode}): {' '.join(argv)}: {detail}")
    return result.stdout


def git(repo: Path, *args: str) -> str:
    return run(["git", "-C", str(repo), *args]).decode().strip()


def require_commit(repo: Path, value: str, label: str) -> str:
    if not SHA40.fullmatch(value):
        raise ExportError(f"{label} must be a lowercase 40-hex commit SHA")
    if git(repo, "cat-file", "-t", value) != "commit":
        raise ExportError(f"{label} is not a commit in the source repository")
    return value


def export(repo: Path, commits: dict[str, str], output: Path) -> None:
    repo = repo.resolve()
    if not (repo / ".git").exists() and git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        raise ExportError("repo-root is not a Git worktree")
    for label, value in commits.items():
        require_commit(repo, value, label)
    candidate = commits["candidate"]
    forgejo_to_local = subprocess.run(
        [
            "git", "-C", str(repo), "merge-base", "--is-ancestor",
            commits["forgejo_main"], commits["local_main"],
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if forgejo_to_local.returncode != 0:
        raise ExportError("local_main does not contain forgejo_main")
    for label in ("github_main", "forgejo_main", "local_main"):
        probe = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", commits[label], candidate],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if probe.returncode != 0:
            raise ExportError(f"candidate does not contain {label}")

    with tempfile.TemporaryDirectory(prefix="dual-forge-export.") as directory:
        mirror = Path(directory) / "proof.git"
        run(["git", "clone", "-q", "--bare", "--shared", str(repo), str(mirror)])
        existing = run(
            ["git", f"--git-dir={mirror}", "for-each-ref", "--format=%(refname)"]
        ).decode().splitlines()
        for ref in existing:
            run(["git", f"--git-dir={mirror}", "update-ref", "-d", ref])
        for label, ref in REFS.items():
            run(["git", f"--git-dir={mirror}", "update-ref", ref, commits[label]])
        payload = run(
            ["git", f"--git-dir={mirror}", "fast-export", "--all", "--use-done-feature"]
        )
    if not payload or len(payload) > MAX_PROOF_BYTES:
        raise ExportError(
            f"proof size must be 1..{MAX_PROOF_BYTES} bytes; got {len(payload)}"
        )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--github-main", required=True)
    parser.add_argument("--forgejo-main", required=True)
    parser.add_argument("--local-main", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        export(
            args.repo_root,
            {
                "github_main": args.github_main,
                "forgejo_main": args.forgejo_main,
                "local_main": args.local_main,
                "candidate": args.candidate,
            },
            args.output,
        )
    except (ExportError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL git-proof export: {exc}", file=sys.stderr)
        return 2
    print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
