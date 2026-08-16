#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 scripts/check_skill_core_boundaries.py --selftest
