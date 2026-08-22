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
│   └── HISTORICAL: #508 durable result carrier + executor provenance + strict result schema
│       (subject 249abc47…; #508 is CLOSED — the lane's successor is the live-464 queue below)
├── codex-v2-live-464-local-handoff-queue.json
│   ├── ACTIVE: #464 fresh signed-in Codex v2 live run — compiled by the #464 wave against its
│   │   merged implementation head (a distinct subject from #508's now-closed queue); executed
│   │   2026-08-22, receipt verdict PASS, ceiling LIVE_EXECUTION_OBSERVED_SHADOW_PENDING
│   └── BLOCKED_BY_PREDECESSOR: #464 independent Shadow readback
├── git-at-any-scale-local-handoff-queue.json
│   ├── COMPLETE: GIT-SCALE-H0 immutable article source packet (#512)
│   ├── ACTIVE: GIT-SCALE-H1 portable hosting-assurance contract denominator (#532)
│   └── BLOCKED_BY_PREDECESSOR: H2 runtime canary (#534), H3 Shadow (#535), H4 path convergence (#536)
├── herdr-local-handoff-queue.json
│   └── ACTIVE: #466 real managed Herdr lifecycle and clean terminal receipt
│       (amended 2026-08-22 contract: named-session isolation; herdr-v3 receipt, sample_count 20,
│       ceiling LIVE_OBSERVER_LIFECYCLE_SHADOW_PENDING)
├── source-evidence-local-handoff-queue.json
│   ├── COMPLETE: #512 GITHUB_ISSUE packet (issue #435) and ARTICLE packet (Cursor git-at-any-scale)
│   └── ACTIVE: #512 next unexecuted source kind (PDF or PRD)
└── spatial-407-local-handoff-queue.json
    ├── COMPLETE: #407/#408/#409/#410 publication, achieved by an alternate route (PR #412 CLOSED unmerged)
    └── ACTIVE: #411 independent live Shadow case-delta canary
```

## Subject groups

All five queues in this directory now bind one admitted subject:

```text
repository  ed3c/skills-shared
commit      5341885f26b5e8e7baf5087a4d661e324f878242
tree        a18e12507f9e621efd5354f58384eded1f1e2a9a
rollback    9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c
```

They were previously split across `249abc47…` (Wave-3 continuation queues), `5ac05420…` (the Spatial publication candidate) and `988a4e79…` (git-at-any-scale). Those bindings are historical: the Spatial publication bytes landed by an alternate route, and the queues were recompiled against the admitted subject above. Before local execution, re-read current `main`; if the required subject moved, recompile rather than applying a stale queue.

## State Machines

### Spatial #407 publication → live Shadow

```text
#408/#409/#410_SOURCE_IMPLEMENTATION_GREEN
→ SKILL_EVAL_COMMIT_PROVENANCE_RED_ON_PR_412
→ PROVENANCE_BLOCKER_FALSIFIED           (988a4e7 carve-out; gate GREEN on PR 412's own range)
→ BYTES_LANDED_VIA_REPLAYED_#419         (PR #412 CLOSED unmerged, retained as forensic source)
→ MERGED_ON_MAIN                         (45dfac8 is an ancestor of the admitted subject)
→ STATIC_CHILD_ISSUES_CLOSEABLE
→ RECOMPILE_OR_ADVANCE_LIVE_SUBJECT
→ #411_INDEPENDENT_BUILDER_SHADOW_CANARY  ACTIVE / NOT_EXERCISED
→ SEMANTIC_PARITY_DELTA_OBSERVED
→ OWNING_ORACLE_READBACK
→ LIVE_SHADOW_CANARY_PASS | HOLD | FAIL
```

The provenance-rebuild segment is historical, not pending: its receipt is `../references/closure-audit/issue-568.json`, acceptance item `412-semantics-on-current-main-with-compliant-provenance` SATISFIED, landing PR #573 commit `9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c`. The GitHub connector history is retained as first-red provenance evidence. Do not add rewritable PR commits to `known_unclassified`, do not move `enforced_from`, do not relabel machine work as Human, and do not weaken `check_commit_roles.py`.

### git-at-any-scale portable hosting assurance

```text
#512_IMMUTABLE_ARTICLE_PACKET_BOUND      COMPLETE (864322 bytes, sha256 25f59fc6…447cab9)
→ #532_PORTABLE_CONTRACT_DENOMINATOR      ACTIVE / eleven contracts + repository registration
                                          + exact-head hosted PASS still open
→ #534_PHYSICAL_HOSTING_RUNTIME_CANARY    BLOCKED / no runtime, storage or benchmark host admitted
→ #535_INDEPENDENT_SHADOW                 BLOCKED / both review subjects absent
→ #536_SHARED_PATH_CONVERGENCE            BLOCKED / #531/#532/#534/#535 subjects not admitted
```

The `#412/#419 path-writer disposition` that used to gate #536 is discharged: both PRs are CLOSED unmerged and their bytes landed by an alternate route. A SKIPPED workflow is still not a PASS.

Actual admitted path (2026-08-22 reconciliation): the states from `SKILL_EVAL_COMMIT_PROVENANCE_RED` through `MERGED_ON_MAIN` were fulfilled by a superseding path rather than a history rewrite. Replayed carrier waves (terminal publication merge `c27f8c3`, committer `agent-macro@claude-code.invalid`) landed the #412 semantic content on `main`; the connector lineage commits (`01067581`, `5ac05420`, `32c049ca`) reached `main` as declared-owner human writes under `evals/commit-roles.json` identity rules, and the exact-head Skill Eval Contract (run 341 at `5341885f`) is green. No rewritable commit was added to `known_unclassified`, `enforced_from` did not move, and no gate was weakened. The reconciled item's exit receipt is `../references/closure-audit/issue-568.json`; `data/handoff/spatial-407/publication-provenance-receipt.json` preserves the supplementary plan-vs-actual, forbidden-promotion and adversarial-audit record. The queue has since been advanced to the #411 item by the reconciliation wave; its live canary remains `NOT_EXERCISED` and still needs a resolved command contract plus independently admitted Builder/Shadow identities.

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
└─ Local queue: spatial-407-provenance-superseded      COMPLETE (bytes landed via replayed #419)
         ↓ admitted main subject
   #411 live independent Shadow canary                ACTIVE / NOT_EXERCISED

#507 MERGED
  ↓
#508 COMPLETE ──subject changed, queue recompiled──> #464 live v2   ACTIVE

#466 ACTIVE external runtime sibling
#467 COMPLETE source compiler method
  ↓ method dependency only
#512 ACTIVE source-evidence sibling (GITHUB_ISSUE + ARTICLE kinds COMPLETE)
#465 COMPLETE historical remote receipt

#531 git-at-any-scale program
├─ GIT-SCALE-H0 / #512 immutable article packet    COMPLETE
│        ↓
├─ GIT-SCALE-H1 / #532 portable contracts          ACTIVE
│        ↓
├─ GIT-SCALE-H2 / #534 physical runtime canary     BLOCKED_BY_PREDECESSOR
│        ↓
├─ GIT-SCALE-H3 / #535 independent Shadow          BLOCKED_BY_PREDECESSOR
│        ↓
└─ GIT-SCALE-H4 / #536 shared path convergence     BLOCKED_BY_PREDECESSOR
```

The Spatial static issues are not closed merely because source suites are green; they require equivalent bytes admitted on `main`, which is now satisfied. #411 is not a Git child of the static implementation unless a future harness literally consumes unmerged parent bytes; its current relationship is process/external evidence.

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

Validate every queue in this directory (the same glob `tests/run-all.sh` uses, so
this list cannot drift out of step with the files on disk), then execute only the
one whose exact subject is current:

```bash
for queue in skills/agentic-tech-lead-orchestration/runtime-handoff/*-local-handoff-queue.json; do
  python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py --queue "$queue"
  python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py --queue "$queue" --selftest
done
```

Then execute only the `ACTIVE` item whose required capabilities and subject are present. Do not advance another queue implicitly.

## Current evidence

```text
Spatial #408/#409/#410 source implementation    PASS / bytes admitted on main 5341885f
Spatial normal exact-head suites                PASS / Skill Suites run 597 on that exact head
Spatial Skill Eval commit provenance            BLOCKER_FALSIFIED (988a4e7 carve-out; gate GREEN on
                                                PR #412's own range) — PR #412 CLOSED unmerged;
                                                Skill Eval Contract run 341 GREEN on 5341885f
Spatial main admission                          PERFORMED / 45dfac8 and 91df786 are ancestors of
                                                5341885f, first contained by 9fe3c6d (PR #573);
                                                supplementary receipt
                                                data/handoff/spatial-407/publication-provenance-receipt.json
Spatial #411 live independent Shadow             NOT_EXERCISED
Codex result-tree binder             PASS / MERGED via #507
Codex durable replay/provenance      PASS / CLOSED_DETERMINISTICALLY via #508 (PR #516);
                                        receipt data/handoff/codex-v2/issue-508-result-carrier-receipt.json
fresh Codex v2 live acceptance       EXECUTED_SHADOW_PENDING / #464; the live run landed 2026-08-22
                                        via codex-v2-live-464-local-handoff-queue.json (receipt
                                        data/handoff/codex-v2/issue-464-live-run-receipt.json,
                                        verdict PASS, ceiling LIVE_EXECUTION_OBSERVED_SHADOW_PENDING).
                                        The historical codex-v2-local-handoff-queue.json (#508,
                                        subject 249abc47…) is superseded by that successor file.
                                        Bind any new lane work to current main re-derived via
                                        git rev-parse — never to 129f53c23a3… (stale)
Herdr real process detection         EXERCISED_PARTIALLY
Herdr terminal clean lifecycle       NOT_EXERCISED / blocker RECLASSIFIED (PR #516) from host-permission
                                        to herdr-0.8.0 AgentInfo API-contract mismatch (no observation
                                        timestamp/process identity/cleanup facts); sample_count 0
source compiler method               COMPLETED_DETERMINISTICALLY / #467 CLOSED
Issue/Article/PDF/PRD truth          EVIDENCE_DEPENDENT / #512 OPEN; first immutable packet (GitHub
                                        issue #435) EXECUTED via PR #516, dispositions OPEN x2 / NOT_APPLICABLE x1
merge/release/production             HUMAN / NOT_PERFORMED except separately admitted subjects
```
