#!/usr/bin/env bash
# Bounded exact-HEAD local verification for the private CI publication gate.
#
# `ci_publish.py verify` runs this once, at a clean HEAD, and records a receipt
# naming this argv and that commit. The receipt is what lets a publication be
# admitted without spending a CI job to discover the same failures.
#
# Two constraints shape what may go in here:
#
#   1. It must leave the worktree byte-identical. `verify` checks cleanliness
#      before and after, and a check that writes a file would fail the run it
#      was meant to certify. PYTHONDONTWRITEBYTECODE keeps __pycache__ out.
#   2. It must be the checks that would otherwise be discovered in CI. A
#      verification narrower than the workflow turns the receipt into a claim
#      the workflow does not support.
#
# Exits non-zero on the first failure, so the receipt is never written for a
# HEAD that did not pass.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

step() { printf '\n=== %s ===\n' "$1"; }

step "eval coverage, mutation lineage, and release contracts"
python3 scripts/check_skill_evals.py
python3 scripts/check_mutation_lineage.py
python3 scripts/check_mutation_targets.py
python3 scripts/check_mutation_promotions.py
python3 scripts/check_capability_unlocks.py
python3 scripts/check_release_receipts.py
python3 scripts/render_scorecard_index.py --check

step "assertion quality and suite arrival"
python3 scripts/check_dead_assertions.py
python3 scripts/check_suite_ci_coverage.py

step "intent-bound constraint closure"
python3 scripts/check_intent_bound_constraints.py \
  contract evals/fixtures/intent-bound-constraint/valid-contract.json
python3 scripts/check_intent_bound_constraints.py \
  receipt evals/fixtures/intent-bound-constraint/valid-receipt.json \
  --contract evals/fixtures/intent-bound-constraint/valid-contract.json

step "intent promotion lifecycle and external authority"
python3 scripts/check_intent_promotions.py selftest
python3 scripts/check_intent_promotion_authority.py --selftest

step "controlled-language contract foundation"
python3 scripts/check_controlled_language_contracts.py bundle \
  --request evals/fixtures/controlled-language/valid-request.json \
  --standard-pack evals/fixtures/controlled-language/valid-standard-pack.json \
  --termbase \
    evals/fixtures/controlled-language/valid-termbase-tn.json \
    evals/fixtures/controlled-language/valid-termbase-tv.json \
  --violation evals/fixtures/controlled-language/valid-violation.json \
  --receipt evals/fixtures/controlled-language/valid-receipt.json

step "executor authority bounds"
python3 scripts/check_executor_authority.py --repo-root .
python3 scripts/check_executor_authority.py --repo-root . --selftest

step "delivery shape comparison controls"
python3 scripts/measure_delivery_shape.py selftest

step "adapter receipt integrity"
python3 skills/repo-agent-native/scripts/check_adapter_receipts.py selftest
python3 skills/repo-agent-native/scripts/check_adapter_receipts.py check

step "prompt baseline record integrity"
python3 skills/dual-forge-repository-loop/scripts/check_prompt_baseline.py selftest
python3 skills/dual-forge-repository-loop/scripts/check_prompt_baseline.py check
python3 skills/dual-forge-repository-loop/scripts/check_prompt_crossstack.py selftest
python3 skills/dual-forge-repository-loop/scripts/check_prompt_crossstack.py check

step "guard controls"
python3 skills/shared-skills-infra/scripts/check_index.py --selftest
python3 skills/shared-skills-infra/scripts/check_index_coverage.py --selftest
python3 skills/shared-skills-infra/scripts/check_index_coverage.py
python3 scripts/check_binding_stale.py --selftest
# Exit 3 is SURFACE, not failure: the body moved and some host has not caught
# up. Collapsing it into failure would make routine drift indistinguishable from
# a malformed contract, and whoever sees it would learn to ignore both.
set +e
python3 scripts/check_binding_stale.py
binding_code=$?
set -e
if [ "${binding_code}" -ne 0 ] && [ "${binding_code}" -ne 3 ]; then
  echo "FAIL check_binding_stale.py exited ${binding_code}" >&2
  exit 1
fi
python3 scripts/check_body_neutrality.py --selftest
python3 scripts/check_body_neutrality.py
python3 scripts/check_ci_publication_profile.py --selftest
python3 scripts/check_ci_publication_profile.py
python3 scripts/skill_eval_plane_selftest.py
python3 scripts/check_skill_eval_plane.py
python3 scripts/check_guard_controls.py --repo-root . --selftest
python3 scripts/check_guard_controls.py --repo-root .

step "commit role classification"
python3 scripts/check_commit_roles.py --repo-root .

step "migration tooling selftests"
# These live outside skills/, so check_suite_ci_coverage.py does not see them
# and no workflow named them. A selftest with no arrival is the #122 shape.
for tool in migration/*.py; do
  printf -- '--- %s\n' "${tool}"
  python3 "${tool}" --selftest
done

step "repository test suites"
for suite in skills/*/tests/run-all.sh; do
  printf -- '--- %s\n' "${suite}"
  bash "${suite}"
done

step "repository unit tests"
# Per file rather than `discover`: tests/ is deliberately not a package, and
# discover refuses a non-importable start directory.
for suite in tests/test_*.py; do
  printf -- '--- %s\n' "${suite}"
  python3 -m unittest "${suite}" 2>&1 | tail -3
done

printf '\nLOCAL VERIFICATION GREEN at %s\n' "$(git rev-parse HEAD)"
