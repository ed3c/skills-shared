#!/usr/bin/env python3
"""#1's mechanical gate: a shared body may not name a specific host repository.

The rule the PRD states is one line -- *move it unchanged to another repository;
is it still true? If not, it is binding, not body* -- and its grep form is that
shared body text must not contain a concrete repository name or an absolute host
path.

Running it today reports 399 lines across 73 files, which is not a reason to
skip the gate. It is the reason to have one: that number is the debt, and until
something counted it, the debt was invisible and free to grow. So this is a
ratchet rather than a pass/fail. The manifest records what each file owes today,
a file may never owe more than its entry, and a file with no entry may owe
nothing at all.

The allowance is a ceiling *and* a floor: an entry higher than the file's actual
count is itself refused. A stale allowance is how a ratchet quietly turns into a
permanent exemption -- the number stops describing anything and nobody notices
the debt was already paid. `--update-baseline` can only lower entries, so the
list cannot be used to admit new debt.

This gate decides nothing about which history is canonical. It makes the
divergence countable, which is what has to happen before that decision can be
made on evidence rather than on preference.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evals" / "body-neutrality.json"
BODY_ROOT = ROOT / "skills"
# An archive of what was superseded is a record, not a shared body.
EXCLUDED_PARTS = {"superseded"}

HOST_REPOSITORIES = (
    "skill-bettor",
    "ts-skill-bettor",
    "antigravity",
    "ix-agy",
    "bettor-arena",
)
# `ts-skill-bettor` contains `skill-bettor`, so a line naming the first must not
# be counted twice. One alternation, longest first, one match per line.
PATTERN = re.compile(
    "|".join(re.escape(name) for name in sorted(HOST_REPOSITORIES, key=len, reverse=True))
    + r"|/Users/[A-Za-z0-9._-]+/"
    + r"|/home/[A-Za-z0-9._-]+/"
    + r"|~/\S"
)


class NeutralityError(Exception):
    pass


def body_files(body_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(body_root.glob("**/*.md"))
        if not EXCLUDED_PARTS & set(path.parts)
    ]


def count_hits(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if PATTERN.search(line)
    )


def measure(body_root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in body_files(body_root):
        hits = count_hits(path)
        if hits:
            counts[path.relative_to(body_root.parent).as_posix()] = hits
    return counts


def load_manifest(path: Path) -> dict[str, int]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise NeutralityError(f"manifest is unreadable: {error}") from error
    except json.JSONDecodeError as error:
        raise NeutralityError(f"manifest is not JSON: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != "body-neutrality/v1":
        raise NeutralityError("manifest.schema must be body-neutrality/v1")
    owed = document.get("owed")
    if not isinstance(owed, dict):
        raise NeutralityError("manifest.owed must be an object of path -> count")
    for name, value in owed.items():
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise NeutralityError(f"manifest.owed[{name!r}] must be a positive integer")
    return owed


def compare(actual: dict[str, int], owed: dict[str, int]) -> list[str]:
    problems: list[str] = []
    for name in sorted(set(actual) | set(owed)):
        has, allowed = actual.get(name, 0), owed.get(name, 0)
        if has > allowed:
            problems.append(
                f"{name}: names a host repository or host path on {has} line(s), "
                f"{allowed} allowed. Move it to a binding, or make the sentence true "
                "in any repository."
            )
        elif has < allowed:
            problems.append(
                f"{name}: allowance is {allowed} but only {has} line(s) remain. "
                f"Lower it to {has or 'nothing'} -- an allowance nobody spends stops "
                "describing the debt and becomes a permanent exemption."
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="lower entries to what the tree actually owes; never raises one",
    )
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    repo_root = args.repo_root.resolve()
    manifest_path = repo_root / "evals" / "body-neutrality.json"
    try:
        actual = measure(repo_root / "skills")
        owed = load_manifest(manifest_path)
    except NeutralityError as error:
        print(f"BODY NEUTRALITY UNUSABLE: {error}", file=sys.stderr)
        return 64

    if args.update_baseline:
        lowered = {
            name: count
            for name, count in owed.items()
            if name in actual and actual[name] < count
        }
        removed = sorted(set(owed) - set(actual))
        raised = sorted(name for name, count in actual.items() if count > owed.get(name, 0))
        if raised:
            print(
                "BODY NEUTRALITY REFUSED: --update-baseline only lowers. These would "
                "rise:\n  " + "\n  ".join(raised),
                file=sys.stderr,
            )
            return 2
        updated = {name: actual[name] for name in owed if name in actual}
        manifest_path.write_text(
            json.dumps({"schema": "body-neutrality/v1", "owed": dict(sorted(updated.items()))},
                       indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"BODY NEUTRALITY BASELINE LOWERED: {len(lowered)} file(s) reduced, "
              f"{len(removed)} cleared")
        return 0

    problems = compare(actual, owed)
    if problems:
        print("BODY NEUTRALITY RED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(
        f"BODY NEUTRALITY GREEN: {sum(actual.values())} line(s) of host binding remain "
        f"in {len(actual)} file(s), none more than the manifest records"
    )
    return 0


def selftest() -> int:
    import tempfile

    def build(root: Path, body: dict[str, str], owed: dict[str, int]) -> Path:
        (root / "skills" / "demo").mkdir(parents=True, exist_ok=True)
        (root / "evals").mkdir(parents=True, exist_ok=True)
        for name, text in body.items():
            path = root / "skills" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (root / "evals" / "body-neutrality.json").write_text(
            json.dumps({"schema": "body-neutrality/v1", "owed": owed}, indent=2) + "\n",
            encoding="utf-8",
        )
        return root

    def run(root: Path) -> list[str]:
        return compare(measure(root / "skills"), load_manifest(root / "evals" / "body-neutrality.json"))

    neutral = "# Demo\n\nThis sentence is true in any repository.\n"
    bound = "# Demo\n\nRun it in skill-bettor.\nThen check antigravity.\n"

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)

        # A neutral body with an empty manifest is the state this is heading for.
        if run(build(root / "clean", {"demo/SKILL.md": neutral}, {})):
            print("FAIL: a neutral body was reported as owing something", file=sys.stderr)
            return 2

        # Recorded debt passes; that is the point of a ratchet.
        if run(build(root / "recorded", {"demo/SKILL.md": bound},
                     {"skills/demo/SKILL.md": 2})):
            print("FAIL: recorded debt was refused", file=sys.stderr)
            return 2

        # New debt in a file that owed nothing.
        problems = run(build(root / "new", {"demo/SKILL.md": bound}, {}))
        if not problems or "2 line(s)" not in problems[0] or "0 allowed" not in problems[0]:
            print(f"FAIL: new debt was not refused: {problems}", file=sys.stderr)
            return 2

        # More debt than recorded.
        problems = run(build(root / "more", {"demo/SKILL.md": bound},
                             {"skills/demo/SKILL.md": 1}))
        if not problems or "1 allowed" not in problems[0]:
            print(f"FAIL: growth beyond the allowance was not refused: {problems}",
                  file=sys.stderr)
            return 2

        # A stale allowance: the debt was paid and the number was left behind.
        problems = run(build(root / "stale", {"demo/SKILL.md": neutral},
                             {"skills/demo/SKILL.md": 2}))
        if not problems or "Lower it to" not in problems[0]:
            print(f"FAIL: a stale allowance was accepted: {problems}", file=sys.stderr)
            return 2

        # `ts-skill-bettor` contains `skill-bettor`. One line, one hit.
        problems = run(build(root / "overlap",
                             {"demo/SKILL.md": "# D\n\nSee ts-skill-bettor here.\n"},
                             {"skills/demo/SKILL.md": 1}))
        if problems:
            print(f"FAIL: an overlapping name was double-counted: {problems}",
                  file=sys.stderr)
            return 2

        # An absolute host path is binding for the same reason a repository name is.
        problems = run(build(root / "hostpath",
                             {"demo/SKILL.md": "# D\n\nEdit ~/.claude/settings.json.\n"},
                             {}))
        if not problems:
            print("FAIL: a host path was accepted in shared body", file=sys.stderr)
            return 2

        # An archived copy is a record of what was superseded, not shared body.
        problems = run(build(root / "archive",
                             {"superseded/old/SKILL.md": bound}, {}))
        if problems:
            print(f"FAIL: an archived file was counted as body: {problems}",
                  file=sys.stderr)
            return 2

    print("SELFTEST GREEN: body neutrality ratchets down and refuses to ratchet up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
