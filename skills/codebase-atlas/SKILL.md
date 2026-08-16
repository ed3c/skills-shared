---
name: codebase-atlas
description: |
  Portable architecture-atlas procedure for inventorying a repository, deriving an evidence-bound topology, compiling a renderer-neutral projection model, asserting structural and interaction coverage, and handing off a share-safe artifact. Concrete visual styles, projection formulas, browser adapters, screenshot matrices, and export profiles are domain modules.
---

# Codebase Atlas Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns repository inventory, evidence-bound topology, projection schema, coverage assertions, interaction requirements, artifact readback, and handoff. Concrete rendering/browser/export profiles live in `modules/domain-profile.md`.

## State machine

```text
REPOSITORY_BOUND
→ INVENTORY_CAPTURED
→ ARCHITECTURE_GRAPH_DERIVED
→ EVIDENCE_LINKS_BOUND
→ PROJECTION_MODEL_COMPILED
→ COVERAGE_ASSERTED
→ ARTIFACT_READBACK_ASSERTED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — repository evidence first.** Architecture nodes, edges, ownership, and counts are derived from the bound repository subject or explicitly weaker evidence.
- **CORE-LAW-002 — model is renderer-neutral.** Visual style, viewport, browser, and projection implementation cannot define architecture truth.
- **CORE-LAW-003 — coverage is executable.** A visually convincing artifact cannot substitute for node/edge/source/interaction/readback assertions.
- **CORE-LAW-004 — modules cannot widen authority.** Renderer modules may specialize presentation but cannot alter architecture facts, hide uncovered areas, or widen browser/network/secret/merge authority.
- **CORE-LAW-005 — artifact claims are scoped.** Share-safety, interaction coverage, and architecture evidence remain separate terminal claims bound to the exact repository/projection subject.

## Procedure

1. Bind repository commit/tree, included/excluded paths, audience, and requested architecture questions.
2. Inventory entry points, packages/components, interfaces, dependencies, state/data flow, runtime surfaces, and evidence anchors.
3. Derive a typed architecture graph whose facts retain source references and evidence classes.
4. Compile a renderer-neutral projection model with stable node/edge identities and required interaction states.
5. Select a concrete renderer/browser/export profile only through `modules/domain-profile.md` when needed.
6. Assert architecture coverage, evidence links, interaction/state requirements, and unsupported-area disclosure.
7. Read back the produced artifact and verify subject identity, links/assets, and share-safety constraints appropriate to the selected profile.

## Module selection

Load `modules/domain-profile.md` only when a concrete renderer, visual style, projection formula, browser adapter, screenshot matrix, interaction profile, or export/share-safety implementation must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill codebase-atlas
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when architecture/coverage/readback requirements pass, or when missing repository/runtime/rendering evidence blocks the requested claim. Handoff includes repository subject, graph/projection identity, uncovered areas, evidence states, and selected profile when any.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
