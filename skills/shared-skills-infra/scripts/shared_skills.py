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
  check    zero-network gate: no shared skill is shadowed, unlinked, or -- once
           its body has been migrated -- bound to one repo (T0)
  link     materialize a shared skill's user-level symlinks (idempotent)
  adopt    move a project's copy in and register it as shared (moves, never deletes)

Exit codes: 0 clean, 1 a ruling is violated, 3 nothing ruled yet / nothing to
do, 4 the input cannot be judged at all. Four codes rather than three because
"I could not tell" and "I checked, and it is fine" must never be the same
answer -- and neither may collapse into "somebody still has to rule on this".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

REPO = Path(__file__).resolve().parents[3]
REGISTRY = REPO / "registry.json"
SITES = REPO / "sites.local.json"
DEFAULT_CODEX_SURFACE = Path.home() / ".agents" / "skills"
DEFAULT_CLAUDE_SURFACE = Path.home() / ".claude" / "skills"
NOTHING_TO_DO = 3
# Not 2: argparse spends 2 on usage errors, and "you typed the command wrong"
# is a different fact from "I read your registry and refuse to judge it".
CANNOT_EVALUATE = 4


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
    for field in ("shared", "repo_owned"):
        entries = data[field]
        if not isinstance(entries, list):
            raise SharedSkillsError(f"registry '{field}' must be a list of entries")
        for position, item in enumerate(entries):
            # Every verb dereferences the name, so an entry without one cannot
            # be reported against, deferred or skipped -- it can only crash. A
            # sentence saying which entry and what to write beats a KeyError
            # traceback that names neither.
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
                raise SharedSkillsError(
                    f"registry '{field}'[{position}] has no usable name -- give it "
                    f'"name": "<skill-directory>" before anything can be said about it'
                )
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
# body neutrality: what survives being copied into the next repo
# --------------------------------------------------------------------------

# The five repos this checkout serves, plus the two absolute-path forms. A
# shared body that names one of them is binding wearing body's clothes: copied
# verbatim into the next repo the sentence becomes false in place, and nothing
# reports it, because prose has no gate of its own -- which is how fourteen
# retarget maps ended up all claiming one repo's lineage while serving five.
# This tuple is the gate's whole jurisdiction, so tests/verify.sh pins it
# literally: widening or narrowing it moves the migration's recorded baseline,
# and that is a ruling somebody makes, never a diff that slips through.
BINDING_REPOS = ("ts-skill-bettor", "skill-bettor", "bettor-arena", "antigravity", "ix-agy")
BINDING_PATHS = ("~/", "/Users/")
SCOPES = ("shared", "private")
# Keys a shared entry may carry. Anything else is a typo, and a typo is worse
# than an unknown value: `body_netural: true` reads as an absent ruling, so a
# body somebody already migrated would sit in the queue forever with nobody
# able to see why.
SHARED_ENTRY_KEYS = frozenset({"name", "admitted", "why", "scope", "body_neutral", "deferred_in"})


def binding_pattern(tokens: tuple[str, ...]) -> re.Pattern[str]:
    """One pattern over the tokens, longest first.

    Alternation is first-match-wins at each scan position, so a token that
    prefixes another *at that same position* silently shadows it: with `bettor`
    in the set, `bettor-arena` gets reported as `bettor` and whoever works the
    queue is sent to a repo that is not the one bound. Sorting by length makes
    that impossible for any token set -- which is why the order the tuples above
    are written in carries no meaning and must not be relied on. Equal-length
    ties break alphabetically rather than by input order: two tokens of the same
    length cannot shadow each other, but leaving the tie to the caller would
    leave one pattern per way of writing the tuple, and "order is inert" would
    become a claim nobody can check.
    """
    longest_first = sorted(tokens, key=lambda token: (-len(token), token))
    return re.compile("|".join(re.escape(token) for token in longest_first))


BINDING = binding_pattern(BINDING_REPOS + BINDING_PATHS)


class BodyHit(NamedTuple):
    """One body line that only stays true in one repo, and what makes it so."""

    file: str                   # relative to this checkout, so it is quotable anywhere
    line: int
    tokens: tuple[str, ...]     # every distinct binding token on that line, leftmost first


def scope_of(item: dict[str, Any]) -> str:
    """Shared unless ruled private.

    A private skill is bound to its owner by construction -- neutralising it
    would be ritual, not portability -- so the rule that forbids repo names
    applies to shared bodies only. Whether the value is one this tool knows is
    `entry_refusals`' question, asked before this is read.
    """
    return item.get("scope", "shared")


def entry_refusals(item: dict[str, Any]) -> list[str]:
    """Everything about one shared entry that makes it unjudgeable, as sentences.

    Returned instead of raised, on purpose. Raising from inside `check`'s loop
    threw away every violation the loop had already found, so one misspelt
    value in an unrelated entry could hide a genuine shadowing copy -- the gate
    would print a single configuration complaint and exit, and the two real
    failures behind it were never printed at all.
    """
    name = item["name"]
    problems: list[str] = []
    unknown = sorted(set(item) - SHARED_ENTRY_KEYS)
    if unknown:
        problems.append(
            f"{name}: unrecognised registry key(s) {', '.join(repr(k) for k in unknown)} -- "
            f"fix the spelling or delete them; a shared entry carries only "
            f"{', '.join(sorted(SHARED_ENTRY_KEYS))}"
        )
    scope = item.get("scope", "shared")
    if scope not in SCOPES:
        # Guessing would silently exempt a shared body from the one rule that
        # keeps it shared, so an unrecognised value is refused, not defaulted.
        problems.append(
            f"{name}: unknown scope {scope!r} -- set it to one of {', '.join(SCOPES)}, or "
            f"drop the key to take the default 'shared'"
        )
    if "body_neutral" in item and not isinstance(item["body_neutral"], bool):
        problems.append(
            f"{name}: body_neutral is {item['body_neutral']!r} -- it is a ruling, so write "
            f"true (migrated, enforce it) or false (not migrated, queue it), not a string"
        )
    return problems


def body_hits(skill: Path) -> list[BodyHit]:
    """Every Markdown line of a skill body that names a repo or an absolute path.

    Markdown only, on purpose: the migration's recorded baseline is counted
    over prose bodies, so widening the file set here would silently move the
    number the burn-down is measured against. Sorted, so the same tree always
    produces the same report -- a baseline that shuffles is not a baseline.
    """
    hits: list[BodyHit] = []
    for file in sorted(skill.rglob("*.md")):
        try:
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            # A body nobody can read cannot be shown to be neutral, and
            # counting it clean is how a gate degrades into decoration. The
            # caller turns this into a refusal, not a violation: nothing here
            # is proven broken, it is proven unjudgeable.
            raise SharedSkillsError(
                f"unreadable body: {file}: {error} -- re-save it as UTF-8 or move it out of "
                f"the skill; a body nobody can read cannot be shown to be neutral"
            ) from error
        for number, line in enumerate(text.splitlines(), start=1):
            tokens = tuple(dict.fromkeys(BINDING.findall(line)))
            if tokens:
                hits.append(BodyHit(os.path.relpath(file, REPO), number, tokens))
    return hits


def _print_queue(queue: list[tuple[str, list[BodyHit]]]) -> None:
    """Print the not-yet-migrated bodies as a measurement, not as an alarm.

    A line can bind through both a repo name and an absolute path, so the two
    subtotals overlap by design: each is the count grep gives for that rule on
    its own, which is what makes the baseline in the issue reproducible.
    """
    hits = [hit for _, skill_hits in queue for hit in skill_hits]

    def tally(rule: tuple[str, ...]) -> str:
        matched = [hit for hit in hits if any(token in rule for token in hit.tokens)]
        return f"{len(matched)} lines/{len({hit.file for hit in matched})} files"

    print(
        f"SURFACE BODY-NOT-NEUTRAL {len(hits)} lines in {len({h.file for h in hits})} files "
        f"still bind the shared body to one repo "
        f"(repo names {tally(BINDING_REPOS)}, absolute paths {tally(BINDING_PATHS)})"
    )
    for name, skill_hits in queue:
        first = skill_hits[0]
        print(
            f"        {name:34s} {len(skill_hits)} lines in "
            f"{len({h.file for h in skill_hits})} files  first: {first.file}:{first.line}"
        )
    print(
        '        Nobody has ruled these yet, so they are the migration queue, not a '
        'violation: a body enters the gate when its entry gains "body_neutral": true.'
    )


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------


def install(registry: dict[str, Any], sites: Sites) -> int:
    """Wire a fresh clone to this machine, then link every shared skill.

    Exits on install's own question -- is this machine wired? -- not on the
    migration's. `install` always writes the sites file and always links, so it
    never has nothing to do; inheriting `check`'s exit 3 would make the first
    documented step of a fresh clone look like a failure and stop every
    `set -e` caller on a queue that belongs to somebody else. A violation or a
    refusal still comes straight through: those say the wiring did not take.
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
    status = check(registry, sites)
    return 0 if status == NOTHING_TO_DO else status


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
    """T0 gate. Fails only on ruled violations, never on unruled duplicates.

    Three states are kept apart in the output and in the exit code: a ruling
    that is violated (1), a ruling nobody has made yet (3), and an entry that
    cannot be judged at all (4). Every one of them is accumulated rather than
    thrown, so no single bad entry can decide what the rest of the tree is
    allowed to report.
    """
    failures: list[str] = []
    refusals: list[str] = []
    queue: list[tuple[str, list[BodyHit]]] = []
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
        # Asked after the symlink facts, which hold regardless of how the entry
        # is spelled: a malformed entry must not be able to hide even its own
        # shadowing, let alone anybody else's.
        problems = entry_refusals(item)
        if problems:
            refusals.extend(problems)
            continue
        if scope_of(item) == "private":
            continue
        try:
            hits = body_hits(canonical)
        except SharedSkillsError as error:
            refusals.append(str(error))
            continue
        if not hits:
            continue
        if item.get("body_neutral"):
            failures.extend(
                f"BODY-NOT-NEUTRAL {name}: {hit.file}:{hit.line} names "
                f"{', '.join(f'`{token}`' for token in hit.tokens)} -- copied verbatim into "
                f"another repo this line stops being true, so it belongs in that repo's "
                f"binding, not in the shared body"
                for hit in hits
            )
        else:
            # Enforcement is opt-in per skill because most bodies have not been
            # migrated yet: switching the rule on everywhere at once would make
            # the gate red for work nobody has started, and a gate that is
            # always red stops being read at all.
            queue.append((name, hits))
    if queue:
        _print_queue(queue)
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    for refusal in refusals:
        # A word of its own, because "FAIL" would file an unanswerable question
        # under the same heading as an answered one.
        print(f"REFUSE {refusal}", file=sys.stderr)
    if failures:
        return 1
    if refusals:
        # Above the queue and below a violation: nothing here is proven broken,
        # but part of the tree was never judged, and a caller reading only the
        # exit code must not be told it came back clean.
        return CANNOT_EVALUATE
    held = f"PASS shared skills hold ({len(registry['shared'])} registered)"
    if queue:
        # Not zero: an unmigrated body is an open question, and reporting it as
        # clean would hide the queue from every caller that only reads the exit
        # code. Not one either: nothing here is broken.
        print(f"{held}; {len(queue)} bodies queued for neutralization")
        return NOTHING_TO_DO
    print(held)
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
        # Every one of these means the same thing: the invariant could not be
        # established from what was handed in. That is a refusal, not a verdict
        # -- reporting it as 1 would claim a rule was checked and broken, and
        # reporting it as 3 would claim somebody merely has yet to decide.
        print(f"REFUSE {error}", file=sys.stderr)
        return CANNOT_EVALUATE


if __name__ == "__main__":
    raise SystemExit(main())
