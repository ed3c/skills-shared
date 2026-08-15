#!/usr/bin/env bash
# Entry point for this skill's controls.
#
# Without this file the suites below were unreachable: the repository runner
# discovers skills/*/tests/run-all.sh, and the CI matrix builds its jobs from the
# same shape. Four passing verifiers sat here executed by nothing, which reads
# exactly like coverage until someone looks for the job that ran them.
set -uo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
total=0
failed=0
while IFS= read -r verifier; do
  echo "RUN ${verifier#"${tests_dir}"/}"
  total=$((total + 1))
  if python3 "${verifier}"; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
done < <(find "${tests_dir}" -maxdepth 1 -name 'verify*.py' -type f | sort)
echo "TOTAL=${total} FAILED=${failed}"
test "${total}" -gt 0
test "${failed}" -eq 0
