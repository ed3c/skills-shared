#!/usr/bin/env bash
# Positive and negative controls for the Tech Lead fan-out contract.
#
# Every negative fixture is derived from a checked-in valid one by exactly one
# mutation, so a control that goes red names a single broken law rather than a
# fixture that was malformed to begin with. Each expectation asserts the refusal
# code, not just a non-zero exit: a checker that refused everything for the wrong
# reason would otherwise pass this suite.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_fanout_contract.py"
fixtures="${test_dir}/fixtures"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

python3 -m py_compile "${checker}"
python3 -m json.tool "${skill_dir}/references/FAN_OUT_CONTRACT.schema.json" >/dev/null

# --- positive controls ------------------------------------------------------
for fixture in valid-tournament valid-cooperative valid-serial-stack; do
  python3 -m json.tool "${fixtures}/${fixture}.json" >/dev/null
  python3 "${checker}" "${fixtures}/${fixture}.json" >/dev/null
  echo "PASS ${fixture}"
done

# --- negative controls ------------------------------------------------------
# mutate <source> <output> <python expression over `plan`>
mutate() {
  python3 - "${fixtures}/$1.json" "${tmp}/$2.json" "$3" <<'PY'
import json, sys
plan = json.loads(open(sys.argv[1], encoding="utf-8").read())
exec(sys.argv[3], {"plan": plan})
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(plan, indent=2) + "\n")
PY
}

expect_refusal() {
  local fixture="$1" code="$2"
  set +e
  python3 "${checker}" "${tmp}/${fixture}.json" >"${tmp}/out" 2>"${tmp}/err"
  local status=$?
  set -e
  if [ "${status}" -ne 2 ]; then
    echo "CONTROL FAILED ${fixture}: expected exit 2, got ${status}" >&2
    cat "${tmp}/err" >&2
    exit 1
  fi
  if ! grep -q "FAN-OUT REFUSED ${code}" "${tmp}/err"; then
    echo "CONTROL FAILED ${fixture}: expected ${code}, got:" >&2
    cat "${tmp}/err" >&2
    exit 1
  fi
  echo "REFUSED ${code} (${fixture})"
}

mutate valid-cooperative path-overlap \
  "plan['workers'][1]['writable_paths'] = ['src/storage/cache.py']"
expect_refusal path-overlap PATH_OVERLAP

mutate valid-tournament mutable-base \
  "plan['base']['immutable'] = False"
expect_refusal mutable-base MUTABLE_BASE

mutate valid-tournament unequal-context \
  "plan['workers'][1]['context_digest'] = 'a' * 64"
expect_refusal unequal-context CONTEXT_DIGEST_MISMATCH

mutate valid-tournament acceptance-writable \
  "plan['workers'][0]['writable_paths'].append('tests/acceptance/verify.sh')"
expect_refusal acceptance-writable ACCEPTANCE_TEST_MUTATED

mutate valid-serial-stack undeclared-dependency \
  "plan['workers'][1].pop('consumes_contracts'); plan['workers'][1].pop('consumes_paths')"
expect_refusal undeclared-dependency UNDECLARED_DEPENDENCY

mutate valid-tournament budget-overflow \
  "plan['budgets']['max_workers'] = 2"
expect_refusal budget-overflow WORKER_BUDGET_OVERFLOW

mutate valid-tournament missing-focus \
  "plan['workers'][2].pop('focus')"
expect_refusal missing-focus MISSING_BRANCH_FOCUS

mutate valid-tournament repeated-focus \
  "plan['workers'][2]['focus'] = plan['workers'][0]['focus']"
expect_refusal repeated-focus MISSING_BRANCH_FOCUS

mutate valid-cooperative premature-convergence \
  "plan['workers'][2]['depends_on'] = ['C-storage']"
expect_refusal premature-convergence PREMATURE_CONVERGENCE

mutate valid-tournament automatic-semantic \
  "plan['semantic_conflict_resolution'] = 'automatic'"
expect_refusal automatic-semantic AUTOMATIC_SEMANTIC_RESOLUTION

mutate valid-tournament automatic-winner \
  "plan['ranking']['winner_admission'] = 'automatic'"
expect_refusal automatic-winner AUTOMATIC_SEMANTIC_RESOLUTION

mutate valid-tournament qualitative-first \
  "plan['ranking']['qualitative_review_after_hard_gates'] = False"
expect_refusal qualitative-first QUALITATIVE_BEFORE_HARD_GATE

mutate valid-tournament cherry-pick \
  "plan['ranking']['cross_competitor_cherry_pick'] = True"
expect_refusal cherry-pick CHERRY_PICK_ACROSS_COMPETITORS

mutate valid-cooperative two-convergence-owners \
  "plan['workers'][1]['role'] = 'convergence'"
expect_refusal two-convergence-owners CONVERGENCE_OWNER_AMBIGUOUS

mutate valid-tournament code-graph-rag \
  "plan['context_bundle']['providers'].append({'name': 'code-graph-rag', 'role': 'semantic-fact', 'required_provider': True, 'state': 'PASS'})"
expect_refusal code-graph-rag FORBIDDEN_CONTEXT_PROVIDER

mutate valid-tournament funnel-laundered \
  "plan['context_bundle']['compiler_truth_funnel'] = {'state': 'PASS'}"
expect_refusal funnel-laundered CONTEXT_FUNNEL_STATE_LAUNDERED

mutate valid-cooperative sibling-consumes-sibling \
  "plan['workers'][1]['depends_on'] = ['C-storage']"
expect_refusal sibling-consumes-sibling UNDECLARED_DEPENDENCY

# A retired provider is allowed to remain as a non-required historical note.
# Without this control the FORBIDDEN_CONTEXT_PROVIDER rule could have been a
# blanket name ban and every test above would still be green.
mutate valid-tournament code-graph-rag-historical \
  "plan['context_bundle']['providers'].append({'name': 'code-graph-rag', 'role': 'projection', 'required_provider': False, 'state': 'ABSENT'})"
python3 "${checker}" "${tmp}/code-graph-rag-historical.json" >/dev/null
echo "PASS code-graph-rag-historical (non-required residue is not a dependency)"

echo "PASS Tech Lead fan-out contract"
