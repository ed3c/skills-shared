#!/usr/bin/env python3
"""Enforce that no execution adapter owns promotion authority.

#29's last acceptance line is "no executor adapter owns promotion authority".
It could not be checked. Both adapters declared
`skill-eval-executor-authority/v1`, no such schema existed, nothing validated
either file, and they expressed the same intent in different vocabularies:

    arena.json     forbidden_claims: [... "ranking-claim-allowed"]
    skill-up.json  promotion_authority: false

Both are correct and neither is checkable against the other. Answering the
acceptance question meant reading two files and knowing which dialect each
spoke, which is not an answer a gate can give.

So the schema now exists, `promotion_authority` is a constant rather than a
boolean -- an adapter cannot answer it differently -- and every adapter carries
both claim lists. What an executor may claim is an enumeration, so a new
adapter cannot invent a claim that sounds admissible.

Exits: 0 all adapters bounded, 2 an adapter overreaches, 64 unusable input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "skill-eval-executor-authority/v1"

# Claims no adapter may ever make, whatever its runtime state. Running cases is
# not deciding what a result means.
NEVER_CLAIMABLE = frozenset({
    "cross-harness-capability-proven",
    "ranking-claim-allowed",
    "promotion-admitted",
})


class Unusable(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Unusable(f"unreadable {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise Unusable(f"unparseable {path}: {error}") from error
    if not isinstance(body, dict):
        raise Unusable(f"{path}: root must be an object")
    return body


def validator(schema: dict[str, Any]):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - environment guard
        raise Unusable(
            "jsonschema is required: the committed schema must decide, not be parsed"
        ) from error
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def check_schema_still_forbids_promotion(schema: dict[str, Any]) -> list[str]:
    """The guard lives in the schema, so the schema is what must be protected.

    An earlier version also re-checked `promotion_authority is not False` in
    Python. The guard-control gate reported it as uncontrolled, correctly: the
    schema's `const: false` already refuses every case, so the Python branch
    could never be the deciding one. Rather than keep a guard whose removal
    changes nothing, the check moved to the layer that actually decides.
    """
    field = (schema.get("properties") or {}).get("promotion_authority")
    if not isinstance(field, dict) or field.get("const") is not False:
        return [
            "the authority schema no longer pins promotion_authority to a "
            "constant false; an adapter could answer it differently"
        ]
    if "promotion_authority" not in (schema.get("required") or []):
        return ["the authority schema no longer requires promotion_authority"]
    return []


def check(root: Path) -> list[str]:
    schema_path = root / "evals" / "schema" / "skill-eval-executor-authority.schema.json"
    schema = load(schema_path)
    problems_schema = check_schema_still_forbids_promotion(schema)
    if problems_schema:
        return problems_schema
    check_against = validator(schema)

    directory = root / "evals" / "runtime" / "executors"
    adapters = sorted(directory.glob("*.json"))
    if not adapters:
        raise Unusable(f"no executor adapters under {directory}")

    problems: list[str] = []
    for path in adapters:
        body = load(path)
        name = path.name
        errors = sorted(check_against.iter_errors(body), key=lambda e: list(e.path))
        if errors:
            where = "/".join(str(part) for part in errors[0].path) or "<root>"
            problems.append(f"{name}: fails the authority schema at {where}: {errors[0].message}")
            continue

        overreach = sorted(set(body.get("allowed_claims") or []) & NEVER_CLAIMABLE)
        if overreach:
            problems.append(
                f"{name}: allows claim(s) no adapter may make: {', '.join(overreach)}"
            )

        missing = sorted(NEVER_CLAIMABLE - set(body.get("forbidden_claims") or []))
        if missing:
            problems.append(
                f"{name}: does not forbid {', '.join(missing)}; an unstated "
                f"prohibition reads as a permitted claim"
            )

        overlap = sorted(set(body.get("allowed_claims") or [])
                         & set(body.get("forbidden_claims") or []))
        if overlap:
            problems.append(
                f"{name}: claim(s) both allowed and forbidden: {', '.join(overlap)}"
            )

        state = body.get("runtime_state")
        if state == "blocked_external_authority" and "physical-run-available" in (
                body.get("allowed_claims") or []):
            problems.append(
                f"{name}: runtime_state is blocked_external_authority while "
                f"allowing physical-run-available"
            )
        if state == "blocked_external_authority" and not body.get("blocking_issue"):
            problems.append(f"{name}: is blocked with no blocking issue recorded")

    return problems


def _selftest(root: Path) -> int:
    import copy
    import tempfile

    canonical = {
        "schema_version": SCHEMA_VERSION,
        "executor": "fixture",
        "repository": "ed3c/fixture",
        "repository_sha": "a" * 40,
        "runtime_state": "available_offline_replay_only",
        "promotion_authority": False,
        "allowed_claims": ["offline-replay-available"],
        "forbidden_claims": sorted(NEVER_CLAIMABLE),
    }

    def run(adapters: list[dict[str, Any]]) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="exec-auth.") as raw:
            work = Path(raw)
            (work / "evals" / "schema").mkdir(parents=True)
            (work / "evals" / "runtime" / "executors").mkdir(parents=True)
            source = root / "evals" / "schema" / "skill-eval-executor-authority.schema.json"
            (work / "evals" / "schema" / source.name).write_text(
                source.read_text(encoding="utf-8"), encoding="utf-8")
            for index, adapter in enumerate(adapters):
                (work / "evals" / "runtime" / "executors" / f"a{index}.json").write_text(
                    json.dumps(adapter, indent=2) + "\n", encoding="utf-8")
            return check(work)

    survived: list[str] = []
    if run([canonical]):
        print(f"SELFTEST RED: canonical adapter refused: {run([canonical])}", file=sys.stderr)
        return 2

    cases: list[tuple[str, Any]] = [
        ("promotion authority claimed",
         lambda a: a.__setitem__("promotion_authority", True)),
        ("a never-claimable claim allowed",
         lambda a: a["allowed_claims"].append("ranking-claim-allowed")),
        ("a prohibition left unstated",
         lambda a: a["forbidden_claims"].remove("promotion-admitted")),
        ("a claim both allowed and forbidden",
         lambda a: a["allowed_claims"].append("promotion-admitted")),
        ("blocked adapter allowing a physical run",
         lambda a: (a.__setitem__("runtime_state", "blocked_external_authority"),
                    a.__setitem__("blocking_issue", "x#1"),
                    a["allowed_claims"].append("physical-run-available"))),
        ("blocked adapter with no blocking issue",
         lambda a: a.__setitem__("runtime_state", "blocked_external_authority")),
        ("invented runtime state",
         lambda a: a.__setitem__("runtime_state", "probably-fine")),
        ("invented claim vocabulary",
         lambda a: a["allowed_claims"].append("basically-works")),
        ("short repository sha",
         lambda a: a.__setitem__("repository_sha", "abc")),
        ("wrong schema version",
         lambda a: a.__setitem__("schema_version", "skill-eval-executor-authority/v2")),
        ("no allowed claims at all",
         lambda a: a.__setitem__("allowed_claims", [])),
    ]
    for name, mutate in cases:
        adapter = copy.deepcopy(canonical)
        mutate(adapter)
        if not run([adapter]):
            survived.append(name)

    # The schema is where the promotion guard now lives, so weakening the
    # schema must be refused too -- otherwise moving the check there would have
    # traded a controlled guard for an uncontrolled one.
    import copy as _copy
    weakened = _copy.deepcopy(load(
        root / "evals" / "schema" / "skill-eval-executor-authority.schema.json"))
    weakened["properties"]["promotion_authority"] = {"type": "boolean"}
    if not check_schema_still_forbids_promotion(weakened):
        survived.append("schema weakened from const false to a boolean")
    dropped = _copy.deepcopy(load(
        root / "evals" / "schema" / "skill-eval-executor-authority.schema.json"))
    dropped["required"].remove("promotion_authority")
    if not check_schema_still_forbids_promotion(dropped):
        survived.append("schema no longer requires promotion_authority")

    # The real committed adapters must pass, or this gate is decorative.
    live = check(root)
    if live:
        print(f"SELFTEST RED: committed adapters refused: {live}", file=sys.stderr)
        return 2

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2
    print(f"SELFTEST GREEN: committed adapters bounded; {len(cases)} overreach "
          f"mutations refused")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()

    try:
        if args.selftest:
            return _selftest(root)
        problems = check(root)
    except Unusable as error:
        print(f"FATAL executor-authority: {error}", file=sys.stderr)
        return 64

    if problems:
        for item in problems:
            print(f"EXECUTOR AUTHORITY RED: {item}", file=sys.stderr)
        return 2

    count = len(list((root / "evals" / "runtime" / "executors").glob("*.json")))
    print(f"EXECUTOR AUTHORITY GREEN: {count} adapter(s), none holding promotion authority")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
