#!/usr/bin/env python3
"""Execute the mechanisable half of `docs/architecture/DOCUMENT_ROUTING.md`.

Nineteen assertions DR-01..DR-19 were written down and none of them ran. #322
names that shape directly -- "Markdown-only route counted as executable" -- and
a routing law that only exists as prose is the control that has to be killed:
it is green by construction, so every drift it describes is invisible.

Zero network. Reads the tree and the indexes that claim to describe it.

Implemented here
----------------
DR-01  Every standard route named in the `AGENTS.md` document-route authority
       block exists. Placeholder rows (`<governed-directory>/...`) are route
       *shapes*, not paths, and are skipped.
DR-02  Every relative Markdown link under the governed surface resolves to a
       path that is actually on the tree. `check_index_coverage.py` also
       resolves links, and it is not made redundant by this one nor this by
       it: that gate can exempt a document at an exact content digest, and it
       was exempting the three projections that held every dead link in the
       repository, including the `file://` one. DR-02 admits no exemption, so
       running it emptied that list.
DR-03  Every `skills/<name>/` has a nearest README, or falls under the
       inheritance `skills/README.md` names ("A small Skill may contain only
       `SKILL.md`") -- which means it must actually ship that `SKILL.md`. A
       directory with neither owns nothing and inherits nothing.
DR-06  (link half) No Markdown link target is a machine-local path: no
       `file://`, no `/Users/...`, no `/home/...`, no `~/project/...`. The
       prose half of DR-06 -- host repository names in shared body text -- is
       already ratcheted by `scripts/check_body_neutrality.py`; duplicating it
       here would create a second rule set for one law.
DR-13  `docs/INDEX.md`'s routed-README set, and the counts it states about
       itself, are reconciled against the tree inventory. A README on the tree
       is either linked from the index or named in it as a known omission;
       every stated number must equal the measured one. An index that reports
       its own completeness in prose is exactly the failure DR-13 describes.
DR-14  No path in an index row whose status cell reads `PLANNED` exists on the
       tree. No such row is in the tree today, so this assertion is vacuous
       right now; `tests/test_document_routes.py` plants one to prove the
       check still goes red when a row appears. `assert_repository_closure_contract.py`
       enforces the same law on a typed closure contract; this one enforces it
       on the Markdown indexes, which are what a reader actually navigates.

Deliberately not implemented, and why
-------------------------------------
DR-04  "A README names owner, purpose, inputs, outputs, state machine,
       evidence, allowed and forbidden changes." Heading-keyword matching
       would pass any README that pasted eight headings and wrote nothing
       under them, so the gate would measure formatting, not ownership.
DR-05  "Markdown does not duplicate a machine authority." Deciding that a
       table duplicates a schema, rather than summarising it as the
       knowledge-continuity rule *requires*, is a semantic judgement.
DR-07  Evidence-vocabulary distinctness. Every one of those six words appears
       in prose that explains the distinction; grep cannot separate a document
       that keeps the states apart from one that discusses them.
DR-08  Target versus current state separation. Mechanising it needs a
       per-document declaration of which one it is; no such declaration
       exists in the tree today, and inventing one here would be a new
       contract smuggled in as a gate.
DR-09  `SKILL.md` procedural versus `modules/` instance. Judging "is this
       sentence a generalization or an instance" is the semantic core of the
       skill-authoring law, not a pattern.
DR-10  Cross-repository agreement. The sibling checkouts are not present, and
       DOCUMENT_ROUTING's own evidence boundary forbids inferring their
       contents from here.
DR-11  Git Town operation vocabulary -- conditional on an admission fact that
       lives outside this repository.
DR-12  Source-proposal promotion. Needs the verification receipt for each
       claim; that is the eval plane's subject, gated by `check_skill_evals.py`.
DR-15..DR-19  Evidence-kind, delivery-state, edge-class, lane and convergence
       distinctness. These are properties of issue/PR/receipt records held on
       the forges, not of the Markdown in this tree. `check_release_receipts.py`
       and `check_intent_promotions.py` own the parts that are local.

Exits: 0 green, 1 a routing assertion is red, 64 the gate could not run.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `[text](target)` and `[text](target "title")`. Reference-style links are not
# used in this tree; if they appear, they resolve to nothing here and DR-02
# would not see them -- which is why the absent-pattern exits below are FATAL
# rather than silent.
LINK = re.compile(r"\[[^\]]*\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
MACHINE_PATH = re.compile(r"^(?:file:|/Users/|/home/|~/(?!\.))")

# DR-13's numbers. Each is FATAL when absent: an index that stopped stating a
# count is not an index that satisfies the count.
INDEX_CLAIMS = (
    ("ship", re.compile(r"(\d+) of (\d+) skill directories ship a")),
    ("routed", re.compile(r"(\d+) are routed above")),
    ("unrouted", re.compile(r"The (\w+) that ship one and are still unrouted")),
    ("bare", re.compile(r"remaining (\d+) directories have no nearest-README")),
)
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


class Unusable(Exception):
    """The gate cannot decide anything, which is not the same as a pass."""


def archive_parts(repo_root: Path) -> set[str]:
    """The archive/evidence exclusion set, taken from the gate that owns it.

    `check_body_neutrality.py` already decides which directory names hold
    superseded records rather than live routes. A second list here would drift
    from that one and the two gates would disagree about what the repository is.
    """
    canonical = (
        repo_root / "skills" / "shared-skills-infra" / "scripts" / "check_body_neutrality.py"
    )
    if not canonical.is_file():
        raise Unusable(f"cannot reach the body-neutrality owner: {canonical}")
    spec = importlib.util.spec_from_file_location("_body_neutrality", canonical)
    if spec is None or spec.loader is None:
        raise Unusable(f"cannot load {canonical}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        _, ownership = module.load_manifest(repo_root / "evals" / "body-neutrality.json")
    except module.NeutralityError as error:
        raise Unusable(f"body-neutrality manifest is unusable: {error}") from error
    return set(ownership["archive_evidence"]["parts"])


def governed_documents(repo_root: Path, excluded: set[str]) -> list[Path]:
    return [
        path
        for path in sorted(repo_root.rglob("*.md"))
        if not (set(path.relative_to(repo_root).parts) & (excluded | {".git"}))
    ]


def standard_routes(repo_root: Path) -> list[str]:
    """The route names AGENTS.md declares under "Document-route authority"."""
    text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    match = re.search(
        r"## Document-route authority.*?```text\n(.*?)```", text, re.DOTALL
    )
    if match is None:
        raise Unusable(
            "AGENTS.md has no `## Document-route authority` text block; DR-01 "
            "has nothing to check, which is not the same as DR-01 passing"
        )
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def check_dr01(repo_root: Path) -> list[str]:
    problems = []
    for route in standard_routes(repo_root):
        if route.startswith("<"):
            continue  # a route shape, resolved per governed directory
        if not (repo_root / route).exists():
            problems.append(
                f"DR-01 AGENTS.md declares the standard route `{route}` and the "
                f"tree has no such path. Create it, or state the binding that "
                f"says why this repository has no such route."
            )
    return problems


def check_dr02_dr06(repo_root: Path, documents: list[Path]) -> list[str]:
    problems = []
    for path in documents:
        relative = path.relative_to(repo_root).as_posix()
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for match in LINK.finditer(line):
                target = match.group(1)
                if MACHINE_PATH.match(target):
                    problems.append(
                        f"DR-06 {relative}:{number} links to the machine-local "
                        f"path `{target}`. A path that only exists on one "
                        f"checkout is not a route."
                    )
                    continue
                if SCHEME.match(target) or target.startswith(("#", "//")):
                    continue
                resolved = target.split("#", 1)[0]
                if not resolved:
                    continue
                if not (path.parent / resolved).exists():
                    problems.append(
                        f"DR-02 {relative}:{number} links to `{target}`, which "
                        f"is not on the tree. Point it at what exists, or drop "
                        f"the claim -- a link to a file that never existed is a "
                        f"routing defect, not a missing file to write."
                    )
    return problems


def check_dr03(repo_root: Path) -> list[str]:
    problems = []
    skills = repo_root / "skills"
    if not skills.is_dir():
        raise Unusable("skills/ is absent; DR-03 has no governed directories")
    for directory in sorted(p for p in skills.iterdir() if p.is_dir()):
        if (directory / "README.md").is_file():
            continue
        # No own README: the inheritance skills/README.md names applies only to
        # a Skill that is small enough to be a single procedural body.
        nearest = None
        for ancestor in directory.parents:
            if (ancestor / "README.md").is_file():
                nearest = ancestor
                break
            if ancestor == repo_root:
                break
        name = directory.relative_to(repo_root).as_posix()
        if nearest is None:
            problems.append(
                f"DR-03 {name}/ has no README.md and no ancestor README to "
                f"inherit from, so the directory has no nearest owner."
            )
        elif not (directory / "SKILL.md").is_file():
            problems.append(
                f"DR-03 {name}/ has neither README.md nor SKILL.md. The "
                f"inheritance in {nearest.relative_to(repo_root).as_posix()}"
                f"/README.md covers a Skill that ships only SKILL.md; this "
                f"directory claims an owner it does not qualify for."
            )
    return problems


def check_dr13(repo_root: Path) -> list[str]:
    index_path = repo_root / "docs" / "INDEX.md"
    if not index_path.is_file():
        raise Unusable("docs/INDEX.md is absent; DR-13 has no index to reconcile")
    index = index_path.read_text(encoding="utf-8")
    skills = repo_root / "skills"
    directories = sorted(p.name for p in skills.iterdir() if p.is_dir())
    ships = [name for name in directories if (skills / name / "README.md").is_file()]
    routed = [name for name in ships if f"../skills/{name}/README.md" in index]
    unrouted = [name for name in ships if name not in routed]

    problems = []
    for name in unrouted:
        if f"`{name}`" not in index:
            problems.append(
                f"DR-13 skills/{name}/README.md is on the tree, is not routed "
                f"from docs/INDEX.md, and is not named there as a known "
                f"omission. An omission that is not named reads as completeness."
            )

    measured = {
        "ship": (len(ships), len(directories)),
        "routed": (len(routed),),
        "unrouted": (len(unrouted),),
        "bare": (len(directories) - len(ships),),
    }
    for key, pattern in INDEX_CLAIMS:
        match = pattern.search(index)
        if match is None:
            raise Unusable(
                f"docs/INDEX.md no longer states its {key!r} count "
                f"(/{pattern.pattern}/). The count is the reconciliation; "
                f"removing it is not satisfying it. Measured now: "
                f"{measured[key]}."
            )
        stated = tuple(
            NUMBER_WORDS.get(value.lower(), None) if not value.isdigit() else int(value)
            for value in match.groups()
        )
        if None in stated:
            raise Unusable(
                f"docs/INDEX.md states its {key!r} count as {match.groups()}, "
                f"which is not a number this gate can read."
            )
        if stated != measured[key]:
            problems.append(
                f"DR-13 docs/INDEX.md states {key}={stated} and the tree has "
                f"{measured[key]}. Reconcile the index with the inventory, not "
                f"with the previous sentence."
            )
    return problems


def check_dr14(repo_root: Path, documents: list[Path]) -> list[str]:
    """A status *cell* reading PLANNED, next to a path that is on the tree.

    Only index table rows are read. Every other `PLANNED` in this tree is the
    word being defined -- DR-14 itself, the closure vocabulary, the state
    enumerations -- and a line-wide match reports those as defects, which was
    the first thing this check did. A status is a cell, not a mention.
    """
    problems = []
    for path in documents:
        relative = path.relative_to(repo_root).as_posix()
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if "PLANNED" not in line or not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip().strip("`").strip() for cell in line.split("|")]
            if "PLANNED" not in cells:
                continue
            candidates = set(CODE_SPAN.findall(line)) | {
                match.group(1).split("#", 1)[0] for match in LINK.finditer(line)
            }
            for candidate in sorted(candidates):
                token = candidate.strip().rstrip(",.;")
                if not token or SCHEME.match(token) or token.startswith("/"):
                    continue
                for base in (repo_root, path.parent):
                    if (base / token).exists():
                        problems.append(
                            f"DR-14 {relative}:{number} marks `{token}` PLANNED "
                            f"and the path exists. An existing path is never "
                            f"PLANNED."
                        )
                        break
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    try:
        documents = governed_documents(repo_root, archive_parts(repo_root))
        problems = (
            check_dr01(repo_root)
            + check_dr02_dr06(repo_root, documents)
            + check_dr03(repo_root)
            + check_dr13(repo_root)
            + check_dr14(repo_root, documents)
        )
    except (Unusable, OSError) as error:
        print(f"DOCUMENT ROUTES UNUSABLE: {error}", file=sys.stderr)
        return 64

    if problems:
        print("DOCUMENT ROUTES RED:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(
        f"DOCUMENT ROUTES GREEN: DR-01/02/03/06/13/14 hold across "
        f"{len(documents)} governed document(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
