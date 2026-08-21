#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
cd "$ROOT"

python3 -m json.tool \
  skills/repository-entropy-reclamation/references/entropy-audit.schema.json \
  >/dev/null
python3 -m json.tool \
  skills/repository-entropy-reclamation/references/example-audit.json \
  >/dev/null
python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py \
  --audit skills/repository-entropy-reclamation/references/example-audit.json
python3 skills/repository-entropy-reclamation/scripts/assert_entropy_audit.py \
  --selftest
python3 -m unittest discover \
  -s skills/repository-entropy-reclamation/tests \
  -p 'test_*.py'
