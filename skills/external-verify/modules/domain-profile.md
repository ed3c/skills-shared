# External verification domain profile

Historical host/search/provider-specific details remain recoverable from pre-refactor blob `d0ad3b0b6d2cd53766f86b030e1bba56637ec7e1`.

## Trigger
Load when a concrete web/search/fetch provider, browser/session carrier, source API, or consumer verification surface must be bound.

## Non-trigger
Do not load for generic claim decomposition, source-strength selection, readback, contradiction handling, citation packet construction, or evidence grading.

## Assumptions
Claims can be decomposed into externally verifiable units and source authority can be ranked independently of one provider.

## Specialization inventory
Provider-specific search/fetch commands, browser behavior, rate limits, query syntax, and consumer truth snapshots belong here.

## Evidence ceiling
Search results are discovery evidence; a claim becomes verified only after authoritative source readback appropriate to the claim.

## Fallback
If a provider is unavailable, preserve the claim/source plan and use another admitted retrieval lane or mark the external verification lane unavailable.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, promote snippets to source truth, hide source disagreement, or widen network/secret/merge authority.
