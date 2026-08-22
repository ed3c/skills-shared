# Agentic Tech Lead runtime handoff

This directory turns current Tech Lead/Shadow reviews into independent Local Handoff Execution Queues. Queue ordering is semantic: unrelated runtime/source planes stay siblings; a successor is serialized only when its exact subject depends on a predecessor.

## Directory map

```text
runtime-handoff/
├── AGENTS.md
│   └── queue admission, subject-mutation, privacy, writer, and exit laws
├── README.md
│   └── current State Machines, DAG, data flow, commands, and evidence ceilings
├── codex-v2-local-handoff-queue.json
│   └── #508 durable result carrier + executor provenance + strict result schema
├── codex-v2-live-464-local-handoff-queue.json
│   └── #464 fresh signed-in Codex v2 live run + Shadow — compiled by the #464 wave against its
│       merged implementation head (a distinct subject from #508's now-closed queue)
├── herdr-local-handoff-queue.json
│   └── #466 real managed Herdr lifecycle and clean terminal receipt
├── source-evidence-local-handoff-queue.json
│   └── #512 immutable Issue/Article/PDF/PRD input → #467 compiler → existing closure ledger
├── git-at-any-scale-local-handoff-queue.json
│   └── #512/#531 immutable source-packet materialization for the git-at-any-scale article claims
└── spatial-407-local-handoff-queue.json
    ├── ACTIVE: #407/#408/#409/#410 provenance-compliant publication rebuild
    └── BLOCKED_BY_PREDECESSOR: #411 independent live Shadow case-delta canary
```

## Subject groups

The original Wave-3 continuation queues bind:

```text
repository  ed3c/skills-shared
commit      249abc47847f8295b1c75c9d4c84457c5126fd89
tree        a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback    d5993267e03b217dcdab9702dab0400ab03df860
```

The Spatial #407 publication queue is a separate mutable-program handoff and binds the semantic source candidate recorded inside `spatial-407-local-handoff-queue.json`. Its rollback is the admitted `main` observed when that queue was compiled. Before local execution, re-read current `main` and PR #412; if either required subject moved, recompile rather than applying a stale queue.

## State Machines

### Spatial #407 publication → live Shadow

```text
#408/#409/#410_SOURCE_IMPLEMENTATION_GREEN
→ CURRENT_MAIN_RECONCILED
→ NORMAL_EXACT_HEAD_SUITES_GREEN
→ SKILL_EVAL_COMMIT_PROVENANCE_RED
→ LOCAL_PROVENANCE_REBUILD_ACTIVE
→ COMPLIANT_MACHINE_IDENTITY_AND_TRAILERS
→ EXACT_SEMANTIC_TREE_REBUILT_ON_CURRENT_MAIN
→ SKILL_SUITES
→ SHARED_SKILLS_INFRA
→ SKILL_EVAL_CONTRACT
→ GIT_TOWN_WORKER
→ READY_FOR_HUMAN_MAIN_ADMIT
→ MERGED_ON_MAIN
→ STATIC_CHILD_ISSUES_CLOSEABLE
→ RECOMPILE_OR_ADVANCE_LIVE_SUBJECT
→ #411_INDEPENDENT_BUILDER_SHADOW_CANARY
→ SEMANTIC_PARITY_DELTA_OBSERVED
→ OWNING_ORACLE_READBACK
→ LIVE_SHADOW_CANARY_PASS | HOLD | FAIL
```

The current GitHub connector history is retained as first-red provenance evidence. Do not add rewritable PR commits to `known_unclassified`, do not move `enforced_from`, do not relabel machine work as Human, and do not weaken `check_commit_roles.py`.

### Codex v2 hardening

```text
#505_FALSE_PASS_EXPOSED
→ #507_RESULT_TREE_BINDER_MERGED
→ #508_DURABLE_CARRIER_DESIGN_BOUND
→ RESULT_OBJECT_RETAINED_BY_EXPLICIT_CARRIER
→ EXECUTOR_PROVENANCE_BOUND
→ STRICT_WORKER_RESULT_SCHEMA_PASS
→ INDEPENDENT_REPLAY_AFTER_ORIGIN_CLEANUP
→ #508_PASS
→ NEW_SUBJECT_ADMITTED
→ RECOMPILE_LOCAL_QUEUE
→ #464_FRESH_SIGNED_IN_V2_RUN
→ CONTROLLER_SOURCE_DIFF_TEST_READBACK
→ INDEPENDENT_SHADOW
→ VERIFIED_LIVE | HOLD | REJECT
```

The current Codex queue stops at #508 because #508 changes the subject required by #464.

### Herdr lifecycle

```text
EXACT_SCRATCH_HOME_AND_WORKTREE_BOUND
→ MANAGED_AGENT_STARTED
→ STABLE_WORKSPACE_PANE_PID_START_SESSION
→ BOUNDED_LIFECYCLE_SAMPLES
→ NONTERMINAL_LIVENESS_ASSERTED
→ TERMINAL_STATE_OBSERVED
→ CLEANUP_AND_ZERO_RESIDUE
→ CONTROLLER_READBACK
→ INDEPENDENT_SHADOW
→ LIVE_HERDR_LIFECYCLE_PASS | BLOCKED_RECEIPT
```

A manual `report-agent` fallback cannot manufacture the terminal branch. Host permission denial remains a blocked receipt, not PASS.

### Source evidence

```text
#467_COMPILER_METHOD_COMPLETED
→ #512_IMMUTABLE_SOURCE_IDENTITY_AND_LOCATION
→ CLAIM_TEXT_AND_DIGEST
→ EXACT_REPOSITORY_COMMIT_TREE
→ COMPLETE_SOURCE_DENOMINATOR
→ COMPILE_SOURCE_CLAIMS_WITH_#467
→ EXISTING_PROBLEM_CLOSURE_CHECKER
→ SOURCE_BOUND_RECEIPT
→ APPLICABILITY_AND_IMPLEMENTATION_EVIDENCE_SEPARATE
→ SHADOW
→ OPEN | IMPLEMENTED_UNVERIFIED | VERIFIED_LOCAL | VERIFIED_LIVE | NOT_APPLICABLE
```

Compiler PASS proves binding, not truth. #467 remains closed as the method owner; #512 owns real source packets.

## Task/process DAG

```text
#407 program
├─ #408 static ICPG contract/checker/evals            SOURCE_IMPLEMENTATION_CLOSED
├─ #409 static Shadow case-delta contract             SOURCE_IMPLEMENTATION_CLOSED
├─ #410 Tech Lead + Molecular ownership gate          SOURCE_IMPLEMENTATION_CLOSED
│        ↓ shared publication/provenance predecessor
└─ Local queue: spatial-407-provenance-rebuild        ACTIVE
         ↓ admitted main subject
   #411 live independent Shadow canary                BLOCKED_BY_PREDECESSOR

#507 MERGED
  ↓
#508 ACTIVE ──subject changes──> new #464 queue
                                 ↓
                              #464 live v2

#466 ACTIVE external runtime sibling
#467 COMPLETE source compiler method
  ↓ method dependency only
#512 ACTIVE source-evidence sibling
#465 COMPLETE historical remote receipt
```

The Spatial static issues are not closed merely because source suites are green. They require equivalent bytes admitted on `main`. #411 is not a Git child of the static implementation unless a future harness literally consumes unmerged parent bytes; its current relationship is process/external evidence.

## Data flow and durable outputs

```text
issue / source + exact subject
→ queue semantic assertion
→ capability/materialization preflight
→ bounded command contract
→ execution or publication rebuild
→ durable reduced receipt
→ owning checker/controller
→ Shadow same-subject readback
→ issue update
→ next queue or Human boundary
```

For Spatial:

```text
Prompt / source behavior
→ ICPG digest + REQUIRED_CASE denominator
→ Tech Lead case ownership
→ Molecular implementation atoms
→ deterministic oracles
→ publication provenance gate
→ admitted main
→ independent live Shadow #411
```

Receipt destinations are under `data/handoff/`; that path is a contract, not proof the file exists.

## Local invocation

Validate only the queue whose exact subject is current:

```bash
python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/codex-v2-local-handoff-queue.json

python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/herdr-local-handoff-queue.json

python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/source-evidence-local-handoff-queue.json

python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json
```

Then execute only the `ACTIVE` item whose required capabilities and subject are present. Do not advance another queue implicitly.

## Current evidence

```text
Spatial #408/#409/#410 source implementation    PASS / candidate only
Spatial normal exact-head suites                PASS
Spatial Skill Eval commit provenance            FAIL / LOCAL_HANDOFF_REQUIRED
Spatial main admission                          NOT_PERFORMED
Spatial #411 live independent Shadow             NOT_EXERCISED
Codex result-tree binder             PASS / MERGED via #507
Codex durable replay/provenance      PASS / CLOSED_DETERMINISTICALLY via #508 (PR #516);
                                        receipt data/handoff/codex-v2/issue-508-result-carrier-receipt.json
fresh Codex v2 live acceptance       NOT_EXERCISED / #464; queue recompile required against
                                        current main (re-derive via git rev-parse main; do not
                                        bind to 129f53c23a3ab15354763167b25bddc45f724c00 — stale,
                                        main has since advanced to 28f3947 then 5341885 then
                                        674cfe1, PR #577)
Herdr real process detection         EXERCISED_PARTIALLY
Herdr terminal clean lifecycle       NOT_EXERCISED / blocker RECLASSIFIED (PR #516) from host-permission
                                        to herdr-0.8.0 AgentInfo API-contract mismatch (no observation
                                        timestamp/process identity/cleanup facts); sample_count 0
source compiler method               COMPLETED_DETERMINISTICALLY / #467 CLOSED
Issue/Article/PDF/PRD truth          EVIDENCE_DEPENDENT / #512 OPEN; first immutable packet (GitHub
                                        issue #435) EXECUTED via PR #516, dispositions OPEN x2 / NOT_APPLICABLE x1
merge/release/production             HUMAN / NOT_PERFORMED except separately admitted subjects
```
