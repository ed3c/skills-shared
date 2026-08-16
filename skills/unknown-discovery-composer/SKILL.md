---
name: unknown-discovery-composer
description: |
  Portable unknown-discovery procedure for classifying known-known, known-unknown, unknown-known, and unknown-unknown states, generating bounded probes, ranking them by information gain and cost, verifying discoveries, and handing unresolved unknowns to the correct owner. Concrete actors, providers, host carriers, consumer catalogs, and repository routes are domain modules.
---

# Unknown Discovery Composer

<!-- PORTABLE_CORE_START -->

## Contract

The core owns knowledge-state classification, probe generation, information-gain ranking, bounded execution, evidence promotion, and handoff. Concrete discovery implementations live in `modules/domain-profile.md`.

## State machine

```text
SUBJECT_BOUND
→ KNOWLEDGE_STATE_CLASSIFIED
→ MATERIAL_UNKNOWNS_SELECTED
→ PROBES_GENERATED
→ PROBES_RANKED
→ BOUNDED_PROBE_EXECUTED
→ DISCOVERY_VERIFIED
→ KNOWLEDGE_STATE_UPDATED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — classify uncertainty explicitly.** Do not collapse known, inferred, missing, contested, and unknowable states into one confidence label.
- **CORE-LAW-002 — probe material unknowns only.** Discovery effort is prioritized by decision impact, expected information gain, cost, reversibility, and safety.
- **CORE-LAW-003 — discovery is not truth until verified.** Hypotheses and provider/tool outputs remain candidate evidence until the required readback/assertion closes.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may bind actors/tools but cannot relabel unknowns without evidence, hide failed probes, or widen provider/secret/merge authority.
- **CORE-LAW-005 — exploration is bounded and traceable.** Every probe records subject, question, cost/budget, result, evidence state, and whether the knowledge state changed.

## Procedure

1. Bind subject, decision/task objective, current evidence, budget, and authority boundaries.
2. Classify known-known, known-unknown, unknown-known, unknown-unknown, contested, and blocked areas.
3. Select only unknowns whose resolution can materially change a decision or implementation.
4. Generate multiple falsifiable probes and rank them by expected information gain per cost/risk.
5. Select concrete execution capability only through `modules/domain-profile.md` when needed.
6. Execute one bounded probe and capture observable evidence.
7. Verify before promoting a discovery to known state; preserve contradictory results and failed probes.
8. Update the knowledge-state map and iterate only while the unresolved material set shrinks.

## Module selection

Load `modules/domain-profile.md` only when a concrete discovery actor/provider, host carrier, consumer catalog, repository path convention, or downstream executor must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill unknown-discovery-composer
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when material unknowns are resolved, remaining probes have poor expected information gain, required capability/authority is absent, or the budget is exhausted. Handoff includes the knowledge-state map, executed/rejected probes, evidence, and next admissible owner.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
