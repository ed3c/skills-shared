# Modules

Domain instances, loaded only when their trigger matches. A module is never
passive context: if the run does not need a concrete surface, tool, provider or
admission authority bound, no module is read.

| Module | Trigger |
|---|---|
| [`domain-profile.md`](domain-profile.md) | a concrete capture surface, product instance, consumer evidence owner, runtime, delivery adapter or Human admission authority must be bound |
| [`shadow-closure-audit.md`](shadow-closure-audit.md) | a claim that a product problem is closed must be audited read-only across the six evidence lanes, or a findings-only review must be handed to an independent reviewer |

A module may narrow a constraint, add an effect boundary, raise the evidence
required, or reduce the authority granted. It may not do the reverse, and it may
not override `CORE-LAW-001` through `CORE-LAW-008` in
[`../SKILL.md`](../SKILL.md). Presence of a tool is not a trigger; a frozen need
recorded at `INPUT_BOUND` is.
