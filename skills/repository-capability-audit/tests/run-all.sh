#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The generated run tree is the only copy of the deterministic observations, the
# core checker verdict and the nested runtime packet. Deleting it on exit is
# right for a laptop and wrong for CI: #222 asks for a replayable artifact, and
# nothing can be uploaded from a directory this script already removed. Naming
# RCA_EVIDENCE_DIR keeps it; leaving it unset keeps the old throwaway behaviour.
OUT="${RCA_EVIDENCE_DIR:-}"
if [ -n "$OUT" ]; then
  mkdir -p "$OUT"
else
  OUT="$(mktemp -d "${TMPDIR:-/tmp}/out.XXXXXXXX")"
  trap 'rm -rf "$OUT"' EXIT
fi

python3 "$HERE/scripts/run_ablation.py" --output "$OUT/run" > "$OUT/report.stdout"
python3 "$HERE/scripts/check_core.py" --report "$OUT/run/effectiveness.json" \
  | tee "$OUT/check-core.stdout"
python3 "$HERE/scripts/publish_source_contribution.py" --skill-root "$HERE" --check \
  | tee "$OUT/source-contribution.stdout"
python3 -m unittest discover -s "$HERE/tests" -p 'test_*.py' -v 2>&1 \
  | tee "$OUT/unittest.stdout"

# The matched hermetic A/B over the three frozen bodies (#351). Its own subject
# is built and torn down inside a TemporaryDirectory, so only the report lands
# here; discover(-p 'test_*.py') cannot see it, which is why it is named.
python3 "$HERE/tests/refactor_proof_ab.py" --output "$OUT/refactor-proof-ab.json" \
  | tee "$OUT/refactor-proof-ab.stdout"

diff -u "$HERE/evals/expected/effectiveness.json" "$OUT/run/effectiveness.json"

test "$(find "$OUT/run/observations" -type f -name '*.json' | wc -l | tr -d ' ')" = "15"
test -s "$OUT/run/runtime/hidden-artifact-omission/packet.zip"

echo "REPOSITORY CAPABILITY AUDIT GREEN"
