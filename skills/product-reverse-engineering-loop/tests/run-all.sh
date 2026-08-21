#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# One entrypoint, one subject. This file used to name six artifacts and three
# compiler stages, and that enumeration is exactly how the three schemas and two
# compilers landed by #370/#371 reached CI through nothing: the suite was green
# because it was still checking the six things it had been told about.
#
# The selftest now derives its subjects from the tree -- every artifact under
# references/, examples/ and tests/fixtures/, reconciled in both directions
# against the schema registry check_prel_contract.py itself carries -- and
# prints every denominator it counted. Adding a schema, an example or a control
# changes the printed numbers without changing this file; adding a schema and no
# artifact turns it red.
python3 "$ROOT/tests/selftest.py"
