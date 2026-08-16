---
name: html-for-decisions
description: |
  Portable decision-projection procedure for binding a decision source of truth, preserving claim/evidence links, compiling an inspectable projection, validating required states and interactions, packaging/readback, and handing the result to a Human decision owner. Concrete renderers, visual schemas, browser adapters, interaction profiles, and export channels are domain modules.
---

# Decision Projection Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns decision-SSOT binding, projection schema, evidence continuity, deterministic validation, packaging/readback, and Human decision handoff. Concrete renderers and channels live in `modules/domain-profile.md`.

## State machine

```text
DECISION_SSOT_BOUND
→ CLAIM_EVIDENCE_GRAPH_BOUND
→ PROJECTION_SCHEMA_BOUND
→ PROJECTION_RENDERED
→ STATES_AND_LINKS_ASSERTED
→ PACKAGE_READBACK_ASSERTED
→ HUMAN_DECISION_READY
```

## Hard laws

- **CORE-LAW-001 — source of truth is upstream.** The projection may organize or compress decisions but may not silently alter their claims, evidence, uncertainty, or authority.
- **CORE-LAW-002 — every material decision remains traceable.** Claims, alternatives, assumptions, risks, and evidence must survive projection with stable references.
- **CORE-LAW-003 — deterministic projection checks outrank appearance.** Visual polish or a successful render cannot substitute for link/state/coverage/readback assertions.
- **CORE-LAW-004 — modules cannot widen authority.** Renderer/channel modules may specialize output but cannot override laws, fabricate evidence, or widen browser/network/secret/merge authority.
- **CORE-LAW-005 — Human decision remains explicit.** A projection can make a decision ready; it cannot silently perform policy, legal, release, or business approval.

## Procedure

1. Bind the decision source, exact subject, audience, required decision questions, and evidence references.
2. Compile a projection schema containing decisions, options, causal links, assumptions, risks, unknowns, and evidence anchors.
3. Select a concrete renderer only through `modules/domain-profile.md` when needed.
4. Render without changing semantic content to satisfy layout constraints.
5. Assert required decision nodes, evidence links, interaction/state coverage, and accessibility/readability invariants appropriate to the output contract.
6. Package and read back the produced artifact; stale/missing assets or broken links fail closed.
7. Hand off to the Human decision owner with unresolved questions and evidence states visible.

## Module selection

Load `modules/domain-profile.md` only when a specific renderer, UI/data schema, browser adapter, visual style, interaction profile, or export channel must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill html-for-decisions
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when required semantic coverage and projection assertions pass, or when missing evidence/render/runtime authority blocks the next transition. Handoff includes decision subject, projection identity, evidence coverage, unresolved items, and Human-owned decision boundary.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
