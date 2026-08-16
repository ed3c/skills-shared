---
name: truth-verify-loop
description: |
  Portable truth-verification procedure for binding a claim and exact subject, choosing the required evidence class, collecting independent evidence, preserving contradictions and absences, applying deterministic vetoes, and emitting a scoped terminal truth state. Concrete judges, providers, fixtures, runtimes, and consumer instances are domain modules.
---

# Truth Verification Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns claim/subject binding, evidence-class selection, independence, contradiction handling, falsification, and terminal truth state. Concrete judge/provider/runtime/fixture choices live in `modules/domain-profile.md`.

## State machine

```text
CLAIM_BOUND
→ SUBJECT_BOUND
→ EVIDENCE_CONTRACT_BOUND
→ EVIDENCE_COLLECTED
→ CONTRADICTIONS_RECONCILED
→ FALSIFYING_CONTROL_RUN
→ VERDICT_DERIVED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — exact claim and subject.** A verdict without a bound claim, scope, and exact subject is invalid.
- **CORE-LAW-002 — evidence class matches claim strength.** Static, deterministic, semantic, runtime, and Human evidence are not interchangeable.
- **CORE-LAW-003 — independent evidence outranks self-report.** A producer cannot certify its own unsupported claim; deterministic vetoes cannot be overruled by advisory prose.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may provide evidence/judge adapters but cannot override laws, suppress contradictions, or widen provider/secret/merge authority.
- **CORE-LAW-005 — verdicts are scoped and falsifiable.** Terminal state records supporting evidence, contradicting evidence, controls, uncertainty, subject, and non-claims.

## Procedure

1. Normalize the claim, subject, scope, success criterion, and failure criterion.
2. Select the minimum evidence class capable of proving or falsifying the claim.
3. Collect primary/direct evidence first; add independent semantic/Human judgment only where deterministic evidence is insufficient.
4. Preserve contradictions, missing evidence, stale subjects, and unsupported coverage as explicit states.
5. Run a falsifying control or counterexample appropriate to the claim class.
6. Derive the verdict mechanically where possible; advisory judges may explain but not override hard failures.
7. Emit a scoped receipt and hand off unresolved claims to the next evidence owner.

## Module selection

Load `modules/domain-profile.md` only when a concrete judge, provider, fixture, runtime carrier, or consumer instance must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill truth-verify-loop
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on a decisive falsification, sufficient verified evidence, unavailable required evidence, subject drift, or authority denial. Handoff includes claim, subject, evidence contract, all evidence states, contradictions, and next admissible evidence lane.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
