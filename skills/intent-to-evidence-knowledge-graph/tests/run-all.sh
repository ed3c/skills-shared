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

if [[ -n "${ITEKG_EXPECTED_SHA:-}" && -n "${ITEKG_REPOSITORY:-}" && -n "${ITEKG_REF:-}" && -n "${ITEKG_PR_NUMBER:-}" && "${ITEKG_PR_NUMBER}" != "0" ]]; then
  if [[ -z "${ITEKG_OBSERVED_AT:-}" ]]; then
    echo "ITEKG_OBSERVED_AT is required for an exact-head PR receipt" >&2
    exit 64
  fi

  evidence_dir="${ITEKG_EVIDENCE_DIR:-${RUNNER_TEMP:-/tmp}/intent-to-evidence-knowledge-graph}"
  mkdir -p "$evidence_dir"

  python3 "$ROOT/tests/build_exact_head_fixture.py" \
    --repository "$ITEKG_REPOSITORY" \
    --ref "$ITEKG_REF" \
    --sha "$ITEKG_EXPECTED_SHA" \
    --pr-number "$ITEKG_PR_NUMBER" \
    --observed-at "$ITEKG_OBSERVED_AT" \
    --graph-out "$evidence_dir/exact-head-graph.json" \
    --authority-out "$evidence_dir/exact-head-authority.json"

  python3 "$ROOT/scripts/check_trace_graph.py" \
    "$evidence_dir/exact-head-graph.json" \
    --authority-snapshot "$evidence_dir/exact-head-authority.json" \
    --expected-sha "$ITEKG_EXPECTED_SHA" \
    --receipt-out "$evidence_dir/exact-head-receipt.json"

  python3 - "$evidence_dir/exact-head-receipt.json" "$evidence_dir/exact-head-graph.json" "$ITEKG_EXPECTED_SHA" "$ITEKG_OBSERVED_AT" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
graph = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
expected_sha = sys.argv[3]
expected_observed_at = sys.argv[4]
assert receipt["status"] == "PASS", receipt
assert receipt["subject"]["sha"] == expected_sha, receipt
mutable = [artifact for artifact in graph["artifacts"] if artifact["mutable"]]
assert mutable, graph
assert all(artifact["observed_subject"]["observed_at"] == expected_observed_at for artifact in mutable), graph
print(json.dumps({
    "exact_head_receipt": "PASS",
    "subject_sha": receipt["subject"]["sha"],
    "observed_at": expected_observed_at,
    "graph_digest": receipt["graph_digest"],
    "authority_snapshot_digest": receipt["authority_snapshot_digest"],
}, sort_keys=True))
PY
fi
