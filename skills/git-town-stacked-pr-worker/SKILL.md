---
name: git-town-stacked-pr-worker
description: |
  Portable stacked-branch worker procedure for representing only true dependency edges, isolating each writer in its own worktree/branch, assigning disjoint path/resource leases, synchronizing boundedly without semantic auto-resolution, re-verifying moved subjects, and handing off review/publication. Concrete forge publication, CI, installer, branch-policy, and remote conventions are domain modules.
---

# Stacked Branch Worker Procedure

<!-- PORTABLE_CORE_START -->

## Contract

The core owns true branch dependencies, isolated writer ownership, path/resource leases, bounded synchronization, stale-result rejection, semantic-conflict refusal, re-verification, and stacked handoff. Concrete publication/host mechanics live in `modules/domain-profile.md`.

## State machine

```text
TASK_GRAPH_BOUND
→ BRANCH_GRAPH_BOUND
→ WORKTREES_ISOLATED
→ LEASES_ADMITTED
→ IMPLEMENTATION_VERIFIED
→ SYNC_ADMITTED
→ GRAPH_SYNCHRONIZED
→ MOVED_SUBJECT_REVERIFIED
→ REVIEW_HANDOFF
```

## Hard laws

- **CORE-LAW-001 — stack edges represent consumed dependencies only.** Path-disjoint sibling work must not be serialized merely for convenience.
- **CORE-LAW-002 — one writer per active mutation subject.** Branch/worktree/path/resource ownership is explicit and overlapping active leases fail closed.
- **CORE-LAW-003 — synchronization is not correctness.** A successful graph/sync operation cannot substitute for the owning implementation assertions after movement.
- **CORE-LAW-004 — modules cannot widen authority.** Domain modules may bind a stack tool/host but cannot fabricate dependencies, auto-resolve semantic conflicts, reuse stale evidence, or widen push/merge/secret authority.
- **CORE-LAW-005 — moved subjects require fresh evidence.** Parent movement, rebase, conflict resolution, or synchronization invalidates stale exact-head receipts for affected children.
- **CORE-LAW-006 — the Stack index is derived, and every required atom is indexed.** `required_atoms` is declared before the work starts over the atom classes `C` contract/schema/interface lock, `K` deterministic core, `A` adapter/provider/substrate, `E` Eval/mutation/fault controls, `X` explicit multi-parent convergence/E2E, and `D` documentation/receipt/handoff. The index is derived from observed Issues, branches, PR heads, trees, parents, changed paths and Gates — never from branch names or the order the work happened to be written in. Deriving the required atoms and then indexing fewer of them is an unmeasured gap, not a smaller Stack; an atom with no paths, no oracle and no Gate is ceremonial and fails closed. Mechanism: `references/MOLECULAR_STACK_INDEX.md`.
- **CORE-LAW-007 — an indexed atom carries its lane, its blockers and whether it may be built on.** Every atom declares one lane and every Gate declares both the lane it requires and the lane its receipt came from; a receipt satisfies only its own lane, an unexercised Gate is null rather than absent, and a published atom may not consume a private-lane parent, because laundering through ancestry needs no forged receipt. A `review-only` atom writes nothing, is never a parent and never merges — it is opened to be read, and an index without that class offers only one way to record it, as something the next Worker may base work on. Open `blockers` stay on the atom; a merged atom carrying a blocker or an unexercised Gate has been smoothed into completion. Mechanism: `references/MOLECULAR_STACK_INDEX.md`.

## Procedure

1. Bind task DAG, exact repository subject, branch graph, path/resource scopes, and verification owners.
2. Create a child edge only when the child consumes unmerged parent contract/bytes/state; otherwise keep work as siblings.
3. Isolate each active writer in a dedicated worktree/branch and admit disjoint leases.
4. Implement and verify each slice on its exact subject before synchronization.
5. Admit bounded synchronization with push/merge disabled unless separately authorized; semantic conflicts stop rather than auto-resolve.
6. After graph movement, rebind exact heads and rerun affected assertions.
7. Hand off the verified branch graph to review/publication authority; branch topology alone creates no publication or merge authority.

## Module selection

Load `modules/domain-profile.md` only when a concrete stack tool, Git host, publication provider, CI carrier, installer/runtime binding, branch naming policy, or consumer convention must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill git-town-stacked-pr-worker
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`.

## Stop and handoff

Stop on overlapping leases, false dependency edges, semantic conflict, failed post-sync verification, unavailable required tool, or Human-owned publication/merge. Handoff includes graph, heads, leases, verification receipts, stale invalidations, and next authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md).

## Publication compatibility contract

These host-specific composition markers remain outside the portable-core boundary so the existing publication Harness keeps its exact safety contract while provider semantics stay modular.

Compose the target Agent instruction surface from the **contents**, not file paths, of [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) and [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md).

Publication profile references:

- `GITHUB_ACTIONS_PUBLICATION_ADOPTION.md`
- `GITHUB_ACTIONS_PUBLICATION_PROFILE.template.md`
- `GITHUB_ACTIONS_PUBLICATION_EVALS.md`
- `GITHUB_ACTIONS_PUBLICATION_REPORT.template.md`
- composition owner: `github-delivery-loop`

Admitted publication intents remain exactly `initial-pr`, `ready-for-review`, and `batched-repair`. The provider circuit remains fail-closed on `billing-open`, stale local verification, old-SHA checks, repeated feedback, or ambiguous PR identity.

Background synchronization may never invoke `git town sync --push`.

Keep local sync, local verification, publication decision, remote publication as mechanically separate evidence states.
