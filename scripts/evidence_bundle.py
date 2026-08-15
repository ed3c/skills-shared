#!/usr/bin/env python3
"""Collect and verify a replayable exact-head evidence bundle.

Exit codes:
  0   bundle collected, or a verified bundle matched its manifest exactly
  2   a verified bundle does not match its manifest
  64  missing, unreadable, or malformed input

A workflow badge is not a run and a green log is not a receipt. This produces a
manifest that binds every collected file to a SHA-256 alongside the exact subject
the job ran on, so a downloaded bundle can be checked later without trusting the
provider UI, and without network access.

Provider identity is read from the environment. What is absent is recorded as
ABSENT rather than defaulted, because a bundle that silently invents a run id is
worse than one that admits it was produced outside CI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

MANIFEST_NAME = "MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
SCHEMA = "exact-head-evidence-bundle/v1"

MISMATCH = 2
INVALID = 64

# Provider facts that identify which run produced this bundle. Absent is a state.
PROVIDER_KEYS = (
    ("repository", "GITHUB_REPOSITORY"),
    ("workflow", "GITHUB_WORKFLOW"),
    ("job", "GITHUB_JOB"),
    ("run_id", "GITHUB_RUN_ID"),
    ("run_attempt", "GITHUB_RUN_ATTEMPT"),
    ("head_sha", "GITHUB_SHA"),
    ("ref", "GITHUB_REF"),
)


def digest_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def walk_files(root: Path) -> list[Path]:
    """Every file under root, hidden and nested included.

    A manifest that skips dotfiles describes a different tree than the one that
    was uploaded, and the difference is exactly where runtime receipts tend to
    live.
    """
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.name != MANIFEST_NAME
    )


def provider_identity(env: dict[str, str]) -> dict[str, str]:
    return {key: env.get(var) or "ABSENT" for key, var in PROVIDER_KEYS}


def runtime_identity() -> dict[str, str]:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "system": platform.system(),
        "machine": platform.machine(),
    }


def collect(sources: list[Path], output: Path, env: dict[str, str], tree_sha: str) -> int:
    missing = [str(source) for source in sources if not source.exists()]
    if missing:
        print(
            f"EVIDENCE-BUNDLE-INVALID absent-source: {','.join(missing)}",
            file=sys.stderr,
        )
        return INVALID

    payload = output / "files"
    payload.mkdir(parents=True, exist_ok=True)
    for source in sources:
        target = payload / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)

    entries = []
    for path in walk_files(payload):
        entries.append(
            {
                "path": str(path.relative_to(output)),
                "sha256": digest_file(path),
                "bytes": path.stat().st_size,
            }
        )
    if not entries:
        print("EVIDENCE-BUNDLE-INVALID empty-bundle: no file collected", file=sys.stderr)
        return INVALID

    manifest = {
        "schema": SCHEMA,
        "subject": {**provider_identity(env), "tree_sha": tree_sha or "ABSENT"},
        "runtime": runtime_identity(),
        "files": entries,
        "file_count": len(entries),
        "replay": f"python3 scripts/evidence_bundle.py verify <bundle-dir>",
    }
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / SUMS_NAME).write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries), encoding="utf-8"
    )
    print(
        f"EVIDENCE-BUNDLE-COLLECTED files={len(entries)} "
        f"head={manifest['subject']['head_sha'][:12]} "
        f"run={manifest['subject']['run_id']} "
        f"python={manifest['runtime']['python_version']}"
    )
    return 0


def verify(bundle: Path) -> int:
    manifest_path = bundle / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"EVIDENCE-BUNDLE-INVALID absent-manifest: {manifest_path}", file=sys.stderr)
        return INVALID
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"EVIDENCE-BUNDLE-INVALID unreadable-manifest: {exc}", file=sys.stderr)
        return INVALID
    if manifest.get("schema") != SCHEMA:
        print(
            f"EVIDENCE-BUNDLE-INVALID schema-mismatch: {manifest.get('schema')!r}",
            file=sys.stderr,
        )
        return INVALID

    problems: list[str] = []
    declared = {entry["path"]: entry for entry in manifest.get("files", [])}
    for path, entry in sorted(declared.items()):
        target = bundle / path
        if not target.is_file():
            problems.append(f"absent-file: {path}")
            continue
        actual = digest_file(target)
        if actual != entry["sha256"]:
            problems.append(f"digest-mismatch: {path} manifest={entry['sha256'][:12]} actual={actual[:12]}")

    # Both directions: an unlisted file in the bundle is as much a manifest defect
    # as a listed file that is missing.
    present = {str(path.relative_to(bundle)) for path in walk_files(bundle)}
    present.discard(SUMS_NAME)
    for extra in sorted(present - set(declared)):
        problems.append(f"unlisted-file: {extra}")

    if problems:
        for problem in problems:
            print(f"EVIDENCE-BUNDLE-RED {problem}", file=sys.stderr)
        return MISMATCH

    subject = manifest.get("subject", {})
    print(
        f"EVIDENCE-BUNDLE-GREEN files={len(declared)} "
        f"head={subject.get('head_sha', 'ABSENT')[:12]} "
        f"run={subject.get('run_id', 'ABSENT')} "
        f"verified offline"
    )
    return 0


def selftest() -> int:
    """Prove the verifier goes red, not only that it goes green."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "receipts"
        (source / ".runtime").mkdir(parents=True)
        (source / "report.json").write_text('{"ok":true}\n', encoding="utf-8")
        (source / ".runtime" / "hidden-receipt.json").write_text('{"h":1}\n', encoding="utf-8")

        bundle = root / "bundle"
        if collect([source], bundle, {"GITHUB_RUN_ID": "1"}, "abc") != 0:
            print("SELFTEST RED: collect failed on a valid source", file=sys.stderr)
            return 1
        manifest = json.loads((bundle / MANIFEST_NAME).read_text(encoding="utf-8"))
        if not any(".runtime/hidden-receipt.json" in entry["path"] for entry in manifest["files"]):
            print("SELFTEST RED: hidden path was not collected", file=sys.stderr)
            return 1
        if verify(bundle) != 0:
            print("SELFTEST RED: a freshly collected bundle did not verify", file=sys.stderr)
            return 1

        tampered = root / "tampered"
        shutil.copytree(bundle, tampered)
        target = tampered / "files" / "receipts" / "report.json"
        target.write_text('{"ok":false}\n', encoding="utf-8")
        if verify(tampered) != MISMATCH:
            print("SELFTEST RED: a tampered file verified", file=sys.stderr)
            return 1

        removed = root / "removed"
        shutil.copytree(bundle, removed)
        (removed / "files" / "receipts" / ".runtime" / "hidden-receipt.json").unlink()
        if verify(removed) != MISMATCH:
            print("SELFTEST RED: a removed hidden file verified", file=sys.stderr)
            return 1

        added = root / "added"
        shutil.copytree(bundle, added)
        (added / "files" / "receipts" / "smuggled.json").write_text("{}\n", encoding="utf-8")
        if verify(added) != MISMATCH:
            print("SELFTEST RED: an unlisted file verified", file=sys.stderr)
            return 1

        empty = root / "empty"
        empty.mkdir()
        if verify(empty) != INVALID:
            print("SELFTEST RED: an absent manifest was not distinct", file=sys.stderr)
            return 1

        if collect([root / "nope"], root / "out", {}, "") != INVALID:
            print("SELFTEST RED: an absent source was not distinct", file=sys.stderr)
            return 1

    print(
        "SELFTEST GREEN: hidden paths collected; tamper, removal, and smuggled-file "
        "each refused; absent manifest and absent source stayed distinct from mismatch"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("sources", nargs="+", type=Path)
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--tree-sha", default="")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("bundle", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.command == "collect":
        return collect(args.sources, args.output, dict(os.environ), args.tree_sha)
    if args.command == "verify":
        return verify(args.bundle)
    parser.error("a command is required unless --selftest")
    return INVALID


if __name__ == "__main__":
    raise SystemExit(main())
