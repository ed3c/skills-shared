#!/usr/bin/env python3
"""Deterministically validate the portable repo-agent-native Skill contract."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

PORTABLE_FRONTMATTER = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
REQUIRED_SKILL_HEADINGS = {
    "## Trigger",
    "## Non-trigger",
    "## Inputs",
    "## Outputs",
    "## Core laws",
    "## State machine",
    "## S0 — Scope",
    "## S1 — Route",
    "## S2 — Discover",
    "## S3 — Retrieve",
    "## S4 — Verify",
    "## S5 — Infer",
    "## S6 — Write",
    "## S7 — Assert",
    "## S8 — Handoff",
    "## Module law",
}
REQUIRED_MODULE_HEADINGS = {
    "## Trigger",
    "## Non-trigger",
    "## Inputs",
    "## Outputs",
    "## Evidence ceiling",
    "## Fallback",
    "## Authoritative laws",
}
REQUIRED_PATHS = {
    "SKILL.md",
    "README.md",
    "agents/openai.yaml",
    "modules/README.md",
    "scripts/check_repo_agent_native.py",
    "tests/verify.sh",
    "evals.json",
}
FORBIDDEN_PORTABLE_PATTERNS = {
    "macOS user path": re.compile(r"/Users/[^\s`]+"),
    "Linux home path": re.compile(r"/home/[^\s`]+"),
    "user-home skill path": re.compile(r"~/(?:\.[^\s`/]+/)+"),
    "consumer name skill-bettor": re.compile(r"\bskill-bettor\b", re.IGNORECASE),
    "consumer name bettor-arena": re.compile(r"\bbettor-arena\b", re.IGNORECASE),
    "consumer name ix-agy": re.compile(r"\bix-agy\b", re.IGNORECASE),
    "consumer name antigravity": re.compile(r"\bantigravity\b", re.IGNORECASE),
}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s|$)")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md: missing opening YAML frontmatter delimiter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            if index == 1:
                raise ValueError("SKILL.md: empty YAML frontmatter")
            return lines[1:index], "\n".join(lines[index + 1 :])
    raise ValueError("SKILL.md: missing closing YAML frontmatter delimiter")


def top_level_frontmatter(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        if line.startswith((" ", "\t")) or not line.strip() or line.lstrip().startswith("#"):
            continue
        match = TOP_LEVEL_KEY_RE.match(line)
        if not match:
            raise ValueError(f"SKILL.md: invalid top-level frontmatter line: {line!r}")
        key = match.group(1)
        value = line.split(":", 1)[1].strip()
        values[key] = value.strip("\"'")
    return values


def validate_links(skill_root: Path, markdown: Path, errors: list[str]) -> None:
    text = read_text(markdown)
    for raw_target in LINK_RE.findall(text):
        target = raw_target.split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (markdown.parent / target).resolve()
        try:
            resolved.relative_to(skill_root.resolve())
        except ValueError:
            errors.append(f"{markdown.relative_to(skill_root)}: link escapes Skill directory: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"{markdown.relative_to(skill_root)}: broken relative link: {raw_target}")


def find_repo_root(skill_root: Path) -> Path:
    if skill_root.parent.name == "skills":
        return skill_root.parent.parent
    return skill_root.parent


def validate_skill(skill_root: Path) -> list[str]:
    skill_root = skill_root.resolve()
    errors: list[str] = []
    for relative in sorted(REQUIRED_PATHS):
        if not (skill_root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    if errors:
        return errors

    skill_path = skill_root / "SKILL.md"
    skill_text = read_text(skill_path)
    if len(skill_text.splitlines()) > 500:
        errors.append("SKILL.md: exceeds 500-line progressive-disclosure budget")
    try:
        frontmatter_lines, body = split_frontmatter(skill_text)
        frontmatter = top_level_frontmatter(frontmatter_lines)
    except ValueError as exc:
        errors.append(str(exc))
        frontmatter, body = {}, skill_text

    unknown = sorted(set(frontmatter) - PORTABLE_FRONTMATTER)
    if unknown:
        errors.append(f"SKILL.md: non-portable top-level frontmatter fields: {', '.join(unknown)}")
    if frontmatter.get("name") != skill_root.name:
        errors.append(f"SKILL.md: name must equal directory name {skill_root.name!r}")
    description = frontmatter.get("description", "").strip()
    if not description:
        errors.append("SKILL.md: description is required")
    elif len(description) > 1024:
        errors.append("SKILL.md: description exceeds 1024 characters")
    if len(frontmatter.get("name", "")) > 64:
        errors.append("SKILL.md: name exceeds 64 characters")
    if frontmatter.get("name") and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", frontmatter["name"]):
        errors.append("SKILL.md: name must use lowercase letters, digits, and single hyphens")

    missing_headings = sorted(REQUIRED_SKILL_HEADINGS - set(body.splitlines()))
    if missing_headings:
        errors.append(f"SKILL.md: missing required headings: {', '.join(missing_headings)}")

    portable_markdown = [skill_path, skill_root / "README.md"]
    portable_markdown.extend(sorted((skill_root / "modules").glob("*.md")))
    for path in portable_markdown:
        text = read_text(path)
        for label, pattern in FORBIDDEN_PORTABLE_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(skill_root)}: forbidden portable content ({label})")
        validate_links(skill_root, path, errors)

    for module in sorted((skill_root / "modules").glob("*.md")):
        if module.name == "README.md":
            continue
        headings = set(read_text(module).splitlines())
        missing = sorted(REQUIRED_MODULE_HEADINGS - headings)
        if missing:
            errors.append(f"modules/{module.name}: missing module headings: {', '.join(missing)}")

    openai_yaml = read_text(skill_root / "agents" / "openai.yaml")
    for token in ("interface:", "display_name:", "short_description:", "policy:", "allow_implicit_invocation:"):
        if token not in openai_yaml:
            errors.append(f"agents/openai.yaml: missing {token}")

    eval_path = skill_root / "evals.json"
    try:
        inventory = json.loads(read_text(eval_path))
    except json.JSONDecodeError as exc:
        errors.append(f"evals.json: invalid JSON: {exc}")
        inventory = {}
    if inventory.get("skill_name") != skill_root.name:
        errors.append("evals.json: skill_name mismatch")
    repo_root = find_repo_root(skill_root)
    referenced = list(inventory.get("behavior_cases", []))
    verifier = inventory.get("verifier")
    if isinstance(verifier, str):
        referenced.append(verifier)
    else:
        errors.append("evals.json: verifier path is required")
    if not referenced:
        errors.append("evals.json: no behavior cases declared")
    for raw in referenced:
        if not isinstance(raw, str) or not raw.strip():
            errors.append("evals.json: referenced paths must be non-empty strings")
            continue
        path = (repo_root / raw).resolve()
        try:
            path.relative_to(repo_root.resolve())
        except ValueError:
            errors.append(f"evals.json: path escapes repository: {raw}")
            continue
        if not path.is_file():
            errors.append(f"evals.json: referenced path does not exist: {raw}")

    return sorted(set(errors))


def copy_external_eval_closure(source_skill: Path, target_repo: Path) -> None:
    source_repo = find_repo_root(source_skill)
    inventory = json.loads(read_text(source_skill / "evals.json"))
    paths = list(inventory.get("behavior_cases", []))
    if isinstance(inventory.get("verifier"), str):
        paths.append(inventory["verifier"])
    for raw in paths:
        source = source_repo / raw
        target = target_repo / raw
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def assert_mutation_fails(skill_root: Path, label: str, mutate) -> None:
    with tempfile.TemporaryDirectory(prefix="repo-agent-native-selftest-") as tmp:
        repo = Path(tmp)
        target = repo / "skills" / skill_root.name
        target.parent.mkdir(parents=True)
        shutil.copytree(skill_root, target)
        copy_external_eval_closure(skill_root, repo)
        mutate(target)
        errors = validate_skill(target)
        if not errors:
            raise AssertionError(f"{label}: planted mutation unexpectedly passed")


def selftest(skill_root: Path) -> int:
    base_errors = validate_skill(skill_root)
    if base_errors:
        for error in base_errors:
            print(f"SELFTEST BASE FAIL {error}", file=sys.stderr)
        return 1

    def unknown_frontmatter(root: Path) -> None:
        path = root / "SKILL.md"
        text = read_text(path).replace("license: MIT\n", "license: MIT\ndisable-model-invocation: true\n", 1)
        path.write_text(text, encoding="utf-8")

    def absolute_path(root: Path) -> None:
        path = root / "SKILL.md"
        path.write_text(read_text(path) + "\nUse /Users/example/private checkout.\n", encoding="utf-8")

    def missing_module_heading(root: Path) -> None:
        path = root / "modules" / "project-memory.md"
        path.write_text(read_text(path).replace("## Evidence ceiling\n", "## Evidence limit\n", 1), encoding="utf-8")

    def broken_link(root: Path) -> None:
        path = root / "SKILL.md"
        path.write_text(read_text(path).replace("modules/document-routing.md", "modules/not-present.md", 1), encoding="utf-8")

    def missing_eval(root: Path) -> None:
        path = root / "evals.json"
        value = json.loads(read_text(path))
        value["behavior_cases"][0] = "evals/cases/repo-agent-native/not-present.json"
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    for label, mutation in (
        ("unknown-frontmatter", unknown_frontmatter),
        ("absolute-path", absolute_path),
        ("missing-module-heading", missing_module_heading),
        ("broken-link", broken_link),
        ("missing-eval", missing_eval),
    ):
        assert_mutation_fails(skill_root, label, mutation)
    print("PASS repo-agent-native structural selftest: 1 positive + 5 planted negatives")
    return 0


def emit_result(skill_root: Path, errors: list[str]) -> None:
    result = {
        "schema_version": "repo-agent-native-structure-check/v1",
        "skill": skill_root.name,
        "state": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    stream = sys.stdout if not errors else sys.stderr
    print(json.dumps(result, indent=2, sort_keys=True), file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_root", nargs="?", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    default_root = Path(__file__).resolve().parents[1]
    skill_root = (args.skill_root or default_root).resolve()
    if args.selftest:
        return selftest(default_root)
    errors = validate_skill(skill_root)
    emit_result(skill_root, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
