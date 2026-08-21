#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m json.tool "$ROOT/references/hosting-assurance.schema.json" >/dev/null
python3 -m json.tool "$ROOT/tests/fixtures/good.json" >/dev/null
python3 "$ROOT/tests/test_checker.py"
python3 -m py_compile "$ROOT/scripts/check_hosting_assurance.py" "$ROOT/tests/test_checker.py"
echo "PASS git-hosting-scale-assurance"
