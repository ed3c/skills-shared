#!/usr/bin/env python3
"""Every skill that ships a test suite must be named by some workflow.

A suite with no CI arrival cannot report a regression. Both #83 and #105 landed
through that gap, and a matrix listing skills by hand reopens it the moment
someone adds a skill and forgets the workflow. This turns remembering into a
failing check.

ponytail: matches on the skill name appearing in a workflow file, not on
proving the suite is actually invoked. That catches the real failure mode -- a
new suite nobody wired up. Upgrade to parsing each workflow's run steps if a
workflow ever names a skill without running its suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

SUITES = ("tests/run-all.sh", "tests/verify.sh")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def skills_with_suites(root: Path) -> list[str]:
    found = []
    for skill in sorted((root / "skills").iterdir()):
        if not skill.is_dir():
            continue
        if any((skill / suite).is_file() for suite in SUITES):
            found.append(skill.name)
    return found


def main() -> int:
    root = repo_root()
    workflows = sorted((root / ".github" / "workflows").glob("*.yml"))
    if not workflows:
        print("SUITE COVERAGE RED: no workflows found", file=sys.stderr)
        return 2

    blob = "\n".join(path.read_text(encoding="utf-8") for path in workflows)
    suites = skills_with_suites(root)
    if not suites:
        print("SUITE COVERAGE RED: no skill test suites found", file=sys.stderr)
        return 2

    uncovered = [name for name in suites if name not in blob]
    if uncovered:
        for name in uncovered:
            print(
                f"SUITE COVERAGE RED: skills/{name} ships a test suite that no "
                f"workflow names; add it to .github/workflows/skill-suites.yml "
                f"or give it a dedicated workflow",
                file=sys.stderr,
            )
        return 2

    print(f"SUITE COVERAGE GREEN: {len(suites)} skill suite(s) have a CI arrival")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
