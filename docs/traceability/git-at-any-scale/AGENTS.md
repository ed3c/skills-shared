# AGENTS.md — Git at any scale closure route

This directory is the zero-context entry for the Cursor **Git at any scale** audit. It is a traceability and assurance-control surface inside `skills-shared`; it is not a Git hosting implementation.

## Mandatory read order

1. Repository root `AGENTS.md` and current `main` commit/tree.
2. This file.
3. `README.md` in this directory.
4. Issue #531 and the exact child issue being executed: #532, #534, #535, or #536.
5. For C1, read merged `skills/git-hosting-scale-assurance/{AGENTS.md,README.md,SKILL.md}` on current `main`.
6. `source-claims.json` and `problem-closure-ledger.json` (pointers to the authoritative `data/handoff/source-evidence/` ledger — do not treat them as a second copy of the claim denominator).
7. `skills/git-town-stacked-pr-worker/molecular-indexes/git-at-any-scale/README.md`.
8. `skills/agentic-tech-lead-orchestration/runtime-handoff/git-at-any-scale-local-handoff-queue.json`.
9. Current GitHub PR/open-writer state and exact workflow receipts before any state transition.

## Current admission epoch — restamped 2026-08-22

```text
main                                    5341885f26b5e8e7baf5087a4d661e324f878242
tree                                    a18e12507f9e621efd5354f58384eded1f1e2a9a
rollback                                9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c
main (2026-08-21 compile subject)       174009203a3ff9bd6ebc4010bc6cab7232dd44a4  HISTORICAL, 182 behind
D1 preparation                          PR #539 / MERGED
C1 implementation                       PR #542 / MERGED — #532 issue stays OPEN
C1 exact head (as merged)               196a75ac04f6ad2c9a6e50b0645d71fea9bf43e3
C1 deterministic gate                   tests/run-all.sh -> PASS positive=1 mutations=20/20 (real run, this head)
C1 issue-contract denominator           still INCOMPLETE (operation-history/durability/ref/cache/gossip/compaction/recovery/benchmark receipt families remain unbuilt)
L1 physical runtime                     EXECUTED_AT_CLEAN_ROOM_CEILING / #534 OPEN (single-node canary receipts under data/handoff/git-at-any-scale/; external-runtime claims stay NOT_EXERCISED)
S1 terminal independent Shadow          FRESH_CONTEXT_HOLD / #535 OPEN (issue-535-shadow-receipt.json, HUMAN_ADMIT_REQUIRED; identity independence unmet)
```

Do not close #532 because PR #542 merged. A merged branch closes its own path lease, not the issue's contract denominator. #532 requires separate operation-history/durability/ref/read/cache/gossip/compaction/recovery/benchmark contracts and the positive/hollow/concurrent/fault fixture denominator stated in the issue. The merged candidate supplies a real, tested aggregate schema/checker and 20 named mutations, but it has not earned the issue terminal.

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
merged implementation PR presented as its parent issue's contract closed
skipped workflow presented as PASS
Stack relation inferred from issue order rather than consumed bytes
shared path has another active writer
Shadow self-review presented as independent evidence
merge/release/provider/account action inferred without Human Admit
```

## Writer law

Current convergence must obey one writer per mutable shared path. At the 2026-08-22 readback (main `5341885f`) PRs #412 and #419 are both CLOSED unmerged — #412 `SUPERSEDED_BY_#419`, #419 `CONSUMED`, both landed via PR #573 (commit `9fe3c6d`), per `skills/agentic-tech-lead-orchestration/references/closure-audit/issue-568.json:17-18,24`. The path-writer conflict at `skills/git-town-stacked-pr-worker/README.md` is therefore cleared, and #536's shared-path convergence at root `README.md`/`AGENTS.md`/`docs/INDEX.md` is unblocked and currently **unowned** — assign a named writer before the next convergence wave. This lease still owns only the dedicated molecular-index README and this directory; the block is lifted, the lease is not widened by default.

The earlier reading — open Draft PRs #412/#419 contending for that path at the 2026-08-21 readback — is retained here as the dated observation it was; it is no longer current.

PR #542 was path-disjoint and owned only `skills/git-hosting-scale-assurance/**`; it merged as a sibling implementation atom, not as a Git child of #539. Both are now merged, but merging does not retroactively create ancestry between them.

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