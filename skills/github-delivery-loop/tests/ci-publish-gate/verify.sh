#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
gate="${skill_dir}/scripts/ci_publish_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$gate" evaluate --snapshot "$test_dir/fixtures/allow-ready.json" \
  > "$scratch/allow.out"
grep -Fx 'ALLOW ready-for-review' "$scratch/allow.out"

if python3 "$gate" evaluate --snapshot "$test_dir/fixtures/block-checkpoint.json" \
  > "$scratch/checkpoint.out" 2> "$scratch/checkpoint.err"; then
  echo "FAIL: draft checkpoint push was admitted" >&2
  exit 1
fi
grep -Fx 'BLOCK unsupported-intent:checkpoint' "$scratch/checkpoint.err"

if python3 "$gate" evaluate --snapshot "$test_dir/fixtures/block-billing.json" \
  > "$scratch/billing.out" 2> "$scratch/billing.err"; then
  echo "FAIL: unresolved billing circuit breaker was admitted" >&2
  exit 1
fi
grep -Fx 'BLOCK billing-circuit-open' "$scratch/billing.err"

python3 -m unittest "$test_dir/test_gate.py" -v

echo 'PASS[ci-publish-gate]: positive path allowed; checkpoint and billing hollows blocked'
