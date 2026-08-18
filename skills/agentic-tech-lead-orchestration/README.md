# `agentic-tech-lead-orchestration`

Portable contract-first orchestration for turning an admitted system/case contract into a dependency-aware branch team and, when the current session reaches a real host/runtime boundary, a zero-context Local Handoff Execution Queue. `SKILL.md` owns the method; `references/` owns host-neutral contracts; `modules/` contains trigger-selected provider/runtime/delivery interpretations; `scripts/` and `tests/` own executable assertions and falsifiers.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. task, capability and scheduler schemas under [`references/`](references/README.md)
4. when Spatial Loop produced an ICPG, read `../spatial-loop-systems-engineering/references/intent-case-proof-graph.md` and bind its exact digest/required-case denominator into the task contract
5. when local/runtime-only evidence remains, `references/local-handoff-queue.schema.json`
6. [`modules/README.md`](modules/README.md), then only selected modules
7. [`scripts/README.md`](scripts/README.md)
8. [`tests/README.md`](tests/README.md)
9. exact issue, PR base/head, workflow and receipt subjects
10. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md) before a global completion claim

## Directory map → State Machine ownership

```text
skills/agentic-tech-lead-orchestration/
├── AGENTS.md                    Agent read order / authority boundary
├── README.md                    topology / State Machines / DAG / data flow
├── SKILL.md                     portable orchestration law
├── references/
│   ├── task-contract.schema.json
│   │     └── exact subject + case_obligations + branch ownership + acceptance
│   ├── example-stack-contract.json
│   ├── capability-plan.schema.json / capability-receipts.schema.json
│   ├── scheduler-lifecycle.schema.json
│   └── local-handoff-queue.schema.json
├── modules/                     trigger-selected capabilities
├── scripts/
│   ├── check_task_contract_schema.py
│   ├── assert_task_contract.py  ← case denominator/ownership hard gate
│   ├── assert_capability_dag.py
│   └── lifecycle/handoff gates
└── tests/
    ├── selftest.py              ← orphan/duplicate/stale case controls
    └── run-all.sh               owning suite
```

## Primary orchestration State Machine

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ CASE_GRAPH_BOUND_OR_EXPLICITLY_NOT_APPLICABLE
→ CASE_OBLIGATIONS_FROZEN
→ CAPABILITY_PLAN_COMPILED
→ CAPABILITY_PLAN_ASSERTED
→ CONTEXT_ADMITTED
→ TASK_DAG_COMPILED
→ TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ CASE_OWNERSHIP_ASSERTED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_AND_CASE_COVERAGE_ASSERTED
→ DELIVERY_HANDOFF
→ HUMAN_ADMIT_REQUIRED
```

## ICPG → Tech Lead DAG

The Tech Lead does not decompose directly from a short prompt when an admitted ICPG exists.

```text
User prompt / source behavior
→ Spatial Loop ICPG
   ├── frozen graph digest
   ├── required-case denominator
   └── invariants / oracles
→ task-contract.case_obligations
   ├── required_case_ids
   ├── branch_case_owners
   └── convergence_owner
→ true task DAG
   ├── path-disjoint sibling Workers
   ├── true child only when unmerged bytes/contracts are consumed
   └── one convergence owner
→ independent result/oracle verification
→ global case-denominator reconciliation
→ delivery / Local Handoff / Human Admit
```

Hard failures before Worker admission:

```text
stale/non-sha case graph identity
required case without owner
required case with multiple owners
owner names an undeclared branch
ownership map invents a case outside denominator
missing/invalid convergence owner
local task success presented as global case closure
```

Case dependencies and Git ancestry are separate. A semantic relation between two cases does not make their implementation branches parent/child. Git parentage exists only when the child consumes unmerged parent bytes/contracts/state.

## End-to-end data flow

```text
Issue / PRD / PDF / short prompt
→ Spatial Loop intent + source-behavior + use/edge-case expansion
→ ICPG exact digest + required denominator
→ Tech Lead task contract
→ capability context + source readback
→ true task DAG + branch→case ownership + path/resource leases
→ isolated attempts
→ independent local oracles
→ candidate comparison
→ one convergence owner
→ global objective + case coverage assertion
→ delivery handoff
    ├── current runtime can continue
    └── physical/local evidence remains → Local Handoff Queue
→ Human Admit
```

`code-graph-rag` remains intentionally inactive. A consumer may retain historical files for migration/audit, but the task contract rejects it as a runtime provider.

## #407 ICPG preparation line

```text
#408 / PR #412   Spatial case contract + checker + semantic-loss mutations
        ↓ consumes case contract
#410            Tech Lead task contract gains exact ICPG denominator/ownership
        ├── task-contract schema
        ├── semantic assertion
        ├── orphan/duplicate/stale controls
        └── README route

#409            Shadow monitor/system-prompt/spec-packet projection
#411            live continuous Shadow canary (external evidence lane)
```

#409 is not automatically a Git child of #410; #411 is a live evidence/process dependency, not a source-code ancestry edge.

## Evidence boundary

```text
ICPG task-contract shape                         IMPLEMENTED_ON_PR_412
required-case denominator/owner semantic gate    IMPLEMENTED_ON_PR_412
orphan/duplicate/stale ownership controls         IMPLEMENTED_ON_PR_412
live Worker execution using ICPG                  NOT_EXERCISED
live continuous Shadow case monitoring            NOT_EXERCISED / #411
Git Town physical stack execution                 NOT_EXERCISED
merge/release/promotion                           HUMAN_ADMIT_REQUIRED
```

A fixture PASS proves the gate can discriminate its planted defects. It does not prove a live Worker consumed the ICPG or that all real-world unknown cases were discovered.
