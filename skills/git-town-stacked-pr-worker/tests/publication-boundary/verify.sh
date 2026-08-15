#!/usr/bin/env bash
# Zero-network positive and mutation controls for Git Town / GitHub Actions publication policy.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_publication_boundary.py"

python3 "${checker}" --root "${skill_dir}"
python3 "${checker}" --root "${skill_dir}" --selftest
python3 -m py_compile "${checker}"
python3 -m json.tool "${skill_dir}/evals.json" >/dev/null

echo "PASS Git Town publication-boundary Harness"
