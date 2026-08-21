# AGENTS.md — Git at any scale closure route

This directory is the zero-context entry for the Cursor **Git at any scale** audit. It is a traceability and assurance-control surface inside `skills-shared`; it is not a Git hosting implementation.

## Mandatory read order

1. Repository root `AGENTS.md` and current `main` commit/tree.
2. This file.
3. `README.md` in this directory.
4. Issue #531 and the exact child issue being executed: #532, #534, #535, or #536.
5. For C1, read Draft PR #542 and `skills/git-hosting-scale-assurance/{AGENTS.md,README.md,SKILL.md}` on its exact head.
6. `source-claims.json` and `problem-closure-ledger.json`.
7. `skills/git-town-stacked-pr-worker/molecular-indexes/git-at-any-scale/README.md`.
8. `skills/agentic-tech-lead-orchestration/runtime-handoff/git-at-any-scale-local-handoff-queue.json`.
9. Current GitHub PR/open-writer state and exact workflow receipts before any state transition.

## Current admission epoch — 2026-08-21

```text
main                                   988a4e790af6a8bee31fd14e00e52a6e944b9f17
D1 preparation                         PR #539 / OPEN / DRAFT / mergeable-clean
C1 implementation candidate            PR #542 / OPEN / DRAFT / mergeable-clean
C1 exact head                           196a75ac04f6ad2c9a6e50b0645d71fea9bf43e3
C1 hosted workflow arrival              Shared Skills Infra = SKIPPED
C1 issue-contract denominator           INCOMPLETE
L1 physical runtime                     NOT_EXERCISED
S1 terminal independent Shadow          NOT_EXERCISED
```

Do not close #532 or merge #542 merely because the branch is mergeable. #532 requires separate operation-history/durability/ref/read/cache/gossip/compaction/recovery/benchmark contracts and the positive/hollow/concurrent/fault fixture denominator stated in the issue. The current candidate supplies a useful aggregate schema/checker and 20 named mutations, but it has not earned the issue terminal.

## Authority boundary

Keep these authorities separate:

```text
Cursor article                       SOURCE_PROPOSAL
skills-shared method contracts       METHOD_PLANE
GitHub issues / PR metadata          DELIVERY_PROJECTION
Git commit/tree/blob                 SOURCE_AND_IMPLEMENTATION_IDENTITY
consumer Git-hosting runtime         PHYSICAL_STORAGE_PLANE
fault/benchmark receipts             LIVE_EVIDENCE
Shadow verdict                       INDEPENDENT_ADVISORY_EVIDENCE
merge/release/infrastructure choice  HUMAN_ADMIT
```

A Method-Plane DAG, issue DAG, Git commit DAG, Git object DAG, WAL index, and Stacked-PR DAG are different graphs. Similar words such as `DAG`, `replica`, `index`, `state`, or `transaction` do not allow evidence to cross these boundaries.

## Stop laws

Stop with `BLOCKED`, `PARTIAL`, or `NOT_EXERCISED` rather than manufacturing completion when any of the following is true:

```text
mutable article URL presented as immutable source bytes
contract PASS presented as physical durability/linearizability PASS
aggregate closure schema presented as the complete #532 receipt family
20 semantic mutations presented as the full #532 fixture denominator
local repository cache presented as source of truth
gossip delivery presented as correctness authority
benchmark claim lacks exact topology/workload/failure denominator
open/mergeable PR presented as merged/admitted implementation
skipped workflow presented as PASS
Stack relation inferred from issue order rather than consumed bytes
shared path has another active writer
Shadow self-review presented as independent evidence
merge/release/provider/account action inferred without Human Admit
```

## Writer law

Current convergence must obey one writer per mutable shared path. At the 2026-08-21 audit, open Draft PRs #412 and #419 both write `skills/git-town-stacked-pr-worker/README.md`; therefore this Git-at-any-scale preparation branch owns only the dedicated molecular-index README, not the canonical Git Town README. Issue #536 owns final shared-path convergence after those writers are reconciled.

PR #542 is path-disjoint and owns only `skills/git-hosting-scale-assurance/**`. It is a sibling implementation atom, not a true Git child of #539.

## Completion packet

Every Worker or Shadow packet reports:

```text
exact repository commit/tree
exact issue and PR subjects
owned paths and active writers checked
source claim IDs consumed
problem IDs owned
State Machine transition attempted
commands/receipts or NOT_EXERCISED reason
issue-contract denominator: implemented vs missing
first-red finding and repair lineage
remaining evidence ceiling
rollback/cleanup subject
next issue / Local Handoff item
Human-owned operations
```

Do not close #531 until its stated parent close gate is satisfied on current admitted subjects.