#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
references="$(cd "$test_dir/../../references/dual-agent-offload" && pwd)"

# Shape first: a semantic gate that cannot parse its own inputs is not a gate.
for document in "$references"/*.json; do
  python3 -m json.tool "$document" >/dev/null
done

python3 "$test_dir/verify.py"
