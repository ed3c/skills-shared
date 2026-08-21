#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

python3 "$ROOT/tests/portfolio-control/foundation_selftest.py"

# This C0 suite proves portable contracts, deterministic graph/join/CI controls,
# prompt persistence and Codex role packaging. It intentionally does not launch
# Codex, mutate GitHub, exercise private repositories, merge or release.
printf '%s\n' 'REPOSITORY-PORTFOLIO-C0-SUITE PASS evidence_ceiling=DETERMINISTIC_STATIC'
