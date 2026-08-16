---
name: loop-harness-review-handoff
description: |
  Portable exact-subject review-handoff procedure for building a zero-access review packet, separating reviewer identity from producer identity, anchoring findings to evidence, preserving dissent and uncertainty, and handing findings to Human/trusted authority without granting the reviewer merge or release power. Concrete reviewer models, providers, carriers, and consumer routes are domain modules.
---

# Review Handoff Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns exact-subject packet construction, reviewer independence, evidence anchoring, findings-only output, dissent preservation, and authority handoff. Concrete reviewer implementations live in `modules/domain-profile.md`.

## State machine

```text
SUBJECT_BOUND
→ REVIEW_CONTRACT_BOUND
→ ZERO_ACCESS_PACKET_BUILT
→ REVIEWER_INDEPENDENCE_BOUND
→ REVIEW_EXECUTED
→ FINDINGS_EVIDENCE_MAPPED
→ DISSENT_PRESERVED
→ AUTHORITY_HANDOFF
```

## Hard laws

- **CORE-LAW-001 — review exact bytes/subject.** Findings bind the artifact, repository, evaluator, and evidence identities actually reviewed.
- **CORE-LAW-002 — reviewer independence is declared.** Same-context, separate-context, separate-model, deterministic checker, and Human review are distinct evidence classes.
- **CORE-LAW-003 — findings require evidence anchors.** Reviewer prose cannot override deterministic failure or become proof without the evidence class required by the claim.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may select a reviewer/carrier but cannot suppress dissent, request private reasoning, or widen provider/secret/merge authority.
- **CORE-LAW-005 — review is findings-only unless authority is separately delegated.** Merge, release, promotion, legal, and policy admission remain external terminal decisions.

## Procedure

1. Bind exact subject, review questions, acceptance criteria, evidence references, and non-goals.
2. Build a zero-access packet sufficient for review without requiring hidden/private reasoning or ambient repository knowledge.
3. Declare the required reviewer independence and capability before selecting an implementation.
4. Select concrete reviewer mechanics only through `modules/domain-profile.md` when needed.
5. Capture findings with severity, evidence anchors, uncertainty, and explicit non-findings.
6. Preserve valid dissent and deterministic vetoes even when a majority or fluent reviewer disagrees.
7. Hand off findings to the owning Human/trusted authority; do not convert review completion into merge/release completion.

## Module selection

Load `modules/domain-profile.md` only when a concrete reviewer/model/provider, host carrier, consumer route, or family-specific review policy must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill loop-harness-review-handoff
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on decisive deterministic failure, insufficient evidence, unavailable required independence, or completion of the review contract. Handoff includes exact subject, findings, evidence anchors, dissent, uncertainty, and next authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
