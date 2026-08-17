#!/usr/bin/env python3
"""Render the cross-Skill adoption audit from the machine ledger.

#322 asked for a rendered report and the traceability index recorded it as
still open. A hand-written one would be a second copy of the ledger that drifts
the first time a criterion changes, so this recomputes the document from
`references/skill-adoption-ledger.json` and `--check` refuses any byte
difference: the Markdown is a projection, never a source.

The report is the gap list, not a full matrix. Ten skills by ten criteria is a
hundred cells of which most are `PASS`, and a table nobody can read is how a
`PARTIAL` with an owner issue disappears into a wall of green.

Paths are arguments. This script is inside a Skill and must not resolve upward
into a repository root to find either its input or its output.

Exits: 0 rendered or fresh, 2 stale under --check, 1 unusable input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "skill-refactor-proof-loop/skill-adoption-ledger/v1"
SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = SKILL_ROOT / "references" / "skill-adoption-ledger.json"
# Ledger-relative path of the ledger itself, for the generated provenance line.
LEDGER_ROUTE = "skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json"
RENDERER_ROUTE = "skills/skill-refactor-proof-loop/scripts/render_adoption_report.py"
STATE_ORDER = ("PASS", "PARTIAL", "NOT_EXERCISED", "NOT_IMPLEMENTED", "ABSENT")


def load(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != SCHEMA:
        raise ValueError(f"{path}: schema must be {SCHEMA}")
    if not isinstance(document.get("skills"), list) or not document["skills"]:
        raise ValueError(f"{path}: ledger declares no skills")
    return document


def render(document: dict) -> str:
    entries = sorted(document["skills"], key=lambda entry: entry["skill"])
    criteria = sorted({name for entry in entries for name in entry["criteria"]})

    lines = [
        f"# Cross-Skill adoption audit — issue #{document['audit_issue']}",
        "",
        f"Generated from `{LEDGER_ROUTE}` by `{RENDERER_ROUTE}`. Do not edit by",
        "hand: CI runs the renderer with `--check` and refuses a byte difference, so an",
        "edit here is reverted rather than believed. Change the ledger.",
        "",
        f"{len(entries)} Skill(s) in scope against {len(criteria)} refactor-proof criteria.",
        "A criterion is one of `PASS`, `PARTIAL`, `NOT_EXERCISED`, `NOT_IMPLEMENTED` or",
        "`ABSENT`; those states do not substitute for one another, and a `PASS` here is a",
        "statement about deterministic repository evidence only.",
        "",
        "## Per-Skill state",
        "",
        "| Skill | Highest proven layer | Golden proof | "
        + " | ".join(STATE_ORDER)
        + " |",
        "|---|---|---|" + "---|" * len(STATE_ORDER),
    ]
    totals = {state: 0 for state in STATE_ORDER}
    for entry in entries:
        counts = {state: 0 for state in STATE_ORDER}
        for criterion in entry["criteria"].values():
            state = criterion["state"]
            if state not in counts:
                raise ValueError(f"{entry['skill']}: unknown criterion state {state!r}")
            counts[state] += 1
            totals[state] += 1
        proof = entry.get("golden_proof_id") or "none"
        lines.append(
            f"| `{entry['skill']}` | `{entry['highest_layer']}` | `{proof}` | "
            + " | ".join(str(counts[state]) for state in STATE_ORDER)
            + " |"
        )
    lines.append(
        "| **total** | | | "
        + " | ".join(str(totals[state]) for state in STATE_ORDER)
        + " |"
    )

    lines += [
        "",
        "## Open criteria",
        "",
        "Every criterion that is not `PASS`, with the issue that owns it. A criterion",
        "with no owner issue is unowned work, which is why the column is never blank by",
        "default.",
        "",
        "| Skill | Criterion | State | Owner issue | Note |",
        "|---|---|---|---|---|",
    ]
    open_rows = 0
    for entry in entries:
        for name in criteria:
            criterion = entry["criteria"].get(name)
            if criterion is None or criterion["state"] == "PASS":
                continue
            open_rows += 1
            owner = criterion.get("owner_issue")
            note = criterion.get("note", "").replace("|", "\\|")
            lines.append(
                f"| `{entry['skill']}` | `{name}` | `{criterion['state']}` | "
                f"{f'#{owner}' if owner else '**unowned**'} | {note} |"
            )
    lines += [
        "",
        f"{open_rows} open criterion row(s). Known issue lanes: "
        + ", ".join(f"#{number}" for number in sorted(document["known_issues"]))
        + ".",
        "",
        "## Evidence boundary",
        "",
        "This report is a projection of a zero-network ledger. It cannot promote any row",
        "to a live-model, delivery, release or Human-admitted state, and `PASS` on",
        "`molecular_traceability` is impossible here by construction: those node states",
        "are read from the forge, not from this tree.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        rendered = render(load(args.ledger))
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"ADOPTION REPORT UNUSABLE: {error}", file=sys.stderr)
        return 1

    if args.check:
        if not args.output.is_file():
            print(f"ADOPTION REPORT STALE: {args.output} is absent", file=sys.stderr)
            return 2
        if args.output.read_text(encoding="utf-8") != rendered:
            print(
                f"ADOPTION REPORT STALE: {args.output} differs from what the ledger "
                f"renders. Re-run without --check; do not edit the report.",
                file=sys.stderr,
            )
            return 2
        print(f"ADOPTION REPORT FRESH: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
