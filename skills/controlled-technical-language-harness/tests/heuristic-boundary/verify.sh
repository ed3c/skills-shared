#!/usr/bin/env bash
# Zero-network controls for the calibrated-heuristic lane: calibration
# admission, and the composition rules that stop a guess concluding a run.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_heuristic_calibration.py"

python3 "${checker}" --selftest
python3 -m py_compile "${checker}"

echo "PASS controlled-language heuristic boundary"
