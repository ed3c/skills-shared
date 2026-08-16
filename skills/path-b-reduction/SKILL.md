---
name: path-b-reduction
description: |
  Portable reduction procedure for shrinking a complex path, plan, or artifact while preserving hard invariants, evidence obligations, interfaces, and rollback. Consumer examples, lineage, actor mappings, and repository-specific reduction targets are domain modules.
---

# Path Reduction Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns invariant extraction, redundancy classification, candidate reduction, information-loss checks, executable validation, and handoff. Concrete consumer reduction profiles live in `modules/domain-profile.md`.

## State machine

```text
SUBJECT_BOUND
→ INVARIANTS_EXTRACTED
→ REDUNDANCY_CLASSIFIED
→ REDUCTION_CANDIDATE_BUILT
→ INFORMATION_LOSS_ASSERTED
→ OWNER_ASSERTIONS_RUN
→ {ADMIT | REVISE | REJECT}
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — invariants before compression.** Extract required behavior, evidence, interfaces, safety boundaries, and rollback before removing anything.
- **CORE-LAW-002 — remove redundancy, not authority.** A reduction may eliminate duplicated or derivable material but cannot silently delete obligations or negative assumptions.
- **CORE-LAW-003 — smaller is not proof.** The reduced form must pass owning assertions and explicit information-loss controls.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may provide concrete reduction cases but cannot override invariants, hide loss, or widen provider/secret/merge authority.
- **CORE-LAW-005 — reduction is reversible and scoped.** Preserve source identity, removed-item rationale, rollback subject, evidence state, and exact admission scope.

## Procedure

1. Bind exact subject, target reduction goal, consumers, and non-goals.
2. Extract hard invariants, interfaces, evidence requirements, failure/rollback obligations, and non-derivable context.
3. Classify material as required, duplicated, derivable, optional, stale, or domain-specific.
4. Build the smallest candidate that preserves all required classes and routes domain-specific material through `modules/domain-profile.md` when needed.
5. Run information-loss controls and the owning executable assertions.
6. Admit only if behavior/evidence/authority are preserved; otherwise revise or reject.
7. Handoff the reduced subject with removal map, evidence, rollback, and remaining tradeoffs.

## Module selection

Load `modules/domain-profile.md` only for concrete consumer cases, repository lineage, actor/provider mappings, or repository-specific reduction targets.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill path-b-reduction
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when a required invariant would be lost, executable assertions fail, evidence is insufficient, or the reduction reaches the declared target. Handoff includes invariant map, removed/deferred material, assertion results, and rollback subject.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
