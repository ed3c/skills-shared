---
name: autoresearch-composer
description: |
  Portable iterative-research composer for freezing an objective and evaluator, generating bounded candidate changes, running matched experiments, preserving regressions and failed arms, and stopping when improvement evidence is sufficient or the budget is exhausted. Host commands, prompt carriers, consumer registries, and runners are domain modules.
---

# Iterative Research Composer

<!-- PORTABLE_CORE_START -->

## Contract

The core owns objective/evaluator binding, candidate generation, matched experimentation, score comparison, bounded retry, and terminal handoff. Concrete host/runner/consumer mechanics live in `modules/domain-profile.md`.

## State machine

```text
OBJECTIVE_BOUND
→ EVALUATOR_FROZEN
→ BASELINE_BOUND
→ CANDIDATE_GENERATED
→ MATCHED_EXPERIMENT_RUN
→ RESULT_VALIDATED
→ {ADOPT | REJECT | ITERATE | BLOCK}
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — freeze objective and evaluator first.** Candidate generation cannot redefine success after results are visible.
- **CORE-LAW-002 — compare matched subjects.** Baseline and candidate runs must match all non-treatment identities and budgets.
- **CORE-LAW-003 — measured evidence outranks candidate prose.** A candidate description or runner success cannot prove improvement.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may bind runners/hosts but cannot alter frozen evaluation, hide failed arms, or widen runtime/secret/merge authority.
- **CORE-LAW-005 — iteration is bounded.** Every retry has a reason, budget, lineage, and terminal state; no-shrink/no-uplift loops stop.

## Procedure

1. Bind objective, exact subject, constraints, evaluator, hard gates, and cost budget.
2. Freeze baseline identity before generating the candidate treatment.
3. Generate the smallest candidate expected to improve the declared metric without violating hard gates.
4. Execute matched baseline/candidate cells through an admitted runner only when needed.
5. Validate run identity, artifacts, exclusions, and negative controls before scoring.
6. Adopt only evidence-supported improvement; preserve regressions and invalid experiments explicitly.
7. Iterate only while expected information gain justifies another bounded candidate.

## Module selection

Load `modules/domain-profile.md` only when a concrete command surface, prompt carrier, consumer registry, or experiment runner must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill autoresearch-composer
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on admitted improvement, hard regression, invalid matching, budget exhaustion, unavailable executor, or Human-owned promotion. Handoff includes objective, baseline/candidate identities, evaluator, results, controls, and remaining uncertainty.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
