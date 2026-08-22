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

# Provider adapter selftests are fixture-deterministic (their live lanes
# self-report NOT_EXERCISED when the provider binary is absent), so routing
# them here gives every adapter the CI arrival its own lease could not add.
python3 "$ROOT/adapters/tree-sitter/selftest.py"
python3 "$ROOT/adapters/sqlite-ledger/selftest.py"
python3 "$ROOT/adapters/scip/selftest.py"
python3 "$ROOT/adapters/buf/selftest.py"
python3 "$ROOT/adapters/semantic-context/selftest.py"

# Same reason as the adapters: the synthesis compilers ship their own gate, and
# a gate nobody runs reports the same green as one that passes. The schemas it
# emits against are already counted by the selftest above; what this adds is
# whether the compiler still produces them.
python3 "$ROOT/synthesis/selftest.py"

# Same reason again for the R1 refactor protocol compiler: it ships its own
# gate, and its state-coverage lane is the only thing in the tree that checks
# every terminal the refactor contracts declare is reachable by compiling a
# committed request rather than by a test constructing one.
python3 "$ROOT/refactor/selftest.py"

# And for the R2 cross-repository Expand & Contract compiler, same contract:
# committed requests, byte-stable projections, every declared state emitted by
# a real compilation, refusals fired from single-field deltas.
python3 "$ROOT/expand-contract/selftest.py"

# The consumer-bootstrap profile gate reconciles the committed thin-binding
# artifact against the tree in both directions; nothing else routes it, so a
# regression in it would otherwise be invisible.
python3 "$ROOT/bootstrap/check_bootstrap_profile.py" --selftest

# The #528 canary receipt is a v0-draft with no frozen schema, so this is the
# only thing standing between it and citing evidence that was never committed.
# It lives beside the receipt on the traceability plane; this suite is the
# DTCR evidence owner and therefore its arrival.
python3 "$ROOT/../../docs/traceability/dual-track-code-review-loop/canary-528/check_paths.py" --selftest
