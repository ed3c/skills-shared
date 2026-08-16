# Truth-verification domain profile

Historical provider, fixture, judge, and consumer specifics remain recoverable from pre-refactor blob `e8a44a63cbdb6e7326f8bab5d379409c77a27c74`.

## Trigger
Load when a concrete judge/provider, fixture substrate, consumer instantiation, or runtime evidence carrier must be selected.

## Non-trigger
Do not load for generic claim binding, evidence collection, contradiction handling, verifier independence, or terminal truth-state assignment.

## Assumptions
Claims, subjects, and evidence sources can be identified independently of any one provider or model.

## Specialization inventory
Named judge/model mappings, fixture repositories, consumer loop layouts, provider sessions, and environment-specific verification commands belong here.

## Evidence ceiling
A model/judge verdict is advisory unless supported by the evidence class required for the claim. Static fixtures cannot prove a live runtime claim.

## Fallback
When a selected judge or provider is unavailable, preserve the claim/evidence packet and use deterministic/source readback where possible; otherwise return an explicit unavailable state.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, suppress contradictory evidence, self-certify a claim, or widen provider/secret/merge authority.
