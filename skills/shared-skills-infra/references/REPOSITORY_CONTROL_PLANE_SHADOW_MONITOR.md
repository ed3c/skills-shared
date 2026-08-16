# Repository Control Plane — Shadow Architect Monitor Contract

Tracking: #298. Canonical Shadow runtime remains `skills/procedural-shadow-runtime`; this document only fixes how repository-control-plane implementation slices consume that runtime law.

## Purpose

The Shadow Architect is a read-only pre-side-effect and close-gate monitor. It observes public task/plan/action-intent and exact repository subjects. It does not receive private reasoning, mutate provider state, resolve semantic conflicts, install host tools, merge, change visibility, or widen filesystem/network/secret authority.

## Candidate receipt

Every repository-control-plane implementation candidate must be reviewable as this public tuple:

```text
base_subject        exact base commit/tree
head_subject        exact candidate commit/tree
semantic_delta      portable law/contract being changed
forbidden_delta     authority/provider/domain changes that must remain absent
required_gates      deterministic commands/assertions for this exact head
runtime_lanes       PASS | ABSENT | NOT_EXERCISED per capability lane
shadow_findings     open critical findings and owning issue IDs
terminal_state      ADMIT | BLOCK | SUPERSEDED | NOT_EXERCISED
```

A receipt is invalid when any subject is a mutable branch name without an exact commit, when a static gate is promoted into live runtime evidence, or when an unresolved critical finding has no owning issue.

## Admission laws

1. Current `main` is authoritative for already-landed #268 procedural-core/domain separation. A reconciliation slice may add a semantic superset but must not restore pre-#268 bodies.
2. Canonical Skill bodies stay in `skills-shared`. Consumer repositories receive only thin requirements/bindings, repository-local policy/adapters and receipts.
3. Binding a capability never implies executing it. `STACK_DELIVERY` and `FORGE_RECONCILIATION` are `NOT_APPLICABLE_WITH_EVIDENCE` unless the exact work item requires them.
4. A child branch/PR is justified only when it consumes unmerged parent bytes/contracts. Path-disjoint work remains sibling work; no fake Git Town stack is created to match a checklist.
5. The zero-network Tech Lead planner must fail closed on missing dependency closure. Provider adapters may assemble the packet but cannot weaken exact-subject DAG laws.
6. Git Town installation remains runtime-env-owned and user-scoped. Forgejo service lifecycle remains runtime-env/host-owned and host-scoped.
7. Automatic merge, automatic semantic conflict resolution, visibility changes, credential values and provider-data egress remain outside this monitor's authority.
8. CI/static success proves only the named deterministic contract for the exact candidate. Git Town, Forgejo, consumer execution, publication, merge and promotion remain `NOT_EXERCISED` without exact live receipts.

## Close gate

A control-plane slice may be marked structurally converged only when:

```text
all admitted deterministic gates pass on the exact head
AND no forbidden delta is present
AND every critical Shadow finding is repaired or has an explicit open owner
AND all live/runtime lanes are truthfully classified
```

`ADMIT` here means the portable repository contract is eligible for repository review/merge under repository policy. It does not itself authorize merge or promotion.
