#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=${TMPDIR:-/tmp}/agentic-tech-lead-receipt-$$.json
QUEUE_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-queue-receipt-$$.json
trap 'rm -f "$TMP" "$QUEUE_TMP"' EXIT HUP INT TERM

# Prove the routing itself, including planted disconnections.
python3 "$ROOT/scripts/check_runtime_reachability.py" --selftest

# Exercise the Draft 2020-12 task-packet shape gate and its planted mutations.
python3 "$ROOT/scripts/check_task_contract_schema.py" --selftest
python3 "$ROOT/scripts/check_task_contract_schema.py" \
  --contract "$ROOT/references/example-stack-contract.json"

# Prove module reachability is also a causal DAG. Fixture mode proves the
# mechanism but cannot authorize live runtime state.
python3 "$ROOT/tests/capability_dag_selftest.py"
python3 "$ROOT/scripts/assert_capability_dag.py" \
  --contract "$ROOT/references/example-stack-contract.json" \
  --plan "$ROOT/references/example-capability-plan.json" \
  --receipts "$ROOT/references/example-capability-receipts.json" \
  --admit-state DELIVERY_HANDOFF \
  --fixture-mode

# Freeze and compare the old monolith, refactor-as-landed, reachability repair,
# and current receipt-gated causal-DAG candidate.
python3 "$ROOT/tests/refactor_ab.py"

# Execute one production-shaped matched task with real linked worktrees and
# subprocess Workers. This proves synthetic runtime closure only; provider,
# model, Git Town and Forgejo lanes remain NOT_EXERCISED.
python3 "$ROOT/tests/real_task_ab.py"

# Exercise semantic/hard-law controls and scheduler lifecycle controls.
python3 "$ROOT/tests/selftest.py"
python3 "$ROOT/tests/scheduler_lifecycle_selftest.py"
python3 -m json.tool "$ROOT/references/scheduler-lifecycle.schema.json" >/dev/null

# Validate the zero-context local handoff queue and its planted controls.
python3 -m json.tool "$ROOT/references/local-handoff-queue.schema.json" >/dev/null
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/references/example-local-handoff-queue.json"
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/references/example-local-handoff-queue.json" \
  --selftest

# A schema-valid one-item queue epoch must validate and run its planted
# controls (issue #317: the selftest used to crash on items[1]).
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/tests/fixtures/local-handoff-queue.single-item.json"
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/tests/fixtures/local-handoff-queue.single-item.json" \
  --selftest

# Emit and inspect the positive semantic task receipt.
python3 "$ROOT/scripts/assert_task_contract.py" \
  --contract "$ROOT/references/example-stack-contract.json" \
  --receipt "$TMP"
python3 - "$TMP" <<'PY2'
import json, sys
from pathlib import Path
receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["verdict"] == "PASS", receipt
assert receipt["claims_not_proven"], receipt
print("agentic-tech-lead receipt control: PASS")
PY2
