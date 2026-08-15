#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical binding-stale gate.

The implementation lives with the shared-skills governance skill, which is what
`shared_skills.py check` calls: one parser, one rule set, one repository-wide
contract. A module must not resolve upward into the repository root, so the gate
lives beside the tool that owns it and this file only forwards. Keep it -- CI and
local verification call this path -- but do not fork the semantics here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skills" / "shared-skills-infra" / "scripts" / "check_binding_stale.py"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not CANONICAL.is_file():
        print(f"FAIL canonical binding-stale gate missing: {CANONICAL}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(CANONICAL), *args], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
