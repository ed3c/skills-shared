#!/usr/bin/env python3
"""Compile observed exports into a byte-stable external projection registry.

    exact Git subjects + an observed external export -> prel/external-projection-registry/v1

A projection is a rendering of a Git-resident subject into an external
document, never implementation, completion, product-truth, merge or release
authority over that subject -- the compiled registry pins `authority` to all
`false` and `evidence_ceiling` to `HUMAN_PROJECTION` on every entry regardless
of what the draft claims, so a draft cannot promote a projection into machine
authority by editing those fields (refusal class
C08_PROJECTION_USED_AS_MACHINE_AUTHORITY).

The draft input carries one field the output schema does not: an optional
per-entry `evidence_dispositions` list, `[{"subject", "disposition"}]` with
`disposition` in `CONFIRMED`/`CONTRADICTED`, where `subject` names one of the
entry's own `canonical_subjects` paths or backlinks. If the same subject is
claimed both CONFIRMED and CONTRADICTED, silently keeping one verdict is how
the contradiction disappears before anyone downstream can see it. This
compiler refuses instead: `K09_CONTRADICTION_DROPPED`. The field is
staging-only and never appears in the compiled artifact.

Exits: 0 green, 2 the compilation is refused, 64 the draft is malformed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PINNED_AUTHORITY = {
    "implementation": False,
    "completion": False,
    "product_truth": False,
    "merge": False,
    "release": False,
}


class Refused(Exception):
    """The draft cannot be compiled without dropping a contradiction or
    granting a projection authority it did not earn."""


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Refused(f"unreadable input {path}: {error}") from error
    if not isinstance(value, dict):
        raise Refused(f"{path}: root must be an object")
    return value


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dedupe_sorted(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return sorted(seen)


def check_no_dropped_contradiction(entry_id: str, dispositions: list[dict]) -> None:
    confirmed: set[str] = set()
    contradicted: set[str] = set()
    for row in dispositions:
        subject = row["subject"]
        disposition = row["disposition"]
        if disposition == "CONFIRMED":
            confirmed.add(subject)
        elif disposition == "CONTRADICTED":
            contradicted.add(subject)
        else:
            raise Refused(
                f"{entry_id}: evidence_dispositions names an unknown disposition "
                f"{disposition!r} for subject {subject!r}"
            )
    clashing = sorted(confirmed & contradicted)
    if clashing:
        raise Refused(
            f"K09_CONTRADICTION_DROPPED {entry_id}: subject(s) {clashing} are "
            f"claimed both CONFIRMED and CONTRADICTED; reconciling that silently "
            f"is how a contradiction disappears before anyone can see it"
        )


def compile_entry(draft: dict) -> dict[str, Any]:
    entry_id = draft.get("id", "<unnamed>")
    dispositions = draft.get("evidence_dispositions") or []
    check_no_dropped_contradiction(entry_id, dispositions)

    return {
        "id": draft["id"],
        "external_kind": draft["external_kind"],
        "external_id": draft["external_id"],
        "observed_revision": draft["observed_revision"],
        "export_digest": draft["export_digest"],
        "canonical_subjects": sorted(
            (dict(row) for row in draft.get("canonical_subjects") or []),
            key=lambda row: row["path"],
        ),
        "backlinks": dedupe_sorted(list(draft.get("backlinks") or [])),
        "read_back": dict(draft["read_back"]),
        "authority": dict(PINNED_AUTHORITY),
    }


def compile_external_projection(source: Path) -> dict[str, Any]:
    draft = load(source)
    if draft.get("schema") != "prel/external-projection-input/v1":
        raise Refused(
            "external projection input must be a prel/external-projection-input/v1 draft"
        )
    drafts = draft.get("entries") or []
    if not drafts:
        raise Refused("no entries: an empty registry projects nothing")

    ids = [row["id"] for row in drafts]
    if len(ids) != len(set(ids)):
        raise Refused(f"duplicate entry id(s) in {sorted(ids)}")

    return {
        "schema": "prel/external-projection-registry/v1",
        "authority": dict(PINNED_AUTHORITY),
        "evidence_ceiling": "HUMAN_PROJECTION",
        "entries": sorted(
            (compile_entry(row) for row in drafts), key=lambda row: row["id"]
        ),
        "human_owned_operations": dedupe_sorted(
            list(draft.get("human_owned_operations") or [])
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="byte-compare --out against a fresh compilation instead of writing it",
    )
    args = parser.parse_args()

    try:
        rendered = canonical(compile_external_projection(args.input))
    except Refused as error:
        print(f"PREL-COMPILE-RED external_projection: {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError) as error:
        print(
            f"PREL-COMPILE-UNUSABLE external_projection: malformed input: {error}",
            file=sys.stderr,
        )
        return 64

    if args.out is None:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        try:
            current = args.out.read_text(encoding="utf-8")
        except OSError as error:
            print(f"PREL-COMPILE-RED missing projection {args.out}: {error}", file=sys.stderr)
            return 2
        if current != rendered:
            print(
                f"PREL-COMPILE-RED {args.out} is not what {args.input.name} compiles "
                f"to; regenerate it rather than editing it",
                file=sys.stderr,
            )
            return 2
        print("PREL-COMPILE-GREEN external_projection projection is current")
        return 0

    args.out.write_text(rendered, encoding="utf-8")
    print(f"PREL-COMPILE-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
