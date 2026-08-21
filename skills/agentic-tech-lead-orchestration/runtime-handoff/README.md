# Agentic Tech Lead runtime handoff

This directory turns the current Tech Lead/Shadow review into three independent Local Handoff Execution Queues. The queues are siblings because they own different runtime/source planes. They are not serialized for presentation convenience.

## Directory map

```text
runtime-handoff/
├── AGENTS.md
│   └── queue admission, subject-mutation, privacy, writer, and exit laws
├── README.md
│   └── current State Machines, DAG, data flow, commands, and evidence ceilings
├── codex-v2-local-handoff-queue.json
│   └── #508 durable result carrier + executor provenance + strict result schema
├── herdr-local-handoff-queue.json
│   └── #466 real managed Herdr lifecycle and clean terminal receipt
└── source-evidence-local-handoff-queue.json
    └── #512 immutable Issue/Article/PDF/PRD input → #467 compiler → existing closure ledger
```

## Shared subject

```text
repository  ed3c/skills-shared
commit      249abc47847f8295b1c75c9d4c84457c5126fd89
tree        a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback    d5993267e03b217dcdab9702dab0400ab03df860
```

## State Machines

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

The current queue stops at #508 because #508 changes the subject required by #464.

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

## Data flow and durable outputs

```text
issue + exact admitted subject
→ queue semantic assertion
→ capability/materialization preflight
→ bounded command contract
→ execution
→ durable reduced receipt
→ owning checker/controller
→ Shadow same-subject readback
→ issue update
→ next queue or Human boundary
```

Receipt destinations are under `data/handoff/`; that path is a contract, not proof the file exists.

## Local invocation

From a clean checkout of `249abc47847f8295b1c75c9d4c84457c5126fd89`:

```bash
python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/codex-v2-local-handoff-queue.json

python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/herdr-local-handoff-queue.json

python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py \
  --queue skills/agentic-tech-lead-orchestration/runtime-handoff/source-evidence-local-handoff-queue.json
```

Then execute only the ACTIVE item whose required capabilities are present. Do not advance another queue implicitly.

## Current evidence

```text
Codex result-tree binder             PASS / MERGED via #507
Codex durable replay/provenance      PASS / CLOSED_DETERMINISTICALLY via #508 (PR #516);
                                        receipt data/handoff/codex-v2/issue-508-result-carrier-receipt.json
fresh Codex v2 live acceptance       NOT_EXERCISED / #464; queue recompile required against
                                        129f53c23a3ab15354763167b25bddc45f724c00 (subject-mutation law)
Herdr real process detection         EXERCISED_PARTIALLY
Herdr terminal clean lifecycle       NOT_EXERCISED / blocker RECLASSIFIED (PR #516) from host-permission
                                        to herdr-0.8.0 AgentInfo API-contract mismatch (no observation
                                        timestamp/process identity/cleanup facts); sample_count 0
source compiler method               COMPLETED_DETERMINISTICALLY / #467 CLOSED
Issue/Article/PDF/PRD truth          EVIDENCE_DEPENDENT / #512 OPEN; first immutable packet (GitHub
                                        issue #435) EXECUTED via PR #516, dispositions OPEN x2 / NOT_APPLICABLE x1
merge/release/production             HUMAN / NOT_PERFORMED
```
