# `agentic-tech-lead-orchestration`

Portable contract-first orchestration for turning one large coding request into a dependency-aware branch team and, when the current session reaches a real host/runtime boundary, a zero-context Local Handoff Execution Queue. `SKILL.md` owns the provider-neutral method; `references/` owns host-neutral contracts; `modules/` contains trigger-selected runtime/projection/delivery interpretations; `scripts/` and `tests/` own executable assertions and falsifiers.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. task, capability and scheduler schemas under [`references/`](references/README.md)
4. when issues #375–#379 or Codex control-plane execution is in scope, [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md), the relevant execution packet under `references/execution-packets/`, and only the selected adapter modules
5. when local/runtime-only evidence remains, `references/local-handoff-queue.schema.json` and the example queue
6. when the work must run in a remote lane while the local one is disconnected, [`references/dual-agent-offload/OFFLOAD_METHOD.md`](references/dual-agent-offload/OFFLOAD_METHOD.md)
7. [`modules/README.md`](modules/README.md), then only selected modules
8. [`scripts/README.md`](scripts/README.md)
9. [`tests/README.md`](tests/README.md)
10. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) and its golden registry
11. exact issue, PR base/head, workflow and receipt subjects
12. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md) before a global completion claim

## Directory map → State Machine ownership

```text
skills/agentic-tech-lead-orchestration/
├── AGENTS.md
│   └── Agent read order, writer/queue leases, evidence and authority boundary
├── README.md
│   └── integration state, directory map, State Machines, DAG and data flow
├── SKILL.md
│   └── portable request → task → capability → Worker → convergence → handoff law
├── references/
│   ├── task/capability/scheduler/closure contracts
│   ├── contracts/
│   │   ├── codex-session-manifest.schema.json             #375
│   │   ├── codex-worker-result.schema.json                #375
│   │   ├── github-issue-dag-receipt.schema.json           #376
│   │   ├── github-ready-wave.schema.json                  #376
│   │   ├── herdr-observer-receipt.schema.json             #377
│   │   └── problem-closure.schema.json                    #378
│   ├── examples/
│   │   ├── herdr-runtime-binding.example.json             #377
│   │   └── problem-closure.example.json                   #378
│   ├── execution-packets/375-codex-sdk.md                 #375
│   ├── execution-packets/376-github-issue-dag.md          #376
│   ├── execution-packets/377-herdr-observer.md            #377
│   ├── execution-packets/378-problem-closure.md           #378
│   ├── dual-agent-offload/
│   └── frozen contract and evidence vocabulary
├── modules/
│   ├── provider-neutral / code-intelligence / delivery modules
│   ├── codex-sdk-controller.md                            #375 runtime executor
│   ├── github-issue-dag-projection.md                     #376 forge projection
│   ├── herdr-runtime-observer.md                          #377 observer only
│   └── problem-closure-ledger.md                          #378 reconciliation
├── scripts/
│   ├── existing task/capability/scheduler/queue gates
│   ├── run_codex_sdk_worker.py                            #375
│   ├── github_issue_dag_projection.py                     #376
│   ├── herdr_runtime_observer.py                          #377
│   ├── check_problem_closure.py                           #378
│   └── render_problem_closure.py                          #378 human projection
└── tests/
    ├── existing structural/causal/matched-task controls
    ├── codex_sdk_controller_selftest.py                   #375
    ├── github_issue_dag_selftest.py                       #376
    ├── herdr_observer_selftest.py                         #377
    └── problem_closure_selftest.py                        #378
```

`tests/run-all.sh` is the shared deterministic convergence gate. It validates the new schemas and executes all four dedicated selftests; it intentionally does **not** pass `--execute` to the Codex adapter, `--apply` to the GitHub projection, or invoke a live Herdr/provider lane.

## Primary orchestration State Machine

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ CAPABILITY_PLAN_COMPILED
→ CAPABILITY_PLAN_ASSERTED
→ CONTEXT_ADMITTED
→ TASK_DAG_COMPILED
→ TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_ASSERTED
→ DELIVERY_HANDOFF
→ HUMAN_ADMIT_REQUIRED
```

Failure/control states include stale attempts, lease expiry, retryable/terminal failure, cancellation, supersession, straggler detach, authority block, semantic conflict, non-decomposable task, and duplicate suppression. A state declared only in a schema or fixture is not runtime evidence.

## Codex control-plane extension State Machine

The provider-neutral State Machine above remains authoritative. The trigger-selected #375–#378 adapters refine only the execution/projection/evidence portions:

```text
TASK_DAG_ASSERTED
→ GITHUB_PROJECTION_COMPILED                     #376
→ REMOTE_READBACK_REQUIRED
→ READY_WAVE_COMPUTED
→ SESSION_PACKET_COMPILED                        #375
→ ISOLATED_WORKTREE_BOUND
→ CODEX_THREAD_STARTED | COMPATIBLE_THREAD_RESUMED
→ ATTEMPT_EXECUTED
→ STRUCTURED_RESULT_COLLECTED
→ CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
→ HERDR_OBSERVATION_OPTIONAL                     #377
→ INDEPENDENT_SHADOW_REVIEW
→ PROBLEM_CLOSURE_RECOMPUTED                     #378
→ NEXT_WAVE | LOCAL_HANDOFF | HUMAN_ADMIT_REQUIRED
```

Authority stays separated:

```text
Tech Lead core       semantic decomposition, dual DAG, leases, convergence
Codex SDK adapter    one bounded execution attempt; never acceptance/merge authority
GitHub DAG adapter   durable completion-edge projection; never semantic truth alone
Herdr adapter        process/worktree/session observation; DONE_CANDIDATE only
closure ledger       typed source→problem→evidence reconciliation; no UI-state laundering
Shadow               independent findings/evidence ceiling; never second writer
Human/repo policy    semantic conflict, merge, release, promotion, rollback
```

## Control-plane DAG and convergence

The current implementation program is a real sibling fan-out, not a serial Stack:

```text
main
├── #375 / PR #451  Codex SDK runtime adapter         SIBLING
├── #376 / PR #452  GitHub Issue DAG projection      SIBLING
├── #377 / PR #453  Herdr runtime observer           SIBLING
├── #378 / PR #454  problem-closure ledger           SIBLING
└── PR #380         documentation foundation         SIBLING
       ↓ exact STATIC_ADMITTED bytes only
#379                 CONVERGENCE
       ↓ shared run-all / README / AGENTS / Git Town / traceability
independent Shadow + exact-head CI
       ↓
HUMAN_ADMIT_REQUIRED
```

The #379 integration subject is intentionally multi-parent: its Git ancestry records the exact sibling heads it consumes. That makes convergence causality inspectable without pretending one sibling is another sibling's parent. A later implementation may use `TRUE_CHILD` only when it actually consumes named unmerged parent bytes.

## Local Handoff Execution Queue State Machine

When a valid next step requires a local host, signed-in carrier, installed tool, device, provider credential, real worktree, Git Town, Forgejo, or another runtime unavailable in the current session:

```text
DELIVERY_HANDOFF or explicit runtime boundary
→ LOCAL_HANDOFF_REQUIRED
→ LOCAL_QUEUE_ASSERTED
→ ACTIVE_ITEM_BOUND
→ RUNTIME_LANE_EXECUTED
→ RECEIPT_ASSERTED
    ├── ITEM_COMPLETED
    │     └── NEXT_ITEM_SELECTED or QUEUE_COMPLETED
    └── ITEM_BLOCKED
          └── preserve receipt + stop/Human handoff
```

A valid queue has exactly one `ACTIVE` item, immutable subject identity, concrete bounded commands, durable receipt requirements, fail-closed exits, and explicit next-item routing. The queue is a continuation contract, not a claim that execution happened.

## Task and branch DAG

```text
contract/interface freeze
├─ path-disjoint implementation sibling A
├─ path-disjoint implementation sibling B
├─ matched tournament replicas for one locked output contract
└─ independent verifier/negative-control leaves
      ↓ verified results only
one convergence owner
      ↓ local + global objective oracles
optional true Stack child only when unmerged parent bytes are consumed
      ↓ delivery or Local Handoff Queue
Human/local-runtime authority
```

False edges are rejected. Path-disjoint work remains siblings. A dependent convergence attempt rebinds its base at lease time to the verified integrated prerequisites; independent candidates retain the common frozen base so comparison remains fair.

## End-to-end data flow

```text
Issue / PRD / PDF / article
→ source identity + exact location where applicable
→ task contract and immutable interface/test anchors
→ current-source readback
→ true task DAG + start/completion readiness edges
→ optional GitHub Issue Dependency projection + exact remote readback
→ ready wave
→ isolated worktree/session attempts
→ Codex runtime result or another admitted executor result
→ independent source/diff/test readback
→ optional Herdr identity/state observation
→ independent Shadow review
→ typed implementation/verification receipts
→ problem-closure recomputation
→ convergence from verified prerequisite bytes
→ frozen global-objective oracle
→ delivery handoff / next wave
    ├── current runtime can continue
    └── local/runtime-only evidence remains → asserted Local Handoff Queue
→ Human Admit
```

`code-graph-rag` is intentionally not an active dependency. A consumer may retain old files for migration/audit, but the task contract assertion rejects it as a runtime provider.

## Evidence ceilings for #375–#379

```text
Codex SDK adapter bytes + selftest          deterministic/static only
Codex SDK live thread/turn                  NOT_EXERCISED until exact runtime receipt
GitHub dependency projection checker        deterministic/static only
GitHub remote dependency mutation/readback  NOT_EXERCISED until explicit live receipt
Herdr observer checker/fallback              deterministic/static only
Herdr live process/worktree observation      NOT_EXERCISED until runtime receipt
problem-closure schema/checker/renderer       deterministic/local consistency only
real article/PDF/provider claim closure       evidence-dependent
#379 shared convergence docs/tests            route + deterministic convergence only
merge/release                                HUMAN_ADMIT_REQUIRED
```

A workflow green state proves only the workflow's exact subject and denominator. It cannot convert a static adapter into live provider evidence.

## Golden refactor proof

The proof-carrying refactor line is:

```text
PR #308  deterministic task/capability reachability,
         receipt-gated causal repair, and Local Handoff Queue contract
└─ PR #315 production-shaped hermetic real-task proof,
           restacked onto the current causal handoff runtime
   └─ PR #323 generalized proof contract and registry
      └─ PR #324 Agent routes and directory State Machines/DAG/data flow
         └─ PR #325 molecular Stack/traceability convergence
```

Frozen treatments:

```text
A  OLD_MONOLITH              a01f53592cda98f61b413b4467afa96356fb4ef7
B0 REFACTOR_AS_LANDED        8b2da7443aff7a9f53412b5af280048203bbd5e9
B1 REACHABILITY_REPAIRED     51c3fd81749598957f2b993c4d31c3b4c8c277c1
B2 CAUSAL_DAG_REPAIRED       current owner SKILL blob bound by registry
```

Matched deterministic result:

```text
A/B1/B2 functional output       PASS and byte-equivalent
B0                               BLOCKED_DISPATCH_ROUTE_ABSENT
B2 task/schema/semantic gates    PASS
B2 capability receipt causality  PASS
parallel worktree processes      PASS on hermetic subject
checkpoint/retry/tournament      PASS on hermetic subject
global objective and cleanup     PASS on hermetic subject
Local Handoff Queue mechanism    contract/selftest evidence only
live model/provider quality      NOT_EXERCISED
Git Town/Forgejo delivery        NOT_EXERCISED
merge                            HUMAN_ADMIT_REQUIRED
```

The proof is registered by `skill-refactor-proof-loop`; its implementation remains here and is not copied into the generalized Skill.

## Remaining evidence DAG

```text
#231 live scheduler receipts
├─ #232 independent Shadow/global objective
├─ #256 exact-subject code-intelligence/executor adapters
└─ #234 real Git Town/dual-forge delivery
      ↓ matched subjects
#312 Phase 2 live A/B
      ↓ external review
Human merge/release admission
```

The #375–#378 live lanes remain additional independent evidence work even after their static mechanisms converge. They are separately owned evidence lanes, not artificial Stack children.

## Tech Lead + Shadow closure responsibility

This Skill owns the plan, task/capability DAG, writer/path/resource leases, Worker admission, convergence owner and Local Handoff Queue. The independent Shadow is not another Worker and must not edit the Tech Lead's branch silently.

```text
Tech Lead result
→ independent procedural-shadow-runtime review on the same immutable subject
→ requirement applicability
→ source/contract/runtime contradictions
→ local task versus global objective
→ evidence ceiling and denominator
→ HOLD / REJECT / ELIGIBLE_FOR_HUMAN_ADMIT
```

A Tech Lead local PASS is not a global-objective PASS. A static or hermetic proof is not a live model/provider/runtime proof. When the current runtime cannot execute the next proof, emit one asserted queue bound to one immutable subject; do not guess host commands or mutate an old epoch after the accepted subject changes.

Relation vocabulary:

```text
SIBLING             path-disjoint work
TRUE_CHILD          named unmerged byte dependency
CONVERGENCE         one shared-index/integration owner
PROCESS_DEPENDENCY  ordering without Git ancestry
EXTERNAL_EVIDENCE   independent receipt lane, no Stack paths
HISTORICAL          admitted/forensic prior subject, not current state authority
```

The full portable audit is in [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md). The current Codex control-plane trace is [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md).

## Local verification

```bash
python3 scripts/check_task_contract_schema.py --selftest
python3 scripts/assert_task_contract.py \
  --contract references/example-stack-contract.json \
  --receipt /tmp/agentic-tech-lead-receipt.json
python3 scripts/assert_local_handoff_queue.py \
  --queue references/example-local-handoff-queue.json --selftest
python3 tests/codex_sdk_controller_selftest.py
python3 tests/github_issue_dag_selftest.py
python3 tests/herdr_observer_selftest.py
python3 tests/problem_closure_selftest.py
python3 tests/real_task_ab.py
sh tests/run-all.sh
```

A local or CI PASS validates only the named subject and evidence layer. Provider installation, index freshness, live Codex/Herdr/GitHub mutation, real source closure, real queue execution, Git Town/Forgejo delivery, merge, release, and production remain separate.
