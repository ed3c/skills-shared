#!/usr/bin/env python3
"""Controls for the matched arm-trial adapter. No host is invoked.

A verifier that needed a provider would be red on every runner without one, and
would then be disabled, which is how a control stops controlling. Everything
here is decidable from the checkout.
"""
from __future__ import annotations

import hashlib
import json
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

# Each committed matrix receipt records a response_digest per cell. The response
# it digests has to exist somewhere, or the digest is a claim about text nobody
# can check. The cells live beside the receipts and are verified against it.
RECEIPTS = Path(__file__).resolve().parents[1] / "evals" / "receipts"
CELLS = RECEIPTS / "arm-cells"
verified = 0
for receipt_path in sorted(RECEIPTS.glob("arm-trials-*.json")):
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    host = receipt["trial_matrix"]["host"]
    for cell in receipt["trial_matrix"]["cells"]:
        cell_path = CELLS / f"cell-{host}-{cell['repetition']}-{cell['arm']}.json"
        if not cell_path.is_file():
            raise SystemExit(
                f"{receipt_path.name} records a response_digest for {host}/{cell['arm']} "
                f"but {cell_path.name} is not committed"
            )
        stored = json.loads(cell_path.read_text(encoding="utf-8"))
        actual = hashlib.sha256(stored["response"].encode()).hexdigest()
        if actual != cell["response_digest"]:
            raise SystemExit(
                f"{cell_path.name}: receipt records {cell['response_digest'][:12]}, "
                f"the committed response hashes to {actual[:12]}"
            )
        if stored["score"] != cell["score"]:
            raise SystemExit(f"{cell_path.name}: committed score disagrees with the receipt")
        verified += 1

print("ARM TRIALS GREEN: selftest passes; absent input exits 64; "
      "the dry-run plan resolves all five arms without invoking a host; "
      f"{verified} committed cell response(s) hash to the digest their receipt records")
