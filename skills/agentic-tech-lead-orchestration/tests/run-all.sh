#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=${TMPDIR:-/tmp}/agentic-tech-lead-receipt-$$.json
QUEUE_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-queue-receipt-$$.json
CONTROL_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-control-plane-$$.md
SOURCE_TMP=${TMPDIR:-/tmp}/agentic-tech-lead-source-ledger-$$.json
trap 'rm -f "$TMP" "$QUEUE_TMP" "$CONTROL_TMP" "$SOURCE_TMP"' EXIT HUP INT TERM

# #605: every gate below judges the tree in front of it, so none of them can see
# a gate that is no longer there — a merge that deletes a check makes this suite
# green *because* the check vanished (proven twice: the #466 receipt paper gate,
# and two per-queue selftest invocations). This runs first: the range base..HEAD
# must still carry every gate file and invocation its own base carried.
# The one named retirement is a9db0bd's: the git-at-any-scale SKIPPED_BY_POLICY
# carve-out documented below retired itself once the queue was recompiled. Once
# main advances past a9db0bd that deletion leaves every range, the run prints
# GATE-PRESERVATION-NOTE for the unused pattern, and the --allow line below is
# to be deleted. An unused pattern is a note rather than a red because the PR
# that lands a retirement is judged against a base that no longer contains it.
python3 "$ROOT/scripts/check_gate_preservation.py" --selftest
python3 "$ROOT/scripts/check_gate_preservation.py" \
  --allow 'assert_local_handoff_queue.py" --queue "$queue" >/dev/null'

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
# newly added queue cannot look admitted by omission. There is no exemption:
# git-at-any-scale was recompiled into the v1 shape, so its former
# SKIPPED_BY_POLICY carve-out retired itself as designed.
# Every queue also runs its own planted-control selftest, so a queue whose gate
# cannot go red is caught here rather than at execution time.
for queue in "$ROOT"/runtime-handoff/*-local-handoff-queue.json; do
  python3 "$ROOT/scripts/assert_local_handoff_queue.py" --queue "$queue"
  python3 "$ROOT/scripts/assert_local_handoff_queue.py" --queue "$queue" --selftest
done

# Close the receipt paper gate (#466): a queue item whose exit requires a
# receipt must have that receipt actually exist and actually validate — the
# queue gate above only checks the path and schema id are DECLARED. A
# blocked/NOT_EXERCISED attempt receipt is a different document class and must
# say so explicitly instead of silently failing the lifecycle contract.
python3 - "$ROOT" <<'PYRC'
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

SKILL = Path(sys.argv[1])
ROOT = SKILL.parents[1]
# #607: every receipt.schema id a runtime-handoff queue names must resolve to a
# contract file that declares that identity. An id with no entry here is red the
# moment its receipt exists, so a new queue cannot ship an unbindable label.
SCHEMA_BY_ID = {
    "agentic-tech-lead/herdr-lifecycle/v1": SKILL / "references/contracts/herdr-lifecycle-receipt.schema.json",
    "agentic-tech-lead/problem-closure/v1": SKILL / "references/contracts/problem-closure.schema.json",
    "agentic-tech-lead/codex-v2-result-carrier/v1": SKILL / "references/contracts/codex-v2-result-carrier-receipt.schema.json",
    "agentic-tech-lead/codex-v2-live-run/v1": SKILL / "references/contracts/codex-v2-live-run-receipt.schema.json",
    "agentic-tech-lead/codex-v2-live-run-shadow/v1": SKILL / "references/contracts/codex-v2-live-run-shadow-receipt.schema.json",
    "agentic-tech-lead/issue-closure-contract/v1": SKILL / "references/issue-closure-contract.schema.json",
    "spatial-loop/live-shadow-case-delta-receipt/v1": SKILL / "references/contracts/live-shadow-case-delta-receipt.schema.json",
    "git-hosting-assurance/v1": SKILL.parent / "git-hosting-scale-assurance/references/hosting-assurance.schema.json",
}
failed = []
checked = 0
for queue_path in sorted((SKILL / "runtime-handoff").glob("*-local-handoff-queue.json")):
    for item in json.loads(queue_path.read_text())["items"]:
        if item.get("exit", {}).get("requires_receipt") is not True:
            continue
        label = f"{queue_path.name}:{item['id']}"
        schema_id = item["receipt"]["schema"]
        receipt_path = ROOT / item["receipt"]["path"]
        if not receipt_path.exists():
            # An ACTIVE/BLOCKED item may legitimately have no receipt yet; a
            # COMPLETE one may not. An id whose family has shipped no receipt at
            # all is checked the day one appears, not answered with a guessed schema.
            if item.get("state") == "COMPLETE":
                failed.append(f"{label}: COMPLETE with no receipt at {receipt_path}")
            continue
        schema_file = SCHEMA_BY_ID.get(schema_id)
        if schema_file is None:
            failed.append(f"{label}: receipt.schema {schema_id!r} resolves to no contract file")
            continue
        checked += 1
        instance = json.loads(receipt_path.read_text())
        if instance.get("state") in {"NOT_EXERCISED", "FAIL", "HUMAN_ADMIT_REQUIRED"}:
            for key in ("state", "evidence_ceiling", "sample_count", "blockers"):
                if key not in instance:
                    failed.append(f"{label}: blocked receipt missing {key}")
            continue
        errors = list(Draft202012Validator(json.loads(schema_file.read_text())).iter_errors(instance))
        binding = instance.get("schema_binding", {})
        if binding.get("state") == "SCHEMA_MISMATCH_DECLARED":
            # #532/#535: a receipt may refuse the schema its queue names, but only
            # out loud -- naming that exact id, holding for Human Admit, and
            # recording a validator readback this gate reproduces error for error.
            # A silent non-conformance and a lie about the readback stay red.
            readback = instance.get("schema_validation_readback", {})
            if (binding.get("queue_named_schema") != schema_id
                    or instance.get("human_admit") != "HUMAN_ADMIT_REQUIRED"
                    or readback.get("conforms") is not False
                    or readback.get("error_count") != len(errors)):
                failed.append(
                    f"{label}: schema mismatch against {schema_id} is misdeclared "
                    f"(observed {len(errors)} validator errors)"
                )
            continue
        if errors:
            failed.append(f"{label}: receipt fails {schema_file.name}: {errors[0].message[:120]}")
if checked == 0:
    failed.append("no receipt was validated: this gate would be vacuously green")
if failed:
    print("RECEIPT-GATE-RED"); [print(" -", f) for f in failed]; sys.exit(1)
print(f"RECEIPT-GATE-GREEN {checked} local handoff receipts bound to their declared contract")
PYRC


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
    "references/contracts/codex-v2-result-carrier-receipt.schema.json",
    "references/contracts/codex-v2-live-run-shadow-receipt.schema.json",
    "references/contracts/github-dag-live-canary-receipt.schema.json",
    "references/contracts/herdr-lifecycle-receipt.schema.json",
    "references/contracts/live-shadow-case-delta-receipt.schema.json",
    "references/contracts/source-claims-input.schema.json",
]
for rel in schemas:
    schema = json.loads((root / rel).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

# check_schema only proves the schema parses. The herdr lifecycle contract is
# named by herdr-local-handoff-queue.json as its receipt, so its queue-level
# envelope must actually admit an honest zero-sample blocked run and a future
# live PASS -- and must still refuse the laundering between them.
herdr = Draft202012Validator(
    json.loads((root / "references/contracts/herdr-lifecycle-receipt.schema.json").read_text(encoding="utf-8"))
)
blocked = {
    "schema": "agentic-tech-lead/herdr-lifecycle/v1", "schema_version": 1,
    "task_ref": "issue-466-live-herdr-managed-lifecycle", "attempt_id": "selftest",
    "subject": {"repository": "ed3c/skills-shared", "commit": "0" * 40, "tree": "1" * 40},
    "blockers": [{"class": "CARRIER_RUNTIME_CONTRACT_MISMATCH", "detail": "d", "unblocking_lane": "u"}],
    "cleanup": {"state": "CLEAN", "residue_count": 0},
    "evidence": [{"argv": ["herdr", "--version"], "exit_code": 0, "finding": "f"}],
    "host": {"class": "CLAUDE_CODE_LOCAL"},
    "plan": {"path": "p", "sha256": "2" * 64},
    "forbidden_promotions_respected": ["permission_denial_to_pass"],
    "lifecycle_state_reached": "EXACT_SCRATCH_HOME_AND_WORKTREE_BOUND_NOT_REACHED",
    "sample_count": 0, "state": "NOT_EXERCISED",
    "controller_readback_required": True, "shadow_review_required": True,
    "evidence_ceiling": "NO_HERDR_LIFECYCLE_SAMPLE",
}
assert not list(herdr.iter_errors(blocked)), [e.message for e in herdr.iter_errors(blocked)]
live_pass = dict(blocked, state="PASS", sample_count=2, sample_digests=["3" * 64, "4" * 64],
                 evidence_ceiling="LIVE_OBSERVER_LIFECYCLE_SHADOW_PENDING")
live_pass.pop("blockers")
assert not list(herdr.iter_errors(live_pass)), [e.message for e in herdr.iter_errors(live_pass)]
assert list(herdr.iter_errors(dict(blocked, state="PASS"))), "zero-sample PASS must be refused"
assert list(herdr.iter_errors(dict(blocked, sample_count=3))), "blocked run with samples must be refused"
print("HERDR-RECEIPT-ENVELOPE-GREEN blocked/live-PASS legal; laundering refused")

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
print("CONTROL-PLANE-SHAPE-GREEN 15 schemas; closure/source examples validated")
PYCP
python3 "$ROOT/tests/codex_sdk_controller_selftest.py"
python3 "$ROOT/tests/github_issue_dag_selftest.py"
python3 "$ROOT/tests/herdr_observer_selftest.py"
python3 "$ROOT/tests/herdr_surface_conformance_selftest.py"
python3 "$ROOT/tests/problem_closure_selftest.py"

# #508: the durable result carrier and the strict worker-result contract. Both
# selftests build a real throwaway repository, publish the carrier, delete the
# originating object store, and then replay. They are deterministic mechanics:
# a green run never promotes #464's live lane.
python3 "$ROOT/tests/codex_result_carrier_selftest.py"
python3 "$ROOT/tests/codex_worker_result_selftest.py"
python3 "$ROOT/tests/codex_pinned_runtime_selftest.py"
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

# #606: the Issue closure ledger. The dedicated workflow owns the same denominator,
# but it only fires on its own paths, so the local suite runs shape, unit controls
# and the semantic gate over every audited packet here as well.
python3 - "$ROOT" <<'PYIC'
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(sys.argv[1])
schema = json.loads((root / "references/issue-closure-contract.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
packets = sorted((root / "references/closure-audit").glob("issue-*.json"))
assert packets, "closure-audit ledger is empty"
for packet in packets:
    errors = list(Draft202012Validator(schema).iter_errors(json.loads(packet.read_text(encoding="utf-8"))))
    assert not errors, (packet.name, [error.message for error in errors])

# Every packet in the ledger is unbound or grandfathered, so nothing on disk yet
# proves the schema ADMITS a bound PASS. A shape that rejected the binding would
# make the #606 law unreachable and no packet would notice until the first one.
bound = json.loads((root / "references/closure-audit/issue-568.json").read_text(encoding="utf-8"))
bound["shadow_review"] = {
    "verdict": "PASS",
    "packet_author": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "writer", "worktree": "w"},
    "shadow_identity": {"host_class": "CLAUDE_CODE_LOCAL", "session_id": "shadow", "worktree": "s"},
    "receipt": {"path": "docs/traceability/shadow.json", "sha256": "0" * 64},
}
assert not list(Draft202012Validator(schema).iter_errors(bound)), "schema refuses a bound PASS"
bound["shadow_review"]["reviewer"] = "some prose"
assert list(Draft202012Validator(schema).iter_errors(bound)), "shadow_review must stay closed to invented fields"
print(f"ISSUE-CLOSURE-SHAPE-GREEN {len(packets)} audited packets; bound PASS admitted, prose reviewer refused")
PYIC
python3 "$ROOT/tests/test_issue_closure_contract.py"
for packet in "$ROOT"/references/closure-audit/issue-*.json; do
  python3 "$ROOT/scripts/assert_issue_closure_contract.py" "$packet" >/dev/null
done

# Permanent planted control for #606: flipping a self-authored HUMAN_ADMIT_REQUIRED
# packet to PASS without naming a Shadow and its receipt must turn the shipped gate
# red at the process boundary, not only inside the unit suite.
python3 - "$ROOT" <<'PYSS'
import json, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
for name in ("issue-407.json", "issue-508.json"):
    packet = json.loads((root / "references/closure-audit" / name).read_text(encoding="utf-8"))
    assert packet["shadow_review"]["verdict"] == "HUMAN_ADMIT_REQUIRED", (name, packet["shadow_review"])
    packet["shadow_review"]["verdict"] = "PASS"
    with tempfile.TemporaryDirectory() as tmp:
        flipped = Path(tmp) / name
        flipped.write_text(json.dumps(packet), encoding="utf-8")
        run = subprocess.run(
            [sys.executable, str(root / "scripts/assert_issue_closure_contract.py"), str(flipped)],
            capture_output=True, text=True,
        )
    assert run.returncode == 2, (name, run.returncode, run.stdout, run.stderr)
    assert "self-authored packet is HUMAN_ADMIT_REQUIRED" in run.stdout, (name, run.stdout)
print("CLOSURE-SELFSIGN-CONTROL-RED unbound PASS refused on issue-407/issue-508")
PYSS
