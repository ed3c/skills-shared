#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
checker="$test_dir/../../scripts/check_decision_html.py"

python3 "$checker" --selftest
python3 "$checker" "$test_dir/fixtures/good/report.html"

if python3 "$checker" "$test_dir/fixtures/hollow/report.html"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi

# Isolating negative control for `selfhost`: identical to the good fixture except
# for one protocol-relative external script. Only selfhost may fail, otherwise the
# aggregate hollow fixture would mask a broken EXTERNAL_RES pattern.
selfhost_out="$(python3 "$checker" "$test_dir/fixtures/hollow-selfhost/report.html" || true)"
echo "$selfhost_out"
if ! grep -q '\[FAIL\] selfhost' <<<"$selfhost_out"; then
  echo "protocol-relative external resource was not detected by selfhost" >&2
  exit 1
fi
if grep -q '\[FAIL\] \(declare\|snapshot\|quiz\|title\)' <<<"$selfhost_out"; then
  echo "selfhost fixture failed an unrelated invariant; control is not isolating" >&2
  exit 1
fi
