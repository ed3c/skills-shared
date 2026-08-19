#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m py_compile \
  "$ROOT/scripts/check_trace_graph.py" \
  "$ROOT/tests/mutation_proof.py" \
  "$ROOT/tests/build_exact_head_fixture.py"

python3 "$ROOT/scripts/check_trace_graph.py" \
  "$ROOT/tests/fixtures/valid-trace-graph.json" \
  --authority-snapshot "$ROOT/tests/fixtures/authority-snapshot.json"

python3 "$ROOT/tests/mutation_proof.py"

if [[ -n "${ITEKG_EXPECTED_SHA:-}" && -n "${ITEKG_REPOSITORY:-}" && -n "${ITEKG_REF:-}" && -n "${ITEKG_PR_NUMBER:-}" ]]; then
  evidence_dir="${ITEKG_EVIDENCE_DIR:-${RUNNER_TEMP:-/tmp}/intent-to-evidence-knowledge-graph}"
  mkdir -p "$evidence_dir"

  python3 "$ROOT/tests/build_exact_head_fixture.py" \
    --repository "$ITEKG_REPOSITORY" \
    --ref "$ITEKG_REF" \
    --sha "$ITEKG_EXPECTED_SHA" \
    --pr-number "$ITEKG_PR_NUMBER" \
    --graph-out "$evidence_dir/exact-head-graph.json" \
    --authority-out "$evidence_dir/exact-head-authority.json"

  python3 "$ROOT/scripts/check_trace_graph.py" \
    "$evidence_dir/exact-head-graph.json" \
    --authority-snapshot "$evidence_dir/exact-head-authority.json" \
    --expected-sha "$ITEKG_EXPECTED_SHA" \
    --receipt-out "$evidence_dir/exact-head-receipt.json"

  python3 - "$evidence_dir/exact-head-receipt.json" "$ITEKG_EXPECTED_SHA" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = sys.argv[2]
assert receipt["status"] == "PASS", receipt
assert receipt["subject"]["sha"] == expected, receipt
print(json.dumps({
    "exact_head_receipt": "PASS",
    "subject_sha": receipt["subject"]["sha"],
    "graph_digest": receipt["graph_digest"],
    "authority_snapshot_digest": receipt["authority_snapshot_digest"],
}, sort_keys=True))
PY
fi
