# Molecular terminal index — Tech Lead + Shadow review 2026-08-20, PR/issue states restamped 2026-08-22

This README is the durable molecular index for the closure audit. Current GitHub metadata remains authoritative for mutable PRs. The topology and relation edges below were compiled on 2026-08-20 against the historical subject in the next section; the PR/issue terminal states carry the 2026-08-22 readback.

## Repository subjects

Current admitted subject — 2026-08-22 readback:

```text
main      5341885f26b5e8e7baf5087a4d661e324f878242
tree      a18e12507f9e621efd5354f58384eded1f1e2a9a
rollback  9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c
```

Subject this index was compiled against — 2026-08-20, HISTORICAL; also the PR #516 execution subject of the Wave-3 continuation queues. Each Local Handoff queue binds its own subject; read the queue file rather than inheriting this one:

```text
main      249abc47847f8295b1c75c9d4c84457c5126fd89
tree      a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback  d5993267e03b217dcdab9702dab0400ab03df860
```

## Relation vocabulary

```text
SIBLING             path/resource-disjoint implementation
TRUE_CHILD          consumes named unmerged parent bytes/contracts
CONVERGENCE         one owner consumes selected sibling/child artifacts and shared paths
PROCESS_DEPENDENCY  ordering without Git ancestry
EXTERNAL_EVIDENCE   independent runtime/provider/source receipt lane
HISTORICAL          admitted, rejected, superseded, or closed-unmerged prior subject
```

A source PR can be `CLOSED_UNMERGED / CONSUMED` while its exact bytes are present through another admitted convergence. That is not an individual merge.

## Wave-3 / Codex v2 index

```text
#455 / #379 Wave-2 control plane             MERGED / HUMAN_ADMITTED
├─ #464 / PR #469 Codex live carrier         CLOSED_UNMERGED / CONSUMED
├─ #465 / PR #470 GitHub canary carrier      CLOSED_UNMERGED / CONSUMED
├─ #466 / PR #471 Herdr lifecycle carrier    CLOSED_UNMERGED / CONSUMED
└─ #467 / PR #472 source compiler            CLOSED_UNMERGED / CONSUMED; ISSUE COMPLETED
          ↓
#468 / PR #480 Wave-3 convergence             MERGED / HUMAN_ADMITTED
          ↓
#497 / PR #504 runtime-readback repairs       MERGED
          ↓
#505 / PR #507 result-tree false-PASS repair  MERGED
          ↓
#508 durable carrier/provenance/schema        CLOSED / COMPLETED (via PR #516)
          ↓ subject-mutation boundary
#464 fresh signed-in v2 run                   PROCESS_DEPENDENCY / OPEN

#512 immutable Issue/Article/PDF/PRD evidence EXTERNAL_EVIDENCE / OPEN
  └─ consumes completed #467 compiler method; does not reopen #467
```

| Atom | Issue/PR | State | Evidence ceiling |
|---|---|---|---|
| `W3-CODEX` | #464/#469 | carrier consumed; issue open | first live run observed, Shadow partial |
| `W3-GH` | #465/#470 | live lane complete | exact one-edge remote canary only; no semantic authority |
| `W3-HERDR` | #466/#471 | open | real process detection partial; terminal clean receipt absent |
| `W3-SOURCE-COMPILER` | #467/#472 | issue completed; carrier consumed | deterministic source binding/compiler only |
| `W3-SOURCE-EVIDENCE` | #512 | open external-evidence successor | Issue/Article/PDF/PRD truth/applicability/verification remain packet-specific |
| `W3-X` | #468/#480 | merged | static/deterministic infrastructure admission |
| `C2-K` | #505/#507 | merged | deterministic result-tree binder, `1/16` |
| `C2-DURABLE` | #508 | closed/completed via PR #516 | durable replay receipt `PASS`; live #464 acceptance remains a separate `NOT_EXERCISED` lane |

The active Codex handoff queue is [`codex-v2-local-handoff-queue.json`](../../../agentic-tech-lead-orchestration/runtime-handoff/codex-v2-local-handoff-queue.json). It ends after #508 because its output changes the subject required for #464. Source evidence uses [`source-evidence-local-handoff-queue.json`](../../../agentic-tech-lead-orchestration/runtime-handoff/source-evidence-local-handoff-queue.json) and is owned by #512.

## Repository entropy index

```text
C #387
├─ K #388 → E #390 ──┐
└─ A #389 ───────────┤
                     X #391
                       ↓
                     D #403 / PR #404
                       ↓ rebuilt/current-main landing
                     UCR #398 / PR #477
```

| Atom | PR | Terminal state |
|---|---:|---|
| C | #387 | `CLOSED_UNMERGED / CONSUMED` |
| K | #388 | `CLOSED_UNMERGED / CONSUMED` |
| A | #389 | `CLOSED_UNMERGED / CONSUMED` |
| E | #390 | `CLOSED_UNMERGED / CONSUMED` |
| X | #391 | `CLOSED_UNMERGED / SUPERSEDED_BY_CURRENT_MAIN_ADMISSION` |
| D | #404 | `CLOSE_AFTER_CURRENT_DOC_CANDIDATE_LANDS` |
| Admission | #477 | `MERGED / HUMAN_ADMITTED` |

The method and CI/registry routes are on main. General safe deletion, unseen-domain coverage, real Git Town execution, release, and production remain separate evidence lanes.

## Formerly held Draft stacks — all terminal at the 2026-08-22 readback

No PR in this section is open. Terminal classifications come from `skills/agentic-tech-lead-orchestration/references/closure-audit/issue-568.json:16-24`; the landing subject for the whole set is PR #573, commit `9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c`, tree `c17678166cee2adba2f92f6099011ec52716ece7`.

### Spatial ICPG → knowledge graph

```text
#412 Spatial ICPG                 CLOSED_UNMERGED / SUPERSEDED_BY_#419
  └─ #419 Knowledge Graph bridge  CLOSED_UNMERGED / CONSUMED  (TRUE_CHILD relation retained)
       └─ #420 machine contracts  CLOSED_UNMERGED / CONSUMED  (TRUE_CHILD relation retained)
            └─ #450 delivery binding CLOSED_UNMERGED / CONSUMED  (TRUE_CHILD relation retained)
```

The TRUE_CHILD edges are historically correct and are the point of this index: each child consumed named unmerged parent bytes at its fork epoch. What changed is the carrier, not the relation. The stated HOLD reasons are resolved or superseded: #412's provenance blocker was falsified (`988a4e7` carve-out, gate GREEN on #412's own range) and its bytes landed through the replayed #419; #420 was re-parented onto that replay (restoring `assert_case_obligations.py`) and consumed; #450 was consumed through the same chain. #411 live Shadow monitoring is a separate lane and remains OPEN.

### Human-led Agentic Engineering

```text
#395 method                  MERGED (auto-merged by reachability at the #573 landing)
  └─ #396 trace/index child  CLOSED_UNMERGED / CONSUMED
```

### Productization preflight

```text
#434 preparation artifacts  CLOSED_UNMERGED (2026-08-21)
  └─ #436 provenance rebuild ISSUE CLOSED (2026-08-22 readback)
```

The preflight checker passed on its old subject. Productization implementation and user/paid/provider evidence are still not present; #436's closure is an issue-state fact, not a Productization evidence claim.

## Publication State Machine

```text
ISSUE_CONTRACTED
→ PATH_AND_BRANCH_LEASED
→ IMPLEMENTATION
→ LOCAL_CONTROLS
→ CURRENT_MAIN_RECONCILIATION
→ EXACT_HEAD_HOSTED_GATES
→ SHADOW_SAME_SUBJECT
→ READY_FOR_HUMAN_ADMIT
→ MERGED
```

Alternative terminals:

```text
CLOSED_UNMERGED / CONSUMED
CLOSED_UNMERGED / SUPERSEDED
DRAFT / HOLD
REJECTED
```

## Data flow

```text
Issue/claim
→ exact subject + relation
→ implementation atom
→ verifier/falsifier
→ convergence owner
→ hosted gates
→ Shadow
→ Human admission or terminal non-merge classification
→ runtime/source Local Handoff when required
```

## Current evidence ceilings

```text
#507 deterministic repair        MERGED
#465 live GitHub canary          VERIFIED_LIVE_REMOTE_CANARY_ONLY
#464 Codex v2                    OPEN / predecessor #508 now CLOSED; its queue must bind the current admitted subject 5341885f
#466 Herdr                       OPEN / blocker RECLASSIFIED (PR #516) from host permission to a
                                 herdr-0.8.0 AgentInfo API-contract mismatch: no observation timestamp,
                                 process identity or cleanup facts; receipt sample_count 0
#467 source compiler             COMPLETED_DETERMINISTICALLY
#512 source truth execution      EVIDENCE_DEPENDENT / OPEN
entropy shared method            ADMITTED
formerly held Draft stacks       TERMINAL — see the section above; no open PR remains in this index
merge/release for held stacks    NOT_PERFORMED beyond the #573 landing
```
