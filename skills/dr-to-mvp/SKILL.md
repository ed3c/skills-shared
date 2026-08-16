---
name: dr-to-mvp
description: |
  Portable research-to-MVP procedure for turning a partially verified research/spec packet into a bounded implementable slice: establish the verified base, expose blocking gaps, close only the gaps required for the MVP, define falsifiable acceptance, build the smallest useful slice, and graduate only on observed evidence. Providers, prototype hosts, consumer loops, and artifact routes are domain modules.
---

# Research-to-MVP Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns verified-base construction, blocking-gap closure, MVP boundary, experiment/acceptance design, graduation, and handoff. Concrete providers/hosts/consumer layouts live in `modules/domain-profile.md`.

## State machine

```text
INPUT_BOUND
→ VERIFIED_BASE_BUILT
→ BLOCKING_GAPS_CLASSIFIED
→ MVP_BOUNDARY_SELECTED
→ ACCEPTANCE_BOUND
→ MVP_IMPLEMENTED_OR_PACKETED
→ EVIDENCE_EVALUATED
→ {GRADUATE | ITERATE | BLOCK}
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — verified base before MVP claims.** Separate grounded facts, assumptions, external unknowns, and product hypotheses before implementation.
- **CORE-LAW-002 — close only blocking gaps.** Research or design work that does not affect the MVP decision stays deferred rather than expanding scope.
- **CORE-LAW-003 — acceptance is falsifiable.** A demo or generated plan cannot substitute for explicit success/failure oracles on the exact MVP subject.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may bind providers/hosts but cannot override core laws, promote unsupported research, or widen provider/secret/merge authority.
- **CORE-LAW-005 — graduation is evidence-bounded.** The MVP graduates only for the scope actually exercised; unresolved production/legal/market/runtime lanes remain explicit.

## Procedure

1. Bind input subject, product question, users, constraints, and decision to be made.
2. Build a verified base from source evidence and explicitly mark assumptions/unknowns.
3. Classify which unknowns block the MVP decision and defer non-blocking research.
4. Select the smallest end-to-end slice that tests the riskiest material assumption.
5. Freeze acceptance, negative controls, budget, rollback, and evidence requirements before execution.
6. Implement or emit an executable task packet; concrete runtime/providers are selected only through `modules/domain-profile.md`.
7. Evaluate observed evidence and choose graduate, iterate, or block without discarding failed outcomes.
8. Handoff next-stage work with exact scope ceiling and unresolved lanes.

## Module selection

Load `modules/domain-profile.md` only when a concrete provider, prototype host, consumer loop, market profile, artifact route, or delivery environment must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill dr-to-mvp
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on accepted MVP evidence, a falsified assumption, unavailable blocking evidence, budget exhaustion, or Human-owned product/legal/release decisions. Handoff includes verified base, deferred gaps, MVP subject, outcomes, and next admissible slice.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
