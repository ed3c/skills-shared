#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORE_BEGIN = "## Portable procedural core"
CORE_END = "## Hard laws and executable assertions"
ATOM_IDS = [f"DL-{i:02d}" for i in range(1, 10)]
LAW_IDS = [f"DL-L{i:02d}" for i in range(1, 11)]
EVIDENCE_STATES = [
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
]
FORBIDDEN_CORE_PATTERNS = [
    (r"\bGitHub\b", "GitHub"),
    (r"\bActions\b", "Actions"),
    (r"\bmerge-admit\b", "merge-admit"),
    (r"\bpull request\b", "pull request"),
    (r"\bPR\b", "PR"),
    (r"\bbilling\b", "billing"),
    (r"\bCodex\b", "Codex"),
    (r"\bClaude\b", "Claude"),
    (r"\bForgejo\b", "Forgejo"),
    (r"`gh\s+[^`]+`", "gh command"),
]


def fail(message: str) -> None:
    raise ValueError(message)


def bounded_core(text: str) -> str:
    start = text.find(CORE_BEGIN)
    end = text.find(CORE_END)
    if start < 0 or end < 0 or end <= start:
        fail("portable core markers are absent or malformed")
    return text[start:end]


def check(root: Path) -> list[str]:
    skill = root / "SKILL.md"
    module = root / "modules" / "github-domain.md"
    evals = root / "evals.json"
    test = root / "tests" / "procedural-core" / "verify.sh"
    for path in (skill, module, evals, test):
        if not path.is_file():
            fail(f"required path absent: {path.relative_to(root)}")

    text = skill.read_text(encoding="utf-8")
    core = bounded_core(text)
    for atom in ATOM_IDS:
        if atom not in core:
            fail(f"procedure atom absent from portable core: {atom}")
    for law in LAW_IDS:
        if law not in text:
            fail(f"hard law absent: {law}")
    for state in EVIDENCE_STATES:
        if state not in text:
            fail(f"evidence state absent: {state}")
    for pattern, label in FORBIDDEN_CORE_PATTERNS:
        if re.search(pattern, core, flags=re.IGNORECASE):
            fail(f"domain token leaked into portable core: {label}")

    rows = [line for line in text.splitlines() if line.startswith("| DL-L")]
    if len(rows) != len(LAW_IDS):
        fail(f"expected {len(LAW_IDS)} hard-law assertion rows, found {len(rows)}")
    for law in LAW_IDS:
        row = next((line for line in rows if f"| {law} |" in line), None)
        if row is None:
            fail(f"hard law has no assertion row: {law}")
        if "`" not in row or ("python3 " not in row and "bash " not in row):
            fail(f"hard law has no executable assertion command: {law}")

    module_text = module.read_text(encoding="utf-8")
    for atom in ATOM_IDS:
        if atom not in module_text:
            fail(f"GitHub domain module does not map portable atom: {atom}")
    for owner in (
        "github_delivery.py",
        "local_verification.py",
        "ci_publish_gate.py",
        "ci_publish.py",
        "github_actions_snapshot.py",
        "merge_gate.py",
    ):
        if owner not in module_text:
            fail(f"GitHub domain executable owner absent: {owner}")

    eval_text = evals.read_text(encoding="utf-8")
    if "DELIVERY-11" not in eval_text or "check_procedural_core.py" not in eval_text:
        fail("procedural-core eval is not registered")

    return [
        f"atoms={len(ATOM_IDS)}",
        f"laws={len(LAW_IDS)}",
        "domain=github-domain.md",
        "assertions=BOUND",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        details = check(args.root.resolve())
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"PROCEDURAL-CORE RED: {exc}", file=sys.stderr)
        return 2
    print("PROCEDURAL-CORE GREEN: " + " ".join(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
