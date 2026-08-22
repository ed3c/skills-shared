#!/usr/bin/env bash
# Discovered by scripts/local_verification.sh. Every nested verifier is mandatory.
set -uo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
total=0
failed=0
while IFS= read -r verifier; do
  echo "RUN ${verifier#"${tests_dir}"/}"
  total=$((total + 1))
  if bash "${verifier}"; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
done < <(find "${tests_dir}" -mindepth 2 -name verify.sh -type f | sort)

echo "TOTAL=${total} FAILED=${failed}"
test "${total}" -gt 0
test "${failed}" -eq 0
