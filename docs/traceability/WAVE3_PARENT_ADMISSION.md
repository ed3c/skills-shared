# Wave 3 parent admission transition

Current authority note for the Wave‑3 live-evidence program.

At Wave‑3 fork time, #464–#467 were created as `TRUE_CHILD` leaves of the then-unmerged #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`. That historical dependency remains valid provenance: every leaf consumed those exact unmerged bytes and none consumed another leaf.

During Wave‑3 convergence, #455 was Human-admitted and merged as the Wave‑2 implementation subject:

```text
ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
parents:
  4ca9417b1da5ff32f1d4d3e7af64a15908749024
  847e56c3418fce920c42d983e84ee44fdc6e8971
tree:
  8a75271851f2e9dd47dd3a019c93e4a0f9272d24
```

The merge tree is exactly the #455 candidate tree, so no Wave‑2 implementation bytes changed at admission. The post-merge admission record and multi-hop route were then landed through provenance-complete PR #475:

```text
main refresh observed for Wave‑3 convergence:
  4be4d6744fe432e4be24d94750bb4fc034aab189
parents:
  ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
  6e9b84acd4e676d444a2be93454a1bb867e34501
```

PR #474 remains closed-unmerged historical evidence because its document-routing gate passed but commit-role provenance failed. PR #475 replayed the same three document blobs with required commit-level provenance; no gate or evidence ceiling was weakened.

From this point forward:

```text
#455 / #379                HUMAN_ADMITTED / MERGED / HISTORICAL_PARENT
#475 admission route        MERGED / CURRENT ROUTING INPUT
#469–#472                   historical TRUE_CHILD provenance of #455; selected candidate bytes
#473                        must consume current main plus the four selected leaf bytes before final admission
```

The concrete `main` SHA above is the refresh input observed for this convergence epoch, not perpetual mutable authority. Re-read `main` immediately before every decision or merge.

This note supersedes any earlier use of the word `unmerged` when that wording is read as **current** #455 state. Earlier documents remain correct as fork-time provenance.

No live evidence state changes because of #455/#475 admission:

```text
live Codex SDK/controller acceptance       NOT_EXERCISED
live GitHub add/readback/remove canary      NOT_EXERCISED
live Herdr lifecycle                        NOT_EXERCISED
article/PDF/PRD truth                      SOURCE_PROPOSAL / EVIDENCE_DEPENDENT
real source/provider closure               EVIDENCE_DEPENDENT
#473 Human Admit / merge / release          NOT_PERFORMED until final exact-head gates + Shadow
```

Machine authority remains current GitHub metadata, Git ancestry, exact-head workflows and runtime receipts.
