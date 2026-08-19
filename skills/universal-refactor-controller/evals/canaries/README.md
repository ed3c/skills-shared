# UCR canary and Golden Refactor corpus

This directory indexes replayable evidence for `universal-refactor-controller`. It stores target identities, issue/PR/workflow references, Complexity Delta and evidence ceilings. It does not copy target implementations.

## Promotion State Machine

```text
CANDIDATE_BOUND
→ MATCHED_ORACLES_FROZEN
→ LOCAL_VERIFIED
→ REMOTE_VERIFIED
→ HOLD_UNMERGED
→ MERGED_IMMUTABLE
→ GOLDEN_ELIGIBLE
→ GOLDEN_PROMOTED
```

A case may stop or move backward when its subject becomes stale or a regression appears. `REMOTE_VERIFIED` is not the same as `GOLDEN_PROMOTED`.

## Durable identity rule

Open PR head SHAs are mutable publication state and must not be embedded here as durable truth. While a candidate remains open, identify it by repository + issue/PR + workflow-run receipt and keep `promotion_state = HOLD_UNMERGED`.

A baseline commit/tree may be recorded because it is an immutable historical treatment. A candidate commit becomes durable only after an admitted immutable delivery state exists.

## Evidence ceiling

Current entries prove bounded transfer across one Skill and one ordinary repository. They do not prove unseen domains, live model uplift, production safety, merge, release, promotion or rollback.