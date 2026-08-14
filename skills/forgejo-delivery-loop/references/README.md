# `forgejo-delivery-loop/references/`

References are reusable, host-neutral contract descriptions selected by the procedure.

- [`contracts.md`](contracts.md) — typed request, route result, idempotency, outbox, receipt, and recovery contract vocabulary.
- [`INTENT_BOUND_CONSTRAINTS.md`](INTENT_BOUND_CONSTRAINTS.md) — the meta-intents these contracts protect, which evaluator discharges each one, and the merge-authority defect this registration closed.

References do not contain consumer line identities, local paths, credentials, live sessions, or repository-specific operator commands. Those belong to consumer bindings and implementation owners.
