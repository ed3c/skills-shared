#!/usr/bin/env python3
"""Deterministic checker for canonical Skill procedural-core/domain boundaries.

The checker is intentionally zero-network. It validates only repository bytes and
never upgrades live runtime/provider evidence.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

START = "<!-- PORTABLE_CORE_START -->"
END = "<!-- PORTABLE_CORE_END -->"
REQUIRED_LAWS = [f"CORE-LAW-{i:03d}" for i in range(1, 6)]
REQUIRED_MODULE_SECTIONS = [
    "## Trigger",
    "## Non-trigger",
    "## Assumptions",
    "## Evidence ceiling",
    "## Fallback",
    "## Forbidden overrides",
]


def load_manifest(root: Path, manifest_path: Path) -> dict:
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    return json.loads(path.read_text(encoding="utf-8"))


def bounded_core(text: str) -> str:
    if START not in text or END not in text:
        raise ValueError("portable-core markers missing")
    before, rest = text.split(START, 1)
    core, _after = rest.split(END, 1)
    if not before.strip():
        raise ValueError("frontmatter/entry metadata missing")
    return core


def check_entry(root: Path, entry: dict) -> list[str]:
    name = entry["name"]
    skill_root = root / "skills" / name
    skill_path = skill_root / "SKILL.md"
    module_path = skill_root / entry["domain_module"]
    errors: list[str] = []

    if not skill_path.exists():
        return [f"{name}: SKILL.md ABSENT"]
    if not module_path.exists():
        errors.append(f"{name}: domain module ABSENT: {entry['domain_module']}")

    text = skill_path.read_text(encoding="utf-8")
    try:
        core = bounded_core(text)
    except ValueError as exc:
        return errors + [f"{name}: {exc}"]

    for law in REQUIRED_LAWS:
        if law not in core:
            errors.append(f"{name}: missing {law}")

    assertion = "python3 scripts/check_skill_core_boundaries.py --skill " + name
    if assertion not in core:
        errors.append(f"{name}: executable assertion route missing")

    if entry["domain_module"] not in core:
        errors.append(f"{name}: core does not route to {entry['domain_module']}")

    # The executable assertion must name the Skill being checked. Exclude that
    # mechanical identifier from the domain-leak scan so a provider-shaped Skill
    # name does not create a false positive while provider semantics in prose still do.
    domain_scan = core.replace(assertion, "")
    lowered = domain_scan.casefold()
    for token in entry.get("forbidden_core_tokens", []):
        if token.casefold() in lowered:
            errors.append(f"{name}: forbidden core token: {token}")

    if module_path.exists():
        module_text = module_path.read_text(encoding="utf-8")
        for heading in REQUIRED_MODULE_SECTIONS:
            if heading not in module_text:
                errors.append(f"{name}: domain module missing section {heading}")
        if "CORE-LAW-" in module_text and "may not override" not in module_text.casefold():
            errors.append(f"{name}: module mentions core laws without override refusal")

    return errors


def run(root: Path, manifest: dict, only: str | None = None) -> list[str]:
    errors: list[str] = []
    selected = [e for e in manifest["skills"] if only is None or e["name"] == only]
    if only and not selected:
        return [f"unknown skill in manifest: {only}"]
    for entry in selected:
        errors.extend(check_entry(root, entry))
    return errors


def selftest(root: Path, manifest: dict) -> list[str]:
    """Plant defects in a disposable copy and prove every class turns red."""
    if not manifest["skills"]:
        return ["selftest: manifest has no skills"]
    entry = manifest["skills"][0]
    name = entry["name"]
    source = root / "skills" / name
    if not source.exists():
        return [f"selftest: source skill missing: {name}"]

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="skill-core-boundary-") as tmp:
        troot = Path(tmp)
        dest = troot / "skills" / name
        dest.parent.mkdir(parents=True)
        shutil.copytree(source, dest)
        local_manifest = {"schema": manifest["schema"], "skills": [entry]}

        if run(troot, local_manifest, name):
            failures.append("selftest: positive control did not pass")
            return failures

        skill_path = dest / "SKILL.md"
        original = skill_path.read_text(encoding="utf-8")

        skill_path.write_text(original.replace("CORE-LAW-001", "CORE-LAW-X001", 1), encoding="utf-8")
        if not run(troot, local_manifest, name):
            failures.append("selftest: missing-law mutation survived")
        skill_path.write_text(original, encoding="utf-8")

        token = entry.get("forbidden_core_tokens", ["__DOMAIN_LEAK__"])[0]
        mutated = original.replace(START, START + "\n" + token, 1)
        skill_path.write_text(mutated, encoding="utf-8")
        if not run(troot, local_manifest, name):
            failures.append("selftest: domain-leak mutation survived")
        skill_path.write_text(original, encoding="utf-8")

        module_path = dest / entry["domain_module"]
        module_original = module_path.read_text(encoding="utf-8")
        module_path.write_text(module_original.replace("## Forbidden overrides", "## Overrides", 1), encoding="utf-8")
        if not run(troot, local_manifest, name):
            failures.append("selftest: module-law-override mutation survived")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=None,
        help="repository to audit; defaults to the checkout owning this script, never the caller's cwd",
    )
    parser.add_argument("--manifest", default="evals/skill-core-boundaries.json")
    parser.add_argument("--skill")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.root is None:
        # Only the silent default carries the wrong-subject risk; an explicit
        # --root (e.g. a hermetic reconstruction arm) is the caller's choice.
        root = Path(__file__).resolve().parent.parent
        if not (root / "AGENTS.md").is_file():
            print(f"SKILL-CORE-RED default subject root {root} does not contain AGENTS.md")
            return 2
    else:
        root = Path(args.root).resolve()
    manifest = load_manifest(root, Path(args.manifest))
    errors = run(root, manifest, args.skill)
    if args.selftest and not errors:
        errors.extend(selftest(root, manifest))

    if errors:
        for error in errors:
            print(f"SKILL-CORE-RED {error}")
        return 2
    scope = args.skill or "ALL"
    print(f"SKILL-CORE-GREEN scope={scope} checked={1 if args.skill else len(manifest['skills'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
