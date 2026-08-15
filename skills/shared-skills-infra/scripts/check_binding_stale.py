#!/usr/bin/env python3
"""#1's second gate: surface bindings whose shared body has moved underneath them.

A skill has two kinds of content. The body is true in any repository; the
binding is true only in one host -- which loops that host runs, pointers into
its private documents, the retarget ledger. #1's ruling puts the binding in
`<repo>/.skill-bindings/<skill>/binding.md` with four fields, one of which is
`body_version`: the shared body's content hash at the moment the binding was
written.

That field is the whole mechanism. When the body changes, every binding pinned
to the old hash is listed at once, so re-retargeting becomes a task with a
checklist instead of something discovered by tripping over it in one repository
at a time. Without it, a fix to the shared body reaches four other repositories
as a silent no-op and gets rediscovered there later.

Three states, three exits, deliberately distinct:

    binding absent   the host has not retargeted this skill. Absence, not
                     breakage: it uses the body's generic form, and reporting it
                     as a failure would make "not adopted" indistinguishable
                     from "adopted and broken".
    current          body_version equals the body hash. Nothing to do.
    stale            body_version disagrees. SURFACE, exit 3 -- this is "time to
                     re-retarget", not "something is wrong", and a caller that
                     cannot tell those apart will either ignore real failures or
                     block on routine drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FIELDS = ("skill", "upstream", "retargeted_at", "body_version")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
# Legacy snapshots live in the binding directory by ruling 5 and deliberately do
# not track `body_version`; they are a record of what the host had before, not a
# claim about the current body.
UNTRACKED_PREFIX = "legacy-skill-"


class BindingError(Exception):
    pass


def body_hash(skill_root: Path) -> str:
    """Content hash of the shared body: every file, path and bytes, sorted.

    Paths are part of the hash because moving a module is a body change even
    when no byte inside it differs, and a binding pinned to the old layout is
    exactly as stale as one pinned to old content.
    """
    digest = hashlib.sha256()
    for path in sorted(p for p in skill_root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(skill_root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        raise BindingError(f"{path.name}: must open with a YAML frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise BindingError(f"{path.name}: frontmatter block is never closed")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise BindingError(f"{path.name}: frontmatter line is not key: value: {line!r}")
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key in fields:
            raise BindingError(f"{path.name}: duplicate frontmatter key {key!r}")
        fields[key] = value
    return fields


def check_binding(directory: Path, skills_root: Path) -> tuple[str, str]:
    """Return (state, detail) for one binding directory."""
    name = directory.name
    path = directory / "binding.md"
    if not path.is_file():
        raise BindingError(
            f"{name}: the slot exists but carries no binding.md; a directory with no "
            "contract is neither an adoption nor an absence"
        )
    fields = parse_frontmatter(path)
    missing = [field for field in REQUIRED_FIELDS if field not in fields]
    if missing:
        raise BindingError(f"{name}: binding.md is missing {missing}")
    extra = sorted(set(fields) - set(REQUIRED_FIELDS))
    if extra:
        raise BindingError(f"{name}: binding.md carries undeclared field(s) {extra}")
    if fields["skill"] != name:
        raise BindingError(
            f"{name}: binding.md names skill {fields['skill']!r}, so the slot and the "
            "contract disagree about what is bound"
        )
    if not fields["upstream"]:
        raise BindingError(f"{name}: upstream must name where the body came from")
    if not DATE_RE.fullmatch(fields["retargeted_at"]):
        raise BindingError(f"{name}: retargeted_at must be YYYY-MM-DD")
    if not DIGEST_RE.fullmatch(fields["body_version"]):
        raise BindingError(
            f"{name}: body_version must be the body's SHA-256, not {fields['body_version']!r}"
        )

    skill_root = skills_root / name
    if not skill_root.is_dir():
        raise BindingError(
            f"{name}: binds a skill that is not in the shared body; a binding to "
            "nothing cannot go stale, it is already wrong"
        )
    actual = body_hash(skill_root)
    if actual == fields["body_version"]:
        return "current", actual
    return "stale", actual


def scan(repo_root: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    slots = repo_root / ".skill-bindings"
    results: dict[str, tuple[str, str]] = {}
    problems: list[str] = []
    if not slots.is_dir():
        return results, problems
    skills_root = repo_root / "skills"
    for directory in sorted(p for p in slots.iterdir() if p.is_dir()):
        try:
            results[directory.name] = check_binding(directory, skills_root)
        except BindingError as error:
            problems.append(str(error))
    return results, problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    repo_root = args.repo_root.resolve()
    try:
        results, problems = scan(repo_root)
    except OSError as error:
        print(f"BINDING UNUSABLE: {error}", file=sys.stderr)
        return 64

    stale = sorted(name for name, (state, _) in results.items() if state == "stale")
    if args.json:
        print(json.dumps(
            {"bindings": {name: state for name, (state, _) in sorted(results.items())},
             "problems": problems}, indent=2, sort_keys=True))

    if problems:
        print("BINDING RED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    if stale:
        # Not a failure. The body moved and these hosts have not caught up, which
        # is the list this gate exists to produce.
        print(f"BINDING SURFACE: {len(stale)} binding(s) pinned to an older body:")
        for name in stale:
            print(f"  {name}: re-retarget, then set body_version to {results[name][1]}")
        return 3
    if not results:
        print("BINDING GREEN: no host has retargeted a shared skill here; "
              "absence, not breakage")
        return 0
    print(f"BINDING GREEN: {len(results)} binding(s), each pinned to the current body")
    return 0


def selftest() -> int:
    def build(root: Path, fields: dict[str, str] | None, *, skill: str = "demo",
              body: str = "method\n", extra_files: dict[str, str] | None = None) -> Path:
        skill_root = root / "skills" / skill
        skill_root.mkdir(parents=True, exist_ok=True)
        (skill_root / "SKILL.md").write_text(body, encoding="utf-8")
        for name, text in (extra_files or {}).items():
            path = skill_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        if fields is not None:
            slot = root / ".skill-bindings" / skill
            slot.mkdir(parents=True, exist_ok=True)
            block = "".join(f"{k}: {v}\n" for k, v in fields.items())
            (slot / "binding.md").write_text(f"---\n{block}---\n\nnotes\n", encoding="utf-8")
        return root

    def contract(root: Path, skill: str = "demo") -> dict[str, str]:
        return {
            "skill": skill,
            "upstream": "antigravity-demo@shared",
            "retargeted_at": "2026-08-14",
            "body_version": body_hash(root / "skills" / skill),
        }

    def state(root: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
        return scan(root)

    def expect_problem(label: str, root: Path, fragment: str) -> int:
        _, problems = state(root)
        if not problems:
            print(f"FAIL {label}: planted defect was not caught", file=sys.stderr)
            return 2
        if fragment not in problems[0]:
            print(f"FAIL {label}: refused for the wrong reason: {problems[0]}",
                  file=sys.stderr)
            return 2
        return 0

    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)

        # Absence is a state, not a failure, and must not read like one.
        root = build(base / "absent", None)
        results, problems = state(root)
        if results or problems:
            print(f"FAIL: an unbound skill was reported as something: "
                  f"{results} {problems}", file=sys.stderr)
            return 2

        root = build(base / "current", None)
        root = build(base / "current", contract(base / "current"))
        results, problems = state(root)
        if problems or results.get("demo", ("", ""))[0] != "current":
            print(f"FAIL: a current binding was not recognised: {results} {problems}",
                  file=sys.stderr)
            return 2

        # The mechanism itself: the body moves, the pin does not.
        root = build(base / "stale", None)
        pinned = contract(base / "stale")
        root = build(base / "stale", pinned, body="method, revised\n")
        results, problems = state(root)
        if problems or results.get("demo", ("", ""))[0] != "stale":
            print(f"FAIL: a moved body did not surface its binding: {results} {problems}",
                  file=sys.stderr)
            return 2

        # A file moved with no byte changed is still a body change, because a
        # binding pinned to the old layout is exactly as stale.
        root = build(base / "moved", None, extra_files={"modules/a.md": "x\n"})
        pinned = contract(base / "moved")
        root = build(base / "moved", pinned, extra_files={"modules/b.md": "x\n"})
        (root / "skills" / "demo" / "modules" / "a.md").unlink()
        results, _ = state(root)
        if results.get("demo", ("", ""))[0] != "stale":
            print("FAIL: a renamed module did not surface its binding", file=sys.stderr)
            return 2

        # Two stale bindings. With one slot per fixture, "surface every binding
        # left behind" and "surface the first one" are the same program, and the
        # list this gate exists to produce would silently be a list of one.
        root = base / "plural"
        for skill in ("alpha", "beta"):
            build(root, None, skill=skill)
        pins = {skill: contract(root, skill) for skill in ("alpha", "beta")}
        for skill in ("alpha", "beta"):
            build(root, pins[skill], skill=skill, body="method, revised\n")
        results, problems = state(root)
        if problems:
            print(f"FAIL: plural fixture reported problems: {problems}", file=sys.stderr)
            return 2
        stale = {name for name, (kind, _) in results.items() if kind == "stale"}
        if stale != {"alpha", "beta"}:
            print(f"FAIL: {len(stale)} of 2 stale bindings surfaced: {stale}",
                  file=sys.stderr)
            return 2

        for label, mutate, fragment in (
            ("missing-field", lambda f: f.pop("upstream"), "missing ['upstream']"),
            ("extra-field", lambda f: f.update({"note": "x"}), "undeclared field(s)"),
            ("slot-name-drift", lambda f: f.update({"skill": "other"}), "disagree about what is bound"),
            ("bad-date", lambda f: f.update({"retargeted_at": "yesterday"}), "must be YYYY-MM-DD"),
            ("bad-digest", lambda f: f.update({"body_version": "abc"}), "must be the body's SHA-256"),
            ("empty-upstream", lambda f: f.update({"upstream": ""}), "upstream must name"),
        ):
            root = build(base / label, None)
            fields = contract(base / label)
            mutate(fields)
            root = build(base / label, fields)
            code = expect_problem(label, root, fragment)
            if code:
                return code

        # A slot with no contract is neither an adoption nor an absence.
        root = build(base / "empty-slot", None)
        (root / ".skill-bindings" / "demo").mkdir(parents=True)
        code = expect_problem("empty-slot", root, "carries no binding.md")
        if code:
            return code

        # A binding to a skill that is not in the shared body cannot go stale.
        root = build(base / "orphan", None)
        fields = contract(base / "orphan")
        root = build(base / "orphan", fields)
        import shutil
        shutil.rmtree(root / "skills" / "demo")
        code = expect_problem("orphan", root, "binds a skill that is not in the shared body")
        if code:
            return code

        root = build(base / "malformed", None)
        slot = root / ".skill-bindings" / "demo"
        slot.mkdir(parents=True)
        (slot / "binding.md").write_text("no frontmatter here\n", encoding="utf-8")
        code = expect_problem("malformed", root, "must open with a YAML frontmatter")
        if code:
            return code

    print("SELFTEST GREEN: a moved body surfaces every binding pinned behind it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
