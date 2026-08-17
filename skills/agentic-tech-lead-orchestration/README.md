# `agentic-tech-lead-orchestration`

Portable contract-first orchestration for turning one large coding request into a dependency-aware branch team and, when the current session reaches a real host/runtime boundary, a zero-context Local Handoff Execution Queue. `SKILL.md` owns the method; `references/` owns host-neutral contracts; `modules/` contains trigger-selected provider/runtime/delivery interpretations; `scripts/` and `tests/` own executable assertions and falsifiers.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. task, capability and scheduler schemas under [`references/`](references/README.md)
4. when local/runtime-only evidence remains, `references/local-handoff-queue.schema.json` and the example queue
5. [`modules/README.md`](modules/README.md), then only selected modules
6. [`scripts/README.md`](scripts/README.md)
7. [`tests/README.md`](tests/README.md)
8. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) and its golden registry
9. exact issue, PR base/head, workflow and receipt subjects

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
│   ├── task-contract.schema.json
│   ├── capability-plan.schema.json
│   ├── capability-receipts.schema.json
│   ├── scheduler-lifecycle.schema.json
│   ├── local-handoff-queue.schema.json
│   ├── example-local-handoff-queue.json
│   ├── prompt/task examples and causal maps
│   └── frozen contract and evidence vocabulary
├── modules/
│   ├── domain-profile.md
│   ├── deterministic-code-intelligence.md
│   ├── semantic-intent-anchor.md
│   ├── agent-executor.md
│   ├── vector-store.md
│   ├── tournament-mode.md
│   └── stacked-delivery.md
├── scripts/
│   ├── task shape and semantic gates
│   ├── capability causal-DAG gate
│   ├── reachability and core-boundary gates
│   ├── scheduler lifecycle validation
│   └── Local Handoff Queue shape/semantic assertion
└── tests/
    ├── structural/reachability A/B
    ├── capability, scheduler and queue mutation controls
    ├── frozen historical treatments
    └── production-shaped matched real-task A/B
```

The executable mechanism index is generated from current bytes:

```bash
python3 ../../scripts/check_skill_entry_routes.py \
  --skill agentic-tech-lead-orchestration --print-index
```

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
Issue / PRD / PDF
→ task contract and immutable interface/test anchors
→ optional semantic intent candidates
→ current-source readback
→ admitted deterministic graph/structural context
→ true task DAG + path/resource leases
→ isolated worktree/process attempts
→ bounded checkpoint/retry/self-heal
→ independent local oracles
→ tournament comparison with complete denominator
→ convergence from verified prerequisite bytes
→ frozen global-objective oracle
→ delivery handoff
    ├── current runtime can continue
    │     → optional Stack/delivery receipts
    └── local/runtime-only evidence remains
          → asserted Local Handoff Queue
          → local/runtime lane
          → durable receipt
          → next queue item or blocked Human handoff
→ Human Admit
```

`code-graph-rag` is intentionally not an active dependency. A consumer may retain old files for migration/audit, but the task contract assertion rejects it as a runtime provider.

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

These issues are separately owned evidence lanes, not artificial Stack children.

## Local verification

```bash
python3 scripts/check_task_contract_schema.py --selftest
python3 scripts/assert_task_contract.py \
  --contract references/example-stack-contract.json \
  --receipt /tmp/agentic-tech-lead-receipt.json
python3 scripts/assert_local_handoff_queue.py \
  --queue references/example-local-handoff-queue.json
python3 scripts/assert_local_handoff_queue.py \
  --queue references/example-local-handoff-queue.json --selftest
python3 tests/real_task_ab.py
sh tests/run-all.sh
```

A local or CI PASS validates only the named subject and evidence layer. Provider installation, index freshness, real model behavior, real queue execution, Git Town/Forgejo delivery, merge, release, and production remain separate.
