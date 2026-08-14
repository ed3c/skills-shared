#!/usr/bin/env bash
# Zero-network positive and mutation controls for controlled-language profile
# admission. Proves the pack is admitted, and that each control #118 requires
# still refuses its own defect.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
repo_root="$(realpath "${skill_dir}/../..")"
checker="${skill_dir}/scripts/check_profile_admission.py"

# The pack must satisfy the landed interchange contract before admission is
# even meaningful: a malformed pack could otherwise be refused for the wrong
# reason and read as a working control.
python3 "${repo_root}/scripts/check_controlled_language_contracts.py" \
  standard-pack "${skill_dir}/evals/standard-pack-ste.json"

python3 "${checker}" --root "${skill_dir}"
python3 "${checker}" --root "${skill_dir}" --selftest
python3 -m py_compile "${checker}"
python3 -m json.tool "${skill_dir}/evals/standard-pack-ste.json" >/dev/null
python3 -m json.tool "${skill_dir}/evals/ste-proposal-derived.rules.json" >/dev/null
python3 -m json.tool "${skill_dir}/evals.json" >/dev/null

echo "PASS controlled-language profile admission"
