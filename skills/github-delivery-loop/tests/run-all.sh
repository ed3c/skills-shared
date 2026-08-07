#!/usr/bin/env bash
set -euo pipefail

script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
total=0
failed=0

while IFS= read -r verifier; do
  total=$((total + 1))
  echo "RUN ${verifier#"$script_dir"/}"
  if bash "$verifier"; then
    echo "PASS"
  else
    failed=$((failed + 1))
    echo "FAIL"
  fi
done < <(find "$script_dir" -name verify.sh -type f | sort)

echo "TOTAL=$total FAILED=$failed"
test "$failed" -eq 0
