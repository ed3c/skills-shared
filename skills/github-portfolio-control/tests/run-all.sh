#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# One entrypoint, three arrivals, no numbers of its own. The suite counts every
# denominator from the bytes at run time, so a fifth schema or a tenth refusal
# code changes the printed line without changing this file.

# 1. The contracts, executed as deciding gates: every positive validates, every
#    refusal control is refused, every control discriminates under knockout of
#    its own named keyword, every schema is routed from all three documents,
#    and a planted defect on a throwaway copy is required to turn it red.
python3 "$ROOT/tests/selftest.py"

# 2. The checker's own gate: the nine cross-document refusal codes each fired on
#    a planted defect, the derived bundle still equals the committed fixture,
#    and no import in it names a network module.
python3 "$ROOT/scripts/compile_portfolio_control.py" --selftest

# 3. The checker run as a caller would run it, against the committed bundle.
#    A compiler whose output moves has no --check worth running, and a --check
#    nobody runs proves the same green as one that passes.
python3 "$ROOT/scripts/compile_portfolio_control.py" \
  --bundle "$ROOT/references/fixtures/example-bundle.json" \
  --check "$ROOT/references/fixtures/example-bundle.verdict.json"
