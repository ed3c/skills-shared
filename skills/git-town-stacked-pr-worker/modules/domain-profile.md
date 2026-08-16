# Stacked-branch delivery domain profile

Historical forge/publication-specific details remain recoverable from pre-refactor blob `36d894d756ceca6d754b4c248b70680c7d199148`.

## Trigger
Load when a concrete Git host, publication provider, CI carrier, branch naming policy, installer/runtime binding, or consumer repository convention must be selected.

## Non-trigger
Do not load for generic branch graph, true dependency edges, isolated worktrees, path/resource leases, bounded synchronization, conflict refusal, or stacked handoff.

## Assumptions
Each active mutation slice has one writer, one isolated worktree/branch subject, explicit dependencies, and an owning verification oracle.

## Specialization inventory
Forge-specific PR publication, CI integration, host command wrappers, installer identities, consumer branch naming, and remote conventions belong here.

## Evidence ceiling
A successful synchronization command proves graph movement only; it cannot prove implementation correctness, CI, review, publication, or merge.

## Fallback
If the preferred stack tool or publication provider is unavailable, preserve the branch/dependency/lease graph and perform only an explicitly admitted local Git fallback or return the lane unavailable.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, manufacture false parent/child edges, auto-resolve semantic conflicts, reuse stale receipts, or widen push/merge/secret authority.
