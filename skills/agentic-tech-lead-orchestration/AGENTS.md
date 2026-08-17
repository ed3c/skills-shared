# AGENTS.md — Agentic Tech Lead integration contract

Read this file before changing `agentic-tech-lead-orchestration`, its golden proof, or any consumer binding that claims to implement it.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. this `AGENTS.md`;
3. this directory's `README.md`;
4. `SKILL.md`;
5. `references/task-contract.schema.json`, `references/capability-plan.schema.json`, `references/capability-receipts.schema.json`, and `references/scheduler-lifecycle.schema.json`;
6. `modules/domain-profile.md`, then only modules whose frozen trigger matches;
7. `scripts/README.md`, executable checkers, and `tests/README.md`;
8. `../skill-refactor-proof-loop/README.md` and its golden registry;
9. exact issue/PR base/head/workflow/evidence subjects.

Do not use chat history, branch names, module presence, provider installation, or issue state as runtime evidence.

## Current integration truth

```text
PR #308  task/schema/semantic/capability reachability and causal-DAG repair
└─ PR #315 matched production-shaped hermetic real-task A/B
   └─ PR #323 generalized refactor-proof contract and golden registry
```

The matched deterministic task establishes:

```text
A_OLD_MONOLITH          PASS
B0_REFACTOR_AS_LANDED   BLOCKED_DISPATCH_ROUTE_ABSENT
B1_REACHABILITY_REPAIRED PASS
B2_CAUSAL_DAG_REPAIRED  PASS

A/B1/B2 final bytes      equivalent
B2 causal/evidence proof strongest
live model/provider uplift NOT_EXERCISED
Git Town/Forgejo delivery  NOT_EXERCISED
merge authority            false
```

## Writer and path rules

- One Worker owns one branch, linked worktree, attempt lineage, and disjoint path/resource lease.
- Tournament replicas may share the same candidate output path only within one frozen tournament contract and isolated worktrees.
- Independent siblings do not become a linear Stack for scheduling convenience.
- A convergence Worker starts from the state containing verified prerequisite bytes, not the original plan base.
- Contracts, acceptance oracles, frozen treatment fixtures, owning eval definitions, and evidence ceilings are read-only to implementation Workers.
- Failed, stale, blocked, cancelled, superseded, and losing candidates remain in the denominator.

## Directory ownership

```text
SKILL.md      portable task/capability/Worker/convergence law
references/   task, capability, scheduler and prompt contracts
modules/      trigger-selected provider/runtime/delivery interpretations
scripts/      deterministic shape, semantics, reachability and lifecycle assertions
tests/        structural, causal, scheduler and matched real-task falsifiers
issues/PRs    exact implementation, publication and evidence subjects
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

## Remaining owners

```text
#312 Phase 2  matched live model/runtime A/B
#231          live scheduler lifecycle and recovery
#232          independent Shadow/global objective
#234          real Git Town + dual-forge delivery
#256          GrepAI/SCIP/Tree-sitter/Serena/SQLite exact-subject receipts
```

Semantic conflict resolution, provider activation, publication, merge, release, promotion, and rollback remain Human/trusted-operator boundaries.

## Completion report

Report changed paths, affected states/edges, treatment and task subjects, local/global oracle results, denominator, process/worktree/lease cleanup, exact PR Stack and workflow state, every `NOT_EXERCISED` lane, rollback subject, and Human Admit still required.
