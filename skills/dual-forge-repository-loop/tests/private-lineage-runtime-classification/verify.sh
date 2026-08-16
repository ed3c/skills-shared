#!/usr/bin/env bash
set -euo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${tests_dir}/../.." && pwd)"
checker="${skill_root}/modes/forgejo-private-repository-loop/scripts/check_runtime_evidence_classification.py"

python3 "${checker}" --selftest
