---
name: shared-skills-infra
description: |
  Portable shared-Skill governance procedure for classifying canonical versus repo-owned bodies, binding immutable Skill identity, detecting shadowing/drift, producing thin projections/bindings, checking freshness, and preserving rollback. Concrete host discovery surfaces, user directories, projection carriers, local checkout layouts, and consumer bootstrap adapters are domain modules.
---

# Shared Skills Infrastructure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns canonical classification, content identity, shadow detection, binding/projection integrity, freshness, rollback, and evidence boundaries. Concrete host surfaces and bootstrap adapters live in `modules/domain-profile.md`.

## State machine

```text
SKILL_CLASSIFIED
→ CANONICAL_IDENTITY_BOUND
→ SHADOW_SCAN_COMPLETE
→ CONSUMER_BINDING_BOUND
→ PROJECTION_RENDERED
→ BYTE_READBACK_ASSERTED
→ FRESHNESS_ASSERTED
→ {ACTIVE | BLOCKED | ROLLBACK}
```

## Hard laws

- **CORE-LAW-001 — one canonical authority per shared Skill.** Shared infrastructure has one content authority; consumer-local copies may not silently shadow it.
- **CORE-LAW-002 — identity is immutable/content-bound.** Execution/projection binds exact Skill bytes or an immutable bundle, never an unqualified mutable branch name.
- **CORE-LAW-003 — projection is not runtime proof.** Copy/symlink/render success proves distribution only; host discovery/model execution requires its own receipt.
- **CORE-LAW-004 — modules cannot widen authority.** Host modules may expose canonical bytes but cannot duplicate bodies, change visibility/access, accept stale bindings, or widen credential/merge authority.
- **CORE-LAW-005 — drift and rollback are explicit.** Stale bindings, shadow copies, broken projections, and superseded versions surface deterministically with a rollback subject.

## Procedure

1. Classify the Skill as shared, repo-owned, or explicitly deferred under the registry authority.
2. Bind canonical content identity and compatibility/ownership metadata.
3. Scan consumer and host surfaces for same-name shadow copies, divergent bodies, or unapproved aliases.
4. Bind thin consumer requirements/configuration without copying canonical procedural bodies.
5. Select a concrete host projection only through `modules/domain-profile.md` when needed.
6. Render/project and read back exact bytes, ownership, and source identity.
7. Check binding freshness after canonical movement; surface stale consumers rather than silently accepting drift.
8. Preserve previous immutable subject for rollback and report runtime discovery as a separate evidence lane.

## Module selection

Load `modules/domain-profile.md` only when a concrete host discovery surface, user-scope directory, projection carrier, local checkout layout, consumer binding, or runtime bootstrap adapter must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill shared-skills-infra
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on shadowing, mutable identity, stale binding, projection mismatch, missing host capability, or Human-owned admission/release decisions. Handoff includes canonical identity, consumer binding state, projection/readback result, runtime evidence state, and rollback subject.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
