#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

python3 "$HERE/scripts/run_ablation.py" --output "$OUT/run" > "$OUT/report.stdout"
python3 "$HERE/scripts/check_core.py" --report "$OUT/run/effectiveness.json"
python3 -m unittest discover -s "$HERE/tests" -p 'test_*.py' -v

diff -u "$HERE/evals/expected/effectiveness.json" "$OUT/run/effectiveness.json"

test "$(find "$OUT/run/observations" -type f -name '*.json' | wc -l | tr -d ' ')" = "15"
test -s "$OUT/run/runtime/hidden-artifact-omission/packet.zip"

echo "REPOSITORY CAPABILITY AUDIT GREEN"
