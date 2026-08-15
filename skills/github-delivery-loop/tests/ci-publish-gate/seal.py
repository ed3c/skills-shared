#!/usr/bin/env python3
"""Seal a fixture receipt to matching evidence for the scratch repository.

The digests bind the scratch repository's exact head and tree, so neither file
can be a static fixture: a checked-in digest would be wrong on every run, and
the positive case would then pass only because the gate refused for a reason
that has nothing to do with what the test is asserting.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

gate_path, repo, receipt_path, evidence_path = (Path(a) for a in sys.argv[1:5])
foreign = len(sys.argv) > 5 and sys.argv[5] == "--foreign"

spec = importlib.util.spec_from_file_location("gate", gate_path)
gate = importlib.util.module_from_spec(spec)
# Register before executing: @dataclass resolves annotations through
# sys.modules[cls.__module__], which is None for a module that was never
# registered, and the gate defines one.
sys.modules["gate"] = gate
spec.loader.exec_module(gate)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True
    ).stdout.strip()


receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
head, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")

evidence = {
    "schema": gate.EVIDENCE_SCHEMA,
    "repository_id": receipt["repository_id"],
    "head_sha": head,
    "tree_sha": tree,
    "contract_sha256": "d" * 64,
    "verified_at": receipt["verified_at"],
    "clean_subject": True,
    "commands": [
        {
            "id": command_id,
            "argv": ["bash", "skills/github-delivery-loop/tests/run-all.sh"],
            "cwd": ".",
            "timeout_seconds": 600,
            "max_output_bytes": 1048576,
            "started_at": receipt["verified_at"],
            "duration_ms": 1200,
            "exit": 0,
            "timed_out": False,
            "spawn_error": None,
            "stdout_bytes": 12,
            "stderr_bytes": 0,
            "stdout_sha256": "b" * 64,
            "stderr_sha256": "c" * 64,
            "stdout_truncated": False,
            "stderr_truncated": False,
        }
        for command_id in receipt["commands"]
    ],
    "status": "PASS",
}
evidence["content_sha256"] = gate.digest_of(evidence)

if not foreign:
    # The honest pairing: the receipt names exactly these bytes.
    receipt["evidence_sha256"] = gate.digest_of(evidence)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

evidence_path.write_text(
    json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
