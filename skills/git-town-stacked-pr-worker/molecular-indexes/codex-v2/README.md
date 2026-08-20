# Molecular terminal index — Tech Lead + Shadow review 2026-08-20

This README is the durable molecular index for the current closure audit. Current GitHub metadata remains authoritative for mutable PRs.

## Exact current repository subject

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
└─ #467 / PR #472 source compiler            CLOSED_UNMERGED / CONSUMED
          ↓
#468 / PR #480 Wave-3 convergence             MERGED / HUMAN_ADMITTED
          ↓
#497 / PR #504 runtime-readback repairs       MERGED
          ↓
#505 / PR #507 result-tree false-PASS repair  MERGED
          ↓
#508 durable carrier/provenance/schema        ACTIVE ISSUE
          ↓ subject-mutation boundary
#464 fresh signed-in v2 run                   PROCESS_DEPENDENCY / OPEN
```

| Atom | Issue/PR | State | Evidence ceiling |
|---|---|---|---|
| `W3-CODEX` | #464/#469 | carrier consumed; issue open | first live run observed, Shadow partial |
| `W3-GH` | #465/#470 | live lane complete | exact one-edge remote canary only; no semantic authority |
| `W3-HERDR` | #466/#471 | open | real process detection partial; terminal clean receipt absent |
| `W3-SOURCE` | #467/#472 | open | source binding works; truth/provider evidence separate |
| `W3-X` | #468/#480 | merged | static/deterministic infrastructure admission |
| `C2-K` | #505/#507 | merged | deterministic result-tree binder, `1/16` |
| `C2-DURABLE` | #508 | active | `NOT_IMPLEMENTED` until independent durable replay |

The active local handoff queue is `../../agentic-tech-lead-orchestration/runtime-handoff/codex-v2-local-handoff-queue.json`. It ends after #508 because its output changes the subject required for #464.

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

## Held open Draft stacks

### Spatial ICPG → knowledge graph

```text
#412 Spatial ICPG                 DRAFT / HOLD
  └─ #419 Knowledge Graph bridge  DRAFT / TRUE_CHILD
       └─ #420 machine contracts  DRAFT / TRUE_CHILD
            └─ #450 delivery binding DRAFT / TRUE_CHILD
```

Reasons for HOLD:

- #412 current head/base moved beyond the exact-head subject quoted in its body; #411 live monitoring remains open.
- #420 is a design artifact below deterministic/runtime completion.
- #450 still requires the #448 exact-head hosted evidence and later traversal/runtime lanes.
- old green runs do not follow current-main or parent movement.

### Human-led Agentic Engineering

```text
#395 method
  └─ #396 trace/index child
```

Both remain Draft. They require a current-main rebuild, exact-head repository gates, and same-subject Shadow before any merge decision.

### Productization preflight

```text
#434 preparation artifacts  DRAFT
  └─ #436 provenance rebuild BLOCKER
```

The preflight checker passed on its old subject, but repository admission remains blocked by commit-role provenance. Productization implementation and user/paid/provider evidence are not present.

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
#464 Codex v2                    OPEN / predecessor #508
#466 Herdr                       OPEN / host permission blocker
#467 source truth                EVIDENCE_DEPENDENT
entropy shared method            ADMITTED
open Draft stacks               HOLD
merge/release for held stacks    NOT_PERFORMED
```
