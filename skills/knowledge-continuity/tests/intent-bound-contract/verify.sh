#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"

python3 "${repo_root}/scripts/check_intent_bound_constraints.py" \
  contract "${test_dir}/intent-contract.json"
python3 -m json.tool "${test_dir}/intent-contract.json" >/dev/null

echo "PASS knowledge-continuity Intent-Bound registration"
