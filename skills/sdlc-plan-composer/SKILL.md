---
name: sdlc-plan-composer
description: |
  Portable SDLC planning procedure for classifying a change, matching required capabilities, extracting invariants, decomposing true dependencies into reviewable slices, defining interfaces and validation, and handing executable task packets to implementation owners. Repository layouts, model/actor mappings, host carriers, and consumer catalogs are domain modules.
---

# SDLC Plan Composer

<!-- PORTABLE_CORE_START -->

## Contract

The core owns task classification, capability requirements, invariant extraction, dependency graph, slice ownership, interface contracts, validation design, and handoff. Concrete planning layouts and actors live in `modules/domain-profile.md`.

## State machine

```text
REQUEST_CLASSIFIED
→ CAPABILITIES_BOUND
→ INVARIANTS_EXTRACTED
→ DEPENDENCY_GRAPH_BUILT
→ SLICES_OWNED
→ INTERFACES_BOUND
→ VALIDATION_BOUND
→ TASK_PACKETS_EMITTED
→ HANDOFF
```

## Hard laws

- **CORE-LAW-001 — plan from constraints and invariants.** A task graph begins from exact requirements, non-goals, current subject, and hard invariants rather than preferred implementation shape.
- **CORE-LAW-002 — dependencies must be real.** A child exists only when it consumes a parent contract/bytes/state; path-disjoint work remains sibling work.
- **CORE-LAW-003 — validation is designed before implementation.** Every material slice has acceptance criteria, falsifying controls, and an owning evidence source.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may select layouts/actors but cannot override invariants, fabricate dependencies, weaken validation, or widen provider/secret/merge authority.
- **CORE-LAW-005 — task packets are executable and bounded.** Each slice records exact subject, allowed paths/effects, dependencies, interfaces, tests, rollback/handoff, and terminal state.

## Procedure

1. Bind request, exact repository/product subject, scope, non-goals, risks, and authority boundary.
2. Classify required capabilities and evidence surfaces before choosing actors/tools.
3. Extract invariants, unknowns, external dependencies, compatibility constraints, and rollback requirements.
4. Build a dependency DAG using true consumed contracts/state only.
5. Assign one owner and non-overlapping mutation scope per active slice.
6. Define interface contracts between dependent slices and convergence ownership for shared indexes/state.
7. Define deterministic assertions, negative controls, runtime evidence lanes, and Human gates before coding.
8. Emit bounded task packets in dependency order and hand them to implementation/runtime owners.

## Module selection

Load `modules/domain-profile.md` only when repository-specific plan layout, actor/provider mapping, host carrier, downstream catalog, or consumer delivery convention must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill sdlc-plan-composer
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop when dependencies cannot be proven, required capabilities/authority are unavailable, validation ownership is missing, or the task requires Human scoping. Handoff includes DAG, invariants, task packets, interfaces, validation, risks, and unresolved unknowns.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
