#!/usr/bin/env bash
# Controls for the integrated A/B canary. The subject under test is the
# experiment's validity, not only its arithmetic: an unfair comparison produces
# the same shape of numbers as a fair one and reads better.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
scorer="${skill_dir}/scripts/score_ab.py"

python3 "${scorer}" --selftest
python3 -m py_compile "${scorer}"
python3 -m json.tool "${test_dir}/fixtures/good-run.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/unfair-run.json" >/dev/null

python3 "${scorer}" --bundle "${test_dir}/fixtures/good-run.json" >/dev/null

# The unfair bundle must be refused, and must emit no metric: a number computed
# from an invalid experiment reads as evidence.
set +e
unfair_output="$(python3 "${scorer}" --bundle "${test_dir}/fixtures/unfair-run.json" 2>&1)"
unfair_code=$?
set -e
if [ "${unfair_code}" -ne 2 ]; then
  echo "FAIL: unfair experiment exited ${unfair_code}, expected 2" >&2
  exit 1
fi
if ! grep -Fq "AB EXPERIMENT INVALID" <<<"${unfair_output}"; then
  echo "FAIL: unfair experiment was not named invalid" >&2
  exit 1
fi
if grep -Fq "deterministic_hard_gate_pass_rate" <<<"${unfair_output}"; then
  echo "FAIL: metrics were emitted for an invalid experiment" >&2
  exit 1
fi

# An unreadable bundle stays distinct from an invalid one.
work="$(mktemp -d)"
set +e
python3 "${scorer}" --bundle "${work}/absent.json" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent bundle exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS controlled-language integrated A/B canary"
