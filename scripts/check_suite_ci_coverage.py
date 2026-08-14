#!/usr/bin/env python3
"""Every skill that ships a test suite must have a CI job that runs it.

A verification surface nobody runs is indistinguishable from one that passes.
Both #83 and #105 landed through that gap (see #122).

The first version of this gate matched on the skill name appearing anywhere in
a workflow file. That is too weak, and #105 is the proof: `git-town-stacked-pr-worker`
was named by its own workflow, the workflow ran, and `tests/run-all.sh` was
still never invoked -- the only job was the live canary. Being mentioned in a
paths filter is not an arrival.

This version resolves what each job actually runs: it expands `strategy.matrix`
and substitutes matrix values into `run:` steps, then requires a step whose
resolved command names the suite entrypoint.

It deliberately fails closed. A construct it cannot resolve -- a matrix
`include`, a suite invoked through a variable it does not expand -- is reported
as unresolvable rather than assumed covered, because assuming coverage is the
exact failure this gate exists to catch.
"""
from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print(
        "SUITE COVERAGE RED: PyYAML is required; the gate refuses to guess "
        "coverage from raw text",
        file=sys.stderr,
    )
    raise SystemExit(2)

SUITES = ("tests/run-all.sh", "tests/verify.sh")
MATRIX_REF = re.compile(r"\$\{\{\s*matrix\.([A-Za-z_][A-Za-z0-9_-]*)\s*\}\}")
ANY_EXPRESSION = re.compile(r"\$\{\{.*?\}\}")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def skills_with_suites(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for skill in sorted((root / "skills").iterdir()):
        if not skill.is_dir():
            continue
        suites = [suite for suite in SUITES if (skill / suite).is_file()]
        if suites:
            found[skill.name] = suites
    return found


def matrix_combinations(job: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Every matrix value combination for a job, plus anything unresolvable."""
    strategy = job.get("strategy")
    if not isinstance(strategy, dict):
        return [{}], []
    matrix = strategy.get("matrix")
    if not isinstance(matrix, dict):
        return [{}], []

    unresolved: list[str] = []
    axes: dict[str, list[Any]] = {}
    for key, value in matrix.items():
        if key in ("include", "exclude"):
            # Resolving include/exclude means reimplementing GitHub's own
            # expansion rules. Report it instead of guessing.
            unresolved.append(f"strategy.matrix.{key}")
            continue
        if isinstance(value, list):
            axes[key] = value
        else:
            unresolved.append(f"strategy.matrix.{key} is not a list")

    if not axes:
        return [{}], unresolved

    names = sorted(axes)
    combos = [
        dict(zip(names, values))
        for values in itertools.product(*(axes[name] for name in names))
    ]
    return combos, unresolved


def resolved_commands(workflow: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """(job name, resolved run command) for every step of every job."""
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        combos, _ = matrix_combinations(job)
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            run = step.get("run")
            if not isinstance(run, str):
                continue
            for combo in combos:
                resolved = MATRIX_REF.sub(
                    lambda match: str(combo.get(match.group(1), match.group(0))), run
                )
                yield job_name, resolved


def main() -> int:
    root = repo_root()
    workflow_dir = root / ".github" / "workflows"
    workflows = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    if not workflows:
        print("SUITE COVERAGE RED: no workflows found", file=sys.stderr)
        return 2

    suites = skills_with_suites(root)
    if not suites:
        print("SUITE COVERAGE RED: no skill test suites found", file=sys.stderr)
        return 2

    commands: list[tuple[str, str, str]] = []
    unresolved: list[str] = []
    for path in workflows:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            unresolved.append(f"{path.name}: not a mapping")
            continue
        jobs = document.get("jobs")
        if isinstance(jobs, dict):
            for job_name, job in jobs.items():
                if isinstance(job, dict):
                    for problem in matrix_combinations(job)[1]:
                        unresolved.append(f"{path.name}:{job_name}: {problem}")
        for job_name, command in resolved_commands(document):
            commands.append((path.name, job_name, command))

    invoked: dict[str, tuple[str, str]] = {}
    leftover_expressions: list[str] = []
    for workflow_name, job_name, command in commands:
        for skill, entrypoints in suites.items():
            for entrypoint in entrypoints:
                if f"skills/{skill}/{entrypoint}" in command:
                    invoked.setdefault(skill, (workflow_name, job_name))
        if "tests/run-all.sh" in command or "tests/verify.sh" in command:
            if ANY_EXPRESSION.search(command):
                leftover_expressions.append(
                    f"{workflow_name}:{job_name}: {command.strip()[:120]}"
                )

    uncovered = sorted(set(suites) - set(invoked))
    failed = False

    for skill in uncovered:
        failed = True
        print(
            f"SUITE COVERAGE RED: skills/{skill} ships {suites[skill][0]} but no "
            f"workflow job runs it. Being named in a paths filter is not an "
            f"arrival -- add it to the skill-suites matrix or give it a job that "
            f"invokes the entrypoint.",
            file=sys.stderr,
        )

    for item in leftover_expressions:
        failed = True
        print(
            f"SUITE COVERAGE RED: a suite invocation still contains an "
            f"unexpanded expression, so coverage cannot be resolved: {item}",
            file=sys.stderr,
        )

    for item in unresolved:
        failed = True
        print(
            f"SUITE COVERAGE RED: unresolvable workflow construct: {item}. "
            f"Teach this gate to expand it rather than assuming coverage.",
            file=sys.stderr,
        )

    if failed:
        return 2

    for skill in sorted(invoked):
        workflow_name, job_name = invoked[skill]
        print(f"  {skill} <- {workflow_name}:{job_name}")
    print(f"SUITE COVERAGE GREEN: {len(suites)} skill suite(s) are run by a CI job")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
