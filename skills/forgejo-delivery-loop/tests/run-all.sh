#!/usr/bin/env bash
set -uo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${tests_dir}/..")"
total=0
failed=0

echo "RUN route selftest"
total=$((total + 1))
if (cd "${skill_dir}" && bun scripts/route.ts --selftest); then echo PASS; else echo FAIL; failed=$((failed + 1)); fi

while IFS= read -r script; do
  echo "RUN ${script#"${tests_dir}/"}"
  total=$((total + 1))
  if bash "${script}"; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
done < <(find "${tests_dir}" -name verify.sh | sort)

echo "TOTAL=${total} FAILED=${failed}"
[ "${failed}" -eq 0 ]
