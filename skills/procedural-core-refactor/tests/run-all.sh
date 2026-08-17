#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RECEIPT=${TMPDIR:-/tmp}/procedural-core-refactor-receipt-$$.json
trap 'rm -f "$RECEIPT"' EXIT HUP INT TERM

python3 -m json.tool "$ROOT/references/refactor-contract.schema.json" >/dev/null
python3 -m json.tool "$ROOT/references/golden-proof.schema.json" >/dev/null
python3 -m json.tool "$ROOT/references/example-refactor-contract.json" >/dev/null
python3 -m json.tool "$ROOT/references/tech-lead-golden-proof.json" >/dev/null

python3 "$ROOT/scripts/check_refactor_contract.py" \
  --contract "$ROOT/references/example-refactor-contract.json" \
  --proof "$ROOT/references/tech-lead-golden-proof.json" \
  --receipt "$RECEIPT"

python3 "$ROOT/tests/selftest.py"

python3 - "$RECEIPT" <<'PY'
import json
import sys
from pathlib import Path
receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["verdict"] == "PASS", receipt
assert receipt["evidence_class"] == "DETERMINISTIC_FIXTURE", receipt
assert receipt["claims_not_proven"], receipt
print("PCR-RECEIPT-GREEN deterministic proof kept below live model/provider/delivery")
PY
