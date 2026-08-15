# `forgejo-delivery-loop/modules/`

Modules are detailed, on-demand domain instances selected by the procedural `SKILL.md`.

- [`delivery-mechanism.md`](delivery-mechanism.md) — four-layer Forgejo tracking shape, registry/receipt SSOTs, materialization trigger, delivery metrics, and maintenance rationale.
- [`forgejo-operations.md`](forgejo-operations.md) — localhost-only operation invariants, M0/G0/V0 state flows, typed requests, idempotency, outbox/recovery, credential-memory boundary, and repo-local operator handoff.

These modules explain the Forgejo domain. They do not own consumer repository names, issue numbers, milestones, credentials, browser sessions, or live receipts, and they do not override `SKILL.md` stop conditions.
