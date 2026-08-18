#!/usr/bin/env bash
# Positive and planted controls for this Skill's own refactor proof. Zero network.
#
# The positive run alone would be worthless: a scorer that says "green" for every
# input reads exactly like one that measured something. So the frozen treatments
# are mutated one at a time and the same entrypoint must go red for the stated
# reason.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
entrypoint="${test_dir}/refactor_ab.py"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/scratch.XXXXXXXX")"
trap 'rm -rf "${scratch}"' EXIT

# good: frozen A/B0 bytes, the live body, and the matched task on this tree
python3 "${entrypoint}" > "${scratch}/report.json"
grep -q "DELIVERY-REFACTOR-AB-GREEN" "${scratch}/report.json"

# hollow: historical bytes are evidence, so drift in a frozen treatment is fatal
# rather than a re-freeze against whatever the file says today
cp -R "${skill_dir}/." "${scratch}/drift"
printf '\nedited to improve the score\n' \
  >> "${scratch}/drift/tests/refactor-proof/fixtures/refactor-as-landed-SKILL.txt"
if python3 "${entrypoint}" --skill-root "${scratch}/drift" \
  >"${scratch}/drift.out" 2>"${scratch}/drift.err"; then
  echo "FAIL: an edited frozen treatment was accepted" >&2
  exit 1
fi
grep -q "frozen treatment drift" "${scratch}/drift.err"

# mutation: the repaired candidate must keep the strength it was repaired to
# restore. Domination alone cannot see this -- B0 never held the criterion, so a
# candidate that drops it still dominates B0 on every other axis.
cp -R "${skill_dir}/." "${scratch}/unrepaired"
python3 - "${scratch}/unrepaired/SKILL.md" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
mutated = text.replace("tests/index/verify.sh", "tests/index/not-wired.sh")
assert mutated != text, "index-discipline claim was already absent from SKILL.md"
path.write_text(mutated, encoding="utf-8")
PY
if python3 "${entrypoint}" --skill-root "${scratch}/unrepaired" \
  >"${scratch}/unrepaired.out" 2>"${scratch}/unrepaired.err"; then
  echo "FAIL: a candidate that dropped the restored strength was accepted" >&2
  exit 1
fi
grep -q "did not restore index_discipline_asserted" "${scratch}/unrepaired.err"

echo "PASS refactor-proof frozen treatments + matched task + drift/unrepaired controls"
