#!/usr/bin/env bash
# Runner for the frozen refactor A/B and its matched hermetic task.
#
# The entrypoint owns every assertion, including its own planted controls, so
# this file stays a single invocation: a wrapper that re-states assertions is a
# second place for them to drift.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "${test_dir}/refactor_ab.py"

echo "PASS refactor proof: frozen treatments, matched hermetic task, planted controls"
