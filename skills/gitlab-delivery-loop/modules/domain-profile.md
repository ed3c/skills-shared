# GitLab delivery domain profile

Historical host-specific detail remains in Git history at pre-refactor blob `290d4310d6e89430f67fc630325890a60b5758b6`.

## Trigger
Load when a concrete GitLab instance, CLI/API surface, merge-request schema, board, runner, permission model, or host-specific publication rule must be bound.

## Non-trigger
Do not load for generic delivery, exact-subject verification, publication admission, remote readback, or merge-authority separation.

## Assumptions
Host configuration, tokens, runner state, and repository bindings are runtime-owned.

## Specialization inventory
CLI commands, merge-request/issue-board schemas, host permission checks, registry paths, and provider-specific publication adapters belong here.

## Evidence ceiling
A successful host command proves only that command on the bound subject; it cannot prove implementation correctness, CI, review, or merge.

## Fallback
If the host adapter is unavailable, preserve the delivery packet and return the host lane as `ABSENT`, `NOT_IMPLEMENTED`, or `NOT_EXERCISED`.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, auto-merge, weaken exact-subject checks, expose secrets, or widen repository access.
