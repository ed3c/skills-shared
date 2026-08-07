#!/usr/bin/env python3
"""Keep infrastructure skills undifferentiated across every project.

One rule, mechanically enforced: a skill is either shared infrastructure --
exactly one copy, in this repo, reached from every project through the two
user-level surfaces -- or repo-owned, living in that repo because it is
genuinely differentiated. Nothing is both. A repository that keeps its own copy
of a shared name silently shadows the shared one (project skills win over user
skills on both hosts), which is how the same fix gets rediscovered in five
places; `check` is what makes that state fail loudly instead.

  report   classify every skill name across the subscribers -- the decision queue
  check    zero-network gate: no shared skill is shadowed or unlinked (T0)
  link     materialize a shared skill's user-level symlinks (idempotent)
  adopt    move a repo's copy in and register it as shared (moves, never deletes)

Exit codes: 0 clean, 1 a rule is violated, 3 nothing to do.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
REGISTRY = REPO / "registry.json"
NOTHING_TO_DO = 3


class SharedSkillsError(RuntimeError):
    """Raised when the shared-skills invariant cannot be established."""


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------


def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedSkillsError(f"unreadable registry: {path}: {error}") from error
    if data.get("schema") != "shared-skills-registry/v1":
        raise SharedSkillsError("registry schema must be shared-skills-registry/v1")
    for field in ("canonical_root", "surfaces", "subscribers", "shared", "repo_owned"):
        if field not in data:
            raise SharedSkillsError(f"registry lacks '{field}'")
    return data


def content_files(path: Path) -> list[Path]:
    return sorted(
        p for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")
    )


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    for file in content_files(path):
        sha.update(file.relative_to(path).as_posix().encode())
        try:
            sha.update(file.read_bytes())
        except OSError:
            sha.update(b"<unreadable>")
    return sha.hexdigest()[:8]


def skill_roots(registry: dict[str, Any]) -> dict[str, Path]:
    """Every directory that a host would discover skills in."""
    roots = {label: Path(p) for label, p in registry["surfaces"].items()
             if not label.startswith("_")}
    for raw in registry["subscribers"]:
        repo = Path(raw)
        roots[f"{repo.name}/.agents"] = repo / ".agents" / "skills"
        roots[f"{repo.name}/.claude"] = repo / ".claude" / "skills"
    return roots


def is_pointer(entry: Path) -> bool:
    """Symlinks and single-SKILL.md forwarders point; they are not copies."""
    if entry.is_symlink():
        return True
    files = content_files(entry)
    return len(files) == 1 and files[0].name == "SKILL.md"


def scan(registry: dict[str, Any]) -> dict[str, dict[str, str]]:
    """name -> {surface label: digest} for real copies only."""
    found: dict[str, dict[str, str]] = {}
    for label, root in skill_roots(registry).items():
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") or not entry.is_dir():
                continue
            if is_pointer(entry):
                continue
            found.setdefault(entry.name, {})[label] = digest(entry)
    return found


def canonical_path(registry: dict[str, Any], name: str) -> Path:
    return REPO / registry["canonical_root"] / name


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------


def report(registry: dict[str, Any]) -> int:
    shared = {item["name"] for item in registry["shared"]}
    owned = {(item["name"], Path(item["repo"]).name) for item in registry["repo_owned"]}
    owned_names = {name for name, _ in owned}
    found = scan(registry)

    violations, unruled = [], []
    for name, places in sorted(found.items()):
        # `scan` only walks the host discovery roots, never this repo, so any
        # hit on a shared name is by definition a copy that shadows canonical.
        if name in shared:
            violations.append((name, places))
        elif name not in owned_names and len(places) > 1:
            unruled.append((name, places))

    print(f"### 已登記共用 ({len(shared)})；已登記 repo 自有 ({len(owned_names)})")
    if violations:
        print(f"\n### 違反：共用 skill 卻有 repo 副本影蓋 ({len(violations)})")
        for name, places in violations:
            print(f"  {name}")
            for label, value in sorted(places.items()):
                print(f"      {label:26s} {value}")
    if unruled:
        print(f"\n### 待人裁：同名多份、尚未登記 ({len(unruled)})")
        for name, places in unruled:
            hashes = {h for h in places.values()}
            verdict = "內容相同→純重複" if len(hashes) == 1 else f"分岔 {len(hashes)} 版"
            print(f"  {name:34s} {len(places)} 份, {verdict}")
            for label, value in sorted(places.items()):
                print(f"      {label:26s} {value}")
    if not violations and not unruled:
        print("\n所有 skill 都已裁決且無影蓋。")
        return 0
    print(f"\n共用被影蓋 {len(violations)}；待裁 {len(unruled)}")
    return 1 if violations else NOTHING_TO_DO


def check(registry: dict[str, Any]) -> int:
    """T0 gate. Fails only on ruled violations, never on unruled duplicates."""
    failures: list[str] = []
    found = scan(registry)
    surfaces = {label: Path(p) for label, p in registry["surfaces"].items()
                if not label.startswith("_")}
    for item in registry["shared"]:
        name = item["name"]
        canonical = canonical_path(registry, name)
        if not canonical.is_dir():
            failures.append(f"MISSING-CANONICAL {name}: {canonical}")
            continue
        for label, root in surfaces.items():
            surface = root / name
            if not surface.is_symlink():
                failures.append(f"NOT-A-SYMLINK {name}: {surface} -- run `link {name}`")
            elif surface.resolve() != canonical.resolve():
                failures.append(f"WRONG-TARGET {name}: {surface} -> {surface.resolve()}")
        for label in sorted(found.get(name, {})):
            failures.append(
                f"SHADOWED {name}: {label} keeps its own copy -- project skills win over "
                f"user skills, so that copy silently replaces the shared one"
            )
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(f"PASS shared skills hold ({len(registry['shared'])} registered)")
    return 0


def link(registry: dict[str, Any], name: str) -> int:
    canonical = canonical_path(registry, name)
    if not canonical.is_dir():
        raise SharedSkillsError(f"not in the shared repo: {canonical}")
    codex_root = Path(registry["surfaces"]["codex_user"])
    claude_root = Path(registry["surfaces"]["claude_user"])
    codex_root.mkdir(parents=True, exist_ok=True)
    claude_root.mkdir(parents=True, exist_ok=True)

    for surface, target in (
        (codex_root / name, canonical),
        # relative, matching the form the other user-level Claude entries use
        (claude_root / name, Path(os.path.relpath(codex_root / name, claude_root))),
    ):
        if surface.is_symlink():
            surface.unlink()
        elif surface.exists():
            raise SharedSkillsError(f"{surface} exists and is not a symlink -- use `adopt`")
        surface.symlink_to(target)
        if surface.resolve() != canonical.resolve():
            raise SharedSkillsError(f"{surface} resolves to {surface.resolve()}")
        if not (surface / "SKILL.md").is_file():
            raise SharedSkillsError(f"SKILL.md unreadable through {surface}")
        print(f"LINKED  {surface} -> {target}")
    return 0


def adopt(registry: dict[str, Any], name: str, source: Path, why: str, backup: Path) -> int:
    """Move a repo's copy into the shared repo and register it. Never deletes."""
    source = source.resolve()
    canonical = canonical_path(registry, name)
    if canonical.exists():
        raise SharedSkillsError(f"already shared: {canonical}")
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise SharedSkillsError(f"source is not a skill directory: {source}")
    if any(item["name"] == name for item in registry["shared"]):
        raise SharedSkillsError(f"{name} is already registered as shared")

    backup.mkdir(parents=True, exist_ok=True)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(canonical))
    print(f"MOVED   {source} -> {canonical}")

    registry["shared"].append({"name": name, "admitted": date.today().isoformat(), "why": why})
    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"REGISTERED {name} in {REGISTRY}")
    return link(registry, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("report", help="classify every skill name; the decision queue")
    commands.add_parser("check", help="zero-network gate over the registered rulings")
    link_parser = commands.add_parser("link", help="materialize a shared skill's symlinks")
    link_parser.add_argument("name")
    adopt_parser = commands.add_parser("adopt", help="move a repo copy in and register it")
    adopt_parser.add_argument("name")
    adopt_parser.add_argument("--from", dest="source", required=True, type=Path)
    adopt_parser.add_argument("--why", required=True)
    adopt_parser.add_argument(
        "--backup-dir", type=Path,
        default=Path(os.environ.get("TMPDIR", "/tmp")) / "shared-skills-superseded",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.command == "report":
            return report(registry)
        if args.command == "check":
            return check(registry)
        if args.command == "link":
            return link(registry, args.name)
        return adopt(registry, args.name, args.source, args.why, args.backup_dir)
    except SharedSkillsError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
