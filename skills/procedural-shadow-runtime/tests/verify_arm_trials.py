#!/usr/bin/env python3
"""Controls for the matched arm-trial adapter. No host is invoked.

A verifier that needed a provider would be red on every runner without one, and
would then be disabled, which is how a control stops controlling. Everything
here is decidable from the checkout.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_arm_trials.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, check=False)


def expect(name: str, expected: int, *args: str) -> None:
    result = run(*args)
    if result.returncode != expected:
        raise SystemExit(
            f"{name}: expected exit {expected}, got {result.returncode}\n{result.stderr[-600:]}"
        )


expect("selftest", 0, "--selftest")

# Absent input is 64, not argparse's 2. Collapsing it into 2 would make a
# forgotten flag look like a semantic refusal.
expect("missing-host-and-output", 64)
expect("missing-output", 64, "--host", "claude-code")

# The plan resolves every binding -- git subject, arm digests, ground truth --
# without spending a provider call, so a broken subject is caught before a run.
plan = run("--host", "claude-code", "--dry-run", "--output",
           str(Path(__file__).resolve().parent / "__dryrun__"))
if plan.returncode != 0:
    raise SystemExit(f"dry-run: expected exit 0, got {plan.returncode}\n{plan.stderr[-600:]}")
for arm in ("A_NO_SKILL", "B_METADATA_ONLY", "C_FULL_SKILL",
            "D_DELTA_CAPSULE", "E_DELTA_CAPSULE_PLUS_HARNESS"):
    if arm not in plan.stdout:
        raise SystemExit(f"dry-run: arm {arm} missing from the plan\n{plan.stdout}")
if "DRY-RUN GREEN" not in plan.stdout:
    raise SystemExit(f"dry-run: no green line\n{plan.stdout}")

print("ARM TRIALS GREEN: selftest passes; absent input exits 64; "
      "the dry-run plan resolves all five arms without invoking a host")
