#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/github_delivery.py"
good="$test_dir/fixtures/good/registry.json"
hollow="$test_dir/fixtures/hollow/registry.json"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$checker" check --registry "$good"

if python3 "$checker" check --registry "$hollow" >"$scratch/hollow.out" 2>"$scratch/hollow.err"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi
grep -q "UNMATERIALIZED portable-loop" "$scratch/hollow.err"
