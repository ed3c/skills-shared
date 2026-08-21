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
#375 / PR #451  Codex SDK controller/session adapter      SIBLING / UNMERGED CANDIDATE
#376 / PR #452  GitHub Issue DAG projection              SIBLING / UNMERGED CANDIDATE
#377 / PR #456  Herdr runtime observer v3                SIBLING / UNMERGED CANDIDATE
#378 / PR #457  problem-closure ledger v3                SIBLING / UNMERGED CANDIDATE
PR #380         traceability/document routing foundation  DOCUMENTATION SIBLING
       ↓ exact consumed candidate bytes
#379 / PR #455  one multi-parent convergence owner       CONVERGENCE CANDIDATE
```

`#379` may consume exact unmerged sibling bytes because convergence is its job. That does **not** admit or merge those siblings and does not make #375→#376→#377→#378 a serial Stack. A `TRUE_CHILD` edge requires a named byte/contract dependency between the actual child and parent.

Current selected sibling heads are read from GitHub immediately before convergence decisions. The current epoch is documented in `../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`; this router does not duplicate mutable head SHAs.

Current mechanism/evidence split:

```text
Codex SDK mechanism
  exact worktree HEAD/tree/clean preflight + writable-lease readback implemented
Codex SDK live thread/turn
  NOT_EXERCISED

GitHub DAG mechanism
  completion-edge projection + repo/default-branch/visibility + expected issue-state
  + closing-PR-reference duplicate preflight implemented
Generic development-link ownership beyond closing references
  RESIDUAL / do not overclaim from closedByPullRequestsReferences
GitHub remote dependency mutation/readback
  NOT_EXERCISED

Herdr observer mechanism
  exact Git subject + worktree/pane/workspace/PID/native-session identity
  + PID start-time + freshness/liveness + terminal cleanup/residue implemented
Herdr DONE_CANDIDATE
  advisory only; controller source/diff/test readback still required
Herdr live observation
  NOT_EXERCISED

problem-closure mechanism
  frozen denominator/source manifest + claim digest + exact repo subject
  + current/historical evidence + exact receipts + supersession validation implemented
real article/PDF/provider closure
  EVIDENCE_DEPENDENT

merge/release
  HUMAN_ADMIT_REQUIRED
```

A shared deterministic suite may prove the exact convergence mechanism. It cannot raise any live lane or convert an unmerged candidate into admitted repository truth.

## Writer, path, and attempt rules

- One Worker owns one branch, linked worktree, attempt lineage, and disjoint path/resource lease.
- Tournament replicas may share one candidate output path only within the same frozen tournament contract and isolated worktrees.
- Independent path-disjoint siblings do not become a linear Stack for scheduling convenience.
- A convergence Worker starts from the state containing the selected prerequisite bytes, not the original plan base.
- Contracts, acceptance oracles, frozen treatment fixtures, owning eval definitions, global-objective assertions, queue schemas, and evidence ceilings are read-only to implementation Workers.
- Failed, stale, blocked, cancelled, superseded, losing, refused, closed-unmerged and historical attempts remain in the denominator.
- An Agent may not weaken tests, change interface locks, erase a predecessor, rewrite a receipt, or delete an unmanaged remote dependency to make an implementation pass.
- Any selected sibling head change after convergence freezes a new epoch: re-read exact head/tree, compare changed bytes, rebind the convergence ancestry, rerun hosted gates, and supersede the earlier Shadow verdict. Never call an earlier green convergence current after one consumed parent moves.

## Codex control-plane authority boundaries

```text
codex-sdk-controller
  may start/resume one compatible SDK thread and return a bounded runtime receipt
  must bind exact 40-hex HEAD/tree and a clean worktree before execution
  must read changed paths after the turn and refuse read-only/out-of-lease mutation
  may not plan the DAG, admit a result, merge, release, or persist credentials/private reasoning

github-issue-dag-projection
  may project validated completion-readiness edges and read them back
  may bind repository visibility/default branch, expected issue state and closing PR refs
  may add missing managed edges only on explicit apply
  may not delete extra unmanaged blockers or treat GitHub metadata as semantic truth
  may not claim generic linked-PR ownership beyond the observed closing-reference surface

herdr-runtime-observer
  may observe exact worktree/pane/workspace/PID/PID-start/session identity, freshness, liveness and cleanup/residue
  stale/future observation, PID reuse, dead nonterminal process, orphan session and terminal residue fail closed
  DONE_CANDIDATE is not implementation PASS
  absence degrades to direct Codex SDK + git worktree, not to failure or success

problem-closure-ledger
  may recompute closure from a frozen source/problem denominator and typed exact-subject evidence/receipts
  SUPERSEDED remains residual and must route to an existing non-cyclic successor
  machine-local worktree paths, stale CURRENT evidence, denominator deletion and source drift fail closed
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

For the GitHub-DAG path, remote `blockedBy` readback must agree with the managed projection before dispatch eligibility is claimed. For Codex, a returned turn is followed by exact worktree/lease readback and then independent source/diff/test acceptance. For Herdr, `DONE_CANDIDATE` requires fresh identity/liveness/cleanup evidence and is followed by controller readback. Problem closure is recomputed only from the frozen denominator and typed exact-subject evidence.

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
#375          HISTORICAL static Codex mechanism lineage; live Codex ownership
              transferred to #464 by the admitted #485 transfer
#376          generic linked-PR ownership beyond closing references remains
              #376 RESIDUAL; live GitHub dependency mutation/readback
              transferred to #465 and satisfied by hosted run 32296935756
#377          HISTORICAL static Herdr observer lineage; live Herdr lifecycle
              ownership transferred to #466
#378          HISTORICAL static closure lineage; real source/provider evidence
              ownership transferred to #467
#379          shared deterministic convergence + route/index completeness
```

These are independent evidence/process lanes except where an explicit convergence subject consumes their bytes. Semantic conflict resolution, provider activation, publication, merge, release, promotion, and rollback remain Human/trusted-operator boundaries.

## Completion report

Report changed paths, affected states/edges, frozen inputs, selected/consumed parent heads, protected old strengths, task/session/queue subjects, local/global oracle results, denominator, process/worktree/lease cleanup, exact PR/DAG/workflow state, superseded convergence epochs, every `NOT_EXERCISED` or evidence-dependent lane, rollback subject, and Human Admit still required.

## Wave 3 live-evidence overlay (#464–#468)

When #464, #465, #466, #467, #468, PR #469–#473, or a live-evidence carrier is in scope, insert this route immediately after the existing Codex control-plane trace:

```text
../../docs/traceability/WAVE3_LIVE_EVIDENCE.md
→ exact current PR #469/#470/#471/#472 heads
→ scripts/compile_codex_live_acceptance.py              #464
→ scripts/github_issue_dag_live_canary.py               #465
→ scripts/collect_herdr_lifecycle.py                    #466
→ scripts/compile_source_claims.py                      #467
→ references/contracts/*live*.schema.json + source-claims-input.schema.json
→ references/wave3-live-handoff-queue.json              #468 runtime continuation
→ tests/codex_live_acceptance_selftest.py
→ tests/github_issue_dag_live_canary_selftest.py
→ tests/herdr_lifecycle_selftest.py
→ tests/source_claim_compiler_selftest.py
→ tests/run-all.sh                                      #468 single shared denominator
→ current PR #473 / workflows / receipts
```

Wave-3 DAG law:

```text
#455 / #379  TRUE_PARENT
├─ #464 / #469  TRUE_CHILD / SIBLING
├─ #465 / #470  TRUE_CHILD / SIBLING
├─ #466 / #471  TRUE_CHILD / SIBLING
└─ #467 / #472  TRUE_CHILD / SIBLING
        ↓ exact selected bytes
#468 / #473  CONVERGENCE
```

The four leaves are true children only of #455 because they consume its unmerged adapter/contracts. They are not children of one another. `#468` is the only writer for shared schemas, `run-all.sh`, Agent routes, Shadow/Git Town indexes, and Wave-3 traceability.

Wave-3 State Machine overlay:

```text
STATIC_CONTROL_PLANE_READY
→ LIVE_EVIDENCE_CARRIER_BOUND
→ EXACT_PARENT_SUBJECT_ASSERTED
→ DETERMINISTIC_CARRIER_CONTROLS_PASS
→ LIVE_RUNTIME_EXECUTION_OPTIONAL
→ CONTENT_BOUND_RECEIPT
→ CONTROLLER / SHADOW READBACK
→ SHARED_WAVE3_CONVERGENCE
→ EXACT_HEAD_HOSTED_GATES
→ LOCAL_HANDOFF_FOR_REMAINING_RUNTIME
→ READY_FOR_HUMAN_ADMIT | HOLD | REJECT
```

Current deterministic denominator must include, unconditionally:

```text
Wave 2: Codex 4/14 + GitHub DAG 7/23 + Herdr 4/18 + closure 6/22
Wave 3: Codex live 1/12 + GitHub canary 1/6 + Herdr lifecycle 2/7 + source compiler 4 kinds/11
10 Draft-2020-12 control-plane schemas
source-claims example → compiler → existing closure checker
Wave-3 Local Handoff Queue assertion
```

Evidence ceilings remain strict:

```text
public live-evidence carrier code      deterministic mechanism only
live Codex SDK/controller receipt      NOT_EXERCISED until real signed-in runtime receipt
live GitHub canary                     NOT_EXERCISED until add/readback/remove receipt
live Herdr lifecycle                   NOT_EXERCISED until real process receipt
article/PDF/PRD truth                  SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
Human Admit / merge / release          HUMAN_ADMIT_REQUIRED / NOT_PERFORMED
```

A carrier name containing `live`, a schema const such as `EXERCISED`, or a deterministic selftest can never manufacture live evidence. Only an exact runtime receipt plus required controller/Shadow readback may raise the corresponding lane.
