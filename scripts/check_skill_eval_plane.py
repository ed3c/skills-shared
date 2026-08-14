#!/usr/bin/env python3
"""Validate that every skill's runnable eval claim is attached to something that runs.

`skills/*/evals.json` is the per-skill claim plane: each entry names a checker,
the test that exercises it, the fixtures on both sides, and what it covers.
Nothing read it. A claim could name a script that had been deleted, a test that
never touched that script, or a fixture path that never existed, and the suite
stayed green -- a short claim plane and a complete one look identical.

The load-bearing rule is that a fixture field must not be polymorphic. Half of
these entries carried a real path and half carried a prose description of what
the selftest mutates, in the same field, so a typo in a path was indistinguishable
from a description. A path is a path and must exist; prose lives in its own field
and obliges the checker to carry an executable selftest instead.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

# `checker_script` is exercised by `test_verify`. A shell test runs it by
# filename; a Python test may import it by module stem. Both count; nothing else
# does.
FIXTURE_PAIRS = (("good_fixture", "good_evidence"), ("hollow_fixture", "hollow_mutations"))


class PlaneError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        # The selftest runs this against a synthetic tree outside the repository.
        return str(path)


def resolve_under(skill: Path, value: str, *, field: str, where: str, must_be_file: bool) -> Path:
    if value.startswith("/") or ".." in Path(value).parts:
        raise PlaneError(f"{where}: {field} must be a relative path inside the skill: {value!r}")
    target = (skill / value).resolve()
    try:
        target.relative_to(skill.resolve())
    except ValueError as exc:
        raise PlaneError(f"{where}: {field} escapes the skill directory: {value!r}") from exc
    # A checker and a test are single files. A fixture is routinely a directory
    # of them, so requiring a file there would refuse a plane that is correct.
    if must_be_file:
        if not target.is_file():
            raise PlaneError(f"{where}: {field} names a file that does not exist: {value!r}")
    elif not target.exists():
        raise PlaneError(f"{where}: {field} names a path that does not exist: {value!r}")
    return target


def nonempty_str(value: object, *, field: str, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlaneError(f"{where}: {field} must be a non-empty string")
    return value


def check_exercised(checker: Path, test: Path, *, where: str) -> None:
    if checker == test:
        # A self-contained contract test is its own checker. Nothing to prove
        # about one exercising the other.
        return
    body = test.read_text(encoding="utf-8", errors="replace")
    if checker.name in body or checker.stem in body:
        return
    raise PlaneError(
        f"{where}: test_verify never names {checker.name} (nor imports {checker.stem}); "
        "this claim is attached to a test that does not exercise it"
    )


def check_case(case: object, skill: Path, index: int) -> tuple[str | None, list[str]]:
    """Return the case id and every problem found, not merely the first.

    An earlier version raised on the first defect, so a second defect in the same
    entry was invisible until the first was fixed -- an entry could hide its own
    shadowing. Collecting them is the difference between one pass and N passes.
    """
    name = skill.name
    problems: list[str] = []

    def collect(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PlaneError as exc:
            problems.append(str(exc))
            return None

    if not isinstance(case, dict):
        return None, [f"{name}: runnable[{index}] must be an object"]
    case_id = collect(nonempty_str, case.get("id"), field="id",
                      where=f"{name}: runnable[{index}]")
    where = f"{name}/{case_id}" if case_id else f"{name}: runnable[{index}]"

    checker = test = None
    raw_checker = collect(nonempty_str, case.get("checker_script"),
                          field="checker_script", where=where)
    if raw_checker:
        checker = collect(resolve_under, skill, raw_checker,
                          field="checker_script", where=where, must_be_file=True)
    raw_test = collect(nonempty_str, case.get("test_verify"), field="test_verify", where=where)
    if raw_test:
        test = collect(resolve_under, skill, raw_test,
                       field="test_verify", where=where, must_be_file=True)
    if checker and test:
        collect(check_exercised, checker, test, where=where)

    for fixture_field, prose_field in FIXTURE_PAIRS:
        if fixture_field not in case:
            problems.append(f"{where}: {fixture_field} must be present, as a path or as null")
            continue
        fixture = case[fixture_field]
        if fixture is None:
            # Whether the described case is really constructed is decided by
            # running it, which is check_guard_controls.py's job, not a substring
            # search here. Three signals were tried and a fourth was already
            # needed; a grab-bag of substrings cannot decide this and a gate that
            # proves less is better than one that guesses.
            collect(nonempty_str, case.get(prose_field), field=prose_field, where=where)
            continue
        if prose_field in case:
            problems.append(
                f"{where}: {fixture_field} is a path, so {prose_field} must be absent; "
                "one of the two, never both")
        raw_fixture = collect(nonempty_str, fixture, field=fixture_field, where=where)
        if raw_fixture:
            collect(resolve_under, skill, raw_fixture,
                    field=fixture_field, where=where, must_be_file=False)

    covers = case.get("covers")
    if not isinstance(covers, list) or not covers:
        problems.append(f"{where}: covers must be a non-empty array")
    else:
        for item in covers:
            collect(nonempty_str, item, field="covers[]", where=where)
        if len(set(map(repr, covers))) != len(covers):
            problems.append(f"{where}: covers contains duplicates")
    collect(nonempty_str, case.get("expected"), field="expected", where=where)
    return case_id, problems


def check_skill(path: Path) -> tuple[int, list[str]]:
    skill = path.parent
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlaneError(f"{rel(path)}: invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PlaneError(f"{rel(path)}: top level must be an object")
    if document.get("skill_name") != skill.name:
        raise PlaneError(f"{rel(path)}: skill_name must equal the directory name {skill.name!r}")
    runnable = document.get("runnable")
    if not isinstance(runnable, list) or not runnable:
        raise PlaneError(f"{rel(path)}: runnable must be a non-empty array; a skill with no "
                         "runnable eval declares no coverage rather than perfect coverage")
    seen: set[str] = set()
    problems: list[str] = []
    for index, case in enumerate(runnable):
        case_id, case_problems = check_case(case, skill, index)
        problems.extend(case_problems)
        if case_id is None:
            continue
        if case_id in seen:
            problems.append(f"{skill.name}: duplicate runnable id {case_id!r}")
        seen.add(case_id)
    return len(runnable), problems


def main() -> int:
    files = sorted(SKILLS.glob("*/evals.json"))
    if not files:
        print("SKILL EVAL PLANE UNUSABLE: no skills/*/evals.json found", file=sys.stderr)
        return 64
    problems: list[str] = []
    total = 0
    for path in files:
        try:
            count, found = check_skill(path)
        except PlaneError as exc:
            problems.append(str(exc))
            continue
        total += count
        problems.extend(found)
    if problems:
        print("SKILL EVAL PLANE RED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"SKILL EVAL PLANE GREEN: {total} runnable claim(s) across {len(files)} skill(s), "
          "each attached to a test that exercises it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
