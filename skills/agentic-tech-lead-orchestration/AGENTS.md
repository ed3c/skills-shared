# AGENTS.md — Agentic Tech Lead integration contract

Read this file before changing `agentic-tech-lead-orchestration`, its golden proof, its Local Handoff Execution Queue, or any consumer binding that claims to implement it.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. this `AGENTS.md`;
3. this directory's `README.md`;
4. `SKILL.md`;
5. `references/task-contract.schema.json`, `references/capability-plan.schema.json`, `references/capability-receipts.schema.json`, and `references/scheduler-lifecycle.schema.json`;
6. when a host/runtime boundary exists, `references/local-handoff-queue.schema.json`, `references/example-local-handoff-queue.json`, and `scripts/assert_local_handoff_queue.py`;
7. `modules/domain-profile.md`, then only modules whose frozen trigger matches;
8. `scripts/README.md`, executable checkers, and `tests/README.md`;
9. `../skill-refactor-proof-loop/README.md` and its golden registry;
10. exact issue/PR base/head/workflow/evidence subjects.

Do not use chat history, branch names, module presence, provider installation, issue state, or a previous successful SHA as current runtime evidence.

## Current integration truth

```text
PR #308  task/schema/semantic/capability reachability,
         causal-DAG repair, and Local Handoff Queue contract
└─ PR #315 matched production-shaped hermetic real-task A/B,
           restacked onto the current causal handoff runtime
   └─ PR #323 generalized refactor-proof contract and golden registry
      └─ PR #324 Agent routes, directory State Machines, DAG and data flow
         └─ PR #325 molecular Stack and traceability convergence
```

The matched deterministic task establishes:

```text
A_OLD_MONOLITH            PASS
B0_REFACTOR_AS_LANDED     BLOCKED_DISPATCH_ROUTE_ABSENT
B1_REACHABILITY_REPAIRED  PASS
B2_CAUSAL_DAG_REPAIRED    PASS
B3_CLOSURE_LAWS_BOUND     PASS

A/B1/B2/B3 final bytes       equivalent
B3 causal/evidence proof     strongest
live model/provider uplift   NOT_EXERCISED
Git Town/Forgejo delivery    NOT_EXERCISED
merge authority              false
```

The Local Handoff Queue adds an executable continuation contract for host/runtime-only work. It does not upgrade the hermetic proof into live runtime evidence.

## Behavioral A/B lane (#316)

The deterministic proof above compares bodies by what their mechanisms admit. It cannot say whether the repaired body changes what a live model orchestrates, which is why every one of its reports ends in `live model/provider uplift NOT_EXERCISED`.

`scripts/run_behavioral_ab.py` is the separate lane that can. Its rubric and both arm blobs were frozen in `evals/behavioral-ab-preregistration.json` and committed before any cell ran; the results and per-cell receipts live in `evals/`. Read the result document for the current numbers rather than restating them here — a summary copied into prose is the first thing to go stale.

Three boundaries hold whatever that document says:

- it is one host, one model, one consumer subject and one repetition count, and the verdict is forced to `INSUFFICIENT_EVIDENCE` below the preregistered repetition minimum;
- linked worktrees and physical Worker processes are closed by `tests/real_task_ab.py`, not by this lane, which runs one host process per cell and claims nothing more;
- provider adapters, Git Town, Forgejo, publication and merge stay in their own lanes, unchanged and still `NOT_EXERCISED`.

Three rubric checks did not discriminate in the first run: `candidates_share_base` and `lease_disjoint` on the tournament shape, `edge_implies_dependency` on the DAG shape. Every arm failed all three in every repetition, for the same reason in both arms — both bodies produce a topology the frozen rubric did not anticipate, where candidates depend on an immutable acceptance-oracle node and the convergence owner writes paths its candidates also wrote. That is a fact about the rubric, not about either treatment, and it is recorded rather than repaired: editing a check after seeing which way it fell is the exact move the preregistration exists to prevent. A future run may widen those three checks only in a new preregistration, frozen before its own cells.

## Writer, path, and attempt rules

- One Worker owns one branch, linked worktree, attempt lineage, and disjoint path/resource lease.
- Tournament replicas may share one candidate output path only within the same frozen tournament contract and isolated worktrees.
- Independent path-disjoint siblings do not become a linear Stack for scheduling convenience.
- A convergence Worker starts from the state containing verified prerequisite bytes, not the original plan base.
- Contracts, acceptance oracles, frozen treatment fixtures, owning eval definitions, global-objective assertions, queue schemas, and evidence ceilings are read-only to implementation Workers.
- Failed, stale, blocked, cancelled, superseded, losing, and refused attempts remain in the denominator.
- An Agent may not weaken tests, change interface locks, erase a predecessor, or rewrite a receipt to make a failed implementation pass.

## Local Handoff Queue rules

A handoff queue is not prose or a TODO list. It is admitted only when it binds:

```text
exact repository/branch/commit/tree subject
exactly one ACTIVE item
concrete runtime lane and bounded command surface
input and predecessor receipt identities
allowed/read-only/forbidden paths
wall-clock/output/retry/cost bounds
required durable receipt and source readback
fail-closed exit classification
explicit next-item routing
cleanup and Human authority
```

Consumer issue IDs, repository commands, provider names, credentials, local paths, sessions, and device identities remain consumer/runtime-owned. They must not be generalized into the portable core.

Allowed queue progress is:

```text
QUEUE_ASSERTED
→ ACTIVE_ITEM_BOUND
→ RUNTIME_LANE_EXECUTED
→ RECEIPT_ASSERTED
    ├── ITEM_COMPLETED → next item or queue complete
    └── ITEM_BLOCKED   → preserve evidence and stop
```

A static queue example proves only packet mechanics. It cannot launch a Worker, prove a local tool, or satisfy provider/Git Town/Forgejo evidence.

## Directory ownership

```text
SKILL.md
  portable task/capability/Worker/convergence/handoff law

references/
  task, capability, scheduler, prompt and Local Handoff Queue schemas/examples

modules/
  trigger-selected provider/runtime/tournament/vector/delivery interpretations

scripts/
  deterministic shape, semantics, reachability, capability, scheduler and queue assertions

tests/
  structural, causal, scheduler, queue and matched real-task falsifiers

issues/PRs
  exact implementation, publication and evidence subjects
```

## Required gates before Worker admission

```text
TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ CAPABILITY_PLAN_ASSERTED
→ predecessor receipts consumed
→ exact task/repository/module/attempt identity bound
→ Worker admitted
```

A fixture receipt may prove the mechanism in fixture mode. It cannot advance a live runtime state.

## Required gates before Local Handoff execution

```text
DELIVERY_HANDOFF or other explicit runtime boundary
→ LOCAL_HANDOFF_REQUIRED
→ queue schema asserted
→ queue semantics asserted
→ exact ACTIVE item selected
→ runtime/environment evidence rebound
→ external/local execution
→ durable receipt asserted
```

A queue cannot infer the runtime, command availability, secret access, provider health, or user session.

## Remaining evidence owners

```text
#312 Phase 2  matched live model/runtime A/B
#231          live scheduler lifecycle and recovery
#232          independent Shadow/global objective
#234          real Git Town + dual-forge delivery
#256          GrepAI/SCIP/Tree-sitter/Serena/SQLite exact-subject receipts
```

These are independent evidence lanes, not artificial Git children. Semantic conflict resolution, provider activation, publication, merge, release, promotion, and rollback remain Human/trusted-operator boundaries.

## Completion report

Report changed paths, affected states/edges, frozen treatments, protected old strengths, task and queue subjects, local/global oracle results, denominator, process/worktree/lease/queue cleanup, exact PR Stack and workflow state, every `NOT_EXERCISED` lane, rollback subject, and Human Admit still required.
