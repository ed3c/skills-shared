#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=${TMPDIR:-/tmp}/agentic-tech-lead-receipt-$$.json
QUEUE_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-queue-receipt-$$.json
CONTROL_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-control-plane-$$.md
SOURCE_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-source-ledger-$$.json
trap 'rm -f "$TMP" "$QUEUE_TMP" "$CONTROL_TMP" "$SOURCE_TMP"' EXIT HUP INT TERM

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

# Prove the #316 behavioral A/B scorer discriminates before it is ever pointed at
# a live host. Zero network, zero spend: fixed packets are scored against the
# pinned consumer tree and every planted defect must turn its own check red.
python3 "$ROOT/scripts/run_behavioral_ab.py" --selftest

# Exercise semantic/hard-law controls and scheduler lifecycle controls.
python3 "$ROOT/tests/selftest.py"
python3 "$ROOT/tests/scheduler_lifecycle_selftest.py"
python3 -m json.tool "$ROOT/references/scheduler-lifecycle.schema.json" >/dev/null

# Validate the zero-context local handoff queues and their planted controls.
python3 -m json.tool "$ROOT/references/local-handoff-queue.schema.json" >/dev/null
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/references/example-local-handoff-queue.json"
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/references/example-local-handoff-queue.json" \
  --selftest
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/references/wave3-live-handoff-queue.json"

# The current Tech Lead runtime/source handoff queues are load-bearing. Execute
# their semantic gate over every queue in runtime-handoff/ so a docs-only or
# newly added queue cannot look admitted by omission. One named exemption:
# git-at-any-scale predates the v1 shape (36 gate FAILs) and its repair is
# owned by ed3c/skills-shared#531/#536 — printed as SKIPPED_BY_POLICY, not hidden.
for queue in "$ROOT"/runtime-handoff/*-local-handoff-queue.json; do
  case "$(basename "$queue")" in
    git-at-any-scale-local-handoff-queue.json)
      # Self-retiring exemption: the moment the file passes its gate, this
      # carve-out must be removed, so a green run under the skip turns the suite red.
      if python3 "$ROOT/scripts/assert_local_handoff_queue.py" --queue "$queue" >/dev/null 2>&1; then
        echo "EXEMPTION STALE: $(basename "$queue") now passes its gate; remove this SKIPPED_BY_POLICY carve-out" >&2
        exit 1
      fi
      echo "SKIPPED_BY_POLICY: $(basename "$queue") pre-v1 shape; repair owned by #531/#536"
      continue
      ;;
  esac
  python3 "$ROOT/scripts/assert_local_handoff_queue.py" --queue "$queue"
done

# A schema-valid one-item queue epoch must validate and run its planted
# controls (issue #317: the selftest used to crash on items[1]).
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/tests/fixtures/local-handoff-queue.single-item.json"
python3 "$ROOT/scripts/assert_local_handoff_queue.py" \
  --queue "$ROOT/tests/fixtures/local-handoff-queue.single-item.json" \
  --selftest

# Validate the repository closure contract and Issue dual-dependency DAG.
# Shape first (the schemas are load-bearing, not decorative), then the semantic
# laws and their planted mutations.
python3 -m json.tool "$ROOT/references/repository-closure-contract.schema.json" >/dev/null
python3 -m json.tool "$ROOT/references/issue-dual-dag.schema.json" >/dev/null
python3 - "$ROOT" <<'PY1'
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

references = Path(sys.argv[1]) / "references"
pairs = [
    ("repository-closure-contract.schema.json", "example-repository-closure-contract.json"),
    ("issue-dual-dag.schema.json", "example-issue-dual-dag.json"),
]
for schema_name, example_name in pairs:
    schema = json.loads((references / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in Draft202012Validator(schema).iter_errors(
            json.loads((references / example_name).read_text(encoding="utf-8"))
        )
    ]
    assert not errors, (schema_name, errors)
    print(f"CLOSURE-SHAPE-GREEN {schema_name} validated {example_name}")
PY1
python3 "$ROOT/scripts/assert_repository_closure_contract.py" \
  --contract "$ROOT/references/example-repository-closure-contract.json" \
  --dag "$ROOT/references/example-issue-dual-dag.json"
python3 "$ROOT/scripts/assert_repository_closure_contract.py" \
  --contract "$ROOT/references/example-repository-closure-contract.json" \
  --dag "$ROOT/references/example-issue-dual-dag.json" \
  --selftest

# Execute the Codex/GitHub-DAG/Herdr/problem-closure control-plane denominator.
# These are deterministic/offline gates. They intentionally do not invoke live
# Codex SDK execution, GitHub dependency mutation, Herdr, or provider/source
# evidence. A green result therefore cannot promote those lanes to live PASS.
python3 - "$ROOT" <<'PYCP'
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(sys.argv[1])
schemas = [
    "references/contracts/codex-session-manifest.schema.json",
    "references/contracts/codex-worker-result.schema.json",
    "references/contracts/codex-worker-result-v2.schema.json",
    "references/contracts/github-issue-dag-receipt.schema.json",
    "references/contracts/github-ready-wave.schema.json",
    "references/contracts/herdr-observer-receipt.schema.json",
    "references/contracts/problem-closure.schema.json",
    "references/contracts/codex-live-acceptance-receipt.schema.json",
    "references/contracts/codex-live-acceptance-receipt-v2.schema.json",
    "references/contracts/github-dag-live-canary-receipt.schema.json",
    "references/contracts/herdr-lifecycle-receipt.schema.json",
    "references/contracts/source-claims-input.schema.json",
]
for rel in schemas:
    schema = json.loads((root / rel).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

closure_schema = json.loads(
    (root / "references/contracts/problem-closure.schema.json").read_text(encoding="utf-8")
)
closure_example = json.loads(
    (root / "references/examples/problem-closure.example.json").read_text(encoding="utf-8")
)
errors = list(Draft202012Validator(closure_schema).iter_errors(closure_example))
assert not errors, [error.message for error in errors]

source_schema = json.loads(
    (root / "references/contracts/source-claims-input.schema.json").read_text(encoding="utf-8")
)
source_example = json.loads(
    (root / "references/examples/source-claims.example.json").read_text(encoding="utf-8")
)
errors = list(Draft202012Validator(source_schema).iter_errors(source_example))
assert not errors, [error.message for error in errors]
print("CONTROL-PLANE-SHAPE-GREEN 12 schemas; closure/source examples validated")
PYCP
python3 "$ROOT/tests/codex_sdk_controller_selftest.py"
python3 "$ROOT/tests/github_issue_dag_selftest.py"
python3 "$ROOT/tests/herdr_observer_selftest.py"
python3 "$ROOT/tests/problem_closure_selftest.py"

# #508: the durable result carrier and the strict worker-result contract. Both
# selftests build a real throwaway repository, publish the carrier, delete the
# originating object store, and then replay. They are deterministic mechanics:
# a green run never promotes #464's live lane.
python3 "$ROOT/tests/codex_result_carrier_selftest.py"
python3 "$ROOT/tests/codex_worker_result_selftest.py"
python3 "$ROOT/tests/codex_live_acceptance_selftest.py"
python3 "$ROOT/tests/github_issue_dag_live_canary_selftest.py"
python3 "$ROOT/tests/herdr_lifecycle_selftest.py"
python3 "$ROOT/tests/source_claim_compiler_selftest.py"
python3 "$ROOT/scripts/check_problem_closure.py" \
  "$ROOT/references/examples/problem-closure.example.json" >/dev/null
python3 "$ROOT/scripts/render_problem_closure.py" \
  "$ROOT/references/examples/problem-closure.example.json" \
  --output "$CONTROL_TMP"
grep -F '> Generated projection. Machine truth remains the checked JSON ledger' \
  "$CONTROL_TMP" >/dev/null

# Prove the source compiler emits the existing problem-closure truth model,
# rather than a second incompatible ledger format.
python3 "$ROOT/scripts/compile_source_claims.py" \
  "$ROOT/references/examples/source-claims.example.json" \
  --output "$SOURCE_TMP"
python3 "$ROOT/scripts/check_problem_closure.py" "$SOURCE_TMP" >/dev/null

# Freeze the portable Dual-Agent offload method contract and its exact-subject
# handoff packet, and prove all sixteen semantic controls still turn red. No
# runtime wire schema, transport, provider or effect lane is claimed here.
bash "$ROOT/tests/dual-agent-offload-contract/verify.sh"

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

# #566: repository-portfolio control core (snapshot/acceptance/multigraph/waves/dispatch).
sh "$ROOT/tests/portfolio-control/run-all.sh"
