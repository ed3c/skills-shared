#!/usr/bin/env python3
"""Controls for the #219 aggregator, and one on the receipts this repository ships.

The aggregator's own selftest covers the refusals. This adds the check that
matters after the fact: the committed arm-trial receipts must still aggregate to
a non-qualifying verdict. If someone later regenerates them at a higher n
without the preregistered conditions, this fails rather than letting the stored
summary quietly become a claim.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "summarise_uplift_matrix.py"
RECEIPTS = SKILL / "evals" / "receipts"
SUMMARY = SKILL / "evals" / "uplift-matrix-summary.json"


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
expect("missing-arguments", 64)
expect("absent-receipt", 64, "--receipt", "h=/definitely/missing.json", "--output", "/dev/null")

arm_receipts = sorted(RECEIPTS.glob("arm-trials-*.json"))
if len(arm_receipts) < 2:
    raise SystemExit(f"expected arm-trial receipts from two hosts, found {len(arm_receipts)}")

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "summary.json"
    args = []
    for receipt in arm_receipts:
        host = receipt.stem.replace("arm-trials-", "").rsplit("-", 1)[0]
        args += ["--receipt", f"{host}={receipt}"]
    result = run(*args, "--output", str(out))
    if result.returncode != 2:
        raise SystemExit(
            f"shipped receipts: expected a non-qualifying exit 2, got {result.returncode}"
        )
    fresh = json.loads(out.read_text(encoding="utf-8"))
    if fresh["qualifies_for_219"]:
        raise SystemExit("shipped receipts now qualify as the #219 matrix without a preregistered run")
    if fresh["contrasts_reported"]:
        raise SystemExit("a contrast was reported from a non-qualifying matrix")

if SUMMARY.is_file():
    stored = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if stored["verdict"] != fresh["verdict"] or stored["qualifies_for_219"] != fresh["qualifies_for_219"]:
        raise SystemExit(
            f"stored summary verdict {stored['verdict']!r} disagrees with a fresh "
            f"aggregation {fresh['verdict']!r}"
        )

print(f"UPLIFT MATRIX GREEN: selftest passes; absent input exits 64; the shipped receipts "
      f"aggregate to {fresh['verdict']} with no contrast reported, and the stored summary agrees")
