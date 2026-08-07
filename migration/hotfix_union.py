#!/usr/bin/env python3
"""Restore files the majority vote discarded, without touching anything else.

The first convergence pass picked a winner per skill by majority across three
repos, but two of those repos are one lineage counted twice (see PRD #1), so the
vote dropped files that existed in only the outvoted copy. Every discarded byte
is still in the backup; this walks it and copies back exactly the files the
shared body does not have.

Deliberately narrow: a file that already exists in the shared body is NEVER
touched, even when the backup's version is larger or newer. Merging same-name
content is per-skill work with a human ruling behind it (PRD slices), and doing
it here would produce a hybrid whose internal pointers nobody has checked.

  hotfix_union.py --backup DIR --shared DIR [--exclude NAME]... [--apply]
  hotfix_union.py --selftest

Exit: 0 done/nothing to do, 1 a pre-existing file changed (must never happen).
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

SKIP_PARTS = {"__pycache__"}


def content_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and not SKIP_PARTS & set(p.parts) and not p.name.endswith(".pyc")
    )


def fingerprint(root: Path) -> dict[str, str]:
    """Hash every file so 'we changed nothing else' is provable, not asserted."""
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in content_files(root)
    }


def plan(backup: Path, shared: Path, exclude: set[str]) -> list[tuple[str, str, Path, Path, int]]:
    """Return (skill, source, src_path, dst_path, size) for files only in backup."""
    restores: list[tuple[str, str, Path, Path, int]] = []
    if not backup.is_dir():
        return restores
    for skill_dir in sorted(backup.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in exclude:
            continue
        target_root = shared / skill_dir.name
        if not target_root.is_dir():
            continue        # not adopted; nothing to restore into
        for source_dir in sorted(skill_dir.iterdir()):
            if not source_dir.is_dir():
                continue
            for path in content_files(source_dir):
                relative = path.relative_to(source_dir).as_posix()
                destination = target_root / relative
                if destination.exists():
                    continue        # same-name merges belong to that skill's slice
                if any(r[3] == destination for r in restores):
                    continue        # first source wins; later ones are duplicates
                restores.append(
                    (skill_dir.name, source_dir.name, path, destination, path.stat().st_size)
                )
    return restores


def run(backup: Path, shared: Path, exclude: set[str], apply: bool) -> int:
    before = fingerprint(shared)
    restores = plan(backup, shared, exclude)
    if not restores:
        print("NOTHING-TO-RESTORE: 共用 body 已含備份中的每個檔案")
        return 0

    for skill, source, src, dst, size in restores:
        verb = "RESTORE" if apply else "WOULD-RESTORE"
        print(f"{verb} {skill}/{dst.relative_to(shared / skill)}  {size:6d}B  <- {source}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    if not apply:
        print(f"\n{len(restores)} 個檔案待聯集回來；加 --apply 執行")
        return 0

    after = fingerprint(shared)
    changed = [f for f, h in before.items() if after.get(f) != h]
    if changed:
        for f in changed:
            print(f"FAIL pre-existing-file-changed: {f}", file=sys.stderr)
        return 1
    added = sorted(set(after) - set(before))
    print(f"\nRESTORED={len(added)}  既有檔案 {len(before)} 個逐一比對 hash，全部未變")
    return 0


def selftest() -> int:
    """good/hollow: only-in-backup files come back; same-name files never move."""
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        shared = root / "shared"
        backup = root / "backup"
        (shared / "demo").mkdir(parents=True)
        (shared / "demo" / "SKILL.md").write_text("shared version\n")
        (shared / "skipme").mkdir(parents=True)
        (shared / "skipme" / "SKILL.md").write_text("shared\n")

        source = backup / "demo" / "skill-bettor_.claude"
        (source / "modules").mkdir(parents=True)
        (source / "SKILL.md").write_text("BACKUP VERSION IS DIFFERENT AND LONGER\n")
        (source / "modules" / "only-here.md").write_text("rescued\n")
        excluded = backup / "skipme" / "skill-bettor_.claude"
        excluded.mkdir(parents=True)
        (excluded / "extra.md").write_text("must not be restored\n")
        orphan = backup / "never-adopted" / "x"
        orphan.mkdir(parents=True)
        (orphan / "SKILL.md").write_text("no target\n")

        if run(backup, shared, {"skipme"}, apply=True) != 0:
            print("FAIL: run reported a changed pre-existing file", file=sys.stderr)
            return 2
        if not (shared / "demo" / "modules" / "only-here.md").is_file():
            print("FAIL: only-in-backup file was not restored", file=sys.stderr)
            return 2
        if (shared / "demo" / "SKILL.md").read_text() != "shared version\n":
            print("FAIL: same-name file was overwritten", file=sys.stderr)
            return 2
        if (shared / "skipme" / "extra.md").exists():
            print("FAIL: excluded skill was touched", file=sys.stderr)
            return 2
        if (shared / "never-adopted").exists():
            print("FAIL: restored into a skill that was never adopted", file=sys.stderr)
            return 2
        if not filecmp.cmp(source / "modules" / "only-here.md",
                           shared / "demo" / "modules" / "only-here.md", shallow=False):
            print("FAIL: restored file is not byte-identical", file=sys.stderr)
            return 2
    print("SELFTEST GREEN")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--shared", type=Path)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.backup or not args.shared:
        parser.error("--backup and --shared are required unless --selftest")
    return run(args.backup, args.shared, set(args.exclude), args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
