# `agentic-tech-lead-orchestration`

Portable contract-first orchestration for turning one large coding request into a dependency-aware Worker DAG, exact-subject evidence, one convergence owner and—when the next proof requires another host/runtime—a zero-context Local Handoff. `SKILL.md` owns provider-neutral law; `references/` owns host-neutral contracts; `modules/` are trigger-selected interpretations; `scripts/` and `tests/` own executable mechanisms and falsifiers.

Current repository-level closure/evidence state: [`../../docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](../../docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md).

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. this README
4. [`references/README.md`](references/README.md) and the exact task/capability/session/receipt contract in scope
5. only trigger-selected [`modules/`](modules/README.md)
6. [`scripts/README.md`](scripts/README.md)
7. [`tests/README.md`](tests/README.md)
8. current public-state trace and exact issue/PR/workflow/runtime subject
9. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md) before global completion
10. [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md) for branch/Molecular delivery

Historical Wave-2/Wave-3 design/failure detail lives in `docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE*.md` and `WAVE3_*.md`. Current GitHub/runtime subjects win if historical wording drifts.

## Directory map → State Machine ownership

```text
skills/agentic-tech-lead-orchestration/
├── AGENTS.md
│   └── local read order, writer/queue leases, authority and completion packet
├── README.md
│   └── current directory ownership, State Machines, DAG, data flow and handoff
├── SKILL.md
│   └── portable request → task/capability DAG → Worker → convergence → handoff law
├── references/
│   ├── task/capability/scheduler/closure contracts
│   ├── contracts/
│   │   ├── codex-session-manifest.schema.json
│   │   ├── codex-worker-result.schema.json
│   │   ├── codex-live-acceptance-receipt-v2.schema.json     #505/#507 current live acceptance
│   │   ├── github-issue-dag-receipt.schema.json             #376
│   │   ├── github-ready-wave.schema.json                    #376
│   │   ├── github-dag-live-canary-receipt.schema.json       #465
│   │   ├── herdr-observer-receipt.schema.json               #377
│   │   ├── herdr-lifecycle-receipt.schema.json              #466
│   │   └── problem-closure.schema.json                      #378/#467
│   ├── execution-packets/                                   immutable/historical worker packets
│   ├── dual-agent-offload/                                  portable local/cloud method contracts
│   ├── wave3-live-handoff-queue.json                        historical exact-subject epoch
│   └── public-main-local-handoff-queue-2026-08-20.json      current local epoch
├── modules/
│   ├── codex-sdk-controller.md                              bounded SDK execution interpretation
│   ├── github-issue-dag-projection.md                       GitHub projection; not semantic DAG truth
│   ├── herdr-runtime-observer.md                            observer only
│   ├── problem-closure-ledger.md                            evidence reconciliation
│   └── other provider/code-intelligence/delivery modules loaded only by trigger
├── scripts/
│   ├── task/capability/scheduler/queue gates
│   ├── run_codex_sdk_worker.py                              Worker + immutable result-tree materialization
│   ├── compile_codex_live_acceptance.py                     controller v2 binder
│   ├── github_issue_dag_projection.py                       generic projection/readback
│   ├── github_issue_dag_live_canary.py                      bounded reversible remote fixture carrier
│   ├── herdr_runtime_observer.py / collect_herdr_lifecycle.py
│   ├── compile_source_claims.py
│   ├── check_problem_closure.py
│   └── render_problem_closure.py                            human projection only
└── tests/
    ├── task/capability/scheduler/matched-task controls
    ├── codex_sdk_controller_selftest.py                     4/14 static SDK mechanics
    ├── codex_live_acceptance_selftest.py                    current v2 1/16 acceptance controls
    ├── github_issue_dag_selftest.py                         current 7/23 producer controls
    ├── github_issue_dag_live_canary_selftest.py             REST live carrier controls
    ├── herdr_observer_selftest.py / herdr_lifecycle_selftest.py
    ├── problem_closure_selftest.py / source compiler controls
    └── run-all.sh                                           shared deterministic convergence gate
```

Directory presence is not evidence that a runtime lane executed.

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

Failure/control states remain explicit: stale attempt, lease expiry, retryable/terminal failure, cancellation, supersession, straggler detach, authority block, semantic conflict, non-decomposable task, duplicate suppression, stale consumed head, residue and historical convergence invalidation.

## Current control-plane DAG

Wave-2 mechanism parents are closed/admitted historical lineage; mutable live ownership moved to Wave-3 successors:

```text
Wave-2 static mechanism lineage
  #375 Codex SDK      ─────→ #464 signed-in Codex live acceptance
  #376 GitHub DAG     ─────→ #465 bounded GitHub remote canary (COMPLETED)
  #377 Herdr observer ─────→ #466 live Herdr lifecycle
  #378 closure ledger ─────→ #467 source/provider evidence

#376 separately retains generic GitHub Development-sidebar residual.
```

Repository convergence history:

```text
#375/#376/#377/#378 SIBLINGS
        ↓ exact selected bytes
#379 / PR #455                     CONVERGENCE / MERGED
        ↓
#464/#465/#466/#467 Wave-3 SIBLINGS at fork
        ↓ exact selected bytes
#468 / PR #480 + #484              CONVERGENCE / POST-MERGE / MERGED
        ↓
#465 hosted GitHub lane             EXTERNAL_EVIDENCE / CLOSED
#485 / PR #503                      live-owner convergence / MERGED
#497 / PR #504                      GitHub producer repair / MERGED
#505 / PR #507                      Codex v2 repair / MERGED
```

These are semantic relations, not a fake serial Git stack.

## Codex v2 result-tree acceptance State Machine

#505/#507 repaired a false-PASS boundary. A Worker `changed_files` list is no longer trusted by assertion alone.

```text
TASK_NODE_READY
→ SESSION_PACKET_COMPILED
→ EXACT_WORKTREE_SUBJECT_BOUND
→ CODEX_THREAD_STARTED | COMPATIBLE_THREAD_RESUMED
→ ATTEMPT_EXECUTED
→ LEASE_READBACK_PASS
→ RESULT_TREE_MATERIALIZED
     private temporary GIT_INDEX_FILE
     branch/index left untouched
→ BASE_TREE_READBACK
     git rev-parse base_sha^{tree}
→ RESULT_TREE_DIFF_READBACK
     exact base→result tree changed-file denominator
→ STRUCTURED_RESULT_BOUND
→ CONTROLLER_SOURCE_DIFF_TEST_READBACK
→ codex-live-acceptance-receipt/v2
→ INDEPENDENT_SHADOW_REVIEW
→ RESULT_ADMITTED | BLOCKED | RETRYABLE
```

Required v2 receipt states:

```text
sdk_execution         EXERCISED
lease_readback        PASS
result_tree_readback  PASS
source_diff_readback  PASS
tests_readback        PASS
acceptance_state      LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE
shadow_review_required true
evidence_ceiling      LIVE_EXECUTION_OBSERVED_SHADOW_PENDING
```

A pre-#507 v1 receipt cannot be promoted to this v2 PASS. The current v2 live lane is `NOT_EXERCISED` until a fresh signed-in run on the exact required subject exists.

## GitHub DAG / remote-effect State Machine

Generic GitHub projection remains a projection of an already asserted semantic DAG:

```text
TASK_DAG_ASSERTED
→ GITHUB_PROJECTION_COMPILED
→ REMOTE_PREFLIGHT_BOUND
→ ISSUE_STATE / REPOSITORY_IDENTITY READBACK
→ completion-edge mutation when explicitly authorized
→ COMPLETE REMOTE READBACK
→ READY_WAVE_COMPUTED
→ PROJECTION_RECEIPT
```

Current generic producer controls are `7 positive / 23 mutations` after #497/#504. The producer parses GitHub's `LinkedIssueConnection` (`nodes` + `totalCount`) fail-closed; legacy bare-list, duplicate, truncation/mismatch, non-int and cross-repository shapes are rejected.

The dedicated #465 hosted canary separately proved one real reversible public fixture edge:

```text
before=[]
→ add blocker #486
→ readback=[486]
→ remove owned edge
→ cleanup=[]
→ receipt sha256 da227e94215a1b28a9e550546242c8a482bd718f7b35d67f159ccaa95f23efe5
```

Evidence ceiling: `REMOTE_CANARY_EDGE_ONLY`, `semantic_authority=false`. It does not close #376's distinct generic Development sidebar link/unlink surface.

## Herdr State Machine

```text
WORKTREE_ALLOCATED
→ HERDR_WORKSPACE_BOUND
→ AGENT_PROCESS_OBSERVED
→ RUNNING | BLOCKED | IDLE | DONE_CANDIDATE
→ identity / PID-start / freshness / liveness / cleanup / residue checks
→ CONTROLLER_READBACK_REQUIRED
→ RECEIPT_VERIFIED
```

`DONE_CANDIDATE` is advisory only. Static observer/lifecycle controls do not prove a real Herdr process. #466 remains independent and `NOT_EXERCISED` until a live runtime receipt exists.

## Source / problem closure State Machine

```text
SOURCE_BOUND
→ CLAIM_EXTRACTED
→ APPLICABILITY_DECIDED
→ REPO_SUBJECT_BOUND
→ TASK/ISSUE LINEAGE LINKED
→ IMPLEMENTATION_EVIDENCE_BOUND
→ VERIFICATION_EVIDENCE_BOUND
→ SHADOW_RECONCILED
→ OPEN | PARTIAL | IMPLEMENTED_UNVERIFIED | VERIFIED_LOCAL |
  VERIFIED_LIVE | NOT_APPLICABLE | HUMAN_ADMIT_REQUIRED
```

Article/PDF/PRD input requires immutable source identity + exact location. Compiler/checker PASS proves binding/consistency only, not source truth. #467 owns stronger source/provider evidence.

## Task / branch DAG

```text
contract/interface freeze
├─ path-disjoint implementation sibling A
├─ path-disjoint implementation sibling B
├─ matched tournament replicas for one locked contract
└─ independent verifier / negative-control leaves
        ↓ verified results only
one convergence owner
        ↓ local + global objective oracles
optional TRUE_CHILD only when named unmerged parent bytes are consumed
        ↓ delivery or Local Handoff
Human / local-runtime authority
```

False edges are rejected. Start-readiness and completion-readiness are distinct.

## End-to-end data flow

```text
Issue / PRD / PDF / article
→ source identity + exact location where applicable
→ immutable repository/base/tree
→ contract and acceptance oracles
→ task/capability dual DAG
→ leases + ready wave
→ isolated Worker attempts
→ result tree / source / diff / test readback
→ optional GitHub/Herdr/source evidence lanes
→ independent Shadow
→ problem denominator recomputation
→ convergence / publication checks
→ current runtime continues OR Local Handoff
→ Human Admit where required
```

No provider/module becomes semantic task-state authority by being installed or executed.

## Current evidence ceilings

```text
Wave-2 mechanism                            ADMITTED / MERGED
Wave-3 infrastructure                      ADMITTED / MERGED
Codex SDK static mechanics                 4 / 14 deterministic
Codex v2 acceptance controls               1 / 16 deterministic; live NOT_EXERCISED
GitHub DAG producer                        7 / 23 deterministic
#465 remote canary                         PASS / REMOTE_CANARY_EDGE_ONLY
Herdr observer/lifecycle                   deterministic only; live NOT_EXERCISED
problem/source compiler                    deterministic consistency only
real article/PDF/provider truth            EVIDENCE_DEPENDENT
release / production                       NOT_PERFORMED
```

## Local Handoff Execution Queue

Old `wave3-live-handoff-queue.json` is immutable history and must not be edited to follow a new subject.

Current exact-subject queue:

[`references/public-main-local-handoff-queue-2026-08-20.json`](references/public-main-local-handoff-queue-2026-08-20.json)

```text
ACTIVE item  #464 signed-in Codex v2 acceptance
bound main   249abc47847f8295b1c75c9d4c84457c5126fd89
bound tree   a24b9b7ace6f4022967d41262ecdc704d5c11646
```

The queue is deliberately single-item. #466 is an independent local evidence lane, not a true serial child; #376 is a manual/UI residual; #467 is external source/provider evidence. They remain on owning issues rather than being falsely serialized.

## Proof-carrying historical line

The canonical refactor proof remains under [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) and [`../../docs/traceability/SKILL_REFACTOR_PROOF_STACK.md`](../../docs/traceability/SKILL_REFACTOR_PROOF_STACK.md). Historical A/B treatment facts are not duplicated here as current runtime claims.

## Local verification

```bash
python3 scripts/check_task_contract_schema.py --selftest
python3 scripts/assert_task_contract.py --contract references/example-stack-contract.json --receipt /tmp/atl-receipt.json
python3 scripts/assert_local_handoff_queue.py --queue references/public-main-local-handoff-queue-2026-08-20.json --selftest
python3 tests/codex_sdk_controller_selftest.py
python3 tests/codex_live_acceptance_selftest.py
python3 tests/github_issue_dag_selftest.py
python3 tests/github_issue_dag_live_canary_selftest.py
python3 tests/herdr_observer_selftest.py
python3 tests/herdr_lifecycle_selftest.py
python3 tests/problem_closure_selftest.py
sh tests/run-all.sh
```

A local/CI PASS validates only its exact subject and evidence layer. Provider availability, live Codex/Herdr, manual Development UI, source truth, Git Town/Forgejo delivery, merge, release and production remain separately evidenced.