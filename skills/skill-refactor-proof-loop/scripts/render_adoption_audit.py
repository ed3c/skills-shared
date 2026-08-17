#!/usr/bin/env python3
"""Render/check the cross-Skill adoption audit report from the machine ledger.

The report is a projection, never a second source. Every number and every cell
below is read out of `references/skill-adoption-ledger.json`, which
`check_skill_adoption_ledger.py` has already replayed against current
repository bytes. `--check` re-renders and byte-compares, so a hand-edited
report, a stale report, or a ledger change that nobody re-rendered is a red
suite rather than a document that quietly disagrees with its own source.

The admission record is named in the header and nothing more: it says which
method is canonical, not what any Skill proved under it.

Exit codes: 0 green, 1 stale/unusable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]
LEDGER = "skills/skill-refactor-proof-loop/references/skill-adoption-ledger.json"
ADMISSION = "skills/skill-refactor-proof-loop/evals/proof-standard-admission.json"
RENDERER = "skills/skill-refactor-proof-loop/scripts/render_adoption_audit.py"
REPORT = "docs/traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md"

# Explicit, so the report's column order never depends on JSON key insertion order.
CRITERIA = [
    ("old_canonical_treatment_frozen", "FROZEN_A"),
    ("refactor_as_landed_treatment_frozen", "FROZEN_B0"),
    ("old_strengths_asserted", "STRENGTHS"),
    ("route_reachable", "ROUTES"),
    ("schema_and_semantic_gates_executable", "GATES"),
    ("hollow_dead_route_controls", "CONTROLS"),
    ("matched_hermetic_task", "HERMETIC"),
    ("golden_proof_registered", "GOLDEN"),
    ("live_model_runtime_ab", "LIVE_AB"),
    ("molecular_traceability", "DELIVERY"),
]
STATES = [
    "PASS",
    "PARTIAL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "NOT_APPLICABLE",
    "HUMAN_ADMIT_REQUIRED",
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def cell(text: str) -> str:
    return str(text).replace("|", "\\|")


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def build_report(ledger: dict, admission: dict) -> str:
    skills = sorted(ledger["skills"], key=lambda entry: entry["skill"])
    subject = admission["admitted_subject"]
    counts = {state: 0 for state in STATES}
    layers: dict[str, int] = {}
    gaps: dict[int, list[tuple[tuple[str, int], list[str]]]] = {}

    for entry in skills:
        layers[entry["highest_layer"]] = layers.get(entry["highest_layer"], 0) + 1
        for order, (name, _) in enumerate(CRITERIA):
            finding = entry["criteria"][name]
            if finding["state"] not in counts:
                # A state the report has no row for would vanish from the totals
                # while the cell count stayed right -- the exact silent lie this
                # report exists to refuse.
                raise ValueError(f"{entry['skill']}:{name}: unrenderable state {finding['state']}")
            counts[finding["state"]] += 1
            if finding["state"] == "PASS":
                continue
            gaps.setdefault(finding["owner_issue"], []).append(((entry["skill"], order), [
                f"`{entry['skill']}`",
                f"`{name}`",
                f"`{finding['state']}`",
                cell(finding.get("note", "—")),
            ]))

    cells = len(skills) * len(CRITERIA)
    owned = sum(len(rows) for rows in gaps.values())
    registered = sum(1 for entry in skills if entry["golden_proof_id"] is not None)

    out = [
        "# Cross-Skill adoption audit — issue #322",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        "",
        f"Rendered from [`{LEDGER}`](../../{LEDGER}) by [`{RENDERER}`](../../{RENDERER}).",
        f"Regenerate with `python3 {RENDERER}`; `--check` re-renders and byte-compares this file.",
        "`skills/skill-refactor-proof-loop/tests/run-all.sh` runs that `--check`, so a stale report is a red suite.",
        "",
        f"The standard this audit applies was admitted by [`{ADMISSION}`](../../{ADMISSION}):",
        f"approver `{admission['approver']}`, decided `{admission['decided_at']}`, `{admission['decision']}`,",
        f"subject `{subject['repository']}@{subject['commit'][:7]}` landed via {subject['landed_via']}.",
        "That record is a decision. It reports no run, no receipt and no measurement, and it promoted no",
        "Skill's proof level. Every state below is as measured by",
        "[`skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py`]"
        "(../../skills/skill-refactor-proof-loop/scripts/check_skill_adoption_ledger.py)",
        "against current repository bytes.",
        "",
        "## Headline",
        "",
    ]
    out.extend(table(["Measure", "Value"], [
        ["Skills classified", str(len(skills))],
        ["Criteria per Skill", str(len(CRITERIA))],
        ["Classification cells", str(cells)],
        ["`PASS` cells", str(counts["PASS"])],
        ["Non-`PASS` gaps", str(cells - counts["PASS"])],
        ["Gaps carrying an owning issue", str(owned)],
        ["Distinct owning issues", str(len(gaps))],
        ["Golden proofs registered", str(registered)],
    ]))
    out.extend(["", "Highest proof layer reached, per Skill:", ""])
    out.extend(table(
        ["Layer", "Skills"],
        [[f"`{layer}`", str(layers[layer])] for layer in sorted(layers)],
    ))
    out.extend(["", "Every classification cell, by state:", ""])
    out.extend(table(
        ["State", "Cells"],
        [[f"`{state}`", str(counts[state])] for state in STATES],
    ))

    out.extend([
        "",
        "## Per-Skill classification",
        "",
        "Column keys, in the order the standard asserts them:",
        "",
        "```text",
    ])
    out.extend(f"{short:<10} {name}" for name, short in CRITERIA)
    out.extend([
        "```",
        "",
    ])
    out.extend(table(
        ["Skill", "Layer", "Proof"] + [short for _, short in CRITERIA],
        [
            [
                f"`{entry['skill']}`",
                f"`{entry['highest_layer']}`",
                f"`{entry['golden_proof_id']}`" if entry["golden_proof_id"] else "none",
            ] + [f"`{entry['criteria'][name]['state']}`" for name, _ in CRITERIA]
            for entry in skills
        ],
    ))

    out.extend([
        "",
        "## Gaps by owner issue",
        "",
        "Every non-`PASS` cell above appears exactly once below, under the issue that owns it.",
        "An issue listed here is not a duplicate of the audit: it already exists in the ledger's",
        f"`known_issues` ({', '.join('#' + str(number) for number in ledger['known_issues'])}).",
    ])
    for issue in sorted(gaps):
        rows = [row for _, row in sorted(gaps[issue], key=lambda item: item[0])]
        plural = "gap" if len(rows) == 1 else "gaps"
        out.extend(["", f"### #{issue} — {len(rows)} {plural}", ""])
        out.extend(table(["Skill", "Criterion", "State", "Why"], rows))

    out.extend([
        "",
        "## Evidence boundary",
        "",
        "This report proves inventory and gap classification against current bytes. It does not prove",
        "model uplift, provider operation, scheduler or Shadow enforcement, Git Town/Forgejo delivery,",
        "merge, release or production readiness. `molecular_traceability` cannot reach `PASS` here at all:",
        "the audit is zero-network, and no offline byte proves current issue or PR delivery state.",
        "",
    ])
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        rendered = build_report(
            load(args.ledger or (root / LEDGER)),
            load(args.admission or (root / ADMISSION)),
        )
        output = args.output or (root / REPORT)
        if args.check:
            if not output.is_file():
                raise ValueError(f"adoption audit report is absent: {output}")
            if output.read_text(encoding="utf-8") != rendered:
                raise ValueError(f"adoption audit report is stale: {output}")
            print(f"ADOPTION-AUDIT-REPORT-GREEN {output.name} matches the ledger byte for byte")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"WROTE {output}")
        return 0
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"ADOPTION-AUDIT-REPORT-RED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
