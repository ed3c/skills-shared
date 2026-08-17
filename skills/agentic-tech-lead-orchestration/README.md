# agentic-tech-lead-orchestration

Portable contract-first orchestration for turning one large coding request into a dependency-aware branch team and, when the current session reaches a real host/runtime boundary, a zero-context Local Handoff Execution Queue. `SKILL.md` owns the method; `modules/` contains optional provider/delivery adapters; `references/` contains stable packet schemas and prompt templates; `scripts/` contains deterministic assertions.

## Current integration state

| Plane | State | Exact proof / owner |
|---|---|---|
| Portable core and provider/domain separation | `IMPLEMENTED` | PR #308 candidate |
| Task schema + semantic pre-dispatch gates | `PASS / DETERMINISTIC_FIXTURE` | `check_task_contract_schema.py` + `assert_task_contract.py` |
| Module route reachability | `PASS / DETERMINISTIC_FIXTURE` | `check_runtime_reachability.py` |
| Trigger/predecessor/receipt causal DAG | `PASS / DETERMINISTIC_FIXTURE` | `assert_capability_dag.py`; PR #308 head `504c18f10d3380be4874a59f7cfad5c290daa93f` |
| Production-shaped worktree/subprocess A/B | `PASS / SYNTHETIC_RUNTIME` | PR #315 head `403a4f041c5f8c07b0d7c8bb0ef2ccc44ac0f113` |
| Local Handoff Execution Queue contract | `IMPLEMENTED` | main-derived queue schema/assertion preserved in #308 |
| Live model/provider adapters | `NOT_EXERCISED` | #256 and #312 Phase 2 |
| Independent live Shadow/global-objective trial | `NOT_EXERCISED` | #232 |
| Live Git Town/Forgejo delivery | `NOT_EXERCISED` | #234 |
| Merge/promotion | `HUMAN_ADMIT_REQUIRED` | repository authority |

The deterministic result is not a live-model quality claim. It proves that the refactored method retains old causal strengths, exposes the B0 regression, and closes module execution through typed receipts on the tested subjects.

## Directory ownership

```text
agentic-tech-lead-orchestration/
├── README.md
│   └── read order, current state, directory/state/DAG/data-flow and trace index
├── SKILL.md
│   └── portable control law, state machine, evidence ceilings and stop/handoff
├── modules/
│   └── trigger-selected provider, execution, tournament and delivery specialization
├── references/
│   └── task, capability, scheduler and local-handoff schemas/examples
├── scripts/
│   └── shape, semantic, reachability, causal-DAG, scheduler and handoff assertions
├── tests/
│   └── positive, mutation, old/new structural A/B and real-task A/B controls
├── cases.json
└── evals.json
```

Provider binaries, indexes, credentials, local paths, worktrees, consumer commands and live receipts remain runtime/consumer-owned. A module file or installed tool does not activate itself.

## State machine and owning surfaces

```text
REQUEST_BOUND                         SKILL.md + task request
→ SYSTEM_CONTRACT_EXTRACTED           task contract
→ CAPABILITY_PLAN_COMPILED            modules/domain-profile.md
→ CAPABILITY_PLAN_ASSERTED            assert_capability_dag.py structure gate
→ CONTEXT_ADMITTED                    selected capability receipts
→ TASK_DAG_COMPILED                   true dependencies + leases
→ TASK_SCHEMA_ASSERTED                check_task_contract_schema.py
→ TASK_SEMANTICS_ASSERTED             assert_task_contract.py
→ WORKERS_ADMITTED                    validated task/capability envelope
→ LEASES_BOUND                        scheduler/consumer runtime
→ ATTEMPTS_EXECUTED                   executor module + attempt receipts
→ RESULTS_VERIFIED                    independent oracles/readback
→ CANDIDATES_COMPARED                 tournament module when selected
→ CONVERGENCE_APPLIED                 one convergence owner
→ GLOBAL_OBJECTIVE_ASSERTED           local + repository/system invariants
→ DELIVERY_HANDOFF                    delivery module or Human authority
→ LOCAL_HANDOFF_COMPILED              only at a real host/runtime boundary
→ LOCAL_HANDOFF_EXECUTED               admitted consumer/runtime authority
```

The former T0–T10 causal narrative is preserved by `references/t0-t10-causal-map.json`. The critical law is not the labels: predecessor evidence is the only legal source for the next admission.

## Capability DAG

```text
frozen task need
→ trigger evidence
→ REQUIRED | OPTIONAL_SELECTED | NOT_APPLICABLE
→ predecessor transitions and output states
→ exact module + task/subject/attempt identity
→ invocation
→ capability receipt
→ cumulative causal assertion
→ downstream state admission
```

Reachability and causality are separate. `SKILL.md → module` proves the route exists; only an identity-matched receipt that consumes predecessor output can advance runtime state. `FIXTURE` receipts are valid only in fixture mode and cannot become live PASS.

## Data flow

```text
Issue / PRD / PDF
→ repository routing and exact subject
→ locked task contract and immutable assertions
→ trigger-selected context capabilities
→ current-source readback
→ true dependency DAG + path/resource leases
→ isolated Worker packets/worktrees
→ bounded attempts, checkpoint/retry and independent oracles
→ candidate denominator and deterministic comparison
→ verified convergence owner
→ global objective + cleanup
→ delivery handoff
→ optional typed Local Handoff Execution Queue
→ live runtime/provider lanes or Human admission
```

The production-shaped canary exercises real linked worktrees and overlapping subprocess Workers, a three-candidate tournament with a failed candidate retained, checkpoint/retry lineage, wrong-base convergence refusal, local-pass/global-fail veto, global objective PASS and clean residue. A, B1 and B2 produced equivalent final bytes; B0 was correctly blocked because its dispatch route was absent. B2's demonstrated advantage is stronger executable admissibility, not superior model-generated code.

## Read order

1. repository instructions and current task packet;
2. this README for current integration truth;
3. `SKILL.md`;
4. `references/task-contract.schema.json`;
5. `references/capability-plan.schema.json` and `references/capability-receipts.schema.json`;
6. `references/local-handoff-queue.schema.json` when a host/runtime boundary exists;
7. `references/fanout-prompt.md`;
8. `modules/README.md`, then only modules selected by the frozen plan;
9. `scripts/README.md` and executable assertions;
10. `tests/README.md`, `tests/run-all.sh`, structural A/B and real-task A/B;
11. `skills/procedural-core-refactor/README.md` for the canonical future-refactor method and golden-proof ledger.

## Local verification

```bash
python3 scripts/check_task_contract_schema.py --contract references/example-stack-contract.json
python3 scripts/assert_task_contract.py --contract references/example-stack-contract.json --receipt /tmp/agentic-tech-lead-receipt.json
python3 scripts/assert_capability_dag.py \
  --contract references/example-stack-contract.json \
  --plan references/example-capability-plan.json \
  --receipts references/example-capability-receipts.json \
  --admit-state DELIVERY_HANDOFF \
  --fixture-mode
python3 scripts/assert_local_handoff_queue.py --queue references/example-local-handoff-queue.json --selftest
sh tests/run-all.sh
```

A local PASS validates only the named packet/mechanism/evidence class. Live providers, index freshness, admitted consumer worktrees, Git Town, Forgejo, publication, signed-in carriers, devices and model quality remain `NOT_EXERCISED` until separate exact-subject receipts exist.

## Golden-proof trace

```text
#307 / PR #308
  old/B0/B1/B2 structural and causal repair
  branch: fix/307-tech-lead-runtime-reachability
  exact head: 504c18f10d3380be4874a59f7cfad5c290daa93f

#312 / PR #315
  production-shaped deterministic real-task A/B
  branch: agent/312-tech-lead-real-task-ab
  exact head: 403a4f041c5f8c07b0d7c8bb0ef2ccc44ac0f113

#326 → #327 → #328 → #329
  canonical procedural-core refactor method
  → executable golden-proof ledger
  → repository docs/registry/CI convergence
```

Remaining terminal live lanes are #231, #232, #234, #256 and #312 Phase 2. PR metadata and exact-head CI remain the publication authority; this README cannot promote a pending or absent workflow to PASS.
