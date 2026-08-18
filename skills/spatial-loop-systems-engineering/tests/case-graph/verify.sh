#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${here}/../../scripts/check_case_graph.py" check "${here}/fixtures/good.json"
python3 "${here}/verify.py"
