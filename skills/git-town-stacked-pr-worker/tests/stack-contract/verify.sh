#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"

python3 "${repo_root}/scripts/check_intent_bound_constraints.py" \
  contract "${test_dir}/fixtures/intent-contract.json"
python3 "${skill_dir}/scripts/check_stack_contract.py" \
  "${test_dir}/fixtures/valid-stack.json"
python3 -m unittest "${test_dir}/test_stack_contract.py" -v
python3 -m py_compile \
  "${skill_dir}/scripts/check_stack_contract.py" \
  "${test_dir}/test_stack_contract.py"
python3 -m json.tool "${skill_dir}/references/STACK_CONTRACT.schema.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/valid-stack.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/intent-contract.json" >/dev/null

echo "PASS Git Town Intent-Bound Stack contract"
