#!/usr/bin/env python3
"""Controls for #216, including the one that matters most: the loop must BLOCK.

A feedback loop that closes without a Human decision is not a feedback loop with
an optional gate -- it is a loop with no gate, and it will look identical in
every report. So the absence of an adjudication record is checked as a refusal
here, not just documented.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "trace_feedback_loop.py"
ADJUDICATION = SKILL / "evals" / "adjudications" / "canary-2026-08-16.json"


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
expect("missing-output", 64)
expect("absent-case-set", 64, "--cases", "/definitely/missing.json", "--output", "/dev/null")

with tempfile.TemporaryDirectory() as tmp:
    unadjudicated = Path(tmp) / "no-human.json"
    result = run("--output", str(unadjudicated))
    if result.returncode != 2:
        raise SystemExit(f"unadjudicated-loop: expected exit 2, got {result.returncode}")
    lanes = json.loads(unadjudicated.read_text(encoding="utf-8"))["lanes"]
    for lane in ("HUMAN_ADJUDICATED", "GOLDEN_ADMITTED", "REGRESSION_REPLAYED"):
        if lanes[lane] != "BLOCKED":
            raise SystemExit(f"unadjudicated-loop: {lane} was {lanes[lane]}, expected BLOCKED")
    for lane in ("PRODUCTION_TRACE", "PII_SCRUBBED"):
        if lanes[lane] != "OBSERVED":
            raise SystemExit(f"unadjudicated-loop: {lane} was {lanes[lane]}, expected OBSERVED")

    closed = Path(tmp) / "closed.json"
    expect("adjudicated-loop", 0, "--adjudication", str(ADJUDICATION), "--output", str(closed))
    report = json.loads(closed.read_text(encoding="utf-8"))
    if any(state != "OBSERVED" for state in report["lanes"].values()):
        raise SystemExit(f"adjudicated-loop: a lane did not close: {report['lanes']}")

    # Coverage is only meaningful if the denominator survives deduplication. A
    # loop that dropped the duplicate from both sides would report 1.0 here.
    counts = report["counts"]
    if counts["duplicates_rejected"] != 1 or counts["feedback_closure_rate"] >= 1.0:
        raise SystemExit(f"closure rate ignored a deduplicated case: {counts}")

    # No scrubbed value may reach the artefact, and no raw one either.
    body = closed.read_text(encoding="utf-8")
    for leaked in ("@example.invalid", "4111111111111111", "555-01"):
        if leaked in body:
            raise SystemExit(f"a raw identifier reached the report artefact: {leaked}")

print("FEEDBACK LOOP GREEN: selftest passes; absent input and absent case set exit 64; "
      "without a Human record the adjudication, admission and replay lanes are BLOCKED; "
      "with one every lane closes; the closure rate keeps the deduplicated case in its "
      "denominator; no raw identifier reaches the report")
