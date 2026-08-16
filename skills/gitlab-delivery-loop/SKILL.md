---
name: gitlab-delivery-loop
description: |
  Portable forge-delivery procedure for exact-subject work-item binding, local verification, bounded publication, remote readback, integration admission, and merge handoff. Concrete host commands, request schemas, boards, runners, permissions, and publication adapters are selected through a domain module.
---

# Forge Delivery Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns delivery semantics, not a specific host. Concrete host mechanics live in `modules/domain-profile.md`.

## State machine

```text
INTENT_BOUND
→ SUBJECT_BOUND
→ WORK_ITEM_BOUND
→ LOCAL_VERIFIED
→ PUBLICATION_ADMITTED
→ REMOTE_PUBLISHED
→ REMOTE_REOBSERVED
→ INTEGRATION_ADMITTED
→ TERMINAL_RECEIPT
```

## Hard laws

- **CORE-LAW-001 — exact subject first.** Every work item, review, publication, and integration claim binds the same reviewed subject or records movement.
- **CORE-LAW-002 — evidence planes stay separate.** Local verification, provider transport, remote observation, CI, review, integration, and merge are not interchangeable.
- **CORE-LAW-003 — executable assertions outrank host state.** A green board, request, or command does not prove implementation correctness.
- **CORE-LAW-004 — modules cannot widen authority.** Host modules cannot override laws, weaken controls, reveal secrets, change access, or invent merge authority.
- **CORE-LAW-005 — terminal receipts are scoped and replayable.** Completion records exact subject, evidence states, blockers, and handoff authority.

## Procedure

1. Bind intent, artifact/repository subject, work item, allowed effects, and rollback subject.
2. Execute the owning local assertions before publication.
3. Select a fixed publication transition through `modules/domain-profile.md` only when a concrete host is bound.
4. Publish without treating transport success as code correctness.
5. Re-observe remote identity/state and reconcile against the reviewed subject.
6. Admit integration only after the required evidence closes on the current subject.
7. Emit a terminal receipt and hand off merge/release to the owning authority.

## Module selection

Load `modules/domain-profile.md` only for host-specific commands, schemas, permissions, board/runners, or publication policy.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill gitlab-delivery-loop
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on stale subject, failed local assertion, missing host adapter, semantic conflict, policy denial, or missing remote readback. Preserve the blocker rather than retrying until green.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).
