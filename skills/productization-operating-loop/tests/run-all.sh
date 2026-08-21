#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# One entrypoint, one subject. The selftest replays every POL contract from
# references/ and counts every denominator on the run, so a new lane schema
# joins the run without this file changing.
python3 "$ROOT/tests/selftest.py"
