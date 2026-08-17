#!/usr/bin/env python3
"""Validate a Molecular Stack index.

A Stack index is only useful if it can be wrong. This gate refuses the six ways
an index quietly stops describing the Stack: a hidden multi-parent convergence,
a path-disjoint sibling dressed up as a serialized child, a required atom that
was never indexed, two atoms holding the same path lease, a mutable open PR head
frozen into the index, and a ceremonial atom that owns nothing and proves
nothing.

Exit codes: 0 pass, 2 index failure, 64 input/usage.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = SKILL_ROOT / "references" / "example-molecular-stack-index.json"

ATOM_LETTERS = {"C", "K", "A", "E", "X", "D"}
STACK_CLASSES = {"root", "sibling", "child", "convergence"}
PR_STATES = {"NOT_CREATED", "DRAFT", "READY", "MERGED"}
OPEN_PR_STATES = {"DRAFT", "READY"}
SHA40 = set("0123456789abcdef")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("index root must be an object")
    return value


def is_sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(ch in SHA40 for ch in text)


def overlap(left: str, right: str) -> bool:
    a = left.strip("/")
    b = right.strip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def validate(index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if index.get("schema_version") != "git-town/molecular-stack-index/v1":
        errors.append("schema_version must be git-town/molecular-stack-index/v1")

    subject = index.get("subject", {})
    if not isinstance(subject, dict) or not is_sha40(subject.get("commit")):
        errors.append("subject.commit must be exact SHA-40")
    if not isinstance(subject, dict) or str(subject.get("repository", "")).count("/") != 1:
        errors.append("subject.repository must use owner/name form")

    main = index.get("main_branch")
    if not isinstance(main, str) or not main.strip():
        errors.append("main_branch must be non-empty")
        main = "main"

    atoms = index.get("atoms")
    if not isinstance(atoms, list) or not atoms:
        return errors + ["atoms must be a non-empty array"]

    by_id: dict[str, dict[str, Any]] = {}
    branches: set[str] = set()
    for position, atom in enumerate(atoms):
        if not isinstance(atom, dict):
            errors.append(f"atoms[{position}] must be an object")
            continue
        atom_id = str(atom.get("id"))
        if atom_id in by_id:
            errors.append(f"{atom_id}: duplicate atom id")
        by_id[atom_id] = atom
        branch = str(atom.get("branch"))
        if branch in branches:
            errors.append(f"{atom_id}: duplicate branch {branch}")
        branches.add(branch)

    required = index.get("required_atoms")
    if not isinstance(required, list) or not required:
        errors.append("required_atoms must be a non-empty array")
        required = []
    indexed_letters = {atom.get("atom") for atom in by_id.values()}
    for letter in required:
        if letter not in ATOM_LETTERS:
            errors.append(f"required_atoms contains unknown atom {letter}")
        elif letter not in indexed_letters:
            errors.append(f"required atom {letter} is missing from the index")

    owner = index.get("convergence_owner")
    if owner not in by_id:
        errors.append("convergence_owner names an unknown atom")
    convergences = [atom_id for atom_id, atom in by_id.items() if atom.get("stack_class") == "convergence"]
    if len(convergences) != 1:
        errors.append("exactly one atom must be the convergence owner")
    elif convergences[0] != owner:
        errors.append(f"{convergences[0]}: convergence atom is not the declared convergence owner")
    roots = [atom_id for atom_id, atom in by_id.items() if atom.get("stack_class") == "root"]
    if len(roots) != 1:
        errors.append("exactly one atom must be the Stack root")

    for atom_id, atom in by_id.items():
        letter = atom.get("atom")
        stack_class = atom.get("stack_class")
        if letter not in ATOM_LETTERS:
            errors.append(f"{atom_id}: invalid atom letter")
        if stack_class not in STACK_CLASSES:
            errors.append(f"{atom_id}: invalid stack_class")

        owns = atom.get("owns_paths")
        consumes = atom.get("consumes_paths")
        gates = atom.get("gates")
        if not isinstance(owns, list) or not isinstance(consumes, list) or not isinstance(gates, list):
            errors.append(f"{atom_id}: owns_paths, consumes_paths and gates must be arrays")
            continue
        if not owns or not gates or not str(atom.get("oracle", "")).strip() or not str(atom.get("purpose", "")).strip():
            errors.append(f"{atom_id}: empty ceremonial atom — an atom owns paths, one oracle and at least one Gate")
        if not str(atom.get("writer_lease", "")).strip():
            errors.append(f"{atom_id}: no writer lease owner")

        parents = atom.get("parents")
        if not isinstance(parents, list):
            errors.append(f"{atom_id}: parents must be an array")
            continue
        unknown = [parent for parent in parents if parent not in by_id]
        for parent in unknown:
            errors.append(f"{atom_id}: unknown parent {parent}")
        known_parents = [by_id[parent] for parent in parents if parent in by_id]
        if len(parents) > 1 and (stack_class != "convergence" or atom_id != owner):
            errors.append(f"{atom_id}: multi-parent convergence is not the declared convergence owner")

        base = atom.get("base_branch")
        parent_branches = [str(parent.get("branch")) for parent in known_parents]
        if stack_class in {"root", "sibling"}:
            if parents:
                errors.append(f"{atom_id}: {stack_class} must not name a parent atom")
            if base != main:
                errors.append(f"{atom_id}: {stack_class} must base on {main}")
            if consumes:
                errors.append(f"{atom_id}: {stack_class} consumes unmerged parent bytes and is really a child")
        elif stack_class == "child":
            if len(parents) != 1:
                errors.append(f"{atom_id}: child must name exactly one parent atom")
            if parent_branches and base not in parent_branches:
                errors.append(f"{atom_id}: base branch is not the exact parent branch")
            if not consumes:
                errors.append(
                    f"{atom_id}: false serialization — a child that consumes no parent path is a path-disjoint sibling"
                )
        elif stack_class == "convergence":
            if len(parents) < 2:
                errors.append(f"{atom_id}: convergence must name at least two parent atoms")
            if parent_branches and base not in parent_branches:
                errors.append(f"{atom_id}: base branch is not the exact parent branch")
            if not consumes:
                errors.append(f"{atom_id}: convergence must consume its parents' paths")

        for consumed in consumes:
            if not any(overlap(consumed, owned) for parent in known_parents for owned in parent.get("owns_paths", [])):
                errors.append(f"{atom_id}: consumed path {consumed} is owned by no declared parent")

        pull_request = atom.get("pr", {})
        if not isinstance(pull_request, dict):
            errors.append(f"{atom_id}: pr must be an object")
            continue
        state = pull_request.get("state")
        head_sha = pull_request.get("head_sha")
        head_source = pull_request.get("head_source")
        if state not in PR_STATES:
            errors.append(f"{atom_id}: invalid pr.state")
        elif state in OPEN_PR_STATES:
            if head_sha is not None:
                errors.append(f"{atom_id}: stale self-embedded open PR head; live provider metadata is the authority")
            if head_source != "LIVE_PROVIDER":
                errors.append(f"{atom_id}: open PR head_source must be LIVE_PROVIDER")
        elif state == "MERGED":
            if not is_sha40(head_sha):
                errors.append(f"{atom_id}: merged atom must record an exact head SHA")
            if head_source != "IMMUTABLE_MERGED":
                errors.append(f"{atom_id}: merged head must be IMMUTABLE_MERGED")
        elif state == "NOT_CREATED":
            if head_sha is not None or head_source != "ABSENT":
                errors.append(f"{atom_id}: uncreated PR must be ABSENT with no head")

    # Path leases are molecular: two atoms never write the same bytes.
    names = sorted(by_id)
    for position, left_id in enumerate(names):
        left = by_id[left_id]
        for right_id in names[position + 1 :]:
            right = by_id[right_id]
            for left_path in left.get("owns_paths", []) or []:
                for right_path in right.get("owns_paths", []) or []:
                    if overlap(left_path, right_path):
                        errors.append(
                            f"overlapping writer leases: {left_id}:{left_path} and {right_id}:{right_path}"
                        )
    return errors


def selftest(index: dict[str, Any]) -> list[str]:
    already_red = validate(index)
    if already_red:
        return [f"positive index is already red: {error}" for error in already_red]

    cases: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("HIDDEN_MULTI_PARENT_CONVERGENCE",
         lambda i: i["atoms"][1].__setitem__("parents", ["ATOM-C1", "ATOM-A1"]),
         "multi-parent convergence is not the declared convergence owner"),
        ("FALSE_SERIALIZATION_OF_PATH_DISJOINT_SIBLINGS",
         lambda i: i["atoms"][1].__setitem__("consumes_paths", []),
         "false serialization"),
        ("MISSING_ATOM_HIDDEN_FROM_INDEX",
         lambda i: i["atoms"].pop(3),
         "required atom E is missing from the index"),
        ("OVERLAPPING_WRITER_LEASES",
         lambda i: i["atoms"][2].__setitem__("owns_paths", ["packages/core/"]),
         "overlapping writer leases"),
        ("STALE_PR_HEAD_REUSED",
         lambda i: i["atoms"][1]["pr"].__setitem__("head_sha", "3" * 40),
         "stale self-embedded open PR head"),
        ("EMPTY_CEREMONIAL_ATOM",
         lambda i: i["atoms"][2].__setitem__("owns_paths", []),
         "empty ceremonial atom"),
        ("CHILD_BASED_OFF_THE_WRONG_BRANCH",
         lambda i: i["atoms"][1].__setitem__("base_branch", "main"),
         "base branch is not the exact parent branch"),
        ("MERGED_HEAD_DOWNGRADED_TO_MUTABLE",
         lambda i: i["atoms"][0]["pr"].__setitem__("head_source", "LIVE_PROVIDER"),
         "merged head must be IMMUTABLE_MERGED"),
        ("SECOND_CONVERGENCE_OWNER",
         lambda i: i["atoms"][5].__setitem__("stack_class", "convergence"),
         "exactly one atom must be the convergence owner"),
        ("CONSUMED_PATH_WITHOUT_A_PARENT_OWNER",
         lambda i: i["atoms"][1].__setitem__("consumes_paths", ["packages/adapter/"]),
         "is owned by no declared parent"),
    ]

    failures: list[str] = []
    for name, mutate, needle in cases:
        candidate = copy.deepcopy(index)
        mutate(candidate)
        if not any(needle.lower() in error.lower() for error in validate(candidate)):
            failures.append(f"control did not turn red: {name}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    try:
        index = load(args.index)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64

    errors = selftest(index) if args.selftest else validate(index)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if args.selftest:
        print("SELFTEST GREEN: Molecular Stack index controls (10 mutations killed)")
    else:
        print(
            f"PASS: Molecular Stack index ({len(index['atoms'])} atom(s), "
            f"required={''.join(index['required_atoms'])}, convergence owner={index['convergence_owner']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
