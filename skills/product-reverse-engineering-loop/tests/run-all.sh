#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REF="$ROOT/references"

# Positive controls: every committed artifact validates against its own schema,
# its semantic laws, and the subjects it names.
python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-product-signal.json"

python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-dossier.json" \
  --input "$REF/example-product-signal.json" \
  --resolve-subjects "$REF"

python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-closure-matrix.json" \
  --input "$REF/example-dossier.json" \
  --resolve-subjects "$REF"

python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-closure-audit.json" \
  --resolve-subjects "$REF"

python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-handoff.json" \
  --input "$REF/example-closure-matrix.json" \
  --resolve-subjects "$REF"

python3 "$ROOT/scripts/check_prel_contract.py" \
  --artifact "$REF/example-prompt-packet.json" \
  --resolve-subjects "$REF" \
  --catalogue "$REF/prompt-catalogue.md"

# Byte-stability: each committed projection is what its input compiles to.
python3 "$ROOT/scripts/compile_prel.py" --stage dossier \
  --input "$REF/example-product-signal.json" \
  --out "$REF/example-dossier.json" --check

python3 "$ROOT/scripts/compile_prel.py" --stage closure \
  --input "$REF/example-dossier.json" \
  --out "$REF/example-closure-matrix.json" --check

python3 "$ROOT/scripts/compile_prel.py" --stage handoff \
  --input "$REF/example-closure-matrix.json" \
  --out "$REF/example-handoff.json" --check

# Negative controls: every refusal code is planted and must go red by its own name.
python3 "$ROOT/tests/selftest.py"
