#!/usr/bin/env bash
# Zero-network controls for the deterministic lane: tokenization rules, sentence
# splitting, exact source-span digests, and word budgets.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
linter="${skill_dir}/scripts/lint_deterministic.py"

python3 "${linter}" --selftest
python3 -m py_compile "${linter}"

# The CLI contract, not only the library: a caller acts on the exit code, so the
# exit code is asserted here rather than assumed from the selftest.
work="$(mktemp -d "${TMPDIR:-/tmp}/work.XXXXXXXX")"
subject="${work}/subject.txt"
printf 'Open the valve and then close the valve and then wait for pressure.\n' > "${subject}"

if python3 "${linter}" --text "${subject}" --word-budget 5 >/dev/null 2>&1; then
  echo "FAIL: over-budget document did not exit non-zero" >&2
  exit 1
fi

python3 "${linter}" --text "${subject}" --word-budget 99 >/dev/null

# An absent subject is a checker error (64), not a document failure (2). If
# those collapsed, a broken invocation would read as a failing document.
set +e
python3 "${linter}" --text "${work}/absent.txt" --word-budget 99 >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent subject exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS controlled-language deterministic linter"
