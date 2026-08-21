#!/usr/bin/env python3
"""Durable result-tree carrier for Codex v2 worker results — issue #508.

A post-turn result tree written with `git write-tree` is immutable inside the
originating object database, but it is not reachable from any ref, is not
transferred by a clone, and may be pruned. A SHA without a retained object is
not a replayable external receipt.

This module binds exactly one explicit carrier:

```text
POST_TURN_TREE_MATERIALIZED
→ two parentless evidence commits (base tree, result tree) under
  refs/evidence/codex-v2/<carrier-id>/{base,result}
→ content-addressed Git bundle + manifest digest
→ INDEPENDENT_CLONE_OR_BUNDLE_READBACK in a scratch repository that has no
  access to the originating object store
→ RESULT_TREE_REPLAY_PASS
```

Parentless evidence commits are used deliberately: the carrier must transport
the two trees under comparison, not the repository history behind them. Nothing
here relies on reflog or accidental object retention, and the implementation
branch is never moved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

CARRIER_KIND = "GIT_BUNDLE_V2"
CARRIER_REF_PREFIX = "refs/evidence/codex-v2"
EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")
EXACT_SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")
MANIFEST_FIELDS = (
    "carrier_kind",
    "carrier_id",
    "repo",
    "base_sha",
    "base_tree_sha",
    "result_tree_sha",
    "changed_paths",
    "base_ref",
    "result_ref",
    "base_evidence_commit",
    "result_evidence_commit",
    "bundle_filename",
    "bundle_sha256",
    "bundle_bytes",
)

# Fixed identity/date so an evidence commit is a pure function of the tree it
# carries: the same result tree always yields the same evidence commit SHA.
_EVIDENCE_IDENTITY = {
    "GIT_AUTHOR_NAME": "codex-v2-evidence",
    "GIT_AUTHOR_EMAIL": "codex-v2-evidence@invalid",
    "GIT_AUTHOR_DATE": "1970-01-01T00:00:00+0000",
    "GIT_COMMITTER_NAME": "codex-v2-evidence",
    "GIT_COMMITTER_EMAIL": "codex-v2-evidence@invalid",
    "GIT_COMMITTER_DATE": "1970-01-01T00:00:00+0000",
}
# Anything that could point Git back at the originating object store.
_INHERITED_GIT_LEAKS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
)


class CarrierError(ValueError):
    pass


def _git(cwd: Path, *args: str, env: dict[str, str] | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise CarrierError(f"git {' '.join(args)} failed: {detail or result.returncode}")
    return result.stdout.strip()


def _clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in _INHERITED_GIT_LEAKS:
        env.pop(key, None)
    env.update(_EVIDENCE_IDENTITY)
    if extra:
        env.update(extra)
    return env


def _repo_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CarrierError("changed path must be a non-empty string")
    path = PurePosixPath(value.replace("\\", "/").strip())
    if path.is_absolute() or ".." in path.parts:
        raise CarrierError(f"changed path must stay repository-relative: {value!r}")
    parts = tuple(part for part in path.parts if part not in (".", ""))
    if not parts:
        raise CarrierError(f"changed path must not be empty: {value!r}")
    return PurePosixPath(*parts).as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def carrier_id_for(task_id: str, attempt_id: str) -> str:
    raw = f"{task_id}-{attempt_id}".strip("/")
    safe = SAFE_ID.sub("-", raw).strip("-.")
    if not safe:
        raise CarrierError("carrier id cannot be derived from empty task/attempt identity")
    return safe


def _diff_tree_paths(cwd: Path, base: str, result: str, env: dict[str, str]) -> list[str]:
    raw = _git(cwd, "diff", "--name-only", "-z", "--no-renames", base, result, "--", env=env)
    return sorted(_repo_path(path) for path in raw.split("\0") if path)


def create_carrier(
    worktree: Path,
    *,
    repo: str,
    base_sha: str,
    base_tree_sha: str,
    result_tree_sha: str,
    changed_paths: list[str],
    out_dir: Path,
    carrier_id: str,
) -> dict[str, Any]:
    """Publish the result tree as a durable, independently replayable carrier."""

    for name, value in (
        ("base_sha", base_sha),
        ("base_tree_sha", base_tree_sha),
        ("result_tree_sha", result_tree_sha),
    ):
        if not EXACT_SHA.fullmatch(str(value)):
            raise CarrierError(f"{name} must be an exact 40-hex Git subject")
    declared = sorted({_repo_path(path) for path in changed_paths})
    if len(declared) != len(changed_paths):
        raise CarrierError("changed_paths must be unique repository-relative paths")

    env = _clean_env()
    worktree = worktree.resolve()
    observed_base_tree = _git(worktree, "rev-parse", f"{base_sha}^{{tree}}", env=env)
    if observed_base_tree != base_tree_sha:
        raise CarrierError(
            f"base_sha does not resolve to base_tree_sha: expected {base_tree_sha} observed {observed_base_tree}"
        )
    if _git(worktree, "cat-file", "-t", result_tree_sha, env=env) != "tree":
        raise CarrierError("result_tree_sha must resolve to a Git tree in the originating repository")
    observed = _diff_tree_paths(worktree, base_tree_sha, result_tree_sha, env)
    if observed != declared:
        raise CarrierError(
            f"carrier denominator mismatch: declared {declared} observed {observed}"
        )

    base_ref = f"{CARRIER_REF_PREFIX}/{carrier_id}/base"
    result_ref = f"{CARRIER_REF_PREFIX}/{carrier_id}/result"
    base_commit = _git(worktree, "commit-tree", base_tree_sha, "-m", f"codex-v2 base {carrier_id}", env=env)
    result_commit = _git(worktree, "commit-tree", result_tree_sha, "-m", f"codex-v2 result {carrier_id}", env=env)
    _git(worktree, "update-ref", base_ref, base_commit, env=env)
    _git(worktree, "update-ref", result_ref, result_commit, env=env)

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_filename = f"codex-v2-{carrier_id}.bundle"
    bundle_path = out_dir / bundle_filename
    if bundle_path.exists():
        bundle_path.unlink()
    _git(worktree, "bundle", "create", str(bundle_path), base_ref, result_ref, env=env)

    manifest = {
        "carrier_kind": CARRIER_KIND,
        "carrier_id": carrier_id,
        "repo": repo,
        "base_sha": base_sha,
        "base_tree_sha": base_tree_sha,
        "result_tree_sha": result_tree_sha,
        "changed_paths": declared,
        "base_ref": base_ref,
        "result_ref": result_ref,
        "base_evidence_commit": base_commit,
        "result_evidence_commit": result_commit,
        "bundle_filename": bundle_filename,
        "bundle_sha256": _sha256_file(bundle_path),
        "bundle_bytes": bundle_path.stat().st_size,
    }
    validate_manifest(manifest)
    (out_dir / f"{bundle_filename}.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def validate_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict):
        raise CarrierError("carrier manifest must be an object")
    missing = sorted(set(MANIFEST_FIELDS) - manifest.keys())
    if missing:
        raise CarrierError(f"carrier manifest missing fields: {', '.join(missing)}")
    extra = sorted(manifest.keys() - set(MANIFEST_FIELDS))
    if extra:
        raise CarrierError(f"carrier manifest has unschematized fields: {', '.join(extra)}")
    if manifest["carrier_kind"] != CARRIER_KIND:
        raise CarrierError(f"unsupported carrier_kind: {manifest['carrier_kind']!r}")
    for field in ("base_sha", "base_tree_sha", "result_tree_sha", "base_evidence_commit", "result_evidence_commit"):
        if not EXACT_SHA.fullmatch(str(manifest[field])):
            raise CarrierError(f"{field} must be an exact 40-hex Git subject")
    if not EXACT_SHA256.fullmatch(str(manifest["bundle_sha256"])):
        raise CarrierError("bundle_sha256 must be exact 64 hex")
    if not isinstance(manifest["bundle_bytes"], int) or isinstance(manifest["bundle_bytes"], bool):
        raise CarrierError("bundle_bytes must be an integer")
    if manifest["bundle_bytes"] <= 0:
        raise CarrierError("bundle_bytes must be positive")
    for field in ("carrier_id", "repo", "bundle_filename"):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise CarrierError(f"{field} must be a non-empty string")
    if "/" in manifest["bundle_filename"] or manifest["bundle_filename"].startswith("."):
        raise CarrierError("bundle_filename must be a plain file name")
    expected_id = manifest["carrier_id"]
    if manifest["base_ref"] != f"{CARRIER_REF_PREFIX}/{expected_id}/base":
        raise CarrierError("base_ref must be the namespaced evidence ref for this carrier id")
    if manifest["result_ref"] != f"{CARRIER_REF_PREFIX}/{expected_id}/result":
        raise CarrierError("result_ref must be the namespaced evidence ref for this carrier id")
    paths = manifest["changed_paths"]
    if not isinstance(paths, list):
        raise CarrierError("changed_paths must be a list")
    normalized = sorted({_repo_path(path) for path in paths})
    if normalized != paths:
        raise CarrierError("changed_paths must be unique, normalized and sorted")


def replay_carrier(manifest: dict[str, Any], bundle_path: Path, scratch_dir: Path | None = None) -> dict[str, Any]:
    """Resolve the result tree from bundle + manifest alone.

    The scratch repository is created outside the originating repository and is
    given no alternates, so a tree that survives only in the originating object
    store cannot satisfy this readback.
    """

    validate_manifest(manifest)
    bundle_path = Path(bundle_path)
    if not bundle_path.is_file():
        raise CarrierError(f"carrier bundle is absent: {bundle_path}")
    observed_bytes = bundle_path.stat().st_size
    if observed_bytes != manifest["bundle_bytes"]:
        raise CarrierError(
            f"carrier bundle size drift: manifest {manifest['bundle_bytes']} observed {observed_bytes}"
        )
    observed_digest = _sha256_file(bundle_path)
    if observed_digest != manifest["bundle_sha256"]:
        raise CarrierError(
            f"carrier bundle digest drift: manifest {manifest['bundle_sha256']} observed {observed_digest}"
        )

    with tempfile.TemporaryDirectory(prefix="codex-v2-replay-", dir=scratch_dir) as temp_dir:
        scratch = Path(temp_dir) / "replay.git"
        env = _clean_env()
        subprocess.run(
            ["git", "init", "-q", "--bare", str(scratch)],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        base_ref = manifest["base_ref"]
        result_ref = manifest["result_ref"]
        fetch = subprocess.run(
            [
                "git", "-C", str(scratch), "fetch", "--no-tags", "--quiet", str(bundle_path.resolve()),
                f"+{base_ref}:{base_ref}", f"+{result_ref}:{result_ref}",
            ],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        if fetch.returncode:
            detail = (fetch.stderr or fetch.stdout).strip()
            raise CarrierError(f"carrier bundle does not carry the declared evidence refs: {detail}")

        for ref, commit in ((base_ref, manifest["base_evidence_commit"]), (result_ref, manifest["result_evidence_commit"])):
            observed_commit = _git(scratch, "rev-parse", f"{ref}^{{commit}}", env=env)
            if observed_commit != commit:
                raise CarrierError(f"{ref} resolves to {observed_commit}, manifest names {commit}")

        for name, ref, tree in (
            ("base_tree_sha", base_ref, manifest["base_tree_sha"]),
            ("result_tree_sha", result_ref, manifest["result_tree_sha"]),
        ):
            if _git(scratch, "cat-file", "-t", tree, env=env, check=False) != "tree":
                raise CarrierError(f"{name} {tree} is absent from the carrier bundle object store")
            observed_tree = _git(scratch, "rev-parse", f"{ref}^{{tree}}", env=env)
            if observed_tree != tree:
                raise CarrierError(f"{ref} carries tree {observed_tree}, manifest names {tree}")

        observed_paths = _diff_tree_paths(scratch, manifest["base_tree_sha"], manifest["result_tree_sha"], env)

    if observed_paths != manifest["changed_paths"]:
        raise CarrierError(
            f"replayed denominator mismatch: manifest {manifest['changed_paths']} observed {observed_paths}"
        )
    return {
        "carrier_kind": manifest["carrier_kind"],
        "carrier_id": manifest["carrier_id"],
        "bundle_sha256": observed_digest,
        "result_tree_sha": manifest["result_tree_sha"],
        "base_tree_sha": manifest["base_tree_sha"],
        "changed_paths": list(observed_paths),
        "replay_source": "BUNDLE_ONLY_SCRATCH_REPOSITORY",
        "result_tree_replay": "PASS",
    }


def _cmd_create(args: argparse.Namespace) -> int:
    manifest = create_carrier(
        Path(args.worktree),
        repo=args.repo,
        base_sha=args.base_sha,
        base_tree_sha=args.base_tree_sha,
        result_tree_sha=args.result_tree_sha,
        changed_paths=list(args.changed_path),
        out_dir=Path(args.out_dir),
        carrier_id=args.carrier_id,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    bundle = Path(args.bundle) if args.bundle else Path(args.manifest).resolve().parent / manifest.get("bundle_filename", "")
    print(json.dumps(replay_carrier(manifest, bundle), indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="publish evidence refs plus a content-addressed bundle")
    create.add_argument("--worktree", required=True)
    create.add_argument("--repo", required=True)
    create.add_argument("--base-sha", required=True)
    create.add_argument("--base-tree-sha", required=True)
    create.add_argument("--result-tree-sha", required=True)
    create.add_argument("--changed-path", action="append", default=[])
    create.add_argument("--out-dir", required=True)
    create.add_argument("--carrier-id", required=True)
    create.set_defaults(func=_cmd_create)

    replay = sub.add_parser("replay", help="resolve the result tree from bundle + manifest only")
    replay.add_argument("--manifest", required=True)
    replay.add_argument("--bundle")
    replay.set_defaults(func=_cmd_replay)

    args = parser.parse_args()
    try:
        return args.func(args)
    except CarrierError as error:
        print(f"CARRIER-FAIL {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
