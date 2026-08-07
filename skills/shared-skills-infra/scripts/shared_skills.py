#!/usr/bin/env python3
"""Keep infrastructure skills undifferentiated across every project.

One rule, mechanically enforced: a skill is either shared infrastructure --
exactly one copy, in this repo, reached from every project through the two
user-level surfaces -- or repo-owned, living in that repo because it is
genuinely differentiated. Nothing is both. A repository that keeps its own copy
of a shared name silently shadows the shared one (project skills win over user
skills on both hosts), which is how the same fix gets rediscovered in five
places; `check` is what makes that state fail loudly instead.

Portable by construction: this checkout's location is derived from __file__ and
the machine-specific paths live in `sites.local.json` (gitignored) or in flags,
never in the versioned registry. Clone anywhere, run `install`, done.

  install  wire this checkout to a machine: surfaces + projects, then link
  report   classify every skill name across the wired projects -- decision queue
  check    zero-network gate: no shared skill is shadowed or unlinked (T0)
  link     materialize a shared skill's user-level symlinks (idempotent)
  adopt    move a project's copy in and register it as shared (moves, never deletes)

Exit codes: 0 clean, 1 a rule is violated, 3 nothing ruled yet / nothing to do.
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
SITES = REPO / "sites.local.json"
DEFAULT_CODEX_SURFACE = Path.home() / ".agents" / "skills"
DEFAULT_CLAUDE_SURFACE = Path.home() / ".claude" / "skills"
NOTHING_TO_DO = 3


class SharedSkillsError(RuntimeError):
    """Raised when the shared-skills invariant cannot be established."""


# The dead-assertion linter deliberately does NOT run from here. It shipped
# wired into `check`, which made a missing or broken linter stop every other
# gate from running at all -- one tool's absence taking out the governance check,
# the shadowing check and the symlink check with it. A gate whose blast radius is
# every other gate costs more than the class of bug it catches.
#
# Run it on its own instead:
#     python3 scripts/check_dead_assertions.py --root <repo>
# It is worth running, and it found real dead assertions the day it was written.
# It just should not be able to take the rest down with it.


# --------------------------------------------------------------------------
# configuration: rulings are versioned, paths are not
# --------------------------------------------------------------------------


def load_registry() -> dict[str, Any]:
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedSkillsError(f"unreadable registry: {REGISTRY}: {error}") from error
    if data.get("schema") != "shared-skills-registry/v2":
        raise SharedSkillsError("registry schema must be shared-skills-registry/v2")
    for field in ("canonical_root", "shared", "repo_owned"):
        if field not in data:
            raise SharedSkillsError(f"registry lacks '{field}'")
    return data


def save_registry(registry: dict[str, Any]) -> None:
    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


class Sites:
    """Machine-specific paths. Flags beat the sites file beats defaults."""

    def __init__(self, path: Path, args: argparse.Namespace) -> None:
        self.path = path
        stored: dict[str, Any] = {}
        if path.is_file():
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise SharedSkillsError(f"unreadable sites file: {path}: {error}") from error
        self.codex_surface = Path(
            getattr(args, "codex_surface", None)
            or stored.get("codex_surface")
            or DEFAULT_CODEX_SURFACE
        ).expanduser()
        self.claude_surface = Path(
            getattr(args, "claude_surface", None)
            or stored.get("claude_surface")
            or DEFAULT_CLAUDE_SURFACE
        ).expanduser()
        raw_projects = list(getattr(args, "project", None) or stored.get("projects") or [])
        self.projects = [Path(p).expanduser() for p in raw_projects]
        # Some repos require the Claude surface to be a forwarder stub rather
        # than a symlink (their own gate checks the stub's contents). Which repos
        # those are is a per-machine fact, so it is configured, never guessed.
        self.claude_forwarder = set(
            getattr(args, "claude_forwarder", None) or stored.get("claude_forwarder_projects") or []
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "_note": "Machine-specific paths only; gitignored on purpose. The versioned "
                     "registry must stay free of absolute paths so any clone works anywhere.",
            "codex_surface": str(self.codex_surface),
            "claude_surface": str(self.claude_surface),
            "projects": [str(p) for p in self.projects],
            "claude_forwarder_projects": sorted(self.claude_forwarder),
        }

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def surfaces(self) -> dict[str, Path]:
        return {"codex_user": self.codex_surface, "claude_user": self.claude_surface}

    def skill_roots(self) -> dict[str, Path]:
        """Every directory a host discovers skills in, labelled for reporting."""
        roots = dict(self.surfaces())
        for project in self.projects:
            roots[f"{project.name}/.agents"] = project / ".agents" / "skills"
            roots[f"{project.name}/.claude"] = project / ".claude" / "skills"
        return roots


# --------------------------------------------------------------------------
# scanning
# --------------------------------------------------------------------------


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


def is_pointer(entry: Path) -> bool:
    """Symlinks and single-SKILL.md forwarders point; they are not copies."""
    if entry.is_symlink():
        return True
    files = content_files(entry)
    return len(files) == 1 and files[0].name == "SKILL.md"


def scan(sites: Sites) -> dict[str, dict[str, str]]:
    """name -> {surface label: digest} for real copies only."""
    found: dict[str, dict[str, str]] = {}
    for label, root in sites.skill_roots().items():
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") or not entry.is_dir() or is_pointer(entry):
                continue
            found.setdefault(entry.name, {})[label] = digest(entry)
    return found


def canonical_path(registry: dict[str, Any], name: str) -> Path:
    return REPO / registry["canonical_root"] / name


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------


def install(registry: dict[str, Any], sites: Sites) -> int:
    """Wire a fresh clone to this machine, then link every shared skill."""
    sites.save()
    print(f"WIRED   {sites.path}")
    print(f"        codex surface : {sites.codex_surface}")
    print(f"        claude surface: {sites.claude_surface}")
    for project in sites.projects:
        marker = "" if project.is_dir() else "  (not on disk yet)"
        print(f"        project       : {project}{marker}")
    for item in registry["shared"]:
        link(registry, sites, item["name"], quiet=True)
    return check(registry, sites)


def report(registry: dict[str, Any], sites: Sites) -> int:
    shared = {item["name"] for item in registry["shared"]}
    owned = {item["name"] for item in registry["repo_owned"]}
    found = scan(sites)

    deferred_by = {i["name"]: set(i.get("deferred_in", [])) for i in registry["shared"]}
    violations, unruled, deferred = [], [], []
    for name, places in sorted(found.items()):
        # `scan` never walks this repo, so any hit on a shared name is a copy
        # that shadows canonical -- unless that repo was explicitly deferred.
        if name in shared:
            skip = deferred_by.get(name, set())
            shadowing = {k: v for k, v in places.items() if k.split("/")[0] not in skip}
            waiting = {k: v for k, v in places.items() if k.split("/")[0] in skip}
            if shadowing:
                violations.append((name, shadowing))
            if waiting:
                deferred.append((name, waiting))
        elif name not in owned and len(places) > 1:
            unruled.append((name, places))

    print(f"### 已登記共用 ({len(shared)})；已登記 repo 自有 ({len(owned)})")
    if violations:
        print(f"\n### 違反：共用 skill 卻有 repo 副本影蓋 ({len(violations)})")
        for name, places in violations:
            print(f"  {name}")
            for label, value in sorted(places.items()):
                print(f"      {label:26s} {value}")
    if unruled:
        print(f"\n### 待人裁：同名多份、尚未登記 ({len(unruled)})")
        for name, places in unruled:
            hashes = set(places.values())
            verdict = "內容相同→純重複" if len(hashes) == 1 else f"分岔 {len(hashes)} 版"
            print(f"  {name:34s} {len(places)} 份, {verdict}")
            for label, value in sorted(places.items()):
                print(f"      {label:26s} {value}")
    if deferred:
        print(f"\n### 已收編但該 repo 的版本延後裁決 ({len(deferred)})")
        for name, places in deferred:
            for label, value in sorted(places.items()):
                print(f"  {name:34s} {label:26s} {value}")
    if not violations and not unruled and not deferred:
        print("\n所有 skill 都已裁決且無影蓋。")
        return 0
    print(f"\n共用被影蓋 {len(violations)}；待裁 {len(unruled)}；延後 {len(deferred)}")
    return 1 if violations else NOTHING_TO_DO


def check(registry: dict[str, Any], sites: Sites) -> int:
    """T0 gate. Fails only on ruled violations, never on unruled duplicates."""
    failures: list[str] = []
    found = scan(sites)
    for item in registry["shared"]:
        name = item["name"]
        canonical = canonical_path(registry, name)
        if not canonical.is_dir():
            failures.append(f"MISSING-CANONICAL {name}: {canonical}")
            continue
        for surface_root in sites.surfaces().values():
            surface = surface_root / name
            if not surface.is_symlink():
                failures.append(f"NOT-A-SYMLINK {name}: {surface} -- run `link {name}`")
            elif surface.resolve() != canonical.resolve():
                failures.append(f"WRONG-TARGET {name}: {surface} -> {surface.resolve()}")
        deferred = set(item.get("deferred_in", []))
        for label in sorted(found.get(name, {})):
            if label.split("/")[0] in deferred:
                continue        # recorded as unruled; `report` still surfaces it
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


def _point(surface: Path, target: Path, canonical: Path, strict: bool) -> bool:
    """Point one surface entry at the canonical skill. Returns True if it moved."""
    if surface.is_symlink():
        surface.unlink()
    elif surface.exists():
        if strict:
            raise SharedSkillsError(f"{surface} exists and is not a symlink -- use `adopt`")
        return False        # a real copy here is a shadow/defer question, not link's job
    surface.parent.mkdir(parents=True, exist_ok=True)
    surface.symlink_to(target)
    if surface.resolve() != canonical.resolve():
        raise SharedSkillsError(f"{surface} resolves to {surface.resolve()}")
    if not (surface / "SKILL.md").is_file():
        raise SharedSkillsError(f"SKILL.md unreadable through {surface}")
    return True


FORWARDER = """---
name: {name}
description: {name} 的本 repo 入口；工作流單一真源在共用 skills repo，本檔零邏輯。
disable-model-invocation: true
---

完整讀取並遵循 canonical skill：`../../../.agents/skills/{name}/SKILL.md`
（相對連結一律以 canonical 目錄解析）。共用基礎設施不得差異化：本檔若寫入
repo 專屬內容，會無聲影蓋共用版。

$ARGUMENTS
"""


def _write_forwarder(surface: Path, name: str) -> bool:
    """Emit a stub instead of a symlink, for repos whose gate requires one."""
    if surface.is_symlink():
        surface.unlink()
    elif surface.is_dir() and not (surface / "SKILL.md").is_file():
        return False        # a real copy: a shadow/defer question, not link's job
    elif surface.is_dir() and len(content_files(surface)) > 1:
        return False        # more than a stub lives here; leave it for `adopt`
    surface.mkdir(parents=True, exist_ok=True)
    (surface / "SKILL.md").write_text(FORWARDER.format(name=name), encoding="utf-8")
    return True


def link(registry: dict[str, Any], sites: Sites, name: str, quiet: bool = False) -> int:
    """Wire every surface -- user-level for discovery, project-level for paths.

    Projects get symlinks too, not because discovery needs them (user scope
    already covers every project) but because repo-owned gates and docs refer to
    `.claude/skills/<name>/SKILL.md` by path. A symlink satisfies those without
    creating a second copy: `scan` treats pointers as pointers, so this cannot
    reintroduce shadowing.
    """
    canonical = canonical_path(registry, name)
    if not canonical.is_dir():
        raise SharedSkillsError(f"not in the shared repo: {canonical}")
    codex_root, claude_root = sites.codex_surface, sites.claude_surface
    codex_root.mkdir(parents=True, exist_ok=True)
    claude_root.mkdir(parents=True, exist_ok=True)

    targets: list[tuple[Path, Path, bool]] = [
        (codex_root / name, canonical, True),
        # relative, matching the form the other user-level Claude entries use
        (claude_root / name, Path(os.path.relpath(codex_root / name, claude_root)), True),
    ]
    deferred = set(
        next((i for i in registry["shared"] if i["name"] == name), {}).get("deferred_in", [])
    )
    linked_forwarders: list[Path] = []
    for project in sites.projects:
        if not project.is_dir() or project.name in deferred:
            continue        # a deferred repo's own version stands until ruled
        # Absolute on both project surfaces on purpose: a relative
        # .claude -> ../../.agents hop resolves to whatever that repo keeps
        # under .agents, which for a diverged repo is its local copy, not
        # canonical -- the link would silently point at the wrong thing.
        targets.append((project / ".agents" / "skills" / name, canonical, False))
        if project.name in sites.claude_forwarder:
            if _write_forwarder(project / ".claude" / "skills" / name, name):
                linked_forwarders.append(project / ".claude" / "skills" / name)
        else:
            targets.append((project / ".claude" / "skills" / name, canonical, False))
    linked = len(linked_forwarders)
    for surface in linked_forwarders:
        if not quiet:
            print(f"FORWARD {surface}")
    for surface, target, strict in targets:
        if _point(surface, target, canonical, strict):
            linked += 1
            if not quiet:
                print(f"LINKED  {surface} -> {target}")
    if quiet:
        print(f"LINKED  {name} ({linked} surfaces)")
    return 0


def adopt(
    registry: dict[str, Any],
    sites: Sites,
    name: str,
    source: Path,
    why: str,
    backup_root: Path,
    dry_run: bool,
    defer: list[str],
) -> int:
    """Move the winning copy in, sweep every other project entry aside, register.

    Sweeping is not optional: "shared" means exactly one copy, so every other
    entry for this name -- rival copies and the pointers aiming at them -- has to
    go, or adoption would immediately produce the shadowing it exists to remove.
    Everything moves to a backup; nothing is deleted.

    `defer` names repos whose copy is left alone *and recorded*, for when the
    ruling that produced the winner did not cover them. Recording beats both
    alternatives: sweeping would decide on their behalf, and leaving them
    unrecorded would make the gate red on a question nobody has answered yet.
    """
    source = source.resolve()
    canonical = canonical_path(registry, name)
    if canonical.exists():
        raise SharedSkillsError(f"already shared: {canonical}")
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise SharedSkillsError(f"source is not a skill directory: {source}")
    if any(item["name"] == name for item in registry["shared"]):
        raise SharedSkillsError(f"{name} is already registered as shared")

    strays = [
        (label, root / name)
        for label, root in sites.skill_roots().items()
        # user surfaces are rebuilt by `link`; only project entries get swept.
        # `.exists()` follows symlinks, so a dangling one needs is_symlink too.
        if label not in ("codex_user", "claude_user")
        and label.split("/")[0] not in defer
        and ((root / name).exists() or (root / name).is_symlink())
    ]
    strays = [(label, path) for label, path in strays if path.resolve() != source]

    if dry_run:
        print(f"DRY-RUN adopt {name}")
        print(f"        {source} -> {canonical}")
        for label, path in strays:
            kind = "symlink" if path.is_symlink() else "copy"
            print(f"        sweep {kind:7s} {label:24s} {path}")
        for repo in defer:
            print(f"        defer  {repo:24s} (left in place, recorded as unruled)")
        return 0

    canonical.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(canonical))
    print(f"MOVED   {source} -> {canonical}")
    for label, path in strays:
        destination = backup_root / name / label.replace("/", "_")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        print(f"SWEPT   {label:24s} {path} -> {destination}")

    entry: dict[str, Any] = {"name": name, "admitted": date.today().isoformat(), "why": why}
    if defer:
        entry["deferred_in"] = sorted(defer)
    registry["shared"].append(entry)
    save_registry(registry)
    print(f"REGISTERED {name}" + (f" (deferred in {', '.join(sorted(defer))})" if defer else ""))
    return link(registry, sites, name)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    def with_paths(sub: argparse.ArgumentParser) -> argparse.ArgumentParser:
        sub.add_argument("--codex-surface", help="default ~/.agents/skills")
        sub.add_argument("--claude-surface", help="default ~/.claude/skills")
        sub.add_argument("--project", action="append", help="repeatable; a repo to govern")
        sub.add_argument(
            "--claude-forwarder", action="append",
            help="repeatable repo name whose .claude surface needs a stub, not a symlink",
        )
        sub.add_argument("--sites", type=Path, default=SITES, help="machine paths file")
        return sub

    with_paths(commands.add_parser("install", help="wire this clone to a machine and link"))
    with_paths(commands.add_parser("report", help="classify every skill name; decision queue"))
    with_paths(commands.add_parser("check", help="zero-network gate over the rulings"))
    link_parser = with_paths(commands.add_parser("link", help="materialize a skill's symlinks"))
    link_parser.add_argument("name")
    adopt_parser = with_paths(commands.add_parser("adopt", help="move a copy in and register"))
    adopt_parser.add_argument("name")
    adopt_parser.add_argument("--from", dest="source", required=True, type=Path)
    adopt_parser.add_argument("--why", required=True)
    adopt_parser.add_argument("--dry-run", action="store_true")
    adopt_parser.add_argument(
        "--defer", action="append", default=[],
        help="repeatable repo name whose copy stays put and is recorded as unruled",
    )
    adopt_parser.add_argument(
        "--backup-dir", type=Path,
        default=Path(os.environ.get("TMPDIR", "/tmp")) / "shared-skills-superseded",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        registry = load_registry()
        sites = Sites(args.sites, args)
        if args.command == "install":
            return install(registry, sites)
        if args.command == "report":
            return report(registry, sites)
        if args.command == "check":
            return check(registry, sites)
        if args.command == "link":
            return link(registry, sites, args.name)
        return adopt(
            registry, sites, args.name, args.source, args.why,
            args.backup_dir, args.dry_run, args.defer,
        )
    except SharedSkillsError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
