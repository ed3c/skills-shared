#!/usr/bin/env bash
set -euo pipefail
owner="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
checker="${owner}/scripts/check_cadg_packet.py"

python3 -m py_compile "${checker}" "${owner}/scripts/check_design_admission.py"
python3 "${checker}" --packet "${owner}/examples/cadg/positive-forward-material-change.json" \
  --receipt "${owner}/examples/cadg/positive-admission-receipt.json"
python3 "${checker}" --packet "${owner}/examples/cadg/positive-reconstructed-history.json"
python3 "${checker}" --selftest

python3 - "${owner}" <<'PY'
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator

owner = Path(sys.argv[1])
packet_schema = json.loads((owner / "references/cadg/cadg-packet.schema.json").read_text())
receipt_schema = json.loads((owner / "references/cadg/cadg-admission-receipt.schema.json").read_text())
Draft202012Validator.check_schema(packet_schema)
Draft202012Validator.check_schema(receipt_schema)
packet_validator = Draft202012Validator(packet_schema)
receipt_validator = Draft202012Validator(receipt_schema)
for name in ("positive-forward-material-change.json", "positive-reconstructed-history.json"):
    packet_validator.validate(json.loads((owner / "examples/cadg" / name).read_text()))
receipt_validator.validate(json.loads((owner / "examples/cadg/positive-admission-receipt.json").read_text()))
print("CADG-SCHEMAS-GREEN draft=2020-12 packets=2 receipts=1")
PY
