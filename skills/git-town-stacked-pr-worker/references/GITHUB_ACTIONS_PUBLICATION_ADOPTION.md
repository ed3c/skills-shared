# Adopting the GitHub Actions publication boundary

This is the publication-specific companion to `ADOPTION.md`. It connects the Git Town Worker to the
canonical `github-delivery-loop` without copying policy or implementation into each consumer repository.

## 1. Resolve both shared Skills

The consumer must resolve the canonical bodies for:

```text
git-town-stacked-pr-worker
  → branch graph, isolated worktrees, bounded local no-push synchronization

github-delivery-loop
  → exact-HEAD publication admission, PR/check snapshot semantics, billing circuit
```

A repository-local copy of either shared name is shadowing and blocks adoption.

## 2. Compose the Agent instruction surface

Compose:

```text
SYSTEM_PROMPT.md
+ PUBLICATION_POLICY.md
+ repository AGENTS/CLAUDE routing
+ filled repository profile
+ filled GitHub publication profile fragment
```

The base prompt alone is insufficient when the Worker can publish to GitHub.

## 3. Implement repository-owned adapters

The consumer owns fixed entrypoints for:

```text
local verification receipt for exact HEAD
trusted GitHub snapshot capture
publication-gate invocation
one allowed push/PR operation
post-push fetch and ancestry verification
trusted-check status capture
```

Do not expose arbitrary shell. The publication adapter consumes gate output and performs exactly one returned
operation.

## 4. Configure workflow cadence

For a private repository, preserve one stable trusted check while avoiding per-checkpoint runs:

```text
draft PR open/synchronize        → no runner-backed heavy job
ready_for_review or reopened     → one trusted run
ready PR gate-approved repair    → one run for the new head
main                             → one integrity run
manual/release                   → explicit heavy/provider lane
```

Use PR/ref-scoped concurrency and cancel obsolete heads. Do not use cost reduction as a reason to delete the
final verifier or treat a skipped draft job as PASS.

## 5. Dogfood before adoption completion

Required observations:

1. positive and hollow snapshots replay offline;
2. a draft PR is visible without a runner-backed trusted job;
3. ready-for-review causes one exact-head trusted run;
4. an obsolete head is cancelled or proven absent;
5. a stale receipt/check and repeated feedback block;
6. `billing-open` blocks push/rerun/no-op commit;
7. post-push remote ancestry equals the admitted subject;
8. merge and promotion remain Human Admit.

Account billing recovery, runner allocation, provider credentials and hosted execution cannot be proven by
static documentation. Leave unrun lanes `NOT_EXERCISED`.
