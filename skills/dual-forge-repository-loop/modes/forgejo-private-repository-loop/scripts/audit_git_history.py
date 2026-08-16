#!/usr/bin/env python3
"""Scan locally reachable Git and worktree surfaces for external denied literals.

The pattern bytes are local-only inputs. The receipt records rule indexes and
content digests, never the matched bytes. Exit 0 is clean, 2 means matches were
found, and 64 means the audit could not complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CLEAN = 0
MATCH = 2
ERROR = 64


@dataclass(frozen=True)
class Rule:
    index: int
    literal: bytes
    digest: str


def git(repo: Path, *args: str, stdin: bytes | None = None, allow_fail: bool = False) -> bytes:
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if done.returncode and not allow_fail:
        detail = done.stderr.decode("utf-8", "replace").strip() or "git failed"
        raise RuntimeError(f"git {' '.join(args)} ({done.returncode}): {detail}")
    return done.stdout


def load_rules(path: Path) -> list[Rule]:
    rules: list[Rule] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        encoded = value.encode("utf-8")
        rules.append(Rule(len(rules) + 1, encoded, hashlib.sha256(encoded).hexdigest()))
    if not rules:
        raise ValueError("patterns file has no active literals")
    return rules


def hits(data: bytes, rules: Iterable[Rule]) -> list[int]:
    lowered = data.lower()
    return [rule.index for rule in rules if rule.literal.lower() in lowered]


def record(
    findings: list[dict[str, object]],
    *,
    surface: str,
    identity: str,
    rule_indexes: list[int],
    data: bytes | None = None,
    path: str | None = None,
) -> None:
    item: dict[str, object] = {
        "surface": surface,
        "identity": identity,
        "rule_indexes": rule_indexes,
    }
    if path is not None:
        item["path"] = path
    if data is not None:
        item["sha256"] = hashlib.sha256(data).hexdigest()
        item["size"] = len(data)
    findings.append(item)


def scan_refs(repo: Path, rules: list[Rule], findings: list[dict[str, object]]) -> list[str]:
    refs = git(repo, "for-each-ref", "--format=%(refname)").decode("utf-8", "replace").splitlines()
    for ref in refs:
        found = hits(ref.encode(), rules)
        if found:
            record(findings, surface="ref-name", identity=ref, rule_indexes=found)
    return refs


def scan_commit_metadata(repo: Path, rules: list[Rule], findings: list[dict[str, object]]) -> int:
    raw = git(repo, "log", "--all", "--format=%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x00%x1e")
    count = 0
    for chunk in raw.split(b"\x1e"):
        chunk = chunk.strip(b"\n\x00")
        if not chunk:
            continue
        fields = chunk.split(b"\x00", 5)
        if len(fields) != 6:
            continue
        oid = fields[0].decode("ascii", "replace")
        payload = b"\x00".join(fields[1:])
        found = hits(payload, rules)
        if found:
            record(
                findings,
                surface="commit-metadata",
                identity=oid,
                rule_indexes=found,
                data=payload,
            )
        count += 1
    return count


def scan_git_config(repo: Path, rules: list[Rule], findings: list[dict[str, object]]) -> int:
    raw = git(repo, "config", "--null", "--list", "--show-origin")
    entries = [entry for entry in raw.split(b"\x00") if entry]
    count = 0
    for entry in entries:
        found = hits(entry, rules)
        if found:
            origin, _, rest = entry.partition(b"\n")
            identity = hashlib.sha256(origin + b"\x00" + rest.split(b"=", 1)[0]).hexdigest()
            record(
                findings,
                surface="git-config",
                identity=identity,
                rule_indexes=found,
                data=entry,
            )
        count += 1
    return count


def scan_objects(
    repo: Path,
    rules: list[Rule],
    findings: list[dict[str, object]],
    max_blob_bytes: int,
) -> tuple[int, int, int]:
    raw = git(repo, "rev-list", "--objects", "--all")
    paths: dict[str, set[str]] = {}
    for line in raw.decode("utf-8", "surrogateescape").splitlines():
        oid, _, path = line.partition(" ")
        paths.setdefault(oid, set())
        if path:
            paths[oid].add(path)
            found = hits(path.encode("utf-8", "surrogateescape"), rules)
            if found:
                record(
                    findings,
                    surface="object-path",
                    identity=oid,
                    path=path,
                    rule_indexes=found,
                )
    if not paths:
        return 0, 0, 0
    checked = git(
        repo,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        stdin=("\n".join(sorted(paths)) + "\n").encode(),
    )
    blobs = tags = lfs_pointers = 0
    for line in checked.decode("ascii", "replace").splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        oid, kind, size_text = parts
        try:
            size = int(size_text)
        except ValueError:
            continue
        if kind == "blob":
            blobs += 1
            if size > max_blob_bytes:
                continue
            data = git(repo, "cat-file", "blob", oid)
            if data.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                lfs_pointers += 1
            found = hits(data, rules)
            if found:
                record(
                    findings,
                    surface="blob-content",
                    identity=oid,
                    path=sorted(paths[oid])[0] if paths[oid] else None,
                    rule_indexes=found,
                    data=data,
                )
        elif kind == "tag":
            tags += 1
            data = git(repo, "cat-file", "-p", oid)
            found = hits(data, rules)
            if found:
                record(
                    findings,
                    surface="annotated-tag",
                    identity=oid,
                    rule_indexes=found,
                    data=data,
                )
    return blobs, tags, lfs_pointers


def scan_alternates(repo: Path, rules: list[Rule], findings: list[dict[str, object]]) -> int:
    git_common = Path(git(repo, "rev-parse", "--git-common-dir").decode().strip())
    if not git_common.is_absolute():
        top = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip())
        git_common = (top / git_common).resolve()
    alternate_file = git_common / "objects" / "info" / "alternates"
    values: list[bytes] = []
    if alternate_file.is_file():
        values.extend(line for line in alternate_file.read_bytes().splitlines() if line)
    env_value = os.environ.get("GIT_ALTERNATE_OBJECT_DIRECTORIES", "")
    if env_value:
        values.extend(part.encode() for part in env_value.split(os.pathsep) if part)
    for index, value in enumerate(values, start=1):
        found = hits(value, rules)
        record(
            findings,
            surface="alternate-object-store",
            identity=f"alternate-{index}",
            rule_indexes=found,
            data=value,
        )
    return len(values)


def scan_lfs_objects(
    repo: Path, rules: list[Rule], findings: list[dict[str, object]], max_bytes: int
) -> int:
    common = Path(git(repo, "rev-parse", "--git-common-dir").decode().strip())
    if not common.is_absolute():
        top = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip())
        common = (top / common).resolve()
    root = common / "lfs" / "objects"
    if not root.is_dir():
        return 0
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        count += 1
        try:
            if path.stat().st_size > max_bytes:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        found = hits(data, rules)
        if found:
            record(
                findings,
                surface="lfs-object-content",
                identity=hashlib.sha256(path.as_posix().encode()).hexdigest(),
                rule_indexes=found,
                data=data,
            )
    return count


def scan_worktree(
    repo: Path, rules: list[Rule], findings: list[dict[str, object]], max_bytes: int
) -> int:
    root = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    count = 0
    for path in sorted(root.rglob("*")):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if ".git" in rel.parts:
            continue
        rel_text = rel.as_posix()
        found = hits(rel_text.encode(), rules)
        if found:
            record(
                findings,
                surface="worktree-path",
                identity=rel_text,
                path=rel_text,
                rule_indexes=found,
            )
        if not path.is_file() or path.is_symlink():
            continue
        count += 1
        try:
            if path.stat().st_size > max_bytes:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        found = hits(data, rules)
        if found:
            record(
                findings,
                surface="worktree-content",
                identity=rel_text,
                path=rel_text,
                rule_indexes=found,
                data=data,
            )
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--patterns", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-bytes", type=int, default=16 * 1024 * 1024)
    parser.add_argument("--skip-worktree", action="store_true")
    args = parser.parse_args()
    try:
        repo = args.repo.resolve()
        if git(repo, "rev-parse", "--is-inside-work-tree").decode().strip() != "true":
            raise RuntimeError("repository is not a non-bare worktree")
        rules = load_rules(args.patterns.resolve())
        findings: list[dict[str, object]] = []
        refs = scan_refs(repo, rules, findings)
        commits = scan_commit_metadata(repo, rules, findings)
        config_entries = scan_git_config(repo, rules, findings)
        blobs, tags, lfs_pointers = scan_objects(repo, rules, findings, args.max_bytes)
        alternates = scan_alternates(repo, rules, findings)
        lfs_objects = scan_lfs_objects(repo, rules, findings, args.max_bytes)
        worktree_files = 0 if args.skip_worktree else scan_worktree(repo, rules, findings, args.max_bytes)
        receipt = {
            "schema": "forbidden-history-audit/v2",
            "head": git(repo, "rev-parse", "HEAD").decode().strip(),
            "patterns_sha256": hashlib.sha256(args.patterns.read_bytes()).hexdigest(),
            "rule_count": len(rules),
            "rule_digests": [rule.digest for rule in rules],
            "inventory": {
                "ref_count": len(refs),
                "commit_count": commits,
                "config_entry_count": config_entries,
                "blob_count": blobs,
                "annotated_tag_count": tags,
                "lfs_pointer_count": lfs_pointers,
                "local_lfs_object_count": lfs_objects,
                "alternate_count": alternates,
                "worktree_file_count": worktree_files,
            },
            "match_count": len(findings),
            "matches": findings,
            "verdict": "FAIL" if findings else "PASS",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(f"HISTORY-AUDIT {receipt['verdict']}: {len(findings)} finding(s)")
        return MATCH if findings else CLEAN
    except (OSError, ValueError, RuntimeError) as error:
        print(f"HISTORY-AUDIT ERROR: {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    raise SystemExit(main())
