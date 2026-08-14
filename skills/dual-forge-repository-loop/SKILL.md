---
name: dual-forge-repository-loop
description: |
  Coordinate a private GitHub repository, GitHub Actions, a local checkout, a local Forgejo implementation forge, isolated worktrees, and final GitHub publication as one evidence-bound delivery loop. Use when ChatGPT on iOS/macOS or another GitHub-connected agent reads a private GitHub repo, implementation should happen through local Forgejo issues/PRs and worktrees, verified changes merge to local main first, then GitHub remote drift/open PR conflicts/issues must be reconciled before exact-head Actions and GitHub publication. NOT for single-forge delivery or as authority to force-push, auto-merge, widen permissions, or fabricate local/Forgejo execution.
license: MIT
compatibility: Any Agent Skills-compatible coding agent. GitHub-connected hosts may perform GitHub operations; local Forgejo/worktree operations require a consumer runtime that actually has that local capability.
metadata:
  version: "1.0.0"
  procedure: "dual-forge-repository-loop/v1"
---

# dual-forge-repository-loop

Treat GitHub and local Forgejo as two distinct control planes over one Git object graph.

```text
GitHub plane
  = private-repository ingress + remote collaboration + GitHub Actions + publication evidence

Local/Forgejo plane
  = implementation issues + isolated worktrees + local verification + Forgejo PRs + local-main integration
```

Neither plane proves the other. Every transition across the boundary binds exact commit SHA and ancestry.

## Composition

This Skill orchestrates, but does not duplicate:

- `spatial-loop-systems-engineering` for pre-implementation invariants and three-failure escalation;
- `forgejo-delivery-loop` for local Forgejo issue/PR/receipt semantics;
- `git-town-stacked-pr-worker` for one-writer isolated worktrees and branch graphs;
- `github-delivery-loop` for GitHub publication admission and exact-head evidence.

## Owned state machine

```text
GITHUB_BOUND
→ LOCAL_SYNCED
→ FORGEJO_ISSUES_BOUND
→ WORKTREES_VERIFIED
→ FORGEJO_PRS_MERGED
→ LOCAL_MAIN_MERGED
→ GITHUB_RECONCILING
    ├── REMOTE_MAIN_DRIFT
    ├── OPEN_PR_CONFLICT
    ├── AFFECTED_GITHUB_ISSUE
    └── RECONCILED
→ GITHUB_ACTIONS_VERIFYING
    ├── STALE_HEAD
    ├── FAIL
    └── EXACT_HEAD_PASS
→ GITHUB_PUBLICATION_READY
→ GITHUB_PUBLISHED
→ HUMAN_MERGE_OR_HANDOFF
```

A state transition is invalid unless the exact subject SHA and the receipts required by that state exist.

## Hard laws

1. **Dual-authority law** — local/Forgejo is implementation authority; GitHub is remote publication and Actions authority. Do not collapse them into one forge identity.
2. **Single object-graph law** — both remotes must refer to the same repository lineage. Cross-plane movement is expressed through commit ancestry, never file copying as an implicit merge.
3. **Local-main-first law** — issue implementation merges through verified Forgejo PRs into local main before GitHub publication reconciliation begins.
4. **Remote-drift law** — before any GitHub push/PR update, fetch/rebind current GitHub main. If it moved, reconcile it into the publication candidate without force overwrite.
5. **Open-PR law** — enumerate open GitHub PRs that target or overlap the changed paths. A conflicting PR remains an explicit blocker until rebased/retargeted/resolved under its own ownership rules.
6. **Issue-namespace law** — `forgejo#N` and `github#N` are different identities even when N matches. Link them with an explicit receipt; never infer equivalence.
7. **Exact-head Actions law** — GitHub Actions evidence is valid only when `actions.head_sha == publication.candidate_sha`.
8. **Reconciliation-before-publication law** — publication is blocked until remote-main drift, affected open PRs, and affected GitHub issues are enumerated and resolved/routed.
9. **No-force law** — no `git push --force`, force ref update, silent history rewrite, or overwrite of concurrent GitHub work.
10. **No-secret law** — credentials/tokens/browser sessions remain host-owned and may not enter repository bindings or receipts.
11. **Three-failure law** — three qualifying failures against the same target invoke the fresh-diagnosis escalation from `spatial-loop-systems-engineering`; no fourth blind patch.
12. **Human-authority law** — test success does not create permission to merge protected GitHub/Forgejo PRs, widen permissions, or promote production state.

## Procedure

### 1. GitHub ingress

From ChatGPT iOS/macOS or another GitHub-connected host, bind:

```text
repository_full_name
remote default branch
exact GitHub main SHA
open GitHub issues/PRs relevant to the requested work
latest relevant GitHub Actions state
```

Connector access proves only that the host can observe/mutate allowed GitHub resources. It does not prove local checkout or Forgejo availability.

### 2. Local and Forgejo binding

A local-capable runtime must independently prove:

```text
local repository path
local main SHA
GitHub remote identity
Forgejo remote identity
Forgejo repository identity
worktree root
credential hygiene
```

Synchronize by Git objects. Do not embed credentials in remote URLs.

### 3. Convert work into Forgejo implementation issues

For each implementation unit create or bind one Forgejo issue containing:

```text
source GitHub issue/PR/request link when applicable
objective + non-goals
exact base SHA
path lease
hard invariants
verification commands
negative controls
rollback subject
```

If a GitHub issue is mirrored locally, record both namespaced identities explicitly.

### 4. Implement in isolated worktrees

One issue gets one branch writer and one isolated worktree. Run the pre-implementation Spatial-Loop gate before high-complexity code. Implement the smallest vertical slice, then run owning tests/oracles and negative controls.

Failure routing:

```text
FAIL #1 → bounded repair
FAIL #2 → bounded repair
FAIL #3 → Forgejo/GitHub incident issue by owning plane + fresh diagnosis + new worktree
```

### 5. Forgejo PR and local-main integration

Only verified work is eligible for a Forgejo PR. After repository-required review/admit, merge to local main. Record:

```text
forgejo_pr
merged_commit
local_main_after_merge
verification receipt
```

Do not push GitHub yet merely because local main is green.

### 6. GitHub reconciliation sweep

Re-observe GitHub immediately before publication:

```text
current GitHub main SHA
all open PRs targeting the same base
changed-file overlap/conflict risk
all open GitHub issues affected by the local-main changes
current branch ancestry
```

Classify every open PR:

```text
UNAFFECTED
CLEANLY_REBASEABLE
NEEDS_OWNER_REBASE
SEMANTIC_CONFLICT
SUPERSEDED_BY_LOCAL_MAIN
BLOCKED_OTHER
```

Do not edit every PR blindly. Fix conflicts only where ownership/admission permits; otherwise create/update an issue or handoff receipt. `do all issues` means every relevant open issue gets a terminal routing state, not that unrelated issues are silently modified.

### 7. Build publication candidate

Construct a candidate that contains both:

```text
latest admitted local main
latest observed GitHub main
```

The candidate must prove ancestry for both. A merge/rebase conflict stops the loop for semantic review; automatic conflict resolution is not authority.

### 8. Exact-head GitHub Actions

Publish only the candidate branch required to obtain GitHub Actions evidence under `github-delivery-loop`. Bind workflow/run/job identities and exact head SHA.

```text
candidate SHA changed after CI → previous CI becomes stale
Actions skipped by policy       → SKIPPED_BY_POLICY, not PASS
no runner / billing blocker     → provider blocker, not test FAIL
```

### 9. GitHub publication

After reconciliation and exact-head Actions pass, update/create the GitHub issue/PR projection. Preserve source Forgejo issue/PR receipts and local merge SHA in the publication body or attached receipt where repository policy allows.

GitHub merge remains governed by the target repository's policy.

## Machine contract

Use [`references/repo-binding.template.json`](references/repo-binding.template.json) as a starting point and validate a run receipt with:

```bash
python3 skills/dual-forge-repository-loop/scripts/check_dual_forge_contract.py path/to/dual-forge-receipt.json
```

The checker proves structural closure and publication ordering only. It cannot prove that Forgejo ran locally, that a conflict was semantically resolved, or that a GitHub Actions result is truthful beyond the supplied receipt.

## Evidence states

Use only:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

ChatGPT iOS/macOS GitHub access, local Forgejo mutation, local worktree execution, Actions execution, and final merge are separate evidence lanes.