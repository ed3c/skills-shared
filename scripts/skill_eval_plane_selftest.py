#!/usr/bin/env python3
"""Plant each shape the eval-plane gate claims to catch and require a distinct refusal.

A gate that reports every defect with the same message cannot send anyone to the
right fix, so each planted case asserts on the substring that names *its* cause,
not merely on the refusal. The positive case is planted too: a plane that this
gate cannot pass is a gate nobody can adopt.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_skill_eval_plane as plane  # noqa: E402

CHECKER = "#!/usr/bin/env python3\n'''fixture checker'''\nif '--selftest' in []:\n    pass\n"
TEST = 'python3 "${skill}/scripts/thing.py" --selftest\n'
TEST_UNRELATED = 'python3 "${skill}/scripts/other.py" replay\n'


def build(root: Path, *, case: dict, checker: str = CHECKER, test: str = TEST,
          skill_name: str = "fixture-skill", runnable: list | None = None) -> Path:
    skill = root / "skills" / skill_name
    (skill / "scripts").mkdir(parents=True, exist_ok=True)
    (skill / "tests").mkdir(parents=True, exist_ok=True)
    (skill / "scripts" / "thing.py").write_text(checker, encoding="utf-8")
    (skill / "tests" / "verify.sh").write_text(test, encoding="utf-8")
    (skill / "fixtures").mkdir(exist_ok=True)
    (skill / "fixtures" / "good.json").write_text("{}\n", encoding="utf-8")
    (skill / "fixtures" / "hollow.json").write_text("{}\n", encoding="utf-8")
    document = {
        "skill_name": skill_name,
        "runnable": runnable if runnable is not None else [case],
    }
    path = skill / "evals.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


def good_case(**overrides) -> dict:
    case = {
        "id": "FIXTURE-1",
        "checker_script": "scripts/thing.py",
        "test_verify": "tests/verify.sh",
        "good_fixture": "fixtures/good.json",
        "hollow_fixture": "fixtures/hollow.json",
        "covers": ["one thing", "another thing"],
        "expected": "good passes and hollow fails",
    }
    case.update(overrides)
    return case


def run(path: Path) -> tuple[bool, str]:
    try:
        _, problems = plane.check_skill(path)
    except plane.PlaneError as exc:
        return False, str(exc)
    return not problems, " | ".join(problems)


def expect_green(label: str, path: Path) -> None:
    ok, message = run(path)
    if not ok:
        raise AssertionError(f"{label}: expected the plane to pass, got {message}")


def expect_red(label: str, path: Path, fragment: str) -> None:
    ok, message = run(path)
    if ok:
        raise AssertionError(f"{label}: planted defect was not caught")
    if fragment not in message:
        raise AssertionError(f"{label}: refused for the wrong reason: {message}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)

        expect_green("baseline", build(root / "base", case=good_case()))

        # A null fixture is legitimate when the evidence really is generated
        # in-process, and only then.
        expect_green("null fixture with a real selftest", build(
            root / "null-ok",
            case=good_case(good_fixture=None, good_evidence="built in-process by the selftest",
                           hollow_fixture=None, hollow_mutations="removes the guard")))

        expect_red("empty runnable", build(root / "empty", case=good_case(), runnable=[]),
                   "declares no coverage")
        expect_red("absent checker", build(root / "no-checker",
                                           case=good_case(checker_script="scripts/gone.py")),
                   "checker_script names a file that does not exist")
        expect_red("absent test", build(root / "no-test",
                                        case=good_case(test_verify="tests/gone.sh")),
                   "test_verify names a file that does not exist")
        expect_red("absent fixture", build(root / "no-fixture",
                                           case=good_case(hollow_fixture="fixtures/gone.json")),
                   "hollow_fixture names a path that does not exist")

        # The one that matters: the claim is attached to a test that never runs
        # the thing it claims to verify.
        expect_red("test does not exercise its checker",
                   build(root / "unrelated", case=good_case(), test=TEST_UNRELATED),
                   "does not exercise it")

        expect_red("null fixture with no prose",
                   build(root / "no-prose", case=good_case(good_fixture=None)),
                   "good_evidence must be a non-empty string")

        # Both at once means the field is polymorphic again, which is the defect
        # this gate exists to remove.
        expect_red("path and prose together",
                   build(root / "both", case=good_case(hollow_mutations="also prose")),
                   "one of the two, never both")
        expect_red("missing fixture key",
                   build(root / "absent-key",
                         case={k: v for k, v in good_case().items() if k != "hollow_fixture"}),
                   "must be present, as a path or as null")

        expect_red("escaping path",
                   build(root / "escape",
                         case=good_case(checker_script="../../../etc/hosts")),
                   "must be a relative path inside the skill")
        expect_red("absolute path",
                   build(root / "absolute", case=good_case(test_verify="/etc/hosts")),
                   "must be a relative path inside the skill")

        expect_red("duplicate ids",
                   build(root / "dupe", case=good_case(),
                         runnable=[good_case(), good_case()]),
                   "duplicate runnable id")
        expect_red("empty covers", build(root / "covers", case=good_case(covers=[])),
                   "covers must be a non-empty array")
        expect_red("duplicate covers",
                   build(root / "dupe-covers", case=good_case(covers=["same", "same"])),
                   "covers contains duplicates")
        expect_red("absent expected", build(root / "expected", case=good_case(expected="  ")),
                   "expected must be a non-empty string")

        # Two defects in one entry: the second must not be shadowed by the first.
        ok, message = run(build(root / "two-defects",
                                case=good_case(checker_script="scripts/gone.py", covers=[])))
        if ok:
            raise AssertionError("two defects: neither was caught")
        if "checker_script names a file that does not exist" not in message:
            raise AssertionError(f"two defects: first defect missing: {message}")
        if "covers must be a non-empty array" not in message:
            raise AssertionError(f"two defects: second defect shadowed by the first: {message}")

        # skill_name drift, planted by writing the document under a different
        # directory than it names.
        path = build(root / "name-drift", case=good_case())
        document = json.loads(path.read_text())
        document["skill_name"] = "some-other-skill"
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        expect_red("skill_name drift", path, "skill_name must equal the directory name")

    print("SELFTEST GREEN: every runnable eval claim is attached to a test that exercises it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
