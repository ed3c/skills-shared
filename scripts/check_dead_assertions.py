#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical dead-assertion linter.

The implementation lives with the shared-skills governance skill so there is one
parser, one rule set, and one repository-wide sweep contract. Keep this root
entrypoint because eval/CI callers use it, but do not fork the semantics here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skills" / "shared-skills-infra" / "scripts" / "check_dead_assertions.py"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not CANONICAL.is_file():
        print(f"FAIL canonical dead-assertion linter missing: {CANONICAL}", file=sys.stderr)
        return 2
    completed = subprocess.run([sys.executable, str(CANONICAL), *args], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
