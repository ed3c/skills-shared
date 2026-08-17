#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

python3 "$ROOT/scripts/check_refactor_proof.py" \
  --contract "$ROOT/references/example-refactor-proof.json"

python3 "$ROOT/scripts/check_golden_proof_registry.py" \
  --registry "$ROOT/references/golden-proof-registry.json"

python3 "$ROOT/scripts/check_refactor_proof_stack.py" \
  --stack "$ROOT/references/refactor-proof-stack.json"

python3 "$ROOT/scripts/check_skill_adoption_ledger.py" \
  --ledger "$ROOT/references/skill-adoption-ledger.json"

python3 "$ROOT/scripts/render_adoption_audit.py" --check

python3 "$ROOT/tests/selftest.py"
python3 "$ROOT/tests/stack_selftest.py"
python3 "$ROOT/tests/adoption_selftest.py"
python3 "$ROOT/tests/render_selftest.py"
