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

## Enforced publication path

The evaluator is deliberately pure; enforcement is layered around it:

1. `.github-delivery/ci-policy.json` enrolls one private repository, names the
   workflow and stable required jobs, and defines the local verifier argv.
2. `ci_workflow_policy.py check` requires one explicit PR cost profile: the
   backwards-compatible `draft-first` profile rejects draft `synchronize` and
   `reopened`; the opt-in `universal` profile requires every opened, synchronized,
   and reopened PR head. Both reject push outside the default
   branch, missing dispatch/concurrency, and mutable action tags.
3. `ci_publish.py verify` executes the configured verifier and writes an
   exact-HEAD receipt under the git directory, outside the committed tree.
4. `ci_publish.py publish` rechecks policy, receipt, snapshot, GitHub remote
   identity and the full-SHA refspec before one push. Ready publications then
   mark the PR ready. Draft-first repairs explicitly dispatch the verifier;
   universal publications also require an open PR and an exact match between the
   target branch and snapshot PR head ref. Universal repairs rely on the required
   `synchronize` event and do not create a duplicate manual run for the same SHA.
5. `ci_publish_guard.py`, registered by `install-ci-publish-guard.py`, blocks a
   raw GitHub `git push` from enrolled repositories on Agent PreToolUse
   surfaces. It leaves an explicit Forgejo remote available.

The host guard cannot intercept a human terminal, a third-party bot, or a
repository that has not enrolled. Do not describe that boundary as universal
GitHub enforcement.

## Workflow shape for private repositories

The workflow must preserve a trusted final check. Select the PR cost profile in
`.github-delivery/ci-policy.json`; omitting `pull_request_mode` remains
`draft-first` for compatibility:

```json
{
  "pull_request_mode": "draft-first"
}
```

The supported profiles are deliberately closed:

- `draft-first` requires exactly `ready_for_review`. Reopened and repair
  publications dispatch the workflow explicitly against the admitted SHA.
- `universal` requires exactly `opened`, `synchronize`, and `reopened`. These
  events cover creation, head changes, and restoration of an open PR. It excludes
  `ready_for_review` because that transition does not change the head and would
  duplicate the preceding `synchronize` run during a managed ready publication.
  Universal mode still consumes more hosted Actions quota than draft-first mode.

In both profiles:

- `push` is limited to the default branch;
- `workflow_dispatch` remains available for explicit runs; draft-first repairs
  use it, while universal repairs rely on the required `synchronize` event;
- workflow-level `concurrency` groups by PR/ref and cancels stale PR runs;
- third-party actions use immutable commit SHAs and permissions remain least
  privilege;
- the check name stays stable so merge policy can require the final result.

Concurrency is a backstop, not the primary cost control: a short job may finish
before the next push arrives, so nothing remains to cancel. GitHub's official
[workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)
documents cancellation behavior.

Selecting `universal` changes scheduling, not billing recovery or release
authority. An open billing circuit still blocks publication; a queued, skipped,
or no-runner check still is not verification. Never use a manually published
success status as a substitute for executing the verifier.

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
    "is_open": true,
    "head_ref": "agent/example",
    "remote_head": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "actionable_feedback": null,
  "billing_blocker": null,
  "recovery": null
}
```

Exit `0` with `ALLOW <intent>` authorizes one publication. Exit `1` is a policy
BLOCK. Exit `2` is malformed evidence. Any nonzero exit stops before `git push`.
