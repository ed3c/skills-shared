---
name: external-verify
description: |
  Portable external-claim verification procedure for decomposing claims, selecting the required source strength, discovering candidate sources, reading authoritative evidence back directly, preserving disagreement, grading confidence, and emitting a citation/evidence packet. Concrete search/fetch providers and host carriers are domain modules.
---

# External Claim Verification

<!-- PORTABLE_CORE_START -->

## Contract

The core owns claim decomposition, evidence requirements, source authority, readback, contradiction handling, citation packet construction, and terminal verification state. Retrieval providers live in `modules/domain-profile.md`.

## State machine

```text
CLAIM_BOUND
→ EVIDENCE_REQUIREMENT_BOUND
→ SOURCE_CANDIDATES_DISCOVERED
→ AUTHORITATIVE_SOURCE_READ
→ CLAIM_EVIDENCE_MAPPED
→ CONTRADICTIONS_RECONCILED
→ VERDICT_DERIVED
→ CITATION_PACKET_EMITTED
```

## Hard laws

- **CORE-LAW-001 — claim granularity is explicit.** Verify atomic claims against a declared evidence requirement rather than treating a paragraph as one truth unit.
- **CORE-LAW-002 — source authority matches claim strength.** Prefer primary/official/current sources when the claim requires them; discovery ranking is not authority.
- **CORE-LAW-003 — direct readback outranks snippets.** Search/provider summaries are candidate pointers until the supporting source is read and mapped to the claim.
- **CORE-LAW-004 — modules cannot widen authority.** Retrieval modules cannot override evidence rules, hide disagreement, or widen network/secret/merge authority.
- **CORE-LAW-005 — verdicts preserve uncertainty.** Unsupported, conflicting, stale, absent, and not-exercised states remain explicit and scoped.

## Procedure

1. Decompose the requested statement into atomic externally verifiable claims.
2. Bind required freshness, jurisdiction/version, source class, and success/failure criteria per claim.
3. Discover candidate sources through an admitted retrieval lane when needed.
4. Read authoritative source content directly and bind locator/date/version.
5. Map each claim to supporting, contradicting, or missing evidence without inference inflation.
6. Reconcile source disagreement by scope, date, authority, and exact wording.
7. Emit verdict, confidence/evidence state, source references, and explicit non-claims.

## Module selection

Load `modules/domain-profile.md` only when a concrete search/fetch provider, browser carrier, source API, or consumer verification adapter must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill external-verify
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when the claim is sufficiently supported/falsified, required authoritative evidence is unavailable, sources remain irreducibly conflicting, or retrieval authority is absent. Handoff includes claim map, source map, disagreement, evidence states, and next admissible verification lane.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
