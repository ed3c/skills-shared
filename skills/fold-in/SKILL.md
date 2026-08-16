---
name: fold-in
description: |
  Portable knowledge fold-in procedure for deciding whether a newly learned item belongs in durable procedure, factual context, rationale/decision history, a trigger-selected domain module, or nowhere permanent; then anchoring load-bearing procedure with executable regression evidence and preserving provenance. Consumer taxonomies, repository lineage, and host-specific ownership are domain modules.
---

# Knowledge Fold-In Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns durable-owner classification, procedure/fact/rationale/domain separation, provenance, executable regression anchoring, verification, and handoff. Concrete consumer owner maps live in `modules/domain-profile.md`.

## State machine

```text
NEW_KNOWLEDGE_BOUND
→ CLASSIFIED
→ DURABLE_OWNER_SELECTED
→ CONTENT_MINIMIZED
→ REGRESSION_ANCHOR_BOUND
→ OWNER_UPDATED
→ READBACK_VERIFIED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — classify before storing.** Separate reusable procedure, observed fact, rationale/decision, domain instance, and transient runtime state before choosing an owner.
- **CORE-LAW-002 — only durable truth enters canonical procedure.** Consumer paths, live provider state, branch/session identities, and one-off examples do not become global law.
- **CORE-LAW-003 — load-bearing procedure needs executable regression evidence.** Documentation-only memory cannot create `PASS` or prove that a rule prevents the failure it describes.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may select repository-specific owners/bindings but cannot override laws, delete provenance, or widen provider/secret/merge authority.
- **CORE-LAW-005 — fold-in is reversible and traceable.** Every mutation preserves source/provenance, reason, exact subject, verification state, and rollback/handoff path.

## Procedure

1. Bind the new knowledge item, source, exact subject, and why it matters.
2. Classify it as reusable procedure, factual context, rationale/decision, domain instance, transient runtime state, or reject/defer.
3. Select the narrowest durable owner; if none exists, preserve an explicit handoff instead of inventing a canonical home.
4. Reduce the content to the durable rule/fact/rationale and move consumer/provider specifics to a trigger-selected module/binding.
5. For load-bearing procedure, bind a positive and falsifying executable assertion or existing regression owner.
6. Update the owner without deleting unique historical/provenance evidence.
7. Read back the exact bytes and run the owning assertion before calling the fold-in complete.

## Module selection

Load `modules/domain-profile.md` only when a concrete consumer owner map, repository lineage, host built-in, migration path, or storage convention is required.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill fold-in
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when no durable owner exists, provenance is insufficient, the proposed rule lacks executable evidence, or a Human-owned semantic/legal decision is required. Handoff includes classification, proposed owner, source, evidence gap, and next admissible action.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
