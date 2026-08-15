#!/usr/bin/env python3
"""#1's mechanical gate: a portable body may not name a specific host repository.

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

Manifest v2 classifies Markdown as portable_body, repo_binding_source,
generated_projection, or archive_evidence. Only portable_body enters this
ratchet. The other classes are not exemptions: their owning projection or
evidence gates must judge them, and an unclassified file defaults to portable.

This gate decides nothing about which history is canonical. It makes the
divergence countable, which is what has to happen before that decision can be
made on evidence rather than on preference.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "evals" / "body-neutrality.json"
BODY_ROOT = ROOT / "skills"
SCHEMA = "body-neutrality/v2"
CONTENT_CLASSES = {
    "portable_body",
    "repo_binding_source",
    "generated_projection",
    "archive_evidence",
}

HOST_REPOSITORIES = (
    "skill-bettor",
    "ts-skill-bettor",
    "antigravity",
    "ix-agy",
    "bettor-arena",
)
# `ts-skill-bettor` contains `skill-bettor`, so a line naming the first must not
# be counted twice. One alternation, longest first, one match per line.
# `~/` is not one thing. `~/.codex/config.toml` is where the Codex CLI reads its
# configuration on every machine and in every repository, so by the PRD's own
# test -- move it unchanged to another repository; is it still true? -- it is
# body, not binding. `~/proj-a/notes.md` is a path in somebody's checkout and
# fails that test.
#
# Measured before deciding: of 84 `~/` hits in the shared body, 83 pointed at
# `~/.claude`, `~/.codex`, `~/.agents` or `~/.gemini`, and exactly one at a
# project directory. Counting the 83 made the number describe something other
# than what the rule is about, and a debt figure that is mostly noise stops
# being read.
#
# The criterion, not a list of tools: a dot-directory under `~/` is a tool's own
# configuration; anything else under `~/` is a path in a project.
PATTERN = re.compile(
    "|".join(re.escape(name) for name in sorted(HOST_REPOSITORIES, key=len, reverse=True))
    + r"|/Users/[A-Za-z0-9._-]+/"
    + r"|/home/[A-Za-z0-9._-]+/"
    + r"|~/(?!\.)\S"
)


class NeutralityError(Exception):
    pass


def body_files(body_root: Path) -> list[Path]:
    return sorted(body_root.glob("**/*.md"))


def count_hits(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if PATTERN.search(line)
    )


def _validate_root(value: object, owner: str) -> str:
    if not isinstance(value, str) or not value:
        raise NeutralityError(f"ownership.{owner}.roots must contain strings")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise NeutralityError(f"ownership root is not a normalized relative path: {value!r}")
    if len(path.parts) < 3 or path.parts[0] != "skills":
        raise NeutralityError(
            f"ownership root may not exclude a repository or whole Skill: {value!r}"
        )
    return path.as_posix()


def load_ownership(document: dict[str, object]) -> dict[str, object]:
    ownership = document.get("ownership")
    if not isinstance(ownership, dict) or set(ownership) != CONTENT_CLASSES:
        raise NeutralityError(
            "manifest.ownership must define exactly portable_body, "
            "repo_binding_source, generated_projection, and archive_evidence"
        )
    portable = ownership.get("portable_body")
    if portable != {"default": True}:
        raise NeutralityError("ownership.portable_body must be the default class")

    normalized: dict[str, object] = {"portable_body": {"default": True}}
    all_roots: list[tuple[str, str]] = []
    for owner in ("repo_binding_source", "generated_projection"):
        rule = ownership.get(owner)
        if not isinstance(rule, dict) or set(rule) != {"roots"}:
            raise NeutralityError(f"ownership.{owner} must contain only roots")
        roots = rule.get("roots")
        if not isinstance(roots, list):
            raise NeutralityError(f"ownership.{owner}.roots must be an array")
        clean_roots = [_validate_root(root, owner) for root in roots]
        if len(set(clean_roots)) != len(clean_roots):
            raise NeutralityError(f"ownership.{owner}.roots contains duplicates")
        normalized[owner] = {"roots": sorted(clean_roots)}
        all_roots.extend((owner, root) for root in clean_roots)

    for index, (left_owner, left) in enumerate(all_roots):
        for right_owner, right in all_roots[index + 1 :]:
            if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
                raise NeutralityError(
                    f"ownership roots overlap: {left_owner}:{left} and {right_owner}:{right}"
                )

    archive = ownership.get("archive_evidence")
    if not isinstance(archive, dict) or set(archive) != {"parts"}:
        raise NeutralityError("ownership.archive_evidence must contain only parts")
    parts = archive.get("parts")
    if not isinstance(parts, list) or any(
        not isinstance(part, str) or not part or "/" in part or part in {".", ".."}
        for part in parts
    ):
        raise NeutralityError(
            "ownership.archive_evidence.parts must be an array of path components"
        )
    if len(set(parts)) != len(parts):
        raise NeutralityError("ownership.archive_evidence.parts contains duplicates")
    normalized["archive_evidence"] = {"parts": sorted(parts)}
    return normalized


def classify(path: Path, body_root: Path, ownership: dict[str, object]) -> str:
    relative = path.relative_to(body_root.parent).as_posix()
    relative_parts = PurePosixPath(relative).parts
    matches: list[str] = []
    for owner in ("repo_binding_source", "generated_projection"):
        rule = ownership[owner]
        assert isinstance(rule, dict)
        for root in rule["roots"]:
            if relative == root or relative.startswith(str(root) + "/"):
                matches.append(owner)
                break
    archive = ownership["archive_evidence"]
    assert isinstance(archive, dict)
    if set(relative_parts) & set(archive["parts"]):
        matches.append("archive_evidence")
    if len(matches) > 1:
        raise NeutralityError(
            f"{relative} matches multiple ownership classes: {', '.join(matches)}"
        )
    return matches[0] if matches else "portable_body"


def measure(
    body_root: Path, ownership: dict[str, object]
) -> tuple[dict[str, int], dict[str, int]]:
    counts: dict[str, int] = {}
    class_counts = {name: 0 for name in sorted(CONTENT_CLASSES)}
    for path in body_files(body_root):
        owner = classify(path, body_root, ownership)
        class_counts[owner] += 1
        if owner != "portable_body":
            continue
        hits = count_hits(path)
        if hits:
            counts[path.relative_to(body_root.parent).as_posix()] = hits
    return counts, class_counts


def load_manifest(path: Path) -> tuple[dict[str, int], dict[str, object]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise NeutralityError(f"manifest is unreadable: {error}") from error
    except json.JSONDecodeError as error:
        raise NeutralityError(f"manifest is not JSON: {error}") from error
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise NeutralityError(f"manifest.schema must be {SCHEMA}")
    if set(document) != {"schema", "ownership", "owed"}:
        raise NeutralityError("manifest fields must be exactly schema, ownership, and owed")
    ownership = load_ownership(document)
    owed = document.get("owed")
    if not isinstance(owed, dict):
        raise NeutralityError("manifest.owed must be an object of path -> count")
    for name, value in owed.items():
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise NeutralityError(f"manifest.owed[{name!r}] must be a positive integer")
    return owed, ownership


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
        owed, ownership = load_manifest(manifest_path)
        actual, class_counts = measure(repo_root / "skills", ownership)
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
            json.dumps(
                {
                    "schema": SCHEMA,
                    "ownership": ownership,
                    "owed": dict(sorted(updated.items())),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
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
        f"in {len(actual)} portable file(s), none more than the manifest records; "
        + " ".join(f"{name}={class_counts[name]}" for name in sorted(class_counts))
    )
    return 0


def selftest() -> int:
    import tempfile

    ownership = {
        "portable_body": {"default": True},
        "repo_binding_source": {"roots": []},
        "generated_projection": {"roots": []},
        "archive_evidence": {"parts": ["superseded"]},
    }

    def build(
        root: Path,
        body: dict[str, str],
        owed: dict[str, int],
        custom_ownership: dict[str, object] | None = None,
    ) -> Path:
        (root / "skills" / "demo").mkdir(parents=True, exist_ok=True)
        (root / "evals").mkdir(parents=True, exist_ok=True)
        for name, text in body.items():
            path = root / "skills" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (root / "evals" / "body-neutrality.json").write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "ownership": custom_ownership or ownership,
                    "owed": owed,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return root

    def run(root: Path) -> list[str]:
        owed, loaded_ownership = load_manifest(root / "evals" / "body-neutrality.json")
        actual, _ = measure(root / "skills", loaded_ownership)
        return compare(actual, owed)

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

        # A machine-local absolute path is binding for the same reason a
        # repository name is.
        problems = run(build(root / "hostpath",
                             {"demo/SKILL.md": "# D\n\nEdit /Users/someone/notes.md.\n"},
                             {}))
        if not problems:
            print("FAIL: a machine path was accepted in shared body", file=sys.stderr)
            return 2

        # A tool's own configuration directory is true in any repository.
        problems = run(build(root / "toolconfig",
                             {"demo/SKILL.md": "# D\n\nEdit ~/.codex/config.toml.\n"},
                             {}))
        if problems:
            print(f"FAIL: a tool config path was counted as binding: {problems}",
                  file=sys.stderr)
            return 2

        # A project directory under ~/ is not.
        problems = run(build(root / "homeproject",
                             {"demo/SKILL.md": "# D\n\nOpen ~/proj-a/README.md.\n"},
                             {}))
        if not problems:
            print("FAIL: a home project path was accepted in shared body",
                  file=sys.stderr)
            return 2

        # Two offenders, because a fixture whose group size is one cannot tell
        # "report every file" apart from "report the first file". #16 names this
        # as the shape that made a whole class of guards unfalsifiable, and both
        # gates added for #1 had it until this case existed.
        problems = run(build(root / "plural",
                             {"demo/SKILL.md": bound, "other/SKILL.md": bound}, {}))
        if len(problems) != 2:
            print(f"FAIL: {len(problems)} of 2 offending files reported: {problems}",
                  file=sys.stderr)
            return 2
        reported = {problem.split(":")[0] for problem in problems}
        if reported != {"skills/demo/SKILL.md", "skills/other/SKILL.md"}:
            print(f"FAIL: the wrong files were reported: {reported}", file=sys.stderr)
            return 2

        # An archived copy is a record of what was superseded, not shared body.
        problems = run(build(root / "archive",
                             {"superseded/old/SKILL.md": bound}, {}))
        if problems:
            print(f"FAIL: an archived file was counted as body: {problems}",
                  file=sys.stderr)
            return 2

        # Repo-binding sources are typed non-body, not a blanket directory
        # exemption. The same bytes outside the admitted root remain debt.
        binding_ownership = {
            **ownership,
            "repo_binding_source": {
                "roots": ["skills/demo/agent-docs"]
            },
        }
        problems = run(build(
            root / "binding-source",
            {"demo/agent-docs/example/AGENTS.md": bound},
            {},
            binding_ownership,
        ))
        if problems:
            print(f"FAIL: typed repo-binding source was counted as body: {problems}",
                  file=sys.stderr)
            return 2
        problems = run(build(root / "untyped-binding", {"demo/AGENTS.md": bound}, {}))
        if not problems:
            print("FAIL: untyped repository binding escaped the portable-body ratchet",
                  file=sys.stderr)
            return 2

    print("SELFTEST GREEN: body neutrality ratchets down and refuses to ratchet up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
