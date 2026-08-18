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

# The refactor proof. Named explicitly rather than discovered: these are the
# entrypoints the golden-proof registry pins, and a discovery rule that stops
# matching them would drop the proof without failing.
for proof in refactor_ab.py real_task_ab.py; do
  echo "RUN ${proof}"
  total=$((total + 1))
  if python3 "${tests_dir}/${proof}" > /dev/null; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
done

echo "TOTAL=${total} FAILED=${failed}"
[ "${failed}" -eq 0 ]
