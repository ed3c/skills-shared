# Wave 3 parent admission transition

Current authority note for the Wave-3 live-evidence program.

At Wave-3 fork time, #464–#467 were created as `TRUE_CHILD` leaves of the then-unmerged #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`. That historical dependency remains valid provenance: every leaf consumed those exact unmerged bytes and none consumed another leaf.

During Wave-3 convergence, #455 was Human-admitted and merged into `main` as merge subject:

```text
ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
parents:
  4ca9417b1da5ff32f1d4d3e7af64a15908749024
  847e56c3418fce920c42d983e84ee44fdc6e8971
tree:
  8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

The merge tree is exactly the #455 candidate tree, so no Wave-2 implementation bytes changed at admission. Post-merge #379 admission documentation was then Human-admitted through PR #475, advancing current main to:

```text
4be4d6744fe432e4be24d94750bb4fc034aab189
```

Current Wave-3 interpretation:

```text
#455 / #379                HUMAN_ADMITTED / MERGED / HISTORICAL_PARENT
#475                        HUMAN_ADMITTED / post-merge documentation authority
main@4be4d674...            CURRENT_ADMITTED_BASE observed for replacement convergence
#469–#472                   fork-time TRUE_CHILD provenance of #455; selected candidate bytes
#473                        HISTORICAL / REJECTED_COMMIT_ROLE
#479                        CURRENT Wave-3 replacement convergence candidate
```

PR #473 reached functional/static convergence after its queue repair: the ATL suite executed the 10-schema / 8-selftest denominator and the Wave-3 Local Handoff Queue semantic gate. Its final repository-wide `Skill Eval Contract` then correctly rejected accidental historical commit `3fe0a79aaeed78b8e529773b241eff07d1c2a4d4`, which had no `Driven-By` or `Driven-On` trailer. That failed lineage remains evidence; the gate was not weakened.

PR #479 rebuilds the exact Wave-3 semantic bytes without that accidental ancestry and semantically reconciles the current #475 admission routes instead of overwriting them.

This note supersedes any earlier use of the word `unmerged` when that wording is read as **current** #455 state, and any earlier use of #473 as the current Wave-3 convergence. Earlier documents remain valid as fork-time/rejected provenance where explicitly marked historical.

No live evidence state changes because of #455/#475 admission or #479 replacement:

```text
live Codex SDK/controller acceptance       NOT_EXERCISED
live GitHub add/readback/remove canary      NOT_EXERCISED
live Herdr lifecycle                       NOT_EXERCISED
article/PDF/PRD truth                      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real source/provider closure               EVIDENCE_DEPENDENT
#479 Human Admit / merge / release          NOT_PERFORMED
```

Machine authority remains current GitHub metadata, Git ancestry, exact-head workflows and runtime receipts.
