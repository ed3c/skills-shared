---
name: shared-skills-infra
description: |
  Govern canonical versus repo-owned Agent Skills, immutable consumer bindings, Domain Decoupling bootstrap, projection freshness, shadow-copy refusal, and rollback. Use when a repository adopts or updates shared Skills, creates a modular consumer control plane, or audits Skill distribution drift.
---

# Shared Skills Infrastructure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns canonical classification, immutable content identity, shadow detection, thin consumer binding, Domain Decoupling bootstrap, projection integrity, freshness, rollback, and evidence boundaries. Concrete host surfaces and bootstrap carriers live in `modules/domain-profile.md`.

## State Machine

```text
SKILL_CLASSIFIED
→ CANONICAL_IDENTITY_BOUND
→ SHADOW_SCAN_COMPLETE
→ CONSUMER_ROUTES_BOUND
→ CONSUMER_BINDING_BOUND
→ PROJECTION_RENDERED
→ BYTE_READBACK_ASSERTED
→ FRESHNESS_ASSERTED
→ {ACTIVE | BLOCKED | ROLLBACK}
```

## Hard laws

- **CORE-LAW-001 — one canonical authority per shared Skill.** A consumer-local body cannot silently shadow canonical shared bytes.
- **CORE-LAW-002 — identity is immutable and content-bound.** Bind exact commit/tree/artifact and Skill digests, never mutable `main` or `latest`.
- **CORE-LAW-003 — projection is not runtime proof.** A generated route, binding, symlink, package, or workflow definition cannot establish host/model execution.
- **CORE-LAW-004 — modules cannot widen authority.** A carrier cannot change visibility, credentials, conflict, merge, release, provider, or rollback authority.
- **CORE-LAW-005 — drift and rollback are explicit.** Stale bindings, broken projections, shadow copies, and superseded subjects fail closed with a rollback subject.
- **CORE-LAW-006 — consumer bootstrap is additive and atomic.** Preserve consumer prose outside managed blocks, refuse unknown generated authorities, and restore every touched byte when a downstream step fails.

## Procedure

1. Classify each Skill as shared, repo-owned, or explicitly deferred under `registry.json`.
2. Bind canonical repository, commit/tree, Skill bytes, profile, and selected adapter identity.
3. Inspect the consumer repository and reject same-name local bodies, unsafe paths, secret-shaped fields, and private-reasoning fields.
4. For a new modular consumer, run `scripts/consumer_bootstrap.py --apply`; for an existing routed consumer, use the narrower `repository_control_plane.py attach` flow.
5. Render only managed document blocks, thin requirements/profile, one generated binding, one read-only workflow adapter, and one subject-bound receipt.
6. Read back exact bytes and verify route closure, source identity, selected Skill closure, receipt freshness, and rollback ancestry.
7. Run host/runtime canaries separately. Preserve `NOT_EXERCISED` and `HUMAN_ADMIT_REQUIRED` lanes.
8. Classify a consumer finding as domain-specific or generic before proposing any shared-core change.

## Module selection

Load `modules/domain-profile.md` only when a concrete host discovery surface, projection carrier, workflow adapter, local checkout layout, consumer binding, or runtime bootstrap adapter must be selected.

## Executable assertions

```bash
python3 scripts/check_skill_core_boundaries.py --skill shared-skills-infra
python3 scripts/check_skill_entry_routes.py --skill shared-skills-infra --print-index
bash skills/shared-skills-infra/tests/consumer-bootstrap/verify.sh
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on shadowing, mutable identity, malformed managed markers, unrecognized generated files, stale binding/receipt bytes, unsafe overwrite, failed atomic rollback, missing host capability, or Human-owned admission. Report exact source/consumer subjects, modified routes, controls, evidence ceiling, and rollback.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
