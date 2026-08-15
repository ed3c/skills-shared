# Git Town Intent-Bound Constraints

This adapter binds the portable Git Town method to the repository-wide `intent-bound-constraint/v1` contract. It does not replace Git Town, `github-delivery-loop`, consumer CI, or Human Admit.

## Meta-intents

| Intent | Protected property | Proof obligations |
|---|---|---|
| `MI-GT-CAUSAL` | branch edges represent real unmerged dependencies | `PO-GT-TRUE-EDGE`, `PO-GT-NO-FAKE-SERIAL` |
| `MI-GT-FRESHNESS` | child evidence is bound to the exact parent and head | `PO-GT-EXACT-PARENT`, `PO-GT-EXACT-RECEIPT` |
| `MI-GT-PARALLEL` | sibling Workers remain path-disjoint | `PO-GT-PATH-LEASE`, `PO-GT-NO-SIBLING-EDGE` |
| `MI-GT-CONVERGENCE` | shared reconciliation has one delayed owner | `PO-GT-CONVERGENCE-OWNER` |
| `MI-GT-HUMAN` | semantic and authority-changing operations remain Human-owned | `PO-GT-HUMAN-BOUNDARY` |

## Constraints

| Constraint | Existing evaluator/control owner | Repair policy |
|---|---|---|
| `C-GT-TRUE-DEPENDENCY` | `check_stack_contract.py`, `GTSP-04` | reclassify branch or declare the consumed contract; one bounded retry |
| `C-GT-EXACT-PARENT` | `check_stack_contract.py`, `GTSP-04/13/14` | bounded local sync to the declared parent; stop on semantic conflict |
| `C-GT-PR-BASE` | `check_stack_contract.py`, `GTSP-04/16` | retarget only after task-packet and graph update |
| `C-GT-SIBLING-DISJOINT` | `check_stack_contract.py`, `GTSP-06` | split or reassign the path lease |
| `C-GT-EVIDENCE-FRESHNESS` | `check_stack_contract.py`, `GTSP-14/18` | regenerate exact-subject evidence |
| `C-GT-CONVERGENCE-DELAY` | `check_stack_contract.py`, `GTSP-04` | keep convergence `NOT_CREATED` until prerequisites are admitted |
| `C-GT-HUMAN-BOUNDARY` | existing prompt/policy controls, `GTSP-12/20` | zero automatic retries |

## Diagnostic loop

```text
wrong parent or stale edge
→ MI-GT-FRESHNESS at risk
→ STALE_PARENT_ANCESTRY
→ SYNC_TO_EXACT_PARENT
→ expect stale_edge_count to decrease
→ re-run ancestry and task controls
→ PASS or BLOCKED_CONFLICT
```

The Agent emits the canonical Diagnostic Reflection Receipt. It does not emit private chain-of-thought.

## Stack class law

```text
foundation
  supplies a new unmerged contract

child
  consumes parent bytes or an unmerged contract

sibling
  consumes the same foundation but not another sibling's bytes

convergence
  is not created until all declared prerequisites are admitted
```

A Git branch graph is not a scheduling queue. Independent work stays as siblings.

## Evidence boundary

The offline checker proves fixture graph semantics only. A live Git Town binary, real worktree, rebase, conflict, remote publication, CI, merge, or release requires its own exact-subject receipt.
