#!/usr/bin/env python3
"""Verify and print executable navigation to owned Skill mechanisms.

Issue #258 found that direct basename lists in SKILL.md drift. The canonical
reading contract in skills/README.md now names this current-tree command once;
the governed Skill manifest determines which entries must remain navigable.
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
COMMON_ROUTE = "python3 scripts/check_skill_entry_routes.py --skill <name> --print-index"


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def check_common_route(repo: Path) -> list[str]:
    contract = repo / "skills" / "README.md"
    if not contract.is_file():
        return ["skills/README.md missing"]
    text = contract.read_text(encoding="utf-8")
    if COMMON_ROUTE not in text:
        return ["shared executable mechanism-navigation route missing from skills/README.md"]
    return []


def check_skill(repo: Path, name: str) -> list[str]:
    skill_root = repo / "skills" / name
    skill = skill_root / "SKILL.md"
    if not skill.is_file():
        return [f"{name}: SKILL.md missing"]
    files = owned_files(skill_root)
    if not files:
        return [f"{name}: no owned scripts/references/modules were discoverable"]
    return []


def run(repo: Path, manifest: dict, only: str | None) -> list[str]:
    errors = check_common_route(repo)
    names = manifest["skills"]
    if only is not None:
        if only not in names:
            return errors + [f"unknown governed Skill: {only}"]
        names = [only]
    for name in names:
        errors.extend(check_skill(repo, name))
    return errors


def selftest(repo: Path, manifest: dict) -> list[str]:
    name = manifest["skills"][0]
    with tempfile.TemporaryDirectory(prefix="skill-entry-route-") as tmp:
        troot = Path(tmp)
        (troot / "skills").mkdir()
        shutil.copy2(repo / "skills" / "README.md", troot / "skills" / "README.md")
        shutil.copytree(repo / "skills" / name, troot / "skills" / name)
        contract = troot / "skills" / "README.md"
        original = contract.read_text(encoding="utf-8")
        contract.write_text(original.replace(COMMON_ROUTE, "ROUTE_REMOVED", 1), encoding="utf-8")
        if not check_common_route(troot):
            return ["selftest: missing common route mutation survived"]
        contract.write_text(original, encoding="utf-8")
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
        print(json.dumps({
            "schema": "skill-entry-index/v1",
            "skill": args.skill,
            "files": owned_files(repo / "skills" / args.skill),
        }, indent=2))
    else:
        print(f"SKILL-ENTRY-GREEN checked={1 if args.skill else len(manifest['skills'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
