#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

python3 "$ROOT/scripts/check_refactor_proof.py" \
  --contract "$ROOT/references/example-refactor-proof.json"

python3 "$ROOT/scripts/check_golden_proof_registry.py" \
  --registry "$ROOT/references/golden-proof-registry.json"

python3 "$ROOT/tests/selftest.py"
