#!/usr/bin/env python3
"""Central home for every managed CLAUDE.md / AGENTS.md, with drift as a red light.

`agent-docs/<key>/<file>` is the single source; the copy inside the repo (or the
host home) is a projection of it. Nothing here compares meaning -- only bytes --
because "these two say the same thing" is exactly the judgement that quietly goes
wrong. ts-skill-bettor and skill-bettor had already diverged on 2026-08-08 (the
big-loop orchestrator role differs, and one still carried eight design rules that
had been ruled into the global file); both files were valid markdown, both were
loaded by their host, and nothing anywhere said a word. `check` is that word.

Three outcomes that must never collapse into each other:
  * managed + identical            -> OK, named
  * managed + differing/missing    -> DRIFT / MISSING, named per file
  * registered as absent, or as an unmanaged target -> ABSENT / UNMANAGED, named

A CLAUDE.md or AGENTS.md that appears at a managed target without being in the
manifest is a FAIL, not a shrug: an unregistered doc is already being loaded by
the host, which is a different urgency from one nobody has ruled on yet. That
mirrors `shared_skills.py`'s unregistered-skill check, for the same reason.

Portable the same way registry.json is: the manifest names repos by directory
name only, and machine paths come from sites.local.json.

  check     zero-network gate: every managed doc matches, nothing unregistered
  diff      unified diff for whatever `check` called DRIFT
  apply     write one direction, named explicitly (never inferred)
  import    adopt a target's current files as the source of truth
  selftest  plant defects in a fixture and prove the gate goes red

Exit codes: 0 clean · 1 a managed doc drifted or an unregistered doc appeared · 64 usage.
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
SHARED_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = SKILL / "agent-docs"
DEFAULT_SITES = SHARED_ROOT / "sites.local.json"
GOVERNED_NAMES = ("CLAUDE.md", "AGENTS.md")
USAGE = 64


class AgentDocsError(RuntimeError):
    """The invariant could not even be evaluated -- never a silent skip."""


# ---------------------------------------------------------------- resolution


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentDocsError(f"unreadable manifest: {path}: {error}") from error
    if data.get("schema") != "agent-docs/v1":
        raise AgentDocsError(f"{path}: schema must be agent-docs/v1")
    if not isinstance(data.get("targets"), list) or not data["targets"]:
        raise AgentDocsError(f"{path}: no targets[]")
    return data


def load_sites(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentDocsError(f"unreadable sites file: {path}: {error}") from error


def target_dir(target: dict[str, Any], sites: dict[str, Any]) -> Path:
    """Where this target's live copy sits. Raises rather than guessing."""
    key = target["key"]
    if target.get("scope") == "global":
        home = target.get("home")
        configured = sites.get(f"{home}_home")
        if configured:
            return Path(configured).expanduser()
        if home in ("claude", "codex"):
            return Path.home() / f".{home}"
        raise AgentDocsError(f"{key}: unknown global home {home!r}")
    for project in sites.get("projects", []):
        candidate = Path(project).expanduser()
        if candidate.name == key:
            return candidate
    raise AgentDocsError(
        f"{key}: no entry in {DEFAULT_SITES.name} projects[] has that directory name -- "
        f"add the path there (machine paths never live in the manifest)"
    )


# ---------------------------------------------------------------- the gate


def budget_notes(name: str, blob: bytes, budgets: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(fatal, surfaced). Truncation is fatal; adherence decay is surfaced."""
    fatal: list[str] = []
    surfaced: list[str] = []
    limit = budgets.get("codex_project_doc_max_bytes")
    if name == "AGENTS.md" and limit and len(blob) >= limit:
        fatal.append(
            f"OVER-CODEX-BUDGET {len(blob)}B >= project_doc_max_bytes {limit}B -- Codex stops "
            f"adding files at the limit, so the tail is dropped with no error"
        )
    soft = budgets.get("claude_md_soft_lines")
    if name == "CLAUDE.md" and soft:
        lines = blob.decode("utf-8", "replace").count("\n") + 1
        if lines > soft:
            surfaced.append(
                f"OVER-CLAUDE-SOFT-LIMIT {lines} lines > {soft} -- loaded in full, but adherence drops"
            )
    return fatal, surfaced


def check(root: Path, sites: dict[str, Any], quiet: bool = False) -> int:
    manifest = load_manifest(root)
    budgets = manifest.get("budgets", {})
    failures: list[str] = []
    surfaced: list[str] = []
    ok = 0

    for target in manifest["targets"]:
        key = target["key"]
        if not target.get("managed", False):
            if not quiet:
                print(f"UNMANAGED  {key}: {target.get('why', 'no reason recorded')}")
            continue
        live = target_dir(target, sites)
        source_dir = root / key
        managed_names = set(target.get("files", []))
        absences = target.get("absent", {})

        for name in target.get("files", []):
            source = source_dir / name
            projection = live / name
            if not source.is_file():
                failures.append(f"NO-SOURCE   {key}/{name}: {source} is not on disk")
                continue
            if not projection.is_file():
                failures.append(
                    f"MISSING     {key}/{name}: managed but absent at {projection} -- "
                    f"either `apply --to-targets` or register it under absent{{}}"
                )
                continue
            blob = source.read_bytes()
            if blob != projection.read_bytes():
                failures.append(f"DRIFT       {key}/{name}: {projection} differs from source")
                continue
            hard, soft = budget_notes(name, blob, budgets)
            failures.extend(f"{note} [{key}/{name}]" for note in hard)
            surfaced.extend(f"{note} [{key}/{name}]" for note in soft)
            if not hard:
                ok += 1
                if not quiet:
                    print(f"OK          {key}/{name}")

        for name, why in absences.items():
            if (live / name).is_file():
                failures.append(
                    f"UNEXPECTED  {key}/{name}: registered absent but present at {live / name}"
                )
            elif not quiet:
                print(f"ABSENT      {key}/{name}: {why}")

        for name in GOVERNED_NAMES:
            if name in managed_names or name in absences:
                continue
            if (live / name).is_file():
                failures.append(
                    f"UNREGISTERED {key}/{name}: {live / name} is loaded by the host but no "
                    f"manifest entry rules on it -- register it (managed or absent)"
                )

    for note in surfaced:
        print(f"SURFACE {note}", file=sys.stderr)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(f"PASS agent docs hold ({ok} managed files identical)")
    return 0


def diff(root: Path, sites: dict[str, Any]) -> int:
    manifest = load_manifest(root)
    shown = 0
    for target in manifest["targets"]:
        if not target.get("managed", False):
            continue
        live = target_dir(target, sites)
        for name in target.get("files", []):
            source, projection = root / target["key"] / name, live / name
            if not source.is_file() or not projection.is_file():
                continue
            a = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            b = projection.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            if a == b:
                continue
            shown += 1
            sys.stdout.writelines(
                difflib.unified_diff(a, b, f"source/{target['key']}/{name}", str(projection))
            )
    if not shown:
        print("no drift")
    return 0


def apply(root: Path, sites: dict[str, Any], to_targets: bool, dry_run: bool) -> int:
    """Copy one direction. `to_targets` is required and never inferred from mtime."""
    manifest = load_manifest(root)
    moved = 0
    for target in manifest["targets"]:
        if not target.get("managed", False):
            continue
        live = target_dir(target, sites)
        for name in target.get("files", []):
            source, projection = root / target["key"] / name, live / name
            src, dst = (source, projection) if to_targets else (projection, source)
            if not src.is_file():
                raise AgentDocsError(f"{target['key']}/{name}: source side missing: {src}")
            if dst.is_file() and dst.read_bytes() == src.read_bytes():
                continue
            print(f"{'WOULD-COPY' if dry_run else 'COPIED'}  {src} -> {dst}")
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                if dst.read_bytes() != src.read_bytes():
                    raise AgentDocsError(f"copy did not land: {dst}")
            moved += 1
    if not moved:
        print("nothing to copy; already identical")
        return 0
    return 0 if dry_run else check(root, sites, quiet=True)


def adopt(root: Path, sites: dict[str, Any], key: str) -> int:
    """Take a target's current files as source -- the import path for a new repo."""
    manifest = load_manifest(root)
    target = next((t for t in manifest["targets"] if t["key"] == key), None)
    if target is None:
        raise AgentDocsError(f"no target keyed {key!r} in the manifest")
    live = target_dir(target, sites)
    (root / key).mkdir(parents=True, exist_ok=True)
    for name in target.get("files", []):
        projection = live / name
        if not projection.is_file():
            raise AgentDocsError(f"{key}/{name}: nothing to adopt at {projection}")
        shutil.copyfile(projection, root / key / name)
        print(f"ADOPTED {projection} -> {root / key / name}")
    return check(root, sites, quiet=True)


# ---------------------------------------------------------------- selftest


FIXTURE_MANIFEST = {
    "schema": "agent-docs/v1",
    "budgets": {"claude_md_soft_lines": 200, "codex_project_doc_max_bytes": 32768},
    "targets": [
        {
            "key": "demo",
            "scope": "repo",
            "managed": True,
            "files": ["AGENTS.md"],
            "absent": {"CLAUDE.md": "registered absence"},
        }
    ],
}


def selftest() -> int:
    """A gate that cannot go red is a green light, not a check. Prove each colour."""
    import tempfile

    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root, repo = base / "agent-docs", base / "demo"
        (root / "demo").mkdir(parents=True)
        repo.mkdir()
        (root / "manifest.json").write_text(json.dumps(FIXTURE_MANIFEST), encoding="utf-8")
        sites = {"projects": [str(repo)]}

        def write(text: str) -> None:
            (root / "demo" / "AGENTS.md").write_text(text, encoding="utf-8")
            (repo / "AGENTS.md").write_text(text, encoding="utf-8")

        def expect(label: str, want: int) -> None:
            got = check(root, sites, quiet=True)
            if got != want:
                failures.append(f"{label}: expected exit {want}, got {got}")

        write("# demo\n")
        expect("identical copies pass", 0)

        (repo / "AGENTS.md").write_text("# demo drifted\n", encoding="utf-8")
        expect("drifted projection fails", 1)

        write("# demo\n")
        (repo / "AGENTS.md").unlink()
        expect("missing projection fails", 1)

        write("# demo\n")
        (repo / "CLAUDE.md").write_text("surprise\n", encoding="utf-8")
        expect("file at a registered absence fails", 1)
        (repo / "CLAUDE.md").unlink()

        FIXTURE_MANIFEST["targets"][0]["absent"] = {}
        (root / "manifest.json").write_text(json.dumps(FIXTURE_MANIFEST), encoding="utf-8")
        (repo / "CLAUDE.md").write_text("unruled\n", encoding="utf-8")
        expect("unregistered doc fails", 1)
        (repo / "CLAUDE.md").unlink()
        expect("back to clean passes", 0)

        write("x" * 40000)
        expect("AGENTS.md over the codex budget fails", 1)

    if failures:
        for failure in failures:
            print(f"SELFTEST-FAIL {failure}", file=sys.stderr)
        return 1
    print("PASS selftest: gate goes red on drift, absence, surprise, unruled and truncation")
    return 0


# ---------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="agent-docs directory")
    parser.add_argument("--sites", type=Path, default=DEFAULT_SITES, help="machine paths file")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="zero-network gate (T0)")
    commands.add_parser("diff", help="unified diff for every drifted file")
    apply_parser = commands.add_parser("apply", help="copy one direction, explicitly")
    direction = apply_parser.add_mutually_exclusive_group(required=True)
    direction.add_argument("--to-targets", action="store_true", help="source -> repos/homes")
    direction.add_argument("--from-targets", action="store_true", help="repos/homes -> source")
    apply_parser.add_argument("--dry-run", action="store_true")
    import_parser = commands.add_parser("import", help="adopt a target's files as source")
    import_parser.add_argument("--key", required=True)
    commands.add_parser("selftest", help="prove the gate can go red")

    args = parser.parse_args(argv)
    try:
        if args.command == "selftest":
            return selftest()
        sites = load_sites(args.sites)
        if args.command == "check":
            return check(args.root, sites)
        if args.command == "diff":
            return diff(args.root, sites)
        if args.command == "import":
            return adopt(args.root, sites, args.key)
        return apply(args.root, sites, args.to_targets, args.dry_run)
    except AgentDocsError as error:
        print(f"FATAL {error}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
