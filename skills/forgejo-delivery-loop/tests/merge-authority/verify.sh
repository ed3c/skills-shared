#!/usr/bin/env bash
# Exhaustive control for the one invariant cases.json can only spot-check:
# no reachable input routes merge to a mutation. cases.json pins the single
# admitted case; this sweeps every request_state, auth_state, loop_size and
# operator-readiness combination, so re-widening merge cannot be hidden by
# editing one expectation.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"

bun "${test_dir}/sweep.ts" "${skill_dir}"

echo "PASS forgejo merge authority sweep"
