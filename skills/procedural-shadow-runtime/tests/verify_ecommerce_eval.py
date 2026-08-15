#!/usr/bin/env python3
"""Executable positive, unsafe-adapter, and input controls for the domain module."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "modules" / "ecommerce-dispute" / "run_evals.py"
CASES = ROOT / "modules" / "ecommerce-dispute" / "cases.json"
REFERENCE = ROOT / "modules" / "ecommerce-dispute" / "reference_adapter.py"
UNSAFE = Path(__file__).resolve().parent / "fixtures" / "unsafe-ecommerce-adapter.py"
SHA40 = "1" * 40
SHA256 = "c" * 64


def run(adapter: Path, cases: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-S",
            str(RUNNER),
            "--adapter",
            str(adapter),
            "--cases",
            str(cases),
            "--repository",
            "ed3c/skills-shared",
            "--subject-sha",
            SHA40,
            "--subject-digest",
            SHA256,
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def expect(result: subprocess.CompletedProcess[str], code: int, label: str) -> None:
    if result.returncode != code:
        raise AssertionError(
            f"{label}: expected exit {code}, got {result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ecommerce-domain-evals-") as tmp:
        directory = Path(tmp)
        positive_output = directory / "positive.json"
        positive = run(REFERENCE, CASES, positive_output)
        expect(positive, 0, "reference-adapter")
        receipt = json.loads(positive_output.read_text(encoding="utf-8"))
        assert receipt["summary"]["execution_state"] == "PASS"
        assert receipt["summary"]["safety_failures"] == 0
        assert len(receipt["case_receipts"]) == 6

        unsafe_output = directory / "unsafe.json"
        unsafe = run(UNSAFE, CASES, unsafe_output)
        expect(unsafe, 2, "unsafe-adapter")
        unsafe_receipt = json.loads(unsafe_output.read_text(encoding="utf-8"))
        assert unsafe_receipt["summary"]["safety_failures"] >= 1

        malformed_cases = directory / "malformed.json"
        malformed_cases.write_text("{not-json", encoding="utf-8")
        expect(run(REFERENCE, malformed_cases, directory / "malformed-output.json"), 64, "malformed-cases")
        expect(run(directory / "absent-adapter.py", CASES, directory / "absent-output.json"), 64, "absent-adapter")

    print("ECOMMERCE DOMAIN EVAL GREEN: positive=1 unsafe_refused=1 input_errors=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
