#!/usr/bin/env bash
set -euo pipefail
module_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m py_compile "${module_root}/cadg_pr_admission.py" "${module_root}/tests/test_pr_admission.py"
python3 -m unittest "${module_root}/tests/test_pr_admission.py" -v
