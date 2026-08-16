#!/usr/bin/env python3
"""Controls for #218 Lane A retrieval. Offline.

The unpinned-ref refusal is checked through the real entry point because it must
happen *before* the fetch: a control that only fires after the network call
would still have leaked a request for a mutable ref.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "retrieve_external_skill.py"


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

# `example.invalid` never resolves, so reaching the network would fail with 64.
# Exit 2 proves the ref was rejected first.
expect("unpinned-ref-refused-before-fetch", 2,
       "--repository", "example/invalid", "--ref", "main",
       "--path", "SKILL.md", "--select", "overview",
       "--output", "/dev/null")

print("EXTERNAL RETRIEVAL GREEN: selftest passes; absent input exits 64; "
      "a mutable ref is refused before any request is made")
