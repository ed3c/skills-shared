---
name: forgejo-delivery-loop
description: |
  Portable forge-delivery procedure for binding an exact local artifact to a tracked work item, verifying it, admitting publication, re-observing the remote result, and handing off integration without treating any forge, credential path, browser session, or local service as universal law.
---

# Forge Delivery Procedure

<!-- PORTABLE_CORE_START -->

## Contract

This core owns the delivery state machine and evidence boundary. Concrete host APIs, credentials, local services, tracking projections, and consumer bindings are selected through `modules/domain-profile.md`.

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

- **CORE-LAW-001 — bind exact subject.** Every delivery claim names the artifact/repository subject it applies to.
- **CORE-LAW-002 — local evidence is not remote evidence.** Verification, publication, remote observation, integration, and merge remain separate states.
- **CORE-LAW-003 — executable verification outranks prose.** A checklist, issue state, or API success cannot substitute for implementation assertions.
- **CORE-LAW-004 — modules cannot widen authority.** Host modules may implement fixed transitions but may not override laws, expose secrets, change visibility, or invent merge authority.
- **CORE-LAW-005 — terminal receipts are scoped.** Every terminal state records subject, work item, evidence state, residual blockers, and next authority.

## Procedure

1. Bind intent, repository/artifact subject, work item, rollback subject, and allowed effects.
2. Verify implementation locally with the owning deterministic assertions.
3. Admit a bounded publication transition; arbitrary shell/ambient authority is not publication policy.
4. Execute the selected host operation only through a module selected by explicit runtime binding.
5. Re-observe the remote artifact and reconcile identity/ancestry/state.
6. Admit integration only for the reviewed subject; stale receipts fail closed.
7. Emit a terminal receipt and hand off merge/release to the owning authority unless explicitly delegated by a pre-existing policy.

## Module selection

Load `modules/domain-profile.md` only for concrete host/API/session/tracking mechanics. Host choice cannot alter the core state machine.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill forgejo-delivery-loop
```

## Evidence states

Use `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED` without collapsing them.

## Stop and handoff

Stop on failed local verification, missing host capability, stale subject, semantic conflict, policy denial, or missing remote readback. Preserve the exact blocker in the receipt.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md) for host-specific mechanics.

## Mechanism index

The portable core routes to these owned mechanisms without importing their host semantics into the bounded core:

- `modules/README.md`
- `modules/commit-role.md`
- `modules/delivery-mechanism.md`
- `modules/domain-profile.md`
- `modules/forgejo-operations.md`
- `scripts/README.md`
- `scripts/agent_docs.py`
- `scripts/issue_state.py`
- `scripts/pre-commit-agent-docs.sh`
- `scripts/route.ts`
- `contracts/forgejo-issue-state-observation.v1.schema.json`
- `contracts/forgejo-issue-state-readback-receipt.v1.schema.json`
- `contracts/forgejo-terminal-issue-state-request.v2.schema.json`
