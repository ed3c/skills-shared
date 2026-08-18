#!/usr/bin/env bash
# Zero-network controls for this repository's checked-in Git Town profile.
#
# The defect these guard against is silent: Git Town ignores an unrecognised
# key, so a misspelling produces a file that parses cleanly and has no effect.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"
checker="${skill_dir}/scripts/check_repository_profile.py"

python3 "${checker}" --repo-root "${repo_root}"
python3 "${checker}" --repo-root "${repo_root}" --selftest
python3 -m py_compile "${checker}"

# The committed profile must be readable by a plain TOML parser, not only by
# this checker's expectations.
python3 -c "
import tomllib, sys
with open('${repo_root}/.git-town.toml', 'rb') as handle:
    body = tomllib.load(handle)
assert body['branches']['main'] == 'main', body['branches']
assert body['sync']['auto-resolve'] is False, body['sync']
assert body['sync']['push-branches'] is False, body['sync']
assert body['sync']['tags'] is False, body['sync']
"

# A checker error is not a policy failure: an absent repository root exits 64.
work="$(mktemp -d "${TMPDIR:-/tmp}/work.XXXXXXXX")"
set +e
python3 "${checker}" --repo-root "${work}" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent repository root exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS Git Town repository profile"
