# AGENTS.md — Agentic Tech Lead integration contract

Read this file before changing `agentic-tech-lead-orchestration`, its golden proof, its Local Handoff Execution Queue, the Codex control-plane adapters, or any consumer binding that claims to implement it.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. this `AGENTS.md`;
3. this directory's `README.md`;
4. `SKILL.md` — provider-neutral core law;
5. `references/task-contract.schema.json`, `references/capability-plan.schema.json`, `references/capability-receipts.schema.json`, and `references/scheduler-lifecycle.schema.json`;
6. when issues #375–#379, Codex SDK, GitHub Issue Dependencies, Herdr, or problem closure are in scope, read `../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`, then the exact `references/execution-packets/375-*.md`–`378-*.md` packet and only the selected modules/contracts;
7. when a host/runtime boundary exists, `references/local-handoff-queue.schema.json`, `references/example-local-handoff-queue.json`, and `scripts/assert_local_handoff_queue.py`;
8. `modules/domain-profile.md`, then only modules whose frozen trigger matches;
9. `scripts/README.md`, executable checkers, and `tests/README.md`;
10. `../skill-refactor-proof-loop/README.md` and its golden registry;
11. exact issue/PR base/head/workflow/evidence subjects;
12. `../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md` before any completion claim.

Do not use chat history, branch names, module presence, provider installation, issue state, terminal `done`, or a previous successful SHA as current runtime evidence.

## Current integration truth

The existing proof-carrying Tech Lead line remains authoritative for the portable core:

```text
PR #308 task/schema/semantic/capability reachability + Local Handoff contract
→ PR #315 matched production-shaped hermetic real-task A/B
→ PR #323 generalized refactor-proof contract and registry
→ PR #324 Agent routes + directory State Machines/DAG/data flow
→ PR #325 Molecular Stack + traceability convergence
```

The Codex control-plane extension is a separate sibling/convergence program:

```text
#375 / PR #451  Codex SDK controller/session adapter      STATIC_ADMITTED / SIBLING
#376 / PR #452  GitHub Issue DAG projection              STATIC_ADMITTED / SIBLING
#377 / PR #453  Herdr runtime observer                   STATIC_ADMITTED / SIBLING
#378 / PR #454  problem-closure ledger                   STATIC_ADMITTED / SIBLING
PR #380         traceability/document routing foundation  DOCUMENTATION SIBLING
       ↓ exact consumed bytes
#379             one multi-parent convergence owner       CONVERGENCE
```

`#379` is allowed to consume those exact unmerged sibling bytes because convergence is its job. That does **not** make #375→#376→#377→#378 a serial Stack. A `TRUE_CHILD` edge requires a named byte/contract dependency between the actual child and parent.

Current evidence ceilings remain:

```text
Codex SDK mechanism                    IMPLEMENTED_ON_CONVERGENCE_SUBJECT
Codex SDK live thread/turn             NOT_EXERCISED
GitHub DAG mechanism                   IMPLEMENTED_ON_CONVERGENCE_SUBJECT
GitHub remote dependency mutation      NOT_EXERCISED
Herdr observer mechanism               IMPLEMENTED_ON_CONVERGENCE_SUBJECT
Herdr live observation                 NOT_EXERCISED
problem-closure mechanism              IMPLEMENTED_ON_CONVERGENCE_SUBJECT
real article/PDF/provider closure      EVIDENCE_DEPENDENT
merge/release                          HUMAN_ADMIT_REQUIRED
```

A shared deterministic suite may raise a mechanism from `STATIC_ADMITTED` to deterministic/exact-head evidence for the convergence subject. It cannot raise any live lane.

## Writer, path, and attempt rules

- One Worker owns one branch, linked worktree, attempt lineage, and disjoint path/resource lease.
- Tournament replicas may share one candidate output path only within the same frozen tournament contract and isolated worktrees.
- Independent path-disjoint siblings do not become a linear Stack for scheduling convenience.
- A convergence Worker starts from the state containing verified prerequisite bytes, not the original plan base.
- Contracts, acceptance oracles, frozen treatment fixtures, owning eval definitions, global-objective assertions, queue schemas, and evidence ceilings are read-only to implementation Workers.
- Failed, stale, blocked, cancelled, superseded, losing, and refused attempts remain in the denominator.
- An Agent may not weaken tests, change interface locks, erase a predecessor, rewrite a receipt, or delete an unmanaged remote dependency to make an implementation pass.

## Codex control-plane authority boundaries

```text
codex-sdk-controller
  may start/resume one compatible SDK thread and return a bounded runtime receipt
  may not plan the DAG, admit a result, merge, release, or persist credentials/private reasoning

github-issue-dag-projection
  may project validated completion-readiness edges and read them back
  may add missing managed edges only on explicit apply
  may not delete extra unmanaged blockers or treat GitHub metadata as semantic truth

herdr-runtime-observer
  may observe workspace/pane/process/session/worktree identity
  DONE_CANDIDATE is not completion
  absence degrades to direct Codex SDK + git worktree, not to failure or success

problem-closure-ledger
  may recompute closure from typed source/implementation/verification/receipt/Shadow evidence
  issue close, PR merge, navigation links, prose, and workflow UI are not verification lanes
```

Every provider-specific adapter remains trigger-selected. Presence of its file or binary does not activate it.

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
  portable provider-neutral task/capability/Worker/convergence/handoff law

references/
  task/capability/scheduler/queue contracts plus trigger-selected control-plane contracts,
  examples and frozen zero-context execution packets

modules/
  trigger-selected provider/runtime/projection/tournament/vector/delivery interpretations

scripts/
  deterministic shape/semantics/reachability/capability/scheduler/queue assertions plus
  bounded Codex/GitHub-DAG/Herdr/problem-closure adapters/checkers

tests/
  structural/causal/scheduler/queue/matched-task falsifiers plus four control-plane selftests

issues/PRs
  exact implementation, publication and evidence subjects
```

`tests/run-all.sh` owns the shared deterministic denominator once a convergence subject contains all required files. Conditional "if file exists" skips are forbidden for required gates.

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

For the GitHub-DAG path, remote `blockedBy` readback must agree with the managed projection before dispatch eligibility is claimed. For Codex, a returned turn is still followed by independent source/diff/test readback. For Herdr, `DONE_CANDIDATE` is followed by the same controller readback. Problem closure is recomputed only from typed admitted evidence.

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
#375          live Codex SDK execution receipt remains open
#376          live GitHub dependency mutation/readback + remote preflight remains open
#377          live Herdr stale/orphan/residue observation remains open
#378          real source/provider claim closure remains evidence-dependent
#379          shared deterministic convergence + route/index completeness
```

These are independent evidence/process lanes except where an explicit convergence subject consumes their bytes. Semantic conflict resolution, provider activation, publication, merge, release, promotion, and rollback remain Human/trusted-operator boundaries.

## Completion report

Report changed paths, affected states/edges, frozen inputs, protected old strengths, task/session/queue subjects, local/global oracle results, denominator, process/worktree/lease cleanup, exact PR/DAG/workflow state, every `NOT_EXERCISED` or evidence-dependent lane, rollback subject, and Human Admit still required.
