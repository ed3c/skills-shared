#!/usr/bin/env python3
"""Capture one default-branch ref through its owning authority lane."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
GITHUB_REMOTE = re.compile(r"^(?:git@github\.com:|ssh://git@github\.com/|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?$")
LOOPBACK_FORGES = {"http://localhost:3000", "http://127.0.0.1:3000"}


class CaptureError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def command(argv: list[str], label: str) -> str:
    try:
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=False, timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CaptureError(f"{label} unavailable") from exc
    if result.returncode != 0:
        raise CaptureError(f"{label} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def object_json(payload: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CaptureError(f"{label} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise CaptureError(f"{label} response must be an object")
    return value


def capture_receipt(argv: list[list[str]], stdout: list[str]) -> dict[str, Any]:
    return {
        "argv": argv,
        "exit_codes": [0] * len(argv),
        "stdout": stdout,
        "stdout_sha256": [hashlib.sha256(value.encode()).hexdigest() for value in stdout],
    }


def github(repo: str, branch: str) -> tuple[str, str, int, dict[str, Any]]:
    repo_argv = ["gh", "api", f"repos/{repo}"]
    repository_stdout = command(repo_argv, "gh api repository")
    repository = object_json(repository_stdout, "repository")
    if repository.get("full_name") != repo or repository.get("default_branch") != branch:
        raise CaptureError("GitHub repository/default branch identity mismatch")
    repository_id = repository.get("id")
    if not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0:
        raise CaptureError("GitHub repository response lacks a numeric ID")
    endpoint = f"repos/{repo}/git/ref/heads/{quote(branch, safe='')}"
    ref_argv = ["gh", "api", endpoint]
    ref_stdout = command(ref_argv, "gh api ref")
    ref = object_json(ref_stdout, "ref")
    sha = (ref.get("object") or {}).get("sha") if isinstance(ref.get("object"), dict) else None
    if not isinstance(sha, str) or SHA40.fullmatch(sha) is None:
        raise CaptureError("GitHub ref response lacks a commit SHA")
    return sha, endpoint, repository_id, capture_receipt(
        [repo_argv, ref_argv], [repository_stdout, ref_stdout]
    )


def credentials(forge_url: str) -> tuple[str, str]:
    parsed = urlparse(forge_url)
    payload = f"protocol={parsed.scheme}\nhost={parsed.netloc}\n\n"
    try:
        result = subprocess.run(
            ["git", "credential", "fill"], input=payload, text=True,
            capture_output=True, check=False, timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        raise CaptureError("Forgejo credential helper timed out") from exc
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if result.returncode != 0 or not fields.get("username") or not fields.get("password"):
        raise CaptureError("Forgejo credentials unavailable")
    return fields["username"], fields["password"]


def forgejo_get(forge_url: str, endpoint: str, auth: str) -> tuple[dict[str, Any], str]:
    url = f"{forge_url}/api/v1/{endpoint}"
    request = Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            if response.geturl() != url:
                raise CaptureError("Forgejo read crossed an origin boundary")
            stdout = response.read().decode()
            return object_json(stdout, "Forgejo API"), stdout
    except (HTTPError, URLError, TimeoutError) as exc:
        raise CaptureError("authenticated Forgejo API read failed") from exc


def forgejo(repo: str, branch: str, forge_url: str) -> tuple[str, str, int, dict[str, Any]]:
    if forge_url not in LOOPBACK_FORGES:
        raise CaptureError("Forgejo URL must be the allowlisted loopback forge")
    owner, name = repo.split("/", 1)
    username, password = credentials(forge_url)
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    root = f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    repository, repository_stdout = forgejo_get(forge_url, root, auth)
    if repository.get("full_name") != repo or repository.get("default_branch") != branch:
        raise CaptureError("Forgejo repository/default branch identity mismatch")
    repository_id = repository.get("id")
    if not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0:
        raise CaptureError("Forgejo repository response lacks a numeric ID")
    endpoint = f"{root}/branches/{quote(branch, safe='')}"
    response, branch_stdout = forgejo_get(forge_url, endpoint, auth)
    commit = response.get("commit")
    sha = commit.get("id") if isinstance(commit, dict) else None
    if not isinstance(sha, str) or SHA40.fullmatch(sha) is None:
        raise CaptureError("Forgejo branch response lacks a commit SHA")
    argv = [
        ["forgejo-api-authenticated-read", f"/api/v1/{root}"],
        ["forgejo-api-authenticated-read", f"/api/v1/{endpoint}"],
    ]
    return sha, endpoint, repository_id, capture_receipt(
        argv, [repository_stdout, branch_stdout]
    )


def remote_repository(repo_root: Path, remote: str, kind: str) -> str:
    output = command(
        [
            "git", "-C", str(repo_root.resolve()), "remote", "get-url",
            "--push", "--all", remote,
        ],
        f"local {kind} remote",
    )
    urls = [line.strip() for line in output.splitlines() if line.strip()]
    if len(urls) != 1:
        raise CaptureError(f"local {kind} remote must have exactly one push URL")
    url = urls[0]
    if kind == "github":
        match = GITHUB_REMOTE.fullmatch(url)
        if match is None:
            raise CaptureError("local GitHub remote is not an exact github.com repository URL")
        return match.group(1)
    parsed = urlparse(url)
    if f"{parsed.scheme}://{parsed.netloc}" not in LOOPBACK_FORGES or parsed.username or parsed.password:
        raise CaptureError("local Forgejo remote is not a credential-free loopback URL")
    value = parsed.path.strip("/")
    return value[:-4] if value.endswith(".git") else value


def local(
    repo_root: Path,
    branch: str,
    repository: str,
    forgejo_repository: str,
    github_remote: str,
    forgejo_remote: str,
) -> tuple[str, str, dict[str, str], dict[str, Any]]:
    top = command(
        ["git", "-C", str(repo_root.resolve()), "rev-parse", "--show-toplevel"],
        "local Git worktree",
    )
    if Path(top).resolve() != repo_root.resolve():
        raise CaptureError("repo-root is not the exact local worktree root")
    github_repository = remote_repository(repo_root, github_remote, "github")
    observed_forgejo_repository = remote_repository(repo_root, forgejo_remote, "forgejo")
    if github_repository.lower() != repository.lower():
        raise CaptureError("local GitHub remote repository identity mismatch")
    if observed_forgejo_repository != forgejo_repository:
        raise CaptureError("local Forgejo remote repository identity mismatch")
    ref = f"refs/heads/{branch}"
    sha = command(["git", "-C", str(repo_root.resolve()), "rev-parse", "--verify", ref], "local git ref")
    if SHA40.fullmatch(sha) is None:
        raise CaptureError("local default branch does not resolve to a commit SHA")
    kind = command(["git", "-C", str(repo_root.resolve()), "cat-file", "-t", sha], "local git object")
    if kind != "commit":
        raise CaptureError("local default branch does not point to a commit")
    bindings = {
        "github_remote": github_remote,
        "github_repository": github_repository,
        "forgejo_remote": forgejo_remote,
        "forgejo_repository": observed_forgejo_repository,
    }
    argv = [
        ["git", "-C", "<repo-root>", "rev-parse", "--show-toplevel"],
        [
            "git", "-C", "<repo-root>", "remote", "get-url",
            "--push", "--all", github_remote,
        ],
        [
            "git", "-C", "<repo-root>", "remote", "get-url",
            "--push", "--all", forgejo_remote,
        ],
        ["git", "-C", "<repo-root>", "rev-parse", "--verify", ref],
        ["git", "-C", "<repo-root>", "cat-file", "-t", sha],
    ]
    stdout = [".", github_repository, observed_forgejo_repository, sha, "commit"]
    return sha, ref, bindings, capture_receipt(argv, stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("authority", choices=["github", "forgejo", "local"])
    parser.add_argument("--repository", required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--forge-url", default="http://localhost:3000")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--github-remote", default="github")
    parser.add_argument("--forgejo-remote", default="forgejo")
    parser.add_argument("--forgejo-repository")
    args = parser.parse_args()
    try:
        if REPOSITORY.fullmatch(args.repository) is None:
            raise CaptureError("repository must be OWNER/REPOSITORY")
        if BRANCH.fullmatch(args.default_branch) is None or ".." in args.default_branch:
            raise CaptureError("default branch is empty or unsafe")
        if args.authority == "github":
            sha, source_identity, repository_id, capture = github(
                args.repository, args.default_branch
            )
            authority, source = "github-api", "gh-api"
            remote_bindings = None
        elif args.authority == "forgejo":
            sha, source_identity, repository_id, capture = forgejo(
                args.repository, args.default_branch, args.forge_url
            )
            authority, source = "forgejo-api", "forgejo-api-authenticated-read"
            remote_bindings = None
        else:
            if args.repo_root is None or not args.forgejo_repository:
                raise CaptureError("local capture requires --repo-root and --forgejo-repository")
            sha, source_identity, remote_bindings, capture = local(
                args.repo_root, args.default_branch, args.repository,
                args.forgejo_repository, args.github_remote, args.forgejo_remote,
            )
            authority, source = "local-git", "git-rev-parse"
            repository_id = None
        captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        stem = f"{args.authority}-main"
        transport_path = args.output_dir / f"{stem}-transport.json"
        observation_path = args.output_dir / f"{stem}-observation.json"
        transport = {
            "schema": "dual-forge-ref-transport/v1",
            "producer": "capture_origin_ref.py",
            "source": source,
            "source_identity": source_identity,
            "authority": authority,
            "repository": args.repository,
            "default_branch": args.default_branch,
            "ref": f"refs/heads/{args.default_branch}",
            "sha": sha,
            "captured_at": captured_at,
            "remote_bindings": remote_bindings,
            "repository_id": repository_id,
            "capture": capture,
        }
        atomic(transport_path, transport)
        observation = {
            "schema": "dual-forge-ref-observation/v1",
            "authority": authority,
            "repository": args.repository,
            "default_branch": args.default_branch,
            "ref": f"refs/heads/{args.default_branch}",
            "sha": sha,
            "captured_at": captured_at,
            "repository_id": repository_id,
            "transport": {
                "path": transport_path.relative_to(args.output_dir.parent).as_posix(),
                "sha256": hashlib.sha256(transport_path.read_bytes()).hexdigest(),
            },
        }
        atomic(observation_path, observation)
    except (CaptureError, OSError) as exc:
        print(f"FAIL origin-ref capture: {exc}", file=sys.stderr)
        return 2
    print(f"WROTE {observation_path} transport={transport_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
