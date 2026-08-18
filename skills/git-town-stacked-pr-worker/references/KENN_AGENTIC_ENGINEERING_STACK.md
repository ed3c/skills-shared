# Kenn Agentic Engineering molecular Stack index

This reference records the molecular delivery shape for internalizing the Kenn-derived workflow. It supplements, and does not replace, the canonical molecular Stack index contract.

## Stack

```text
S1  kenn-ae/design-control-plane
    ROOT / TERMINAL METHOD SLICE
    issue #392
    owns `skills/human-led-agentic-engineering/**`
    provides Human Design Gate, Design Adversary, provider boundaries, schema/checker

└─ S2 kenn-ae/shared-index-trace
      TRUE_CHILD / CONVERGENCE-INDEX SLICE
      consumes S1 method bytes
      owns shared traceability/index documentation

External evidence lanes
    #232 independent Shadow canary              HISTORICAL VERIFIED
    #234 real Git Town + dual-forge canary      PROCESS_DEPENDENCY / OPEN
    #393 commit/branch review provider          PROCESS_DEPENDENCY / OPEN
    #394 intent/observability providers         PROCESS_DEPENDENCY / OPEN

Cross-repository consumer
    bettor-arena #189                           PROCESS_DEPENDENCY / OPEN
```

## Laws

- S2 is a true child only because its closure map references the S1 method artifact.
- #232/#234/#393/#394 are not Git parents merely because the workflow waits on their evidence.
- `bettor-arena` cannot be a Git child across repositories; it binds an immutable shared commit/release.
- provider implementation leaves are siblings when their writer paths/resources are disjoint.
- one convergence owner updates shared indexes and aggregate consumer closure after prerequisites are stable.
- no Agent owns merge, release, provider permission widening, repository visibility, or destructive rollback.

## README integration status

The method-relative Stack is also documented in `skills/human-led-agentic-engineering/README.md`. The canonical `git-town-stacked-pr-worker/README.md` remains the owner of general Stack laws; this reference is linked from the Kenn closure trace until a safe whole-file README update can be made without risking loss of its existing large historical index.
