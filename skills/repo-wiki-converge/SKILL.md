---
name: repo-wiki-converge
description: |
  Generalized repository-to-wiki convergence procedure: bind an exact repository subject, extract grounded facts, separate author and judge roles, iterate only on evidence-backed defects, and stop when declared coverage and verification criteria are met. Provider models, wiki engines, knowledge-base transports, and consumer paths are domain modules rather than core law.
---

# Repository Wiki Convergence Procedure

<!-- PORTABLE_CORE_START -->

## Contract

Use this Skill when the task is to turn a readable repository into a reviewable explanatory corpus or wiki and converge it against repository ground truth. The core owns subject binding, author/judge separation, claim verification, coverage, bounded repair, and terminal handoff. Concrete execution profiles live in `modules/domain-profile.md`.

## State machine

```text
REPOSITORY_BOUND
→ FACT_SURFACE_MAPPED
→ AUTHOR_DRAFTED
→ CLAIMS_JUDGED
→ DEFECTS_CLASSIFIED
→ {REVISE | ACCEPT | BLOCK}
→ CONVERGENCE_ASSERTED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — exact repository subject.** Every draft and judgment binds the same immutable repository subject or explicitly records subject movement.
- **CORE-LAW-002 — author and judge are distinct responsibilities.** A writer cannot certify its own unsupported claims; concrete actor/provider choices live outside the core.
- **CORE-LAW-003 — source evidence wins.** Repository source/readback and deterministic checks outrank model confidence, prose quality, or successful publication.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may select author/judge/transport implementations but may not override laws or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — convergence is bounded and falsifiable.** Acceptance requires declared claim/coverage criteria, preserved defects, evidence states, and a terminal receipt or handoff.

## Procedure

1. Bind repository commit/tree, scope, excluded paths, target audience, and required output contract.
2. Map architecture, entry points, invariants, interfaces, failure paths, and evidence sources before drafting.
3. Produce a draft whose repository facts carry source references or explicitly weaker evidence states.
4. Judge claims against the bound subject; classify unsupported, stale, incomplete, contradictory, and merely stylistic findings separately.
5. Revise only evidence-bearing defects; never use reviewer prose alone as proof that a repository fact changed.
6. Re-run claim and coverage assertions on the same subject after each revision.
7. Stop on acceptance, blocked evidence, budget exhaustion, or subject drift requiring rebind.

## Module selection

Load `modules/domain-profile.md` only when a concrete author/judge implementation, wiki generator, publication transport, knowledge store, or consumer binding is required.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill repo-wiki-converge
```

## Evidence states

Keep `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED` distinct. Draft generation or successful transport alone cannot become convergence `PASS`.

## Stop and handoff

Handoff binds repository subject, accepted and unresolved claims, coverage criteria, evidence states, domain/runtime identities when used, and the next admissible action. Subject movement invalidates stale claim receipts.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Existing specialist modules remain optional extensions and may not replace the portable laws.
