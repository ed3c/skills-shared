#!/usr/bin/env bash
# Discovered by scripts/local_verification.sh, which loops skills/*/tests/run-all.sh.
# skills/shared-skills-infra/tests/verify.sh is also invoked directly, by name,
# from .github/workflows/shared-skills-infra.yml -- this file exists so the
# same suite is *also* reachable the way every other skill's suite is,
# and so a new sub-suite dropped under tests/<name>/verify.sh is picked up
# here unconditionally, with no per-suite existence guard to fall out of sync.
set -uo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
total=0
failed=0

run() {
  echo "RUN ${1#"${tests_dir}"/}"
  total=$((total + 1))
  if bash "${1}"; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
}

run "${tests_dir}/verify.sh"
while IFS= read -r verifier; do
  run "${verifier}"
done < <(find "${tests_dir}" -mindepth 2 -name verify.sh -type f | sort)

echo "TOTAL=${total} FAILED=${failed}"
test "${total}" -gt 0
test "${failed}" -eq 0
