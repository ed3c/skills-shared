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
  merge    fold every version of one skill into canonical as a union, not a vote

Exit codes: 0 clean, 1 a rule is violated, 3 nothing ruled yet / nothing to do.
"""

from __future__ import annotations

import argparse
import difflib
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
# Superseded content is moved here rather than removed, so `adopt` and `merge`
# have to agree on where it lands or a recovery would go looking in one of two
# places with no way to know which.
DEFAULT_BACKUP = Path(os.environ.get("TMPDIR", "/tmp")) / "shared-skills-superseded"
NOTHING_TO_DO = 3


class SharedSkillsError(RuntimeError):
    """Raised when the shared-skills invariant cannot be established."""


class NothingToDo(SharedSkillsError):
    """Raised when the request was well formed but there was nothing to do.

    Kept distinct from its parent because collapsing the two makes a tool that
    found nothing indistinguishable from a tool that refused, and a caller that
    cannot tell those apart has to guess whether a red run means broken or empty.
    """


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


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


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


# --------------------------------------------------------------------------
# union merge: the one verb that must never choose
# --------------------------------------------------------------------------

Version = tuple[str, Path]


def _source_label(index: int) -> str:
    """A, B, C ... so a two-sided diff can be named the way a human reads one."""
    return chr(ord("A") + index) if index < 26 else f"S{index + 1}"


def _resolve_sources(paths: list[Path], destination: Path) -> list[Version]:
    """Label every distinct version, with the destination always among them.

    Two `--from` paths that resolve to the same directory are one version, not
    two: a surface symlink aimed at another source is the same lineage seen
    twice, and counting one lineage twice is exactly what made the first
    convergence attempt believe it had a majority. The destination joins the
    list even when nobody passed it, because a file it already holds has to be
    compared against the incoming ones -- otherwise a same-named file from
    somewhere else would overwrite it with no diff and no ruling.
    """
    versions: list[Version] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if not resolved.is_dir():
            raise SharedSkillsError(f"source is not a directory: {path}")
        if resolved in seen:
            continue
        seen.add(resolved)
        versions.append((_source_label(len(versions)), resolved))
    if destination.is_dir() and destination.resolve() not in seen:
        versions.append((_source_label(len(versions)), destination.resolve()))
    if len(versions) < 2:
        lone = versions[0][1] if versions else destination
        raise NothingToDo(
            f"nothing to fold: every path names the same single version ({lone}), and "
            f"folding one version into itself changes nothing. A lone version going "
            f"somewhere nothing exists yet is `adopt <name> --from <path> --why ...`, "
            f"which also registers it; to merge, pass a second, genuinely different version"
        )
    return versions


def _inventory(sources: list[Version]) -> dict[str, list[Version]]:
    """Every relative path any version carries, with the versions carrying it."""
    inventory: dict[str, list[Version]] = {}
    for label, root in sources:
        for file in content_files(root):
            inventory.setdefault(file.relative_to(root).as_posix(), []).append((label, file))
    return inventory


def _refuse_type_clash(inventory: dict[str, list[Version]]) -> None:
    """Refuse a union that would need one name to be a file and a directory at once.

    A fork that turned `modules` into `modules/` is exactly the divergence this
    verb exists to fold, but no directory tree can hold both spellings, and
    discovering that halfway through the copy raised a bare FileExistsError and
    left a half-built staging directory behind -- which then blocked every retry
    of that name until a human moved it aside. Say it before anything is
    written, and name the rename that unblocks it.
    """
    held = set(inventory)
    for relpath in sorted(held):
        parts = relpath.split("/")
        for depth in range(1, len(parts)):
            prefix = "/".join(parts[:depth])
            if prefix not in held:
                continue
            as_file = ", ".join(label for label, _ in inventory[prefix])
            as_dir = ", ".join(label for label, _ in inventory[relpath])
            raise SharedSkillsError(
                f"versions disagree about what '{prefix}' is: {as_file} keep it as a file, "
                f"{as_dir} keep '{relpath}' inside it as a directory. No union can hold both "
                f"and nothing was written -- rename one side in its own version (say to "
                f"'{prefix}.md'), then merge again"
            )


def _symlinked_dirs(root: Path) -> list[Path]:
    """Every directory symlink inside a version, named without following one.

    Deliberately `os.walk`, never `rglob`: rglob's refusal to descend a
    directory symlink is the exact behaviour being audited here, so auditing it
    with itself would reproduce the blind spot instead of finding it. os.walk
    lists a symlinked directory in `dirnames` (is_dir follows the link) while
    followlinks=False stops it from descending -- which is precisely "name it,
    do not enter it". __pycache__ is pruned so the two walkers agree on scope:
    the union never carries it, so a link to one loses nothing.
    """
    found: list[Path] = []
    for parent, dirnames, _ in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if name != "__pycache__"]
        for name in sorted(dirnames):
            entry = Path(parent) / name
            if entry.is_symlink():
                found.append(entry)
    return found


def _refuse_symlinked_dirs(sources: list[Version]) -> None:
    """Refuse a version whose subtree hangs off a directory symlink.

    The union walk starts at the version root and does not descend one, so
    every file under the link is absent from the union -- while
    `_uncarried_dirs` starts its walk AT the link, does descend, finds the
    directory full and therefore says nothing. Two walkers disagreeing about
    one tree, and the disagreement was silent: the subtree vanished under exit
    0 with no NOTE, no CONFLICT and no FAIL. That is the shape of loss this
    verb exists to prevent, reached through the one thing it never inspected.

    Refusing is the ruling, rather than following the link, because following
    it is itself a ruling this verb has no standing to make. Carrying the link
    would write a machine-specific path into a versioned canonical that every
    project reaches by symlink -- the one thing this checkout refuses to
    version. Carrying the target's files would quietly turn a link into a copy,
    so the next merge of the same pair would find the copy and the link's target
    standing as two versions that now have to be diffed. Name it, write nothing,
    and say which edit unblocks it.
    """
    for label, root in sources:
        for entry in _symlinked_dirs(root):
            raise SharedSkillsError(
                f"{label} reaches '{entry.relative_to(root).as_posix()}' through a directory "
                f"symlink -> {os.readlink(entry)}, and the union walk does not descend one, so "
                f"every file under it would be dropped without a word. Nothing was written -- "
                f"replace the link with a real directory in that version (`cp -RL`), or pass a "
                f"version that already holds those files directly, then merge again"
            )


def _uncarried_dirs(sources: list[Version]) -> list[str]:
    """Name every directory the union will not carry, because it holds no file.

    The union is over files: git cannot record an empty directory, so promoting
    one would promise canonical something the next clone silently drops. A
    version's directory vanishing under exit 0 is the shape of loss this verb
    exists to prevent, so it is reported even though it is not a failure.
    """
    notices: list[str] = []
    for label, root in sources:
        for entry in sorted(root.rglob("*")):
            if not entry.is_dir() or "__pycache__" in entry.parts:
                continue
            if content_files(entry):
                continue
            notices.append(
                f"NOTE    {entry.relative_to(root).as_posix()}/ is an empty directory in "
                f"{label}; the union is over files, so it is not carried (git cannot "
                f"record an empty directory either)"
            )
    return notices


def _classify(
    inventory: dict[str, list[Version]]
) -> tuple[dict[str, Version], dict[str, list[Version]]]:
    """Split into what the union takes and what only a human can settle.

    Agreement is decided by bytes, never by how many versions hold the file: one
    version holding a file is enough to keep it, and a file three versions agree
    on is the same single file. Counting would reintroduce the vote.
    """
    take: dict[str, Version] = {}
    conflicts: dict[str, list[Version]] = {}
    for relpath, versions in sorted(inventory.items()):
        if len({file_digest(file) for _, file in versions}) == 1:
            take[relpath] = versions[0]
        else:
            conflicts[relpath] = versions
    return take, conflicts


def _diff_lines(left: Version, right: Version, relpath: str) -> list[str]:
    """A hunk-by-hunk diff of two versions of one file, or an honest refusal.

    Binary content has no readable diff, and printing a decoded approximation of
    it would let someone rule on a file they never actually saw.
    """
    try:
        before = left[1].read_text(encoding="utf-8").splitlines(keepends=True)
        after = right[1].read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return [f"      (binary content: {left[0]} and {right[0]} differ, no readable diff)"]
    hunks = difflib.unified_diff(
        before, after,
        fromfile=f"{left[0]} {relpath}", tofile=f"{right[0]} {relpath}",
    )
    return [f"      {line.rstrip(chr(10))}" for line in hunks]


def _conflict_report(relpath: str, versions: list[Version]) -> list[str]:
    """Name both sides with their size, digest and path, then show the diff."""
    lines = [f"CONFLICT {relpath} ({len(versions)} versions disagree)"]
    for label, file in versions:
        lines.append(
            f"      {label}  {file.stat().st_size:>8d} bytes  {file_digest(file)}  {file}"
        )
    for right in versions[1:]:
        lines.extend(_diff_lines(versions[0], right, relpath))
    return lines


def _verify_union(
    built: Path, sources: list[Path], destination: Path, reported: set[str]
) -> list[str]:
    """Recount from what the caller named, never from the merge plan.

    The one guarantee this verb sells -- a file that only one version carries
    survives -- has to be checked against a fresh walk, resolved here rather
    than handed over by the planner. Taking the planner's already-parsed version
    list would make this blind to every defect in the parse itself: a planner
    that dropped a `--from` before it ever looked at it would be checked against
    the shortened list it invented, so the union could shrink and still report
    success. That is the exact failure that lost a module to the majority vote,
    so the recount starts from argv and resolves the paths a second time.
    """
    counted: dict[str, list[Version]] = {}
    seen: set[Path] = set()
    failures: list[str] = []
    for path in [*sources, destination]:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        if not resolved.is_dir():
            if resolved == destination.resolve():
                continue        # no incumbent canonical: it carries nothing to recount
            raise SharedSkillsError(
                f"cannot verify the union: {path} is no longer a directory, so what it "
                f"carried can no longer be counted; the staged union is at {built} -- "
                f"restore the source and merge again"
            )
        seen.add(resolved)
        label = _source_label(len(seen) - 1)
        # Audited here as well as before the copy, and with a walker that is not
        # content_files: every count below is content_files' own answer, so a
        # defect in the enumeration layer is invisible to a recount built on it.
        # A tree this walk cannot reach is not a small union, it is a wrong one.
        for entry in _symlinked_dirs(resolved):
            failures.append(
                f"UNWALKED {entry.relative_to(resolved).as_posix()}: {label} reaches it through "
                f"a directory symlink, which the file walk does not descend, so whatever it "
                f"holds is absent from the union and no count here would have missed it"
            )
        for file in content_files(resolved):
            counted.setdefault(file.relative_to(resolved).as_posix(), []).append((label, file))
    for relpath, versions in sorted(counted.items()):
        target = built / relpath
        if len({file_digest(file) for _, file in versions}) > 1:
            if relpath not in reported:
                failures.append(
                    f"UNREPORTED {relpath}: versions disagree but no ruling was surfaced"
                )
            continue
        held_by = ", ".join(label for label, _ in versions)
        if not target.is_file():
            failures.append(f"DROPPED {relpath}: held by {held_by} but missing from {built}")
        elif target.read_bytes() != versions[0][1].read_bytes():
            failures.append(f"ALTERED {relpath}: does not match the bytes {held_by} carry")
    return failures


def _unused_path(candidate: Path) -> Path:
    """Two merges on one day are two records; the second must not land on the first."""
    attempt, suffix = candidate, 2
    while attempt.exists():
        attempt = candidate.with_name(f"{candidate.name}-{suffix}")
        suffix += 1
    return attempt


def merge(
    registry: dict[str, Any],
    name: str,
    sources: list[Path],
    backup_root: Path,
    dry_run: bool,
) -> int:
    """Fold every version of one skill into canonical as a union, not a vote.

    The rule: a file only one version carries survives, unconditionally. The
    first convergence attempt picked a winner by content hash and lost whole
    modules that way -- and its majority was an illusion, because two of the
    three versions were batch imports of a single lineage. A union cannot be
    fooled by a miscounted vote, so this verb refuses to be a chooser at all.

    Files whose bytes disagree are never resolved here: the report names both
    sides and stops with `nothing ruled yet`, because deciding between two
    authored paragraphs is a human's call and a tool that guessed would be the
    same mistake wearing a different rule. Versions may be partial trees -- a
    superseded backup is a legitimate one -- so no version needs a SKILL.md.
    """
    destination = canonical_path(registry, name)
    versions = _resolve_sources(sources, destination)
    _refuse_symlinked_dirs(versions)
    inventory = _inventory(versions)
    _refuse_type_clash(inventory)
    take, conflicts = _classify(inventory)
    solo = sum(1 for holders in inventory.values() if len(holders) == 1)
    notices = _uncarried_dirs(versions)

    if dry_run:
        print(f"DRY-RUN merge {name} -> {destination}")
        for label, root in versions:
            print(f"        {label}  {root}  ({len(content_files(root))} files)")
        print(f"        take   {len(take)} files, {solo} of them held by one version only")
        print(f"        rule   {len(conflicts)} files need a human ruling")
        for notice in notices:
            print(notice)
        for relpath, holders in conflicts.items():
            for line in _conflict_report(relpath, holders):
                print(line)
        return NOTHING_TO_DO if conflicts else 0

    # A union with nothing in it is not a union. Promoting one would create a
    # skill directory that exists and holds no file, which downstream reads as a
    # finished merge, and it would do that while every single file was still
    # waiting on a human. Report and stop before anything is built, so no
    # staging directory is left to block the retry that follows the ruling.
    carried = [relpath for relpath in conflicts if (destination / relpath).is_file()]
    if not take and not carried:
        for notice in notices:
            print(notice)
        for relpath, holders in conflicts.items():
            for line in _conflict_report(relpath, holders):
                print(line)
        print(
            f"UNRESOLVED {len(conflicts)} files need a human ruling; none was auto-selected, "
            f"so the union would be empty and {destination} was left untouched"
        )
        return NOTHING_TO_DO

    # The union is built beside the destination and only moved into place once
    # it verifies. Building in place would leave a half-merged canonical behind
    # on failure, and since nothing here is ever deleted, that wreckage would be
    # indistinguishable from a finished merge to everything downstream.
    staging = destination.parent / f".{name}.merging"
    if staging.exists():
        raise SharedSkillsError(f"an earlier merge left {staging} behind; move it aside and retry")
    # No explicit mkdir: every path that reaches here copies at least one file,
    # and each copy makes its own parents. The one case that took nothing at all
    # returned above, precisely so that an empty directory can never be built.

    added: list[str] = []
    for relpath, (label, chosen) in take.items():
        target = staging / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(chosen, target)
        if not (destination / relpath).is_file():
            added.append(f"ADDED   {relpath:52s} <- {label}")
    for relpath in conflicts:
        standing = destination / relpath
        if not standing.is_file():
            continue        # no incumbent to carry, and picking a side is not ours
        # Carrying the destination's own bytes forward is the status quo, not a
        # ruling: leaving it out would delete an unresolved file by omission.
        target = staging / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(standing, target)

    failures = _verify_union(staging, sources, destination, set(conflicts))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        print(
            f"FAIL merge {name} is incomplete and was not promoted: {destination} is untouched "
            f"and the partial union is at {staging}",
            file=sys.stderr,
        )
        return 1

    if destination.is_dir():
        snapshot = _unused_path(backup_root / name / f"pre-merge-{date.today().isoformat()}")
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destination), str(snapshot))
        print(f"SUPERSEDED {destination} -> {snapshot}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staging), str(destination))
    for line in added:
        print(line)
    for notice in notices:
        print(notice)
    print(
        f"UNION   {destination}: {len(content_files(destination))} files from "
        f"{len(versions)} versions, {solo} of them held by one version only"
    )
    for relpath, holders in conflicts.items():
        for line in _conflict_report(relpath, holders):
            print(line)
    if conflicts:
        print(f"UNRESOLVED {len(conflicts)} files need a human ruling; none was auto-selected")
        return NOTHING_TO_DO
    return 0


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
    adopt_parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP)
    # merge takes no surface flags on purpose: it folds directories named on the
    # command line into this checkout and never touches a machine's wiring, so
    # asking it for a sites file would imply a coupling it does not have.
    merge_parser = commands.add_parser(
        "merge", help="union every version of a skill; never drops a file"
    )
    merge_parser.add_argument("name")
    merge_parser.add_argument(
        "--from", dest="sources", action="append", required=True, type=Path,
        help="repeatable; a directory holding one version of this skill",
    )
    merge_parser.add_argument("--dry-run", action="store_true")
    merge_parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        registry = load_registry()
        if args.command == "merge":
            return merge(registry, args.name, args.sources, args.backup_dir, args.dry_run)
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
    except NothingToDo as error:
        # Deliberately not FAIL/1: there was nothing to act on, and a caller that
        # sees the refusal code for an empty request will go looking for a broken
        # rule that does not exist. Must be caught before its parent class.
        print(f"NOTHING {error}", file=sys.stderr)
        return NOTHING_TO_DO
    except SharedSkillsError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
