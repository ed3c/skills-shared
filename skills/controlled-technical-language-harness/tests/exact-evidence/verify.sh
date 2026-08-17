#!/usr/bin/env bash
set -euo pipefail

skill_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 "${skill_root}/scripts/check_exact_evidence.py" selftest
python3 -m py_compile \
  "${skill_root}/scripts/check_exact_evidence.py" \
  "${skill_root}/scripts/exact_evidence_core.py" \
  "${skill_root}/scripts/exact_evidence_calibration.py"

tmp="$(mktemp -d "${TMPDIR:-/tmp}/tmp.XXXXXXXX")"
trap 'rm -rf "${tmp}"' EXIT
printf '{not-json' >"${tmp}/bad.json"
set +e
python3 "${skill_root}/scripts/check_exact_evidence.py" deterministic \
  --repo-root "${skill_root}/../.." \
  --case "${tmp}/bad.json" >/dev/null 2>&1
code=$?
set -e

test "${code}" -eq 64
printf 'EXACT EVIDENCE GREEN: selftest, compile, and usage boundary passed\n'
