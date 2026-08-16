---
name: judge-loop-chooser
description: |
  Portable judge-loop selection procedure for classifying the deliverable and risk, binding required evidence and independence, constructing a zero-access review packet, choosing an admissible judge capability, and handing final authority to the correct owner. Concrete model/provider mappings, consumer registries, and host carriers are domain modules.
---

# Judge Loop Chooser

<!-- PORTABLE_CORE_START -->

## Contract

The core owns deliverable/risk classification, evidence tier, independence level, review packet, judge-capability requirements, and Human Admit routing. Concrete judge implementations live in `modules/domain-profile.md`.

## State machine

```text
DELIVERABLE_CLASSIFIED
→ RISK_BOUND
→ EVIDENCE_TIER_BOUND
→ INDEPENDENCE_BOUND
→ REVIEW_PACKET_BUILT
→ JUDGE_CAPABILITY_SELECTED
→ VERDICT_CAPTURED
→ AUTHORITY_HANDOFF
```

## Hard laws

- **CORE-LAW-001 — choose from deliverable and risk, not favorite actor.** Judge requirements are derived before choosing an implementation.
- **CORE-LAW-002 — independence is explicit.** Self-review, same-context review, separate-context review, separate-model review, deterministic verification, and Human judgment are distinct capabilities.
- **CORE-LAW-003 — evidence contract outranks judge prose.** A judge cannot promote unsupported evidence or override deterministic failure.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may map capabilities to concrete actors but cannot downgrade required independence or widen provider/secret/merge authority.
- **CORE-LAW-005 — final authority is scoped.** Review verdict, merge/release/legal/business admission, and promotion remain separate terminal authorities.

## Procedure

1. Classify deliverable type, blast radius, reversibility, uncertainty, and downstream authority.
2. Bind the minimum evidence tier and required reviewer independence.
3. Build a zero-access packet containing exact subject, claims, artifacts, acceptance criteria, and evidence references without private reasoning.
4. Define the judge capability contract before selecting an implementation.
5. Select a concrete implementation only through `modules/domain-profile.md` when needed.
6. Capture findings, verdict, evidence references, uncertainty, and dissent separately.
7. Hand off the result to the correct authority; a reviewer cannot silently acquire merge/release/legal authority.

## Module selection

Load `modules/domain-profile.md` only when a concrete judge/model/provider, consumer registry, family taxonomy, or host carrier must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill judge-loop-chooser
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when the required judge capability is unavailable, independence cannot be established, deterministic failure is found, or final Human/trusted authority is required. Handoff includes deliverable class, evidence tier, independence, verdict, dissent, and next authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
