#!/usr/bin/env python3
"""Verify Driven-By / Driven-On trailers over a commit range.

The mechanism this replaces did not fail; it never started. Around 1100 of
1138 commits across these repositories carry `t <t@t.t>`, the unset default,
so `git log --author=...` cannot select the full set of *any* driver. That is
not incomplete signal — it is a classification that never ran.

Two reasons it never ran, both addressed here:

  1. Wrong dimension. A driver is a property of a commit; `git config` is a
     property of a repository. One repository carries human decisions, main-loop
     delivery and small-loop iteration at once, so a per-repo identity can only
     label the dominant driver correctly and silently mislabels the rest.
  2. No gate. Convention alone produced 1100 unclassified commits. A rule with
     no gate is a rule nobody applies, which is the failure this repository
     keeps rediscovering.

The vocabulary lives in `evals/commit-roles.json` so the gate and the humans
read the same list, and adding a mechanism extends the trailer domain rather
than the identity field.

Exits: 0 all commits classified, 2 violations found, 64 usage or unreadable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TRAILER = re.compile(r"^(?P<key>[A-Za-z][A-Za-z-]*):[ \t]*(?P<value>.+?)\s*$")
DEFAULT_VOCABULARY = Path("evals/commit-roles.json")


class Unusable(Exception):
    """Could not read the input at all. Not a violation."""


def load_vocabulary(path: Path) -> dict[str, Any]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable vocabulary {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"unparseable vocabulary {path}: {error}") from error
    if body.get("schema") != "commit-role-vocabulary/v2":
        raise Unusable("vocabulary schema must be commit-role-vocabulary/v2")
    for field in (
        "driven_by",
        "driven_on",
        "identity_rules",
        "enforced_from",
        "legacy_imports",
    ):
        if field not in body:
            raise Unusable(f"vocabulary is missing {field}")
    return body


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise Unusable(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def commits(repo: Path, rev_range: str) -> list[dict[str, str]]:
    """One record per commit. \x1e separates records, \x1f separates fields."""
    raw = git(repo, "log", "--no-merges", "--format=%H\x1f%an\x1f%ae\x1f%cn\x1f%ce\x1f%B\x1e",
              rev_range)
    found: list[dict[str, str]] = []
    for chunk in raw.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 6:
            continue
        found.append({
            "sha": parts[0], "author_name": parts[1], "author_email": parts[2],
            "committer_name": parts[3], "committer_email": parts[4], "body": parts[5],
        })
    return found


def trailers(body: str) -> dict[str, list[str]]:
    """Trailers from the final block, which is where git itself looks."""
    lines = body.rstrip().splitlines()
    block: list[str] = []
    for line in reversed(lines):
        if not line.strip():
            break
        block.append(line)
    out: dict[str, list[str]] = {}
    for line in reversed(block):
        match = TRAILER.match(line)
        if match:
            out.setdefault(match.group("key"), []).append(match.group("value"))
    return out


def check_commit(
    record: dict[str, str],
    vocabulary: dict[str, Any],
    legacy_unclassified: set[str] | None = None,
) -> list[str]:
    problems: list[str] = []
    short = record["sha"][:12]
    found = trailers(record["body"])
    rules = vocabulary["identity_rules"]

    # Commits that reached main untrailed are listed one by one rather than
    # excused by a rule. A widened rule would report nothing; a list reports its
    # own length, which is the honest measure of how far adoption has to go.
    # An entry is only honoured for a commit that genuinely lacks the trailers,
    # so the list cannot be used to skip a commit that could simply be fixed.
    listed = {
        item["commit_sha"]
        for item in (vocabulary.get("known_unclassified") or {}).get("commits", [])
    }
    if record["sha"] in listed or record["sha"] in (legacy_unclassified or set()):
        if found.get("Driven-By") or found.get("Driven-On"):
            return [
                f"{short}: listed as unclassified but does carry trailers; the "
                f"exception list is for commits that cannot be fixed, not for "
                f"skipping ones that can"
            ]
        return []

    # Rule 4 first: an unset identity is refused whatever the trailers say,
    # because the trailers would be labelling a commit nobody claimed.
    for field in ("author_email", "committer_email"):
        if record[field].lower() in {item.lower() for item in rules["unset_identities"]}:
            problems.append(
                f"{short}: {field} {record[field]!r} is an unset default identity; "
                f"nothing recorded who drove this commit"
            )

    # A forge-created commit carries its driver in its committer address. A
    # squash merge is performed by the forge, not by whoever wrote the branch,
    # and the forge will never add a trailer. Requiring one would make every
    # merge a violation, and a gate that fails on every merge gets switched off.
    forge_roles = {k.lower(): v for k, v in rules.get("forge_committer_roles", {}).items()}
    forge_role = forge_roles.get(record["committer_email"].lower())
    if forge_role is not None and record["author_email"] != record["committer_email"]:
        if forge_role not in vocabulary["driven_by"]:
            problems.append(
                f"{short}: committer {record['committer_email']!r} maps to role "
                f"{forge_role!r}, which is not in the vocabulary"
            )
        return problems

    by = found.get("Driven-By") or []
    on = found.get("Driven-On") or []

    if not by:
        problems.append(f"{short}: no Driven-By trailer")
    elif len(by) > 1:
        problems.append(f"{short}: {len(by)} Driven-By trailers; a commit has one driver")
    elif by[0] not in vocabulary["driven_by"]:
        problems.append(
            f"{short}: Driven-By {by[0]!r} is not in the vocabulary "
            f"({', '.join(sorted(vocabulary['driven_by']))})"
        )

    if not on:
        problems.append(f"{short}: no Driven-On trailer")
    elif len(on) > 1:
        problems.append(f"{short}: {len(on)} Driven-On trailers; a commit has one host")
    elif on[0] not in vocabulary["driven_on"]:
        problems.append(
            f"{short}: Driven-On {on[0]!r} is not in the vocabulary "
            f"({', '.join(sorted(vocabulary['driven_on']))})"
        )

    # Rule 3: a machine role may not wear a real address.
    if len(by) == 1 and by[0] in vocabulary["driven_by"]:
        role = vocabulary["driven_by"][by[0]]
        if role["machine"]:
            pattern = re.compile(rules["machine_author_email_pattern"])
            match = pattern.match(record["author_email"])
            if match is None:
                problems.append(
                    f"{short}: Driven-By {by[0]} is a machine role but the author "
                    f"address {record['author_email']!r} is not a "
                    f"<role>@<host>.invalid address; machine work would count "
                    f"toward a person's contribution graph"
                )
            elif match.group("role") != by[0]:
                problems.append(
                    f"{short}: author address names role {match.group('role')!r} "
                    f"while Driven-By says {by[0]!r}"
                )
            elif len(on) == 1 and match.group("host") != on[0]:
                problems.append(
                    f"{short}: author address names host {match.group('host')!r} "
                    f"while Driven-On says {on[0]!r}"
                )

    # A forge committer is expected on a merged commit and is not drift: git
    # preserves the author and rewrites the committer, which is the
    # decision-versus-execution split this vocabulary is built on.
    committer = record["committer_email"].lower()
    forge = {item.lower() for item in rules["forge_committer_addresses"]}
    if committer in forge:
        pass

    return problems


def resolve_legacy_imports(repo: Path, vocabulary: dict[str, Any]) -> set[str]:
    admitted: set[str] = set()
    imports = vocabulary["legacy_imports"]
    if not isinstance(imports, list):
        raise Unusable("legacy_imports must be an array")
    for index, item in enumerate(imports):
        label = f"legacy_imports[{index}]"
        if not isinstance(item, dict):
            raise Unusable(f"{label} must be an object")
        expected = {
            "id",
            "tip_sha",
            "admitted_against_sha",
            "unclassified_commit_count",
            "unclassified_commits_sha256",
            "note",
        }
        if set(item) != expected:
            raise Unusable(f"{label} fields drifted")
        tip = item["tip_sha"]
        against = item["admitted_against_sha"]
        for field, value in (("tip_sha", tip), ("admitted_against_sha", against)):
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
                raise Unusable(f"{label}.{field} must be an exact commit SHA")
            git(repo, "cat-file", "-e", f"{value}^{{commit}}")
        records = commits(repo, f"{against}..{tip}")
        unclassified = sorted(
            record["sha"] for record in records if check_commit(record, vocabulary)
        )
        payload = "".join(f"{sha}\n" for sha in unclassified).encode("ascii")
        digest = hashlib.sha256(payload).hexdigest()
        if item["unclassified_commit_count"] != len(unclassified):
            raise Unusable(
                f"{label} count drifted: declared {item['unclassified_commit_count']} "
                f"measured {len(unclassified)}"
            )
        if item["unclassified_commits_sha256"] != digest:
            raise Unusable(f"{label} commit-set digest drifted")
        overlap = admitted.intersection(unclassified)
        if overlap:
            raise Unusable(f"{label} overlaps another legacy import")
        admitted.update(unclassified)
    return admitted


def evaluate(
    repo: Path,
    rev_range: str,
    vocabulary: dict[str, Any],
    legacy_unclassified: set[str] | None = None,
) -> tuple[int, list[str]]:
    records = commits(repo, rev_range)
    problems: list[str] = []
    for record in records:
        problems.extend(check_commit(record, vocabulary, legacy_unclassified))
    return len(records), problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--vocabulary", type=Path, default=None)
    parser.add_argument("--range", dest="rev_range", default=None,
                        help="commit range; defaults to enforced_from..HEAD")
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    vocabulary_path = args.vocabulary or (repo / DEFAULT_VOCABULARY)

    try:
        vocabulary = load_vocabulary(vocabulary_path)
        start = vocabulary["enforced_from"]["commit_sha"]
        rev_range = args.rev_range or f"{start}..HEAD"
        try:
            git(repo, "cat-file", "-e", f"{start}^{{commit}}")
        except Unusable:
            # A start point this repository cannot see means the range is
            # meaningless; scanning everything would be worse than stopping.
            print(
                f"FATAL commit-roles: enforced_from {start[:12]} is not a commit "
                f"in this repository",
                file=sys.stderr,
            )
            return 64
        legacy_unclassified = resolve_legacy_imports(repo, vocabulary)
        total, problems = evaluate(repo, rev_range, vocabulary, legacy_unclassified)
    except Unusable as error:
        print(f"FATAL commit-roles: {error}", file=sys.stderr)
        return 64

    if problems:
        for item in problems:
            print(f"COMMIT ROLE RED: {item}", file=sys.stderr)
        print(f"COMMIT ROLE RED: {len(problems)} violation(s) over {total} commit(s) "
              f"in {rev_range}", file=sys.stderr)
        return 2

    listed = len((vocabulary.get("known_unclassified") or {}).get("commits", []))
    imported = len(legacy_unclassified)
    suffix = f"; {listed} listed, {imported} legacy-imported as unclassified"
    print(f"COMMIT ROLE GREEN: {total} commit(s) classified in {rev_range}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
