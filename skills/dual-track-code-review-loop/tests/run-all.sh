#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# One entrypoint, one subject. The selftest replays the whole C0 contract from
# references/ and counts every denominator on the run, so there is nothing here
# to keep in step with it: adding a schema or a control changes the printed
# numbers without changing this file.
#
# DTCR_REFERENCES overrides the subject for a planted-defect run. It is
# deliberately not set here, so a normal invocation always reads the tree.
python3 "$ROOT/tests/selftest.py"
