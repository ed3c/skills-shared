#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

python3 -m unittest discover \
  -s skills/universal-refactor-controller/tests \
  -p 'test_*.py' \
  -v

python3 -m py_compile \
  skills/universal-refactor-controller/scripts/assert_controller_gate.py \
  skills/universal-refactor-controller/tests/test_assert_controller_gate.py \
  skills/universal-refactor-controller/tests/test_golden_refactor_corpus.py
