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
  bind     record that a repo retargeted a shared body, pinned to that body

Exit codes: 0 clean, 1 a rule is violated, 3 nothing ruled yet / nothing to do
-- which is where a stale binding lands: it is owed work, not a broken thing.
`install` ends with `check` and returns its code verbatim, 3 included: wiring
that reports success while the gate would not is the silent state again.
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
# A binding is a directory, not a file, because a retarget produces several
# records at once: the retarget ledger, the legacy snapshot it replaced, that
# repo's own panorama. Only `binding.md` is contractual; the rest is free.
BINDING_DIR = ".skill-bindings"
BINDING_FILE = "binding.md"
BINDING_FIELDS = ("skill", "upstream", "retargeted_at", "body_version")


class SharedSkillsError(RuntimeError):
    """Raised when the shared-skills invariant cannot be established."""


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
# bindings: which shared body a repo retargeted, and whether that body moved
# --------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, str | None]:
    """Split a `--- key: value --- rest` document. Stdlib only, so no YAML: the
    four fields are flat strings and a real parser would be a dependency bought
    for nothing.

    The third element is None for a well-formed block, else a sentence naming
    what is wrong with the block itself. Without it a caller can only report the
    fields it failed to see, so a file carrying all four fields under an unclosed
    `---` gets diagnosed as missing all four -- a verdict nobody can act on,
    because every field it names is sitting right there.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text, "has no `---` frontmatter block at the top"
    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "".join(lines[index + 1:]), None
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return {}, text, "opens a `---` frontmatter block that never closes"


def binding_record_state(binding: Path, name: str, body_version: str) -> tuple[str, str]:
    """Classify one binding *file*: (state, detail). Never returns "absent" --
    the file was named, so it either reads as a record or it does not.

    Split out from `binding_state` so a candidate record can be judged before it
    becomes the record: `bind` validates what it staged through this same
    function, rather than through a second copy of the rules that could drift
    from the one the gate actually runs.
    """
    if not binding.is_file():
        return "incomplete", f"{binding.parent} has no {BINDING_FILE}"
    try:
        text = binding.read_text(encoding="utf-8")
    except OSError as error:
        return "incomplete", f"{binding} is unreadable: {error}"
    fields, _, malformed = parse_frontmatter(text)
    if malformed:
        return "incomplete", (
            f"{binding} {malformed} -- the four fields have to sit inside a closed block "
            f"for anything to read them"
        )
    missing = [field for field in BINDING_FIELDS if not fields.get(field)]
    if missing:
        return "incomplete", f"{binding} lacks {', '.join(missing)}"
    if fields["skill"] != name:
        # Bindings get copied between repos, and a copy that keeps the original
        # `skill:` is exactly how a record becomes false in place: the slot says
        # one thing, the record another, and the hash it pins belongs to neither.
        return "incomplete", (
            f"{binding} declares skill: {fields['skill']} while sitting in the slot for {name}"
        )
    if fields["body_version"] != body_version:
        return "stale", (
            f"{binding} pins body_version {fields['body_version']}, body is now {body_version}"
        )
    return "current", ""


def binding_state(project: Path, name: str, body_version: str) -> tuple[str, str]:
    """Classify one repo's binding for one shared skill: (state, detail).

    The three states have to stay apart all the way to the exit code. Absence
    means this repo never retargeted and uses the shared body's generic form --
    a legitimate resting state, so calling it broken would leave most repos
    permanently red. Stale means the body moved since the retarget: owed work,
    surfaced, not failed. Incomplete means the record itself no longer says what
    it was pinned to, and no amount of re-running fixes that.
    """
    slot = project / BINDING_DIR / name
    if not slot.is_dir():
        return "absent", ""
    return binding_record_state(slot / BINDING_FILE, name, body_version)


def orphan_bindings(registry: dict[str, Any], projects: list[Path]) -> list[str]:
    """Binding slots naming a skill this registry does not know.

    `check` walks the registry, so a slot whose name was renamed out of it -- or
    dropped from it -- is never opened again. Every subscriber's ledger for that
    name goes quiet at once, and the last thing anybody saw was a PASS.
    """
    known = {item["name"] for item in registry["shared"]}
    orphans: list[str] = []
    for project in projects:
        root = project / BINDING_DIR
        if not root.is_dir():
            continue
        for slot in sorted(root.iterdir()):
            if slot.name.startswith(".") or not slot.is_dir() or slot.name in known:
                continue
            orphans.append(
                f"ORPHAN-BINDING {slot}: no shared skill named {slot.name} is registered -- "
                f"rename the slot to the name it is bound to now, or move it aside"
            )
    return orphans


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------


def install(registry: dict[str, Any], sites: Sites) -> int:
    """Wire a fresh clone to this machine, then link every shared skill.

    Ends with `check` and returns its code unchanged, 3 included -- a stale
    binding or an uncloned project makes the wiring incomplete, and an `install`
    that reported 0 over a gate saying otherwise would be the silent state this
    tool exists to end.
    """
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
    """T0 gate. Fails only on ruled violations, never on unruled duplicates, and
    never on a binding that merely fell behind: that one is surfaced instead."""
    failures: list[str] = []
    surfaced: list[str] = []
    # "incomplete" is counted but not printed in the tally: it already shows up
    # as a FAIL line, and a broken record is not a population to keep score of.
    tally = {"current": 0, "stale": 0, "absent": 0, "incomplete": 0}
    found = scan(sites)
    # A governed repo that is not on disk cannot be asked the binding question at
    # all, so its bindings leave the tally. Dropping it quietly would make "I
    # could not look" read exactly like "I looked and it was clean" -- and
    # `install` prints `(not on disk yet)`, so this is a state sites files really
    # reach, not a hypothetical.
    reachable = [project for project in sites.projects if project.is_dir()]
    unreachable = [project for project in sites.projects if not project.is_dir()]
    for project in unreachable:
        surfaced.append(
            f"UNREACHABLE-PROJECT {project}: governed but not on disk, so none of its bindings "
            f"were read -- clone it there, or drop it from {sites.path}"
        )
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
        body_version = digest(canonical)
        for project in reachable:
            # A deferred repo still runs its own copy, so there is no shared body
            # for a binding there to pin: checking one would judge a question the
            # ruling deliberately left open. `bind` refuses to write one for the
            # same reason -- see the refusal there.
            if project.name in deferred:
                continue
            state, detail = binding_state(project, name, body_version)
            tally[state] += 1
            if state == "incomplete":
                failures.append(f"BINDING-INCOMPLETE {name}: {detail}")
            elif state == "stale":
                surfaced.append(
                    f"BINDING-STALE {name}: {detail} -- re-retarget, then "
                    f"`bind {name} --repo {project}`"
                )
    surfaced.extend(orphan_bindings(registry, reachable))
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    for line in surfaced:
        print(f"SURFACE {line}")
    # Printed on every path, because absence is a state and a state nobody counts
    # is indistinguishable from a state nobody checked.
    print(
        f"BINDINGS {tally['current']} current, {tally['stale']} stale, "
        f"{tally['absent']} not retargeted"
    )
    # The population that tally was computed over, for the same reason: a number
    # is only readable next to the size of the set it was counted from.
    print(f"PROJECTS {len(reachable)} on disk, {len(unreachable)} unreachable")
    if failures:
        return 1
    if surfaced:
        return NOTHING_TO_DO
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


BINDING_TEMPLATE = """---
skill: {name}
upstream: {upstream}
retargeted_at: {today}
body_version: {body_version}
---
"""

BINDING_PROSE = """
# {name} — 本 repo 的 binding

共用 body 是通用形態；只在本 repo 為真的東西住這裡：retarget 取捨帳、
指向本 repo 私有文件的指針、被取代的舊版快照。
判準：原封不動搬到另一個 repo，它還為真嗎？為真＝body。

`body_version` 釘的是 retarget 當下的共用 body 內容 hash。body 一動，
`check` 就把本檔列成 BINDING-STALE——那是「該重新 retarget」的清單，
不是壞掉。對齊完跑 `bind` 重釘。
"""


def bind(
    registry: dict[str, Any],
    sites: Sites,
    name: str,
    repo: Path,
    upstream: str | None,
) -> int:
    """Record that this repo retargeted a shared body, pinned to that body.

    Restamping keeps everything below the frontmatter untouched: that prose is
    the retarget ledger, which is the one thing a binding exists to hold. A tool
    that rewrote the whole file would destroy the record while claiming to
    maintain it.

    It refuses rather than papers over: a repo `check` never walks, a repo whose
    copy of this skill was deferred, and an existing record `check` already calls
    broken. Every one of those would end with a record on disk that no gate ever
    confirms -- which is the exact state this whole mechanism exists to end.
    """
    if sites.path.expanduser().resolve() != SITES.resolve():
        # The governed set lives in the sites file, so choosing the file chooses
        # the set: `--sites my-own.json` listing the target repo is the `--project`
        # bypass one step further out, and dropping the `--project` flag alone
        # leaves it wide open. A write may only trust the file the gate reads with
        # no arguments, because that is the set `check` will actually walk.
        raise SharedSkillsError(
            f"{sites.path} is not the sites file `check` reads ({SITES}) -- the governed set a "
            f"write trusts has to be the one the gate later walks, or the binding is a record "
            f"nothing verifies; wire the repo in with `install --project <repo>` and bind again"
        )
    entry = next((item for item in registry["shared"] if item["name"] == name), None)
    if entry is None:
        raise SharedSkillsError(
            f"{name} is not registered as shared -- only a shared body gets bindings"
        )
    canonical = canonical_path(registry, name)
    if not canonical.is_dir():
        raise SharedSkillsError(f"not in the shared repo: {canonical}")
    repo = repo.expanduser().resolve()
    if not repo.is_dir():
        # mkdir(parents=True) below would otherwise conjure the repo itself out
        # of a typo, and a binding in a repo that does not exist is unfindable.
        raise SharedSkillsError(f"no such repo on this machine: {repo}")
    governed = {project.expanduser().resolve() for project in sites.projects}
    if repo not in governed:
        # `check` only walks the wired projects, so a binding anywhere else is a
        # record nothing ever verifies -- the silent state this gate exists to end.
        raise SharedSkillsError(
            f"{repo} is not a governed project -- add it with `install --project` first"
        )
    if repo.name in set(entry.get("deferred_in", [])):
        # `check` deliberately never reads a deferred repo's bindings: it runs its
        # own copy, so there is no shared body for a record there to pin. Writing
        # one anyway produces precisely the unverified record the refusal above
        # exists to prevent -- the same hole, entered from the other side.
        raise SharedSkillsError(
            f"{name} is deferred in {repo.name}, which runs its own copy -- there is no shared "
            f"body to pin there; settle the defer (`adopt` it, or drop `deferred_in`) first"
        )

    binding = repo / BINDING_DIR / name / BINDING_FILE
    fields: dict[str, str] = {}
    prose = BINDING_PROSE.format(name=name)
    if binding.is_file():
        # Restamping a record `check` calls broken would clear that FAIL without
        # anyone reading the file, and inherit an `upstream` line that may belong
        # to whichever repo the record was copied from. A false provenance that
        # passes is worse than a failure that stops you.
        existing_state, existing_detail = binding_state(repo, name, digest(canonical))
        if existing_state == "incomplete":
            raise SharedSkillsError(
                f"{binding} is broken, not merely stale: {existing_detail} -- `bind` restamps a "
                f"record, it never repairs one; fix the file by hand, or move it aside and bind "
                f"again with --upstream to start a fresh record"
            )
        fields, prose, _ = parse_frontmatter(binding.read_text(encoding="utf-8"))
    upstream = upstream or fields.get("upstream")
    if not upstream:
        raise SharedSkillsError(
            "a new binding needs --upstream: which upstream this repo retargeted from"
        )
    body_version = digest(canonical)
    binding.parent.mkdir(parents=True, exist_ok=True)
    # Stage, judge the bytes that actually landed, then swap in one atomic step.
    # Writing binding.md first and asserting afterwards means every refusal has
    # already destroyed the record it refused to write: an `upstream` carrying a
    # `---` line closes the frontmatter early, so the file loses two fields and
    # the assertion fires over a ledger that is already gone. A record this tool
    # declines to write must not exist on disk in any form -- including a staged
    # one, which would sit in the slot as a second record no gate ever reads.
    staged = binding.with_name(f".{BINDING_FILE}.staged")
    staged.write_text(
        BINDING_TEMPLATE.format(
            name=name,
            upstream=upstream,
            today=date.today().isoformat(),
            body_version=body_version,
        )
        + prose,
        encoding="utf-8",
    )
    state, detail = binding_record_state(staged, name, body_version)
    if state != "current":
        staged.unlink()
        raise SharedSkillsError(
            f"refusing to write a binding that would not read back as current ({state}): "
            f"{detail} -- the frontmatter is flat `key: value` lines, so a field carrying a "
            f"newline or a `---` ends the block early; {binding} is untouched"
        )
    os.replace(staged, binding)
    # Assert the state the message is about to claim, now from the real path: a
    # stamp that does not read back as current would be a green line over a
    # binding `check` still surfaces.
    state, detail = binding_state(repo, name, body_version)
    if state != "current":
        raise SharedSkillsError(f"binding did not take ({state}): {detail or binding}")
    print(f"BOUND   {binding} -> body_version {body_version}")
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
    adopt_parser.add_argument(
        "--backup-dir", type=Path,
        default=Path(os.environ.get("TMPDIR", "/tmp")) / "shared-skills-superseded",
    )
    # `bind` deliberately gets no --project/--surface flags. `Sites` lets a
    # --project flag replace the governed set outright, so accepting one here
    # would let the writer declare its own target governed and walk straight
    # through the refusal in `bind`. The governed set a write trusts has to be
    # the persisted one `check` will later walk, not one invented per command.
    # --sites survives only because the tests need a synthetic world; it is the
    # same door one step further out, so `bind` refuses any path but the default.
    bind_parser = commands.add_parser("bind", help="pin a repo's binding to the body")
    bind_parser.add_argument("name")
    bind_parser.add_argument(
        "--sites", type=Path, default=SITES,
        help=f"must be {SITES}: the governed set a write trusts is the one `check` reads",
    )
    bind_parser.add_argument(
        "--repo", required=True, type=Path, help="the governed repo that retargeted",
    )
    bind_parser.add_argument(
        "--upstream", help="what this repo retargeted from; remembered on restamp",
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
        if args.command == "bind":
            return bind(registry, sites, args.name, args.repo, args.upstream)
        return adopt(
            registry, sites, args.name, args.source, args.why,
            args.backup_dir, args.dry_run, args.defer,
        )
    except SharedSkillsError as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
