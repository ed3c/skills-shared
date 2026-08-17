#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
checker="${repo_root}/skills/dual-forge-repository-loop/scripts/check_local_handoff.py"
manifest="${repo_root}/skills/dual-forge-repository-loop/tests/local-handoff/fixtures/repository-native.json"

python3 "${checker}" --selftest
python3 "${checker}" --repo-root "${repo_root}" "${manifest}"

# A required ZIP must turn the gate red even if its digest shape and tracked flag
# look plausible. Generate only the manifest mutation in tmp; no archive bytes are
# needed for this negative control.
tmp="$(mktemp "${TMPDIR:-/tmp}/tmp.XXXXXXXX")"
trap 'rm -f "${tmp}"' EXIT
python3 - "${manifest}" "${tmp}" <<'PY'
import json, sys
src, dst = sys.argv[1:]
doc = json.load(open(src, encoding="utf-8"))
doc["required_inputs"].append({
    "path": "repository-multi-agent-runtime-v2.1-runtime-validation.zip",
    "git_tracked": True,
    "sha256": "0" * 64,
})
json.dump(doc, open(dst, "w", encoding="utf-8"), indent=2)
PY

set +e
python3 "${checker}" --repo-root "${repo_root}" "${tmp}" >/dev/null
code=$?
set -e
if [ "${code}" -ne 2 ]; then
  echo "FAIL: required ZIP mutation was not refused with exit 2 (got ${code})" >&2
  exit 1
fi

echo "PASS local handoff is repository-native and ZIP-independent"
