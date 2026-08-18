#!/usr/bin/env bash
# Controls for the frozen-treatment A/B. The comparison itself is arithmetic
# over substrings; what has to be proved is that each of its three refusals
# actually bites, because a freeze that cannot detect drift, a preservation
# claim that cannot detect a lost guarantee, and a non-regression rule that
# cannot detect a regression all look exactly like a green run.
set -euo pipefail

skill_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
scorer="${skill_root}/scripts/refactor_ab.py"

python3 -m py_compile "${scorer}"
python3 "${scorer}" >/dev/null

work="$(mktemp -d "${TMPDIR:-/tmp}/refactor-treatments.XXXXXXXX")"
trap 'rm -rf "${work}"' EXIT

# Each planted defect gets its own copy of the Skill, and must be refused by
# its own error code. A shared return code would let one live rule cover for
# two dead ones.
plant() {
  local name="$1" expected="$2"
  shift 2
  local root="${work}/${name}"
  rm -rf "${root}"
  cp -R "${skill_root}" "${root}"
  "$@" "${root}"
  set +e
  local output code
  output="$(python3 "${scorer}" --skill-root "${root}" 2>&1)"
  code=$?
  set -e
  if [ "${code}" -ne 2 ]; then
    echo "FAIL: planted ${name} exited ${code}, expected 2" >&2
    exit 1
  fi
  if ! grep -Fq "${expected}" <<<"${output}"; then
    echo "FAIL: planted ${name} was not refused as ${expected}" >&2
    exit 1
  fi
}

drift_a_frozen_treatment() {
  printf '\n' >>"$1/tests/refactor-treatments/fixtures/old-canonical-SKILL.txt"
}

delete_the_relocated_strength() {
  local owner="$1/scripts/check_privacy_routing.py"
  python3 - "${owner}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("durable_receipt_fields", "receipt_fields"),
                encoding="utf-8")
PY
}

# Drops a guarantee B1 introduced and B2 inherited, rather than one of the
# baseline strengths, so this arm exercises the non-regression rule alone
# instead of riding on the old-strength rule.
regress_the_live_body() {
  local body="$1/SKILL.md"
  python3 - "${body}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("never sniffed from content",
                                                         "inferred from content"),
                encoding="utf-8")
PY
}

plant drifted-treatment TREATMENT_BLOB_DRIFT drift_a_frozen_treatment
plant relocated-strength-deleted OLD_STRENGTH_LOST delete_the_relocated_strength
plant live-body-regressed TREATMENT_REGRESSION regress_the_live_body

# An absent subject is not a failed comparison.
rm -rf "${work}/empty" && mkdir -p "${work}/empty"
set +e
python3 "${scorer}" --skill-root "${work}/empty" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent treatments exited ${absent_code}, expected 64" >&2
  exit 1
fi

printf 'PASS controlled-language frozen-treatment A/B: 3 planted defects refused by name\n'
