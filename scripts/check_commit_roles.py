#!/usr/bin/env python3
"""Verify Driven-By / Driven-On trailers over the correct commit subject.

Commit provenance has two independent dimensions:

* Driven-By: actor role.
* Driven-On: execution host.

Known local machine hosts require the synthetic ``<role>@<host>.invalid`` author
identity because the local harness controls Git identity. Any other known
Driven-On host is a cloud execution domain: cloud endpoints are not required to
forge a local Git identity and may use an already-declared owner/endpoint
address. Unknown hosts remain invalid because Driven-On is vocabulary-bound.

Exits: 0 all commits classified, 2 violations found, 64 usage or unreadable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TRAILER = re.compile(r"^(?P<key>[A-Za-z][A-Za-z-]*):[ \t]*(?P<value>.+?)\s*$")
DEFAULT_VOCABULARY = Path("evals/commit-roles.json")
LOCAL_MACHINE_HOSTS = frozenset({"claude-code", "codex-cli", "codex-app", "shell"})


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
    for field in ("driven_by", "driven_on", "identity_rules", "enforced_from", "legacy_imports"):
        if field not in body:
            raise Unusable(f"vocabulary is missing {field}")
    return body


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise Unusable(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def commits(repo: Path, rev_range: str) -> list[dict[str, str]]:
    raw = git(repo, "log", "--no-merges", "--format=%H\x1f%an\x1f%ae\x1f%cn\x1f%ce\x1f%B\x1e", rev_range)
    found: list[dict[str, str]] = []
    for chunk in raw.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 6:
            continue
        found.append({"sha": parts[0], "author_name": parts[1], "author_email": parts[2], "committer_name": parts[3], "committer_email": parts[4], "body": parts[5]})
    return found


def trailers(body: str) -> dict[str, list[str]]:
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


def execution_domain(host: str, vocabulary: dict[str, Any]) -> str:
    if host not in vocabulary["driven_on"]:
        raise Unusable(f"unknown Driven-On host {host!r}")
    return "LOCAL" if host in LOCAL_MACHINE_HOSTS else "CLOUD"


def declared_cloud_addresses(rules: dict[str, Any]) -> set[str]:
    return {address.lower() for address in rules.get("declared_owner_addresses", {})}


def check_machine_identity(record: dict[str, str], by_value: str, on_value: str | None, vocabulary: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    short = record["sha"][:12]
    rules = vocabulary["identity_rules"]
    pattern = re.compile(rules["machine_author_email_pattern"])
    match = pattern.match(record["author_email"])

    if match is not None:
        if match.group("role") != by_value:
            problems.append(f"{short}: author address names role {match.group('role')!r} while Driven-By says {by_value!r}")
        elif on_value is not None and match.group("host") != on_value:
            problems.append(f"{short}: author address names host {match.group('host')!r} while Driven-On says {on_value!r}")
        return problems

    if on_value is None or on_value not in vocabulary["driven_on"]:
        return problems

    if execution_domain(on_value, vocabulary) == "LOCAL":
        problems.append(
            f"{short}: Driven-By {by_value} runs on local host {on_value!r} but author {record['author_email']!r} is not <role>@<host>.invalid; local machine provenance must not depend on a person's identity or count machine work toward a person's contribution graph"
        )
        return problems

    if record["author_email"].lower() not in declared_cloud_addresses(rules):
        problems.append(
            f"{short}: cloud host {on_value!r} used undeclared endpoint author {record['author_email']!r}; declare the attributable cloud endpoint identity instead of depending on local Git config"
        )
    return problems


def check_commit(record: dict[str, str], vocabulary: dict[str, Any], legacy_unclassified: set[str] | None = None) -> list[str]:
    problems: list[str] = []
    short = record["sha"][:12]
    found = trailers(record["body"])
    rules = vocabulary["identity_rules"]

    listed = {item["commit_sha"] for item in (vocabulary.get("known_unclassified") or {}).get("commits", [])}
    if record["sha"] in listed or record["sha"] in (legacy_unclassified or set()):
        if found.get("Driven-By") or found.get("Driven-On"):
            return [f"{short}: listed as unclassified but does carry trailers; the exception list is for commits that cannot be fixed, not for skipping ones that can"]
        return []

    for field in ("author_email", "committer_email"):
        if record[field].lower() in {item.lower() for item in rules["unset_identities"]}:
            problems.append(f"{short}: {field} {record[field]!r} is an unset default identity; nothing recorded who drove this commit")

    forge_roles = {key.lower(): value for key, value in rules.get("forge_committer_roles", {}).items()}
    forge_role = forge_roles.get(record["committer_email"].lower())
    if forge_role is not None and record["author_email"] != record["committer_email"]:
        if forge_role not in vocabulary["driven_by"]:
            problems.append(f"{short}: committer {record['committer_email']!r} maps to role {forge_role!r}, which is not in the vocabulary")
        return problems

    owner_roles = {key.lower(): value for key, value in rules.get("declared_owner_addresses", {}).items()}
    owner_role = owner_roles.get(record["author_email"].lower())
    if owner_role is not None and not found.get("Driven-By") and not found.get("Driven-On"):
        if owner_role not in vocabulary["driven_by"]:
            problems.append(f"{short}: author {record['author_email']!r} maps to role {owner_role!r}, which is not in the vocabulary")
        return problems

    by = found.get("Driven-By") or []
    on = found.get("Driven-On") or []

    if not by:
        problems.append(f"{short}: no Driven-By trailer")
    elif len(by) > 1:
        problems.append(f"{short}: {len(by)} Driven-By trailers; a commit has one driver")
    elif by[0] not in vocabulary["driven_by"]:
        problems.append(f"{short}: Driven-By {by[0]!r} is not in the vocabulary ({', '.join(sorted(vocabulary['driven_by']))})")

    if not on:
        problems.append(f"{short}: no Driven-On trailer")
    elif len(on) > 1:
        problems.append(f"{short}: {len(on)} Driven-On trailers; a commit has one host")
    elif on[0] not in vocabulary["driven_on"]:
        problems.append(f"{short}: Driven-On {on[0]!r} is not in the vocabulary ({', '.join(sorted(vocabulary['driven_on']))})")

    if len(by) == 1 and by[0] in vocabulary["driven_by"] and vocabulary["driven_by"][by[0]]["machine"]:
        problems.extend(check_machine_identity(record, by[0], on[0] if len(on) == 1 else None, vocabulary))

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
        expected = {"id", "tip_sha", "admitted_against_sha", "unclassified_commit_count", "unclassified_commits_sha256", "note"}
        if set(item) != expected:
            raise Unusable(f"{label} fields drifted")
        tip = item["tip_sha"]
        against = item["admitted_against_sha"]
        for field, value in (("tip_sha", tip), ("admitted_against_sha", against)):
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
                raise Unusable(f"{label}.{field} must be an exact commit SHA")
            git(repo, "cat-file", "-e", f"{value}^{{commit}}")
        records = commits(repo, f"{against}..{tip}")
        unclassified = sorted(record["sha"] for record in records if check_commit(record, vocabulary))
        payload = "".join(f"{sha}\n" for sha in unclassified).encode("ascii")
        digest = hashlib.sha256(payload).hexdigest()
        if item["unclassified_commit_count"] != len(unclassified):
            raise Unusable(f"{label} count drifted: declared {item['unclassified_commit_count']} measured {len(unclassified)}")
        if item["unclassified_commits_sha256"] != digest:
            raise Unusable(f"{label} commit-set digest drifted")
        overlap = admitted.intersection(unclassified)
        if overlap:
            raise Unusable(f"{label} overlaps another legacy import")
        admitted.update(unclassified)
    return admitted


def evaluate(repo: Path, rev_range: str, vocabulary: dict[str, Any], legacy_unclassified: set[str] | None = None) -> tuple[int, list[str]]:
    records = commits(repo, rev_range)
    problems: list[str] = []
    for record in records:
        problems.extend(check_commit(record, vocabulary, legacy_unclassified))
    return len(records), problems


def select_rev_range(repo: Path, vocabulary: dict[str, Any], explicit_range: str | None = None, base_ref: str | None = None) -> str:
    if explicit_range:
        return explicit_range
    advertised_base = (base_ref if base_ref is not None else os.environ.get("GITHUB_BASE_REF", "")).strip()
    if advertised_base:
        resolved: str | None = None
        for candidate in (f"origin/{advertised_base}", advertised_base):
            result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", f"{candidate}^{{commit}}"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                resolved = result.stdout.strip()
                break
        if resolved is None:
            raise Unusable(f"advertised PR base {advertised_base!r} cannot be resolved; refusing to widen to enforced history")
        merge_base = git(repo, "merge-base", resolved, "HEAD").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", merge_base):
            raise Unusable(f"invalid merge-base for PR base {advertised_base!r}")
        return f"{merge_base}..HEAD"
    start = vocabulary["enforced_from"]["commit_sha"]
    try:
        git(repo, "cat-file", "-e", f"{start}^{{commit}}")
    except Unusable:
        raise Unusable(f"enforced_from {start[:12]} is not a commit in this repository")
    return f"{start}..HEAD"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--vocabulary", type=Path, default=None)
    parser.add_argument("--range", dest="rev_range", default=None)
    args = parser.parse_args()
    default_root = args.repo_root is None
    repo = (Path(__file__).resolve().parent.parent if default_root else args.repo_root).resolve()
    vocabulary_path = args.vocabulary or (repo / DEFAULT_VOCABULARY)
    try:
        if default_root and not (repo / "AGENTS.md").is_file():
            raise Unusable(f"default subject root {repo} does not contain AGENTS.md")
        vocabulary = load_vocabulary(vocabulary_path)
        rev_range = select_rev_range(repo, vocabulary, args.rev_range)
        legacy_unclassified = resolve_legacy_imports(repo, vocabulary)
        total, problems = evaluate(repo, rev_range, vocabulary, legacy_unclassified)
    except Unusable as error:
        print(f"FATAL commit-roles: {error}", file=sys.stderr)
        return 64
    if problems:
        for item in problems:
            print(f"COMMIT ROLE RED: {item}", file=sys.stderr)
        print(f"COMMIT ROLE RED: {len(problems)} violation(s) over {total} commit(s) in {rev_range}", file=sys.stderr)
        return 2
    listed = len((vocabulary.get("known_unclassified") or {}).get("commits", []))
    imported = len(legacy_unclassified)
    suffix = f"; {listed} listed, {imported} legacy-imported as unclassified"
    print(f"COMMIT ROLE GREEN: {total} commit(s) classified{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
