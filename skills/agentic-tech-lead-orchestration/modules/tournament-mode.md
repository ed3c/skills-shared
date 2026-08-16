# Tournament-mode adapter

## Trigger

Use an Orca/ADE-style fan-out when multiple independent implementations of the same locked contract can be compared by the same deterministic oracles.

## Non-trigger

Do not use when alternatives require different public architecture, share writable paths, lack a common oracle, or would consume more budget than the expected decision value.

## Purpose

Run differentiated Workers in isolated Worktrees, reject boundary violations, and select one coherent base implementation.

## Assumptions

All branches start from the same commit, share identical locked interfaces/tests, have disjoint Worktrees, fixed focuses, bounded budgets, and a declared selection policy.

## State machine

```text
locked contract → N isolated branches → differentiated prompts
→ gates → boundary filter → deterministic comparison
→ one base winner → optional proven cherry-picks → handoff
```

Failure states: `BASE_DIVERGED`, `CONTRACT_DIVERGED`, `WORKTREE_COLLISION`, `ORACLE_NOT_COMMON`, `BUDGET_EXHAUSTED`, `NO_VALID_CANDIDATE`, `INCOMPATIBLE_CHERRY_PICK`.

## Inputs

Common task contract, branch focuses, Worker identities, budgets, gates, and selection criteria.

## Outputs and effects

Candidate branches, receipts, rejected reasons, selected base, optional compatible patches, and cleanup record.

## Evidence class and freshness

Selection quality is bounded to the declared subject and oracles; model reputation or prose cannot override a failed gate.

## Fallback

Use one Stack-mode Worker with independent review, or revise the contract before another tournament.

## Core laws that remain authoritative

`../SKILL.md` owns locked architecture, path leases, test immutability, selection order, budgets, and Human boundaries.

## Consumer-owned values

ADE/Orca installation, model accounts, tokens, subscriptions, rate limits, worktree roots, UI, remote control, and live receipts remain consumer-owned.
