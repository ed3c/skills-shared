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
seen=""
while IFS= read -r verifier; do
  echo "RUN ${verifier#"${tests_dir}"/}"
  total=$((total + 1))
  seen="${seen} $(basename "${verifier}")"
  if python3 "${verifier}"; then echo PASS; else echo FAIL; failed=$((failed + 1)); fi
done < <(find "${tests_dir}" -maxdepth 1 -name 'verify*.py' -type f | sort)

# The golden-proof entrypoint must be discovered here, not merely exist.
# skills/skill-refactor-proof-loop/references/golden-proof-registry.json names
# this file as the runner that executes verify_refactor_ab.py; a rename or a
# move out of the discovered set would leave the registry pointing at a file
# nothing runs, which is the hollow route the registry exists to refuse.
case "${seen} " in
  *" verify_refactor_ab.py "*) ;;
  *) echo "MISSING verify_refactor_ab.py: the registered golden-proof entrypoint was not discovered"
     failed=$((failed + 1)) ;;
esac
echo "TOTAL=${total} FAILED=${failed}"
test "${total}" -gt 0
test "${failed}" -eq 0
