#!/usr/bin/env python3
"""Build the five treatment arms #219 requires, and prove they actually differ.

Exit codes:
  0   all five arms built and pairwise distinct
  2   two arms produced identical treatment bytes
  64  a source Skill or reference is absent

The arms are worth distinguishing precisely:

    A NO_SKILL                    nothing
    B METADATA_ONLY               name and one-line description; no procedure text
    C FULL_SKILL                  the whole Skill body
    D DELTA_CAPSULE               only the procedures applicable to this task,
                                  as a Context Capsule, with expected observation
    E DELTA_CAPSULE_PLUS_HARNESS  the capsule plus the executable checker that
                                  enforces it

B exists to separate "the model saw a name it recognises" from "the model read a
procedure". D exists to separate "more text helped" from "the applicable
procedures helped" -- the confound #225 could not resolve, where the candidate was
eight times longer than its baseline. E exists to separate advice from
enforcement.

An arm set whose members are not byte-distinct measures nothing, so that is
checked here rather than assumed downstream.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]

INVALID = 64
IDENTICAL = 2

CAPSULE_PROCEDURES = [
    {
        "procedure_id": "procedural-shadow.bind-exact-subject",
        "criticality": "must",
        "expected_observation": "every claim cites a path resolved from the pinned tree",
    },
    {
        "procedure_id": "procedural-shadow.declare-non-claims",
        "criticality": "must",
        "expected_observation": "the answer states explicitly what its evidence does not support",
    },
    {
        "procedure_id": "procedural-shadow.no-escalation-without-trigger",
        "criticality": "should",
        "expected_observation": "a documentation-only subject is declined rather than audited",
    },
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skill_body() -> str:
    return (SKILL / "SKILL.md").read_text(encoding="utf-8")


def metadata_only(body: str) -> str:
    """Name and description only -- recognisable, but carrying no procedure."""
    front = re.match(r"^---\n(.*?)\n---\n", body, re.S)
    fields = {}
    if front:
        for line in front.group(1).splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
    name = fields.get("name", "procedural-shadow-runtime")
    description = fields.get("description", "")[:300]
    return (
        f"A Skill named `{name}` is available.\n"
        f"Its stated purpose: {description}\n"
        "Its procedures are not included here."
    )


def delta_capsule() -> str:
    capsule = {
        "schema": "context-capsule/v1-uplift-arm",
        "checkpoint": "BEFORE_ANSWER",
        "procedures": CAPSULE_PROCEDURES,
        "note": "Only procedures applicable to this task are injected. "
                "The full Skill body is deliberately withheld.",
    }
    return (
        "Apply exactly these procedures. Nothing else from any Skill applies.\n\n"
        + json.dumps(capsule, indent=2, sort_keys=True)
    )


def harness_text() -> str:
    """The enforcement half: what will actually be checked, and how."""
    return (
        "\n\n===== ENFORCEMENT =====\n\n"
        "Your answer is checked mechanically after you write it:\n"
        "- every path in evidence_paths must exist in the pinned tree; "
        "a path that does not is counted as a false pass;\n"
        "- non_claims must be non-empty, or the evidence packet is judged incomplete;\n"
        "- tree_sha must equal the one you were given, or exact-subject continuity fails.\n"
        "These are not advice. They are the gates your output is scored against."
    )


def build() -> dict[str, str]:
    body = skill_body()
    capsule = delta_capsule()
    return {
        "A_NO_SKILL": "",
        "B_METADATA_ONLY": metadata_only(body),
        "C_FULL_SKILL": body,
        "D_DELTA_CAPSULE": capsule,
        "E_DELTA_CAPSULE_PLUS_HARNESS": capsule + harness_text(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not (SKILL / "SKILL.md").is_file():
        print(f"ARMS-INVALID absent-skill: {SKILL / 'SKILL.md'}", file=sys.stderr)
        return INVALID

    arms = build()
    args.output.mkdir(parents=True, exist_ok=True)

    digests: dict[str, str] = {}
    manifest: list[dict[str, Any]] = []
    for name, text in arms.items():
        path = args.output / f"{name}.txt"
        path.write_text(text, encoding="utf-8")
        digest = sha256_text(text)
        digests.setdefault(digest, name)
        manifest.append({
            "arm": name,
            "bytes": len(text.encode("utf-8")),
            "digest": digest,
        })

    collisions = [
        (a["arm"], b["arm"])
        for i, a in enumerate(manifest) for b in manifest[i + 1:]
        if a["digest"] == b["digest"]
    ]
    if collisions:
        for left, right in collisions:
            print(f"ARMS-IDENTICAL {left} and {right} produce the same bytes",
                  file=sys.stderr)
        return IDENTICAL

    (args.output / "arm-manifest.json").write_text(
        json.dumps({
            "schema": "uplift-arm-manifest/v1",
            "arms": manifest,
            "set_digest": sha256_text(json.dumps(sorted(m["digest"] for m in manifest))),
            "pairwise_distinct": True,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for item in manifest:
        print(f"{item['arm']:<30} {item['bytes']:>7} bytes  {item['digest'][:12]}")
    print(f"ARMS-GREEN five arms built, pairwise distinct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
