#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# One entrypoint, three subjects, no filename list in any of them. Every
# denominator below is counted on the run, so a new lane schema or a new planted
# control moves the printed numbers without this file changing.
#
#   selftest          replays every POL contract from references/ against itself
#   compiler selftest replays the composition compiler against itself: byte
#                     stability, the six output contracts, every K-code
#   evidence plane    replays the whole stack against one honest composition and
#                     nineteen single-edit false promotions, and reopens the
#                     first green
#
# The compiler selftest is invoked here rather than left to whoever remembers:
# a --selftest nothing runs is a validation surface that exists and does not
# decide anything.
python3 "$ROOT/tests/selftest.py"
python3 "$ROOT/scripts/compile_pol_composition.py" --selftest
python3 "$ROOT/tests/evidence_plane.py"
