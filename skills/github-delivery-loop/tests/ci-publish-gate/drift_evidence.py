#!/usr/bin/env python3
"""Change the evidence and re-derive its own digest, but not the receipt's.

This is the compact-only path stated as a fixture: the evidence is internally
consistent and the receipt is internally perfect, and the only thing wrong is
that the receipt's `evidence_sha256` describes bytes that no longer exist. That
is precisely what nothing recomputed before.

Leaving `content_sha256` stale would also be refused, but by the content-digest
check standing in front of the receipt check -- the control would pass while
proving nothing about the rule it is named after.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

gate_path, evidence_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

spec = importlib.util.spec_from_file_location("gate", gate_path)
gate = importlib.util.module_from_spec(spec)
sys.modules["gate"] = gate
spec.loader.exec_module(gate)

evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
evidence["contract_sha256"] = "9" * 64
body = {key: value for key, value in evidence.items() if key != "content_sha256"}
evidence["content_sha256"] = gate.digest_of(body)
evidence_path.write_text(
    json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
