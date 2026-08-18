# Forge delivery domain profile

Historical host-specific detail is preserved in Git history at pre-refactor blob `9f47aa5d8c90b1141afd7ca15ef06e086c7f2fbb`.

## Trigger
Load for a concrete forge host, local service, credential broker, issue/PR projection, browser carrier, or consumer tracking policy.

## Non-trigger
Do not load for generic delivery state transitions, exact-subject receipts, publication admission, or integration handoff.

## Assumptions
Host endpoints, credentials, local services, and repository bindings are runtime-owned and explicitly selected.

## Specialization inventory
Concrete forge API mechanics, local-host routing, login/session handling, issue/milestone projection, credential transport, and runtime-environment integration belong here.

## Evidence ceiling
A reachable host or successful API call proves only that bound operation. It cannot prove implementation correctness, publication, integration, or merge.

## Fallback
If the selected host is unavailable, keep the delivery packet and outbox/recovery state explicit and return the host lane as unavailable rather than successful.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, auto-resolve semantic conflicts, expose credentials, change repository visibility, or create merge/release authority.
