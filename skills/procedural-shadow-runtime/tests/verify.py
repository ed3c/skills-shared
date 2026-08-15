#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_runtime_receipt.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_RECEIPT = json.loads((FIXTURES / "valid-receipt.json").read_text(encoding="utf-8"))
VALID_CAPSULE = json.loads((FIXTURES / "valid-capsule.json").read_text(encoding="utf-8"))


def run(receipt: dict, capsule: dict | None = None) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        receipt_path = tmp_path / "receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        args = [sys.executable, str(CHECKER), str(receipt_path)]
        if capsule is not None:
            capsule_path = tmp_path / "capsule.json"
            capsule_path.write_text(json.dumps(capsule), encoding="utf-8")
            args.append(str(capsule_path))
        return subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode


def expect(name: str, receipt: dict, expected: int, capsule: dict | None = None) -> None:
    actual = run(receipt, capsule)
    if actual != expected:
        raise SystemExit(f"{name}: expected exit {expected}, got {actual}")


expect("positive", VALID_RECEIPT, 0, VALID_CAPSULE)

mutations: list[tuple[str, dict, dict | None]] = []

r = copy.deepcopy(VALID_RECEIPT)
r["dispositions"] = []
mutations.append(("missing-must-disposition", r, VALID_CAPSULE))

r = copy.deepcopy(VALID_RECEIPT)
r["dispositions"][0]["state"] = "PLANNED"
mutations.append(("non-terminal-pass", r, VALID_CAPSULE))

r = copy.deepcopy(VALID_RECEIPT)
r["evidence"] = []
mutations.append(("verified-without-evidence", r, VALID_CAPSULE))

r = copy.deepcopy(VALID_RECEIPT)
r["assertions"] = []
mutations.append(("verified-without-assertion", r, VALID_CAPSULE))

r = copy.deepcopy(VALID_RECEIPT)
del r["applicable_procedures"][0]["source"]["content_sha256"]
mutations.append(("source-without-content-digest", r, VALID_CAPSULE))

r = copy.deepcopy(VALID_RECEIPT)
r["private_reasoning"] = "forbidden"
mutations.append(("raw-private-reasoning", r, VALID_CAPSULE))

c = copy.deepcopy(VALID_CAPSULE)
c["context_digest"] = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
mutations.append(("stale-context-capsule", VALID_RECEIPT, c))

c = copy.deepcopy(VALID_CAPSULE)
c["expires_at_checkpoint"] = "FIRST_GREEN"
mutations.append(("expired-capsule", VALID_RECEIPT, c))

c = copy.deepcopy(VALID_CAPSULE)
c["authority"]["shadow_read_only"] = False
mutations.append(("shadow-write-authority", VALID_RECEIPT, c))

c = copy.deepcopy(VALID_CAPSULE)
c["authority"]["private_data_egress"] = "ALLOW"
mutations.append(("private-data-egress", VALID_RECEIPT, c))

for name, receipt, capsule in mutations:
    expect(name, receipt, 2, capsule)

with tempfile.TemporaryDirectory() as tmp:
    malformed = Path(tmp) / "bad.json"
    malformed.write_text("{not-json", encoding="utf-8")
    rc = subprocess.run([sys.executable, str(CHECKER), str(malformed)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode
    if rc != 64:
        raise SystemExit(f"malformed-input: expected exit 64, got {rc}")

missing_rc = subprocess.run([sys.executable, str(CHECKER), "/definitely/missing.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode
if missing_rc != 64:
    raise SystemExit(f"missing-input: expected exit 64, got {missing_rc}")

print(f"PROCEDURAL SHADOW RUNTIME GREEN: positive=1 mutations_refused={len(mutations)} input_errors=2")
