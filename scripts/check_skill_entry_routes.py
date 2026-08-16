#!/usr/bin/env python3
"""Verify and print executable navigation from SKILL.md to owned mechanisms.

Issue #258 showed that hand-maintained basename indexes drift. This checker makes
navigation procedural: each governed SKILL.md names this command, and the command
indexes current repository bytes under scripts/, references/, and modules/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "evals" / "skill-entry-routes.json"
ROOTS = ("scripts", "references", "modules")


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def route_command(name: str) -> str:
    return f"python3 scripts/check_skill_entry_routes.py --skill {name} --print-index"


def owned_files(skill_root: Path) -> list[str]:
    result: list[str] = []
    for root_name in ROOTS:
        root = skill_root / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                result.append(path.relative_to(skill_root).as_posix())
    return result


def check_skill(repo: Path, name: str) -> list[str]:
    skill_root = repo / "skills" / name
    skill = skill_root / "SKILL.md"
    if not skill.is_file():
        return [f"{name}: SKILL.md missing"]
    text = skill.read_text(encoding="utf-8")
    command = route_command(name)
    errors = []
    if command not in text:
        errors.append(f"{name}: executable mechanism-navigation route missing")
    files = owned_files(skill_root)
    if not files:
        errors.append(f"{name}: no owned scripts/references/modules were discoverable")
    return errors


def run(repo: Path, manifest: dict, only: str | None) -> list[str]:
    names = manifest["skills"]
    if only is not None:
        if only not in names:
            return [f"unknown governed Skill: {only}"]
        names = [only]
    errors: list[str] = []
    for name in names:
        errors.extend(check_skill(repo, name))
    return errors


def selftest(repo: Path, manifest: dict) -> list[str]:
    name = manifest["skills"][0]
    source = repo / "skills" / name
    with tempfile.TemporaryDirectory(prefix="skill-entry-route-") as tmp:
        troot = Path(tmp)
        (troot / "skills").mkdir()
        shutil.copytree(source, troot / "skills" / name)
        skill = troot / "skills" / name / "SKILL.md"
        original = skill.read_text(encoding="utf-8")
        command = route_command(name)
        if command not in original:
            return ["selftest positive fixture lacks navigation command"]
        skill.write_text(original.replace(command, "ROUTE_REMOVED", 1), encoding="utf-8")
        if not check_skill(troot, name):
            return ["selftest: missing route mutation survived"]
        skill.write_text(original, encoding="utf-8")
        injected = troot / "skills" / name / "modules" / "new-unindexed-fixture.md"
        injected.parent.mkdir(parents=True, exist_ok=True)
        injected.write_text("fixture\n", encoding="utf-8")
        if "modules/new-unindexed-fixture.md" not in owned_files(troot / "skills" / name):
            return ["selftest: current-tree navigation failed to discover a new file"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--skill")
    parser.add_argument("--print-index", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    manifest = load_manifest(args.manifest)
    errors = run(repo, manifest, args.skill)
    if args.selftest and not errors:
        errors.extend(selftest(repo, manifest))
    if errors:
        for error in errors:
            print(f"SKILL-ENTRY-RED {error}", file=sys.stderr)
        return 2
    if args.print_index:
        if not args.skill:
            print("--print-index requires --skill", file=sys.stderr)
            return 64
        files = owned_files(repo / "skills" / args.skill)
        print(json.dumps({"schema":"skill-entry-index/v1","skill":args.skill,"files":files}, indent=2))
    else:
        print(f"SKILL-ENTRY-GREEN checked={1 if args.skill else len(manifest['skills'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
