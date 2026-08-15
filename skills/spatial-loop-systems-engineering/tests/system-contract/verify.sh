#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${test_dir}/../.." && pwd)"
checker="${skill_root}/scripts/check_system_contract.py"
good="${test_dir}/fixtures/good.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

green_output="$(python3 "${checker}" check "${good}")"
grep -Fq "CONTRACT GREEN: subject=bounded-worker-prototype gate=READY_FOR_PROTOTYPE" \
  <<<"${green_output}"

python3 - "${good}" "${tmp}" <<'PY'
import copy
import json
import sys
from pathlib import Path

source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
target = Path(sys.argv[2])

def emit(name, mutate):
    document = copy.deepcopy(source)
    mutate(document)
    (target / name).write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

emit("no-oracle.json", lambda d: d["invariants"][0].pop("oracle"))
emit("no-teardown.json", lambda d: d.__setitem__("teardown", []))
emit(
    "ready-without-runtime.json",
    lambda d: d["implementation_gate"].update(
        {
            "status": "READY_FOR_IMPLEMENTATION",
            "claim_level": "IMPLEMENTATION_CANDIDATE",
            "blocking_unknowns": [],
        }
    ),
)
emit(
    "vague-performance.json",
    lambda d: d["objective"].update(
        {"statement": d["objective"]["statement"] + " It must be low-latency."}
    ),
)
emit(
    "pass-without-evidence.json",
    lambda d: d["capabilities"][0].update({"state": "PASS", "evidence": []}),
)
emit(
    "dangling-state.json",
    lambda d: d["states"]["transitions"][0].update({"to": "MISSING_STATE"}),
)
emit(
    "dangling-teardown-transition.json",
    lambda d: d["teardown"][0].update({"release_transition": "T-MISSING"}),
)
PY

expect_red() {
  local name="$1"
  local file="$2"
  local reason="$3"
  local output
  local code

  set +e
  output="$(python3 "${checker}" check "${file}" 2>&1)"
  code=$?
  set -e

  if [[ "${code}" -ne 2 ]]; then
    echo "${name}: expected exit 2, got ${code}" >&2
    echo "${output}" >&2
    return 1
  fi
  if ! grep -Fq "${reason}" <<<"${output}"; then
    echo "${name}: missing expected reason: ${reason}" >&2
    echo "${output}" >&2
    return 1
  fi
}

expect_red \
  "invariant oracle" \
  "${tmp}/no-oracle.json" \
  "invariants[0].oracle: must be an object"

expect_red \
  "teardown symmetry" \
  "${tmp}/no-teardown.json" \
  "teardown: must be a non-empty array"

expect_red \
  "required capability gate" \
  "${tmp}/ready-without-runtime.json" \
  "required capability C-CGROUP is NOT_EXERCISED, not PASS"

expect_red \
  "performance closure" \
  "${tmp}/vague-performance.json" \
  "performance claim requires at least one performance_budgets entry"

expect_red \
  "evidence binding" \
  "${tmp}/pass-without-evidence.json" \
  "capabilities[0].evidence: PASS requires evidence"

expect_red \
  "state reference" \
  "${tmp}/dangling-state.json" \
  "references unknown state MISSING_STATE"

expect_red \
  "teardown transition reference" \
  "${tmp}/dangling-teardown-transition.json" \
  "references unknown transition T-MISSING"

set +e
missing_output="$(python3 "${checker}" check "${tmp}/absent.json" 2>&1)"
missing_code=$?
set -e

[[ "${missing_code}" -eq 64 ]]
grep -Fq "CONTRACT INPUT ERROR: file not found" <<<"${missing_output}"

printf 'SELFTEST GREEN: positive contract admitted; 7 planted defects refused; absent input stayed distinct\n'
