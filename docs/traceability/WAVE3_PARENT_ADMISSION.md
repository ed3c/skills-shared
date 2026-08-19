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

The merge tree is exactly the #455 candidate tree, so no Wave-2 implementation bytes changed at admission. From this point forward:

```text
#455 / #379                HUMAN_ADMITTED / MERGED / HISTORICAL_PARENT
main@ca31e0b1...            CURRENT_ADMITTED_BASE for Wave-3 convergence
#469–#472                   historical TRUE_CHILD provenance of #455; selected candidate bytes
#473                        must be refreshed onto and target current main
```

This note supersedes any earlier use of the word `unmerged` when that wording is read as **current** #455 state. Earlier documents remain correct as fork-time provenance.

No live evidence state changes because of #455 admission:

```text
live Codex SDK/controller acceptance       NOT_EXERCISED
live GitHub add/readback/remove canary      NOT_EXERCISED
live Herdr lifecycle                       NOT_EXERCISED
article/PDF/PRD truth                      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real source/provider closure               EVIDENCE_DEPENDENT
#473 Human Admit / merge / release          NOT_PERFORMED
```

Machine authority remains current GitHub metadata, Git ancestry, exact-head workflows and runtime receipts.