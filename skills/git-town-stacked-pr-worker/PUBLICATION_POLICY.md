# GitHub Actions Publication Policy Addendum

This addendum is part of the portable `git-town-stacked-pr-worker` instruction contract. Compose it with
`SYSTEM_PROMPT.md` whenever a Worker can publish a branch, create/update a GitHub PR, transition a PR to ready,
or trigger a private-repository GitHub Actions workflow.

## 1. Authority split

```text
Git Town
  owns: branch parentage + bounded local synchronization

github-delivery-loop
  owns: exact-HEAD GitHub publication admission
        + GitHub Actions billing/spending circuit semantics

Consumer repository
  owns: snapshot capture + local-verification receipt + CI workflow
        + repository-specific push wrapper + post-push ancestry verifier

Human / trusted operator
  owns: billing recovery statement + merge + permission changes
        + release/promotion/production decisions
```

Do not duplicate `ci_publish_gate.py` policy in the Worker implementation. Resolve it through the shared
`github-delivery-loop` binding or a repository-admitted equivalent with the same versioned schemas and evals.

## 2. Required profile fields

The consumer profile must resolve:

```text
CI_PUBLICATION_GATE=<PATH_OR_TYPED_ENTRYPOINT>
CI_PUBLICATION_SNAPSHOT_SCHEMA=github-actions-publish-snapshot/v1
CI_LOCAL_VERIFICATION_SCHEMA=github-delivery-local-verification/v1
CI_ALLOWED_INTENTS=initial-pr,ready-for-review,batched-repair
CI_DRAFT_PR_RUNNER_POLICY=no-runner
CI_BILLING_CIRCUIT_POLICY=fail-closed
CI_OBSOLETE_HEAD_POLICY=cancel-in-progress
CI_TRUSTED_CHECK_NAME=<STABLE_CHECK_NAME>
```

Missing or unresolved values are `ABSENT` and produce `BLOCKED_POLICY`.

## 3. Worker algorithm

A Worker that reaches a possible publication boundary must execute this order:

```text
local edits and commits
→ dry-run Git Town sync --no-push
→ bounded Git Town sync --no-push
→ post-sync ancestry verification
→ task evals and negative controls on exact local HEAD
→ exact-HEAD local verification receipt
→ trusted GitHub state snapshot
→ ci_publish_gate.py evaluate --intent <intent> (receipt and the evidence its digest names)
→ ALLOW? execute exactly one returned operation
→ fetch remote and verify ancestry/head identity
→ record GitHub trusted-check state separately
```

No earlier step authorizes a later one.

## 4. Three publication intents

### `initial-pr`

Use only when no PR/remote publication exists for the branch.

Allowed operation:

```text
one push
+ create one draft PR
```

The draft PR is a review surface, not a request to allocate a runner.

### `ready-for-review`

Use only after the planned local batch is complete and all exact-HEAD local evals pass.

Allowed operation:

```text
optional one push for the final local batch
+ one draft → ready transition
```

This is the first normal runner-backed trusted PR check.

### `batched-repair`

Use only for new actionable CI or review feedback bound to the current remote head.

Allowed operation:

```text
one push containing the complete response batch
```

The same feedback identity can be consumed only once.

## 5. Background synchronization

Unattended/background execution must remain:

```bash
git town sync --stack --non-interactive --no-auto-resolve --no-push
```

Forbidden in a background loop:

```text
git town sync --push
raw git push
gh pr ready
workflow rerun
no-op commit
merge / ship
permission or billing mutation
```

A background loop may prepare a publication proposal and receipt. It may not bypass the publication gate.

## 6. Billing circuit breaker

When GitHub reports that a runner did not start because of payment or spending-limit state, the snapshot state is:

```text
billing-open
```

The Worker must:

- stop publication;
- preserve the branch and exact local verification receipt;
- avoid rerun, no-op commit, checkpoint push, and workflow weakening;
- report the blocker as account/infrastructure state, not test `FAIL`;
- wait for an owner-authored recovery receipt with a later timestamp.

A recovery receipt admits one new attempt. It does not prove that a runner will be allocated.

## 7. Workflow posture

A private-repository deterministic PR workflow should normally have:

```text
draft PR opened/synchronized
  → no runner-backed job

ready_for_review / reopened
  → one trusted run

ready PR synchronize after gate-approved batched repair
  → one run for the new head
  → obsolete in-progress head cancelled

push to main
  → one final integrity run

workflow_dispatch
  → explicit recovery or diagnostic path
```

Use PR/ref-scoped concurrency with `cancel-in-progress: true`. Keep the stable trusted check; do not solve cost
by deleting the final verifier. Heavy model, browser, mobile, macOS, cloud-provider, and multi-seed matrices
belong to manual/nightly/release lanes unless the consumer explicitly admits a different budget.

## 8. Evidence lanes

Report these independently:

| Lane | Meaning |
|---|---|
| local sync | Git Town synchronization and ancestry |
| local verification | exact local HEAD passed repository evals |
| publication decision | gate `ALLOW` or `BLOCK` with stable reason |
| remote publication | branch/PR operation actually occurred |
| remote ancestry | fetched remote equals the admitted local subject |
| GitHub trusted check | exact remote head obtained a runner-backed result |
| billing circuit | closed, billing-open, or unknown |
| Human Admit | merge/promotion decision |

`ALLOW` is not a remote push receipt. A remote push is not a GitHub check. A GitHub check is not merge authority.
A draft job intentionally suppressed by policy is `SKIPPED_BY_POLICY`, never PASS.

## 9. Required controls

At minimum, the consumer must kill these mutations:

- change `--no-push` to `--push` in unattended sync;
- omit the publication-gate reference;
- publish a draft checkpoint without an admitted intent;
- reuse a local verification receipt from an older SHA;
- treat an old-SHA CI result as current;
- consume the same feedback twice;
- retry while `billing-open`;
- report a skipped/no-runner job as PASS;
- expose merge, `git town ship`, permission changes, or promotion to the Worker.

## 10. Completion boundary

Publication integration is complete only when:

1. both shared Skills resolve without shadowing;
2. the repository profile names the exact gate and schemas;
3. local sync is proven no-push;
4. exact-HEAD local receipt production is proven;
5. positive and hollow publication snapshots are replayed offline;
6. one real draft publication proves no runner-backed trusted job was requested;
7. one ready-for-review publication obtains the stable trusted check;
8. a planted stale-head or billing-open case fails closed;
9. post-push remote ancestry is verified;
10. merge and promotion remain Human Admit.

Any unrun live lane remains `NOT_EXERCISED`.
