#!/usr/bin/env python3
"""Plant first-only canonical-drift mutants and require the real fixture to kill each."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parent.parent
SOURCE = SKILL_DIR / "scripts" / "check_canonical_drift.py"
VERIFY = TEST_DIR / "verify.sh"

MUTATIONS = {
    "first-unpushed": (
        "lines = ahead.splitlines()",
        "lines = ahead.splitlines()[:1]",
    ),
    "first-behind": (
        "lines = behind.splitlines()",
        "lines = behind.splitlines()[:1]",
    ),
    "first-dirty": (
        "lines = dirty.splitlines()",
        "lines = dirty.splitlines()[:1]",
    ),
}


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                failures.append(
                    f"{name}: mutation anchor count is {source.count(needle)}, expected exactly 1"
                )
                continue
            mutant = root / f"{name}.py"
            mutant.write_text(source.replace(needle, replacement), encoding="utf-8")
            env = os.environ.copy()
            env["DRIFT_SCRIPT"] = str(mutant)
            env["CANONICAL_DRIFT_MUTANT_RUN"] = "1"
            done = subprocess.run(
                ["bash", str(VERIFY)],
                cwd=TEST_DIR,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            if done.returncode == 0:
                failures.append(f"{name}: SURVIVED; fixture did not distinguish first-only behavior")
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(f"PASS canonical drift mutation proof: {len(MUTATIONS)} first-only mutants killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
