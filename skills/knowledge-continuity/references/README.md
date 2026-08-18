# `knowledge-continuity/references/`

This directory owns reusable, domain-neutral contracts and templates selected by the procedural `SKILL.md`.

- [`DOCUMENT_ROUTING_CONTRACT.md`](DOCUMENT_ROUTING_CONTRACT.md) — same-name routes and assertion vocabulary for modular repositories.
- [`INTENT_BOUND_CONSTRAINTS.md`](INTENT_BOUND_CONSTRAINTS.md) — the registered intent-bound constraint contract for this Skill.
- [`continuity-audit.schema.json`](continuity-audit.schema.json) — machine shape of one audit record; its semantics are enforced by `../scripts/assert_continuity_audit.py`.

References do not contain consumer branches, secrets, provider sessions, live receipts, or product-specific current state. Domain applications belong in `../modules/`.
