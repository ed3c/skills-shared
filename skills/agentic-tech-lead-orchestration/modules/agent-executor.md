# Agent executor adapter

## Trigger

Use Serena or another admitted executor when a Worker needs symbol-aware navigation or bounded edits in one isolated Worktree.

## Non-trigger

Do not grant an executor planner authority, shared-path ownership, test mutation, remote publication, merge, or provider activation.

## Purpose

Apply one prompt packet inside one path lease and return a diff plus execution receipt.

## Assumptions

Exact project/worktree identity, language-server health, allowed/read-only paths, command allowlist, effect policy, budget, timeout, and cleanup are declared.

## State machine

```text
packet → workspace identity → capability/policy check → bounded edit
→ local gates → receipt → accept / repair / stop
```

Failure states: `WRONG_WORKTREE`, `LANGUAGE_SERVER_UNHEALTHY`, `PATH_ESCAPE`, `ASSERTION_MUTATION`, `COMMAND_NOT_ALLOWED`, `BUDGET_EXHAUSTED`, `RESIDUE_DETECTED`.

## Inputs

Worker prompt packet, context manifest, lease, branch identity, test commands, retry limit, and stop states.

## Outputs and effects

Repository-local edits inside the lease, diff, commands/exits, diagnostics, tests, retries, and cleanup receipt.

## Evidence class and freshness

Executor prose is advisory. Only deterministic source/diff/gate receipts prove performed work for the recorded branch subject.

## Fallback

Use another admitted executor or Human implementation while preserving the same contract and assertions.

## Core laws that remain authoritative

`../SKILL.md` owns architecture authority, one-writer leases, immutable tests, repair bounds, and Human boundaries.

## Consumer-owned values

Serena project config, MCP surface, executable/version, worktree paths, secrets, network policy, model, branch, and live receipts remain consumer-owned.
