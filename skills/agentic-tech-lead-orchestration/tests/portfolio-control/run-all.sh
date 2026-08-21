#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(cd "$HERE/../.." && pwd)"
python3 -m py_compile \
  "$SKILL/scripts/check_repository_portfolio_prompt_pack.py" \
  "$HERE/selftest.py"
python3 "$SKILL/scripts/check_repository_portfolio_prompt_pack.py"
python3 "$HERE/selftest.py"
printf 'PORTFOLIO PROMPT FOUNDATION GREEN\n'
