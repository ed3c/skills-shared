# Judge-loop selection domain profile

Historical model, provider, and consumer-specific mappings remain recoverable from pre-refactor blob `7a1abe4bb6b64c485466ec49656a8c0eba6488a2`.

## Trigger
Load when a concrete judge implementation, model/provider mapping, consumer registry, family taxonomy, or execution carrier must be selected.

## Non-trigger
Do not load for generic deliverable classification, evidence-tier selection, independence requirements, zero-access review packet design, or Human Admit routing.

## Assumptions
Judge requirements can be derived from the deliverable, risk, evidence class, and required independence before choosing a concrete actor.

## Specialization inventory
Named model/provider mappings, consumer family registries, host command surfaces, and repository-specific judge policies belong here.

## Evidence ceiling
A selected judge or model verdict is advisory unless the evidence contract for the deliverable admits that class of judgment.

## Fallback
If the preferred judge is unavailable, choose the next implementation that satisfies the frozen independence/evidence contract or return the lane as unavailable.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, downgrade required independence, let a producer self-certify, or widen provider/secret/merge authority.
