---
name: dr-research-loop
description: |
  Portable research loop for binding a source and objective, extracting knowns, classifying unresolved claims, dispatching only evidence-worthy gaps to optional research capabilities, harvesting provenance, measuring coverage, and stopping on verified convergence or an explicit blocker. Source types, providers, scoring rubrics, consumer loops, and storage targets are domain modules.
---

# Evidence-Gated Research Loop

<!-- PORTABLE_CORE_START -->

## Contract

The core owns source/objective binding, known/unknown separation, research-gap routing, evidence harvest, convergence, and handoff. Concrete source/provider/market/consumer mechanics live in `modules/domain-profile.md`.

## State machine

```text
OBJECTIVE_BOUND
→ SOURCE_BOUND
→ KNOWN_SET_EXTRACTED
→ GAPS_CLASSIFIED
→ RESEARCH_PLAN_ADMITTED
→ EVIDENCE_HARVESTED
→ COVERAGE_ASSERTED
→ {ITERATE | CONVERGED | BLOCKED}
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — bind objective and subject.** Research begins from an exact source/objective and declared output contract.
- **CORE-LAW-002 — research only real gaps.** Existing grounded knowledge must not be re-researched merely because an optional provider exists.
- **CORE-LAW-003 — provenance outranks fluency.** Provider/model prose cannot become verified truth without source/provenance appropriate to the claim.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may specialize source/provider routing but cannot override laws, hide unresolved evidence, or widen network/secret/merge authority.
- **CORE-LAW-005 — convergence is measured.** Every iteration must shrink or reclassify the named gap set under a bounded budget and terminate with explicit residual gaps/evidence states.

## Procedure

1. Bind research objective, source subject, scope, constraints, and required deliverable.
2. Extract already-grounded claims and evidence references before requesting new research.
3. Classify gaps by claim type, importance, evidence need, and whether they are answerable.
4. Admit the smallest research plan that can falsify or close the material gaps.
5. Select concrete source/provider mechanics only through `modules/domain-profile.md`.
6. Harvest evidence with provenance and keep inference separate from observation.
7. Recompute coverage and preserve contradictory or unresolved claims in the denominator.
8. Iterate only while expected information gain justifies the next action; otherwise stop or hand off.

## Module selection

Load `modules/domain-profile.md` only for concrete source adapters, provider roles, proposal/market/license profiles, consumer loops, or storage targets.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill dr-research-loop
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on verified coverage, no-shrink iterations, unavailable evidence, policy/authority denial, subject drift, or budget exhaustion. Handoff binds objective, subject, evidence set, remaining gaps, and next admissible action.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
