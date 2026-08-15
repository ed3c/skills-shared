#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = (
    "skill.md-native",
    "chromium",
    "playwright",
    "docker",
    "openshell",
    "cloudflare",
    "android",
    "github",
    "localhost",
    "127.0.0.1",
    "errno",
    "worked example",
    "case study",
    "例如",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    atoms = json.loads((ROOT / "evals" / "contract.json").read_text(encoding="utf-8"))
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    lowered = text.lower()

    failures: list[str] = []
    for token in BANNED:
        if token.lower() in lowered:
            failures.append(f"domain/example token leaked into SKILL.md: {token}")

    expected = {item["id"] for item in atoms["retained"]}
    observed = set(re.findall(r"RCA-\d{3}", text))
    if observed != expected:
        failures.append(
            f"core rule IDs differ: missing={sorted(expected-observed)} extra={sorted(observed-expected)}"
        )
    for rule_id in sorted(expected):
        if text.count(f"### {rule_id} ") != 1:
            failures.append(f"{rule_id} must have exactly one core heading")
        ablation = report["ablations"].get(rule_id)
        if not ablation or not ablation.get("effective"):
            failures.append(f"{rule_id} lacks a deciding runtime ablation delta")
        if not ablation or ablation.get("score_delta", 0) >= 0:
            failures.append(f"{rule_id} removal did not reduce score")

    if set(report["runtime_supported_rules"]) != expected:
        failures.append("runtime-supported rule set differs from core")
    if report["core_supported_fraction"] != 1.0:
        failures.append("core-supported fraction must remain 1.0")
    if report["profiles"]["candidate_trimmed_skill"]["metrics"]["score"] != 1.0:
        failures.append("candidate profile must satisfy all committed cases")
    if report["profiles"]["no_skill"]["metrics"]["score"] >= report["profiles"]["candidate_trimmed_skill"]["metrics"]["score"]:
        failures.append("no_skill must not tie or outperform the candidate")

    if failures:
        for failure in failures:
            print(f"CORE RED: {failure}")
        return 2
    print(
        "CORE GREEN: every SKILL.md rule has a deciding runtime delta; "
        "domain instances remain outside the core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
