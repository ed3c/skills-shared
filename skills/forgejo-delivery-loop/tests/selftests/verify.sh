#!/usr/bin/env bash
# This skill's two selftests, reachable from the runner rather than only from
# memory. Both already existed and both already plant defects and assert red;
# what was missing was anything that ran them without someone deciding to.
# Zero network.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"

python3 "${skill_dir}/scripts/agent_docs.py" selftest > /dev/null
echo "  agent_docs: red on drift, absence, surprise, unruled, truncation, bad --key, staged drift"

if command -v bun > /dev/null 2>&1; then
  bun run "${skill_dir}/scripts/route.ts" --selftest > /dev/null
  echo "  route: cases.json trigger/polarity arms hold"
else
  # Named, not skipped quietly: a machine without bun leaves the router
  # unverified, which must not read the same as a router that passed.
  echo "  route: SKIPPED -- bun is not on this machine, the router was NOT verified" >&2
fi

echo "PASS selftests"
