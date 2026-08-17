#!/usr/bin/env python3
"""Generate leave-one-rule-out treatment files for the #230 live ablation.

Exit codes:
  0   all 13 candidate_minus_RCA-0XX treatment files were written
  64  SKILL.md is missing, unreadable, or its RCA-0XX headings are malformed

For every `### RCA-0XX --- Title` section in SKILL.md this writes a sibling
file with only that section's heading and body removed, byte-identical to
SKILL.md everywhere else. `run_agent_cell.py --treatment-file` takes each
output directly (#230's "Required receipt binding" names the ablated
treatment digest, so the file it hashes must actually be missing exactly one
rule, not a hand-trimmed copy).

This only produces the treatment files. Running them through a live Agent
happens in run-230-ablation.sh; the deterministic core ablation in
run_ablation.py measures which rule removal moves a scripted fixture, which
is a different question answered on different bytes.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MALFORMED = 64

HEADING_RE = re.compile(r"^#{1,6}[ \t]")
RCA_HEADING_RE = re.compile(r"^### (RCA-\d{3}) ")
EXPECTED_RULE_COUNT = 13


class Malformed(Exception):
    pass


def find_rca_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map each RCA-0XX id to its [start, end) line range, heading included.

    A section ends at the next heading of any level, or at end of file. RCA
    headings are level 3 in the current document; this does not assume that
    level, only that some enclosing heading eventually closes the section.
    """
    heading_indices = [i for i, line in enumerate(lines) if HEADING_RE.match(line)]
    sections: dict[str, tuple[int, int]] = {}
    for position, index in enumerate(heading_indices):
        match = RCA_HEADING_RE.match(lines[index])
        if not match:
            continue
        rule_id = match.group(1)
        end = (
            heading_indices[position + 1]
            if position + 1 < len(heading_indices)
            else len(lines)
        )
        if rule_id in sections:
            raise Malformed(f"duplicate-rule-heading: {rule_id}")
        sections[rule_id] = (index, end)
    return sections


def expected_rule_ids() -> list[str]:
    return [f"RCA-{n:03d}" for n in range(1, EXPECTED_RULE_COUNT + 1)]


def generate(skill_text: str) -> dict[str, str]:
    lines = skill_text.splitlines(keepends=True)
    sections = find_rca_sections(lines)

    expected = expected_rule_ids()
    missing = sorted(set(expected) - set(sections))
    extra = sorted(set(sections) - set(expected))
    if missing or extra:
        raise Malformed(
            f"rule-heading-set-mismatch: missing={missing} extra={extra}"
        )

    treatments: dict[str, str] = {}
    for rule_id, (start, end) in sections.items():
        ablated = lines[:start] + lines[end:]
        treatments[rule_id] = "".join(ablated)
    return treatments


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-file",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "SKILL.md",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        skill_text = args.skill_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ABLATION-TREATMENT-INVALID absent-input: {args.skill_file}", file=sys.stderr)
        return MALFORMED
    except (OSError, UnicodeError) as exc:
        print(f"ABLATION-TREATMENT-INVALID unreadable-input: {exc}", file=sys.stderr)
        return MALFORMED

    try:
        treatments = generate(skill_text)
    except Malformed as exc:
        print(f"ABLATION-TREATMENT-INVALID {exc}", file=sys.stderr)
        return MALFORMED

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for rule_id in sorted(treatments):
        out_path = args.output_dir / f"candidate_minus_{rule_id}.md"
        out_path.write_text(treatments[rule_id], encoding="utf-8")

    print(
        f"ABLATION-TREATMENT-GREEN rules={len(treatments)} output={args.output_dir} "
        "-- treatment files written, no live Agent run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
