---
name: dual-forge-repository-loop
description: |
  Portable two-plane repository procedure for binding exact local and remote subjects, implementing on the admitted local plane, verifying before publication, reconciling ancestry and remote state, publishing only a current verified candidate, and preserving distinct evidence states for every plane. Concrete forge hosts, CI providers, desktop/model carriers, credentials, remotes, and consumer bindings are domain modules.
---

# Dual-Plane Repository Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns two-plane subject identity, local-first implementation, verification, ancestry/state reconciliation, publication admission, evidence separation, and handoff. Concrete host/runtime mechanics live in `modules/domain-profile.md`.

## State machine

```text
PLANES_BOUND
→ EXACT_SUBJECTS_BOUND
→ LOCAL_IMPLEMENTATION_ADMITTED
→ LOCAL_VERIFIED
→ LOCAL_INTEGRATION_BOUND
→ REMOTE_STATE_REOBSERVED
→ ANCESTRY_RECONCILED
→ PUBLICATION_CANDIDATE_ADMITTED
→ TERMINAL_RECEIPT
```

## Hard laws

- **CORE-LAW-001 — every plane has an exact subject.** Repository, branch, commit/tree, work item, and publication identities are explicit before a cross-plane claim is made.
- **CORE-LAW-002 — one plane cannot proxy another.** Local verification, remote host observation, CI, publication, review, integration, and merge remain distinct evidence states.
- **CORE-LAW-003 — local verified subject precedes publication.** Remote transport cannot be used as a substitute for implementation correctness or current-source readback.
- **CORE-LAW-004 — modules cannot widen authority.** Host modules may bind concrete planes/adapters but cannot conflate evidence, auto-resolve semantic conflicts, change access/visibility, expose secrets, or create merge authority.
- **CORE-LAW-005 — publication requires current ancestry reconciliation.** A candidate must contain admitted local integration and reconcile with the currently observed remote base; stale observations/receipts fail closed.

## Procedure

1. Bind each repository/transport plane, exact current subjects, permitted effects, privacy boundary, and rollback subjects.
2. Select the implementation plane and isolate work according to the owning branch/worktree/lease procedure.
3. Implement and run local deterministic assertions before any publication claim.
4. Integrate locally only after slice verification and preserve the exact integrated subject.
5. Re-observe the remote base, work items, open review state, and relevant provider evidence instead of trusting cached state.
6. Prove ancestry/reconciliation between local integrated subject and the current remote base; semantic conflicts stop.
7. Admit a publication candidate only when current local verification and remote reconciliation apply to the same candidate.
8. Execute concrete transport only through `modules/domain-profile.md`, then read back the remote result and emit a plane-scoped terminal receipt.

## Module selection

Load `modules/domain-profile.md` only when concrete forge hosts, CI providers, desktop/runtime carriers, credentials, remotes, issue/PR identities, or publication adapters must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill dual-forge-repository-loop
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED` per plane.

## Stop and handoff

Stop on failed local assertions, stale remote observation, ancestry mismatch, semantic conflict, unavailable required plane, privacy/authority denial, or Human-owned merge/release. Handoff includes exact subjects for every plane, verification/reconciliation states, candidate identity, blockers, and rollback subjects.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Existing mode-specific subtrees remain trigger-selected implementations and may not replace the portable laws.
