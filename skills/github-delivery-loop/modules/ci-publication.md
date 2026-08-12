# Private-repository CI publication

## Problem boundary

Incremental local commits are cheap and preserve intent. In a private GitHub
repository, publishing every commit can create one billed job per SHA. GitHub
rounds each job's partial minute up to a whole minute, so a successful eight-second
job can still consume one included minute. See GitHub's official
[Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing).

The 2026-08-12 `ed3c/skills-shared` incident is the physical receipt: draft PR
#42 published at least 28 distinct heads in roughly 19 minutes. Each relevant
head triggered `Skill Eval Contract`. Later jobs had no runner or steps and the
GitHub check annotation named recent payment failure or a spending-limit increase.
Those runs were not test failures and supplied no verification evidence.

Do not solve this by disabling the only verification workflow or treating a
skipped job as PASS. Separate local iteration cadence from remote publication.

## Three publication intents

`ci_publish_gate.py evaluate` accepts only:

1. `initial-pr` — publish a reviewed local batch to create the draft PR. The
   snapshot must show that no PR exists yet.
2. `ready-for-review` — publish the final reviewed batch before changing the PR
   from draft to ready. The PR must still be draft and its remote head must differ.
3. `repair` — publish one batch after actionable CI/review feedback against the
   current remote head. Local verification must finish after that feedback; the
   same feedback timestamp cannot authorize a second publication.

There is deliberately no `checkpoint` intent. Commit as often as needed locally;
push once at a meaningful state transition.

Every intent requires `local_verification.status=passed` on the exact 40-character
`local_head`. Success from an older SHA is a BLOCK. A local receipt does not become
a GitHub status merely because its JSON shape is valid.

## Billing circuit breaker

When a GitHub check annotation identifies the account-level no-runner billing or
spending-limit condition, record:

```json
{
  "billing_blocker": {
    "kind": "account-billing-no-runner",
    "observed_at": "2026-08-12T05:00:00Z"
  },
  "recovery": null
}
```

All publication intents then BLOCK. Do not rerun, push a no-op commit, or push the
next local fix: none changes account billing. Recovery requires a receipt whose
`author` equals the repository owner, whose `status` is `actions-restored`, and
whose timestamp is later than the blocker. Because evaluation is intentionally
zero-network, the snapshot producer must retain the owner-authored issue/comment
URL or billing-operation receipt outside this sanitized snapshot. Shape validation
does not prove that the external action happened.

GitHub documents that private-repository hosted runners consume included quota,
and usage can be blocked after quota exhaustion without a valid payment method or
by budgets. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Workflow shape for private repositories

The workflow should preserve a trusted final check while avoiding automatic work
for every draft synchronization:

- `pull_request` handles ready-for-review/open-ready transitions, not every draft
  `synchronize` event;
- `push` is limited to the default branch;
- `workflow_dispatch` runs the final check after one admitted repair batch;
- workflow-level `concurrency` groups by PR/ref and cancels stale PR runs;
- third-party actions use immutable commit SHAs and permissions remain least
  privilege;
- the check name stays stable so merge policy can require the final result.

Concurrency is a backstop, not the primary cost control: a short job may finish
before the next push arrives, so nothing remains to cancel. GitHub's official
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)
documents cancellation behavior.

For a draft-first repository, one safe shape is to create the workflow run on PR
events but guard the billed job so it runs only for an opened non-draft PR,
`ready_for_review`, or `reopened`. After an admitted repair publication, dispatch
the workflow explicitly against that exact branch/SHA. Never use a manually
published success status as a substitute for executing the verifier.

## Snapshot example

```json
{
  "schema": "github-ci-publish-snapshot/v1",
  "repository": "owner/private-repository",
  "repository_owner": "owner",
  "private": true,
  "intent": "ready-for-review",
  "local_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "local_verification": {
    "head_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "status": "passed",
    "completed_at": "2026-08-12T05:10:00Z"
  },
  "pull_request": {
    "number": 42,
    "is_draft": true,
    "remote_head": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "actionable_feedback": null,
  "billing_blocker": null,
  "recovery": null
}
```

Exit `0` with `ALLOW <intent>` authorizes one publication. Exit `1` is a policy
BLOCK. Exit `2` is malformed evidence. Any nonzero exit stops before `git push`.
