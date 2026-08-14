#!/usr/bin/env bash
# Controls for binding an A/B comparison to external authority bytes.
#
# The A/B scorer reads its evaluator identity from a field the caller wrote, so
# a comparison can be perfectly fair between arms and still be measured by an
# evaluator that never ran. This composition refuses that.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"
wrapper="${skill_dir}/scripts/score_ab_authority.py"

python3 "${wrapper}" --repo-root "${repo_root}" --selftest
python3 -m py_compile "${wrapper}" "${skill_dir}/scripts/ab_authority_selftest.py"

# An absent manifest is unusable input (64), not a refused composition (2).
work="$(mktemp -d)"
set +e
python3 "${wrapper}" --repo-root "${repo_root}" --manifest "${work}/absent.json" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent manifest exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS controlled-language authority-bound A/B"
