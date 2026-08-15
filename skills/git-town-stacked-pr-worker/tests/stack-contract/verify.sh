#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"

python3 "${repo_root}/scripts/check_intent_bound_constraints.py" \
  contract "${test_dir}/fixtures/intent-contract.json"
python3 "${skill_dir}/scripts/check_stack_contract.py" \
  "${test_dir}/fixtures/valid-stack.json"
# Run the file, not `-m unittest <path>`: unittest resolves its arguments as
# dotted module names, so an absolute path became an empty module name and this
# line raised ValueError on every Python it was ever run under. The module has
# its own unittest.main() entry point.
python3 "${test_dir}/test_stack_contract.py" -v
python3 -m py_compile \
  "${skill_dir}/scripts/check_stack_contract.py" \
  "${test_dir}/test_stack_contract.py"
python3 -m json.tool "${skill_dir}/references/STACK_CONTRACT.schema.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/valid-stack.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/intent-contract.json" >/dev/null

echo "PASS Git Town Intent-Bound Stack contract"
