#!/usr/bin/env bash
# This skill's routing selftest, reachable from the runner rather than only from
# memory. It already existed and already asserts across 19 balanced cases; what
# was missing was anything that ran it without someone deciding to. A selftest
# nobody reaches reports nothing, and reports it in the same green as one that
# runs. Zero network.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
route="${skill_dir}/scripts/route.ts"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

python3 "${skill_dir}/scripts/agent_docs.py" selftest > /dev/null
echo "  agent_docs: red on drift, absence, surprise, unruled, truncation, bad --key, staged drift"

if ! command -v bun > /dev/null 2>&1; then
  echo "FAIL bun is required to run ${route##*/}; a selftest that cannot run has not passed" >&2
  exit 70
fi

# 1. the selftest itself, over the committed case corpus.
bun run "${route}" --selftest > "${scratch}/green.out"
grep -q "^SELFTEST GREEN forgejo-delivery-loop" "${scratch}/green.out"

# 2. it must be able to go red, or its green above means nothing. The corpus is
#    the input, so a case whose expected verdict is inverted is the smallest
#    honest defect to plant: the router is untouched and only the claim moves.
cp -R "${skill_dir}/scripts" "${scratch}/scripts"
cp "${skill_dir}/cases.json" "${scratch}/cases.json"
python3 - "${scratch}/cases.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
cases = json.loads(path.read_text(encoding="utf-8"))
cases[0]["should_trigger"] = not cases[0]["should_trigger"]
path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
PY
set +e
bun run "${scratch}/scripts/route.ts" --selftest > "${scratch}/red.out" 2> "${scratch}/red.err"
red_rc=$?
set -e
if [ "${red_rc}" -eq 0 ]; then
  echo "FAIL: an inverted trigger verdict was accepted; the selftest cannot go red" >&2
  exit 1
fi
grep -q "trigger verdict mismatch" "${scratch}/red.out" "${scratch}/red.err"

# 3. the corpus balance rule is itself a guard: shrinking one arm must be
#    refused, or "at least five per arm" is prose rather than a check.
cp "${skill_dir}/cases.json" "${scratch}/cases.json"
python3 - "${scratch}/cases.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
cases = json.loads(path.read_text(encoding="utf-8"))
keep = [c for c in cases if not c["should_trigger"]]
keep += [c for c in cases if c["should_trigger"]][:1]
path.write_text(json.dumps(keep, indent=2) + "\n", encoding="utf-8")
PY
set +e
bun run "${scratch}/scripts/route.ts" --selftest > "${scratch}/thin.out" 2> "${scratch}/thin.err"
thin_rc=$?
set -e
if [ "${thin_rc}" -eq 0 ]; then
  echo "FAIL: a corpus with one trigger case was accepted" >&2
  exit 1
fi
grep -q "five cases per trigger/polarity arm" "${scratch}/thin.out" "${scratch}/thin.err"

echo "PASS forgejo routing selftest, reachable and able to go red"
