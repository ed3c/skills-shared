#!/usr/bin/env python3
"""Compile evidence-bound requests into a byte-stable session dispatch request.

    evidence-bound request draft -> prel/session-dispatch-request/v1

A dispatch request is not a running session: `lifecycle_state` is pinned to
`LAUNCH_REQUESTED` and `running_session` is pinned to `null` on every
compiled document, regardless of what the draft claims, because only a
carrier that actually observed a session may assert otherwise -- and it
asserts that in a `prel/session-receipt/v1` document, never by editing this
one (refusal class C09_SESSION_REQUEST_PROMOTED_TO_RUNNING).

The draft input carries one field the output schema does not: an optional
`evidence_dispositions` list per request, `[{"subject", "disposition"}]` with
`disposition` in `CONFIRMED`/`CONTRADICTED`. If the same named subject
appears with both dispositions inside one request, the draft is asserting
two contradictory verdicts about one piece of evidence and reconciling that
silently -- by keeping whichever arrived last, or by dropping one -- is
exactly how a contradiction disappears before anyone can see it disappear.
This compiler refuses instead: `K09_CONTRADICTION_DROPPED`. The field is
staging-only and never appears in the compiled artifact.

Every array the output schema marks `uniqueItems` is deduplicated and sorted
here, so two drafts differing only in item order or in harmless repeats
compile to the same bytes.

Exits: 0 green, 2 the compilation is refused, 64 the draft is malformed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PINNED_AUTHORITY = {"merge": False, "permission": False, "secret": False, "production": False}


class Refused(Exception):
    """The draft cannot be compiled without dropping a contradiction or
    inventing session state the draft did not earn."""


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


def dedupe_sorted(items: list[Any]) -> list[Any]:
    seen: list[Any] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    try:
        return sorted(seen)
    except TypeError:
        return sorted(seen, key=json.dumps)


def check_no_dropped_contradiction(request_id: str, dispositions: list[dict]) -> None:
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
                f"{request_id}: evidence_dispositions names an unknown disposition "
                f"{disposition!r} for subject {subject!r}"
            )
    clashing = sorted(confirmed & contradicted)
    if clashing:
        raise Refused(
            f"K09_CONTRADICTION_DROPPED {request_id}: subject(s) {clashing} are "
            f"claimed both CONFIRMED and CONTRADICTED; reconciling that silently "
            f"is how a contradiction disappears before anyone can see it"
        )


def compile_request(draft: dict) -> dict[str, Any]:
    request_id = draft.get("id", "<unnamed>")
    dispositions = draft.get("evidence_dispositions") or []
    check_no_dropped_contradiction(request_id, dispositions)

    lease = draft["lease"]
    compiled = {
        "id": draft["id"],
        "relation": draft["relation"],
        "parent_request_id": draft.get("parent_request_id"),
        "base": {"commit": draft["base"]["commit"], "tree": draft["base"]["tree"]},
        "branch": draft["branch"],
        "lease": {
            "paths": dedupe_sorted(list(lease.get("paths") or [])),
            "resources": dedupe_sorted(list(lease.get("resources") or [])),
        },
        "start_dependencies": sorted(
            (dict(row) for row in draft.get("start_dependencies") or []),
            key=lambda row: row["subject"],
        ),
        "completion_dependencies": sorted(
            (dict(row) for row in draft.get("completion_dependencies") or []),
            key=lambda row: row["subject"],
        ),
        "evidence_ceiling": {
            "highest_claimable_lane": draft["evidence_ceiling"]["highest_claimable_lane"],
            "cannot_establish": dedupe_sorted(
                list(draft["evidence_ceiling"].get("cannot_establish") or [])
            ),
        },
        "oracles": sorted(
            (dict(row) for row in draft.get("oracles") or []),
            key=lambda row: row["id"],
        ),
        "negative_controls": dedupe_sorted(list(draft.get("negative_controls") or [])),
        "rollback": {
            "subject": draft["rollback"]["subject"],
            "commit": draft["rollback"]["commit"],
        },
        "stop_states": dedupe_sorted(list(draft.get("stop_states") or [])),
        "output_paths": dedupe_sorted(list(draft.get("output_paths") or [])),
        "human_owned_operations": dedupe_sorted(
            list(draft.get("human_owned_operations") or [])
        ),
        "requests_private_reasoning": False,
        "authority": dict(PINNED_AUTHORITY),
        "consumer_binding": dict(draft.get("consumer_binding") or {}),
    }
    return compiled


def compile_session_dispatch(source: Path) -> dict[str, Any]:
    draft = load(source)
    if draft.get("schema") != "prel/session-dispatch-input/v1":
        raise Refused(
            "session dispatch input must be a prel/session-dispatch-input/v1 draft"
        )
    drafts = draft.get("requests") or []
    if not drafts:
        raise Refused("no requests: an empty dispatch launches nothing")

    ids = [row["id"] for row in drafts]
    if len(ids) != len(set(ids)):
        raise Refused(f"duplicate request id(s) in {sorted(ids)}")

    return {
        "schema": "prel/session-dispatch-request/v1",
        "lifecycle_state": "LAUNCH_REQUESTED",
        "running_session": None,
        "refusal_classes": dedupe_sorted(list(draft.get("refusal_classes") or [])),
        "requests": sorted(
            (compile_request(row) for row in drafts), key=lambda row: row["id"]
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
        rendered = canonical(compile_session_dispatch(args.input))
    except Refused as error:
        print(f"PREL-COMPILE-RED session_dispatch: {error}", file=sys.stderr)
        return 2
    except (KeyError, TypeError) as error:
        print(
            f"PREL-COMPILE-UNUSABLE session_dispatch: malformed input: {error}",
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
        print("PREL-COMPILE-GREEN session_dispatch projection is current")
        return 0

    args.out.write_text(rendered, encoding="utf-8")
    print(f"PREL-COMPILE-GREEN wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
