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
   from draft to ready. The PR must still be draft. If the exact reviewed HEAD is
   already remote, the only admitted operation is the no-push ready transition;
   otherwise one final push precedes that transition.
3. `batched-repair` — publish one batch after actionable CI/review feedback
   against the current remote head. The local subject must be a new exact HEAD;
   the same feedback ID cannot authorize a second publication.

There is deliberately no `checkpoint` intent. Commit as often as needed locally;
push once at a meaningful state transition.

Every intent requires a separate `github-delivery-local-verification/v1` receipt
with `status=PASS` on the exact local Git HEAD. Success from an older SHA is a
BLOCK. A local receipt does not become a GitHub status merely because its JSON
shape is valid.

## Billing circuit breaker

When a trusted GitHub observation identifies the account-level no-runner billing
or spending-limit condition, the snapshot records:

```json
{
  "actions": {
    "circuit": "billing-open",
    "observed_at": "2026-08-12T05:00:00Z",
    "blocker": "billing-or-spending-limit",
    "checks": []
  }
}
```

All publication intents then BLOCK. Recovery requires a separate
`github-actions-billing-recovery/v1` receipt bound to the numeric repository ID,
repository owner, exact blocker timestamp, and a later recovery timestamp.
Because evaluation is intentionally zero-network, the trusted capture lane must
retain the owner-authored issue/comment URL or billing-operation receipt outside
this sanitized decision input. Shape validation does not prove the external
action happened.

GitHub documents that private-repository hosted runners consume included quota,
and usage can be blocked after quota exhaustion without a valid payment method or
by budgets. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Enforced publication path

The evaluator is deliberately pure; enforcement is layered around it:

1. `.github-delivery/ci-policy.json` (`github-ci-policy/v2`) enrolls one private
   repository, names one primary publication workflow/job and may declare
   auxiliary `repair_feedback_checks` workflow/job pairs. It also points to one
   repository-owned local verification contract. The primary remains the sole
   billing/cost-control check; auxiliary checks grant feedback identity, not a
   second publication scheduler. A known account-level no-runner annotation on
   any declared check still opens the repository billing circuit.
2. `ci_workflow_policy.py check` requires one explicit PR cost profile: the
   backwards-compatible `draft-first` profile rejects draft `synchronize` and
   `reopened`; the opt-in `universal` profile requires every opened, synchronized,
   and reopened PR head. Both reject push outside the default
   branch, missing dispatch/concurrency, and mutable action tags.
3. `ci_publish.py verify` delegates to `local_verification.py`, which executes the
   contract's fixed argv and writes exact-HEAD receipt plus detailed evidence
   under the git directory, outside the committed tree.
4. `ci_publish.py publish` rechecks policy, receipt, snapshot, GitHub remote
   identity, observed branch, and full-SHA refspec before one push. Its live
   capture resolves every declared workflow path to a provider workflow ID, so
   another workflow cannot collide by reusing the same job name. Capture also
   binds the exact Actions job and its step count. A completed `skipped` job with
   zero steps is retained as a non-execution observation and does not create a
   false rerun conflict; missing step provenance remains conservative. A partially
   observed declaration set, an incomplete check, or two executed checks are
   ambiguous and block repair. One or more actionable declared failures become one ordered,
   deterministic feedback identity for the whole repair batch. Initial
   publication creates a draft PR; ready publication marks it ready. Draft-first
   batched repairs explicitly dispatch the verifier;
   universal publications also require an open PR and an exact match between the
   target branch and snapshot PR head ref. Universal repairs rely on the required
   `synchronize` event and do not create a duplicate manual run for the same SHA.
   After every zero-network precondition passes, the wrapper writes
   `github-actions-publish-decision-manifest/v1` under the Git directory. The
   manifest binds the evaluation time, stable required check name, admitted
   operation, and raw SHA-256 digests of the canonical policy, snapshot, exact-HEAD
   verification receipt/evidence/contract, and optional billing-recovery receipt.
   A later dual-origin proof must replay those exact bytes; the manifest alone is
   admission evidence, not evidence that a network command succeeded.
5. `ci_publish_guard.py`, registered by `install-ci-publish-guard.py`, blocks a
   raw GitHub `git push` from enrolled repositories on Agent PreToolUse
   surfaces. It recognizes direct `git`, `git-push`, `exec`, admitted `env`
   forms, Git aliases, repository selection, and remote resolution. It leaves an
   explicit Forgejo remote available.

The host guard cannot intercept a human terminal, a third-party bot, or a
repository that has not enrolled. Do not describe that boundary as universal
GitHub enforcement. Its legacy hook input is a shell command string, not a
resolved process event. Therefore arbitrary shell evaluation is deliberately
outside the parser's sound interface. Direct argv-like Git/`git-push`, `exec`,
`env`, literal shell pushes, and literal `git -C <enrolled>` invocations with
variable/backtick expansion are covered; the last category fails closed even
when the hook cwd is outside the repository. Static Forgejo pushes remain
available. `-c` is recognized both alone and in normal combined shell option
forms such as `-lc`. A shell program that computes executable, repository path, and remote
without leaving those literals is outside this parser's claim. Universal
prevention requires a host enforcement point that supplies resolved
executable/argv/cwd/environment/remote after shell evaluation.

The Actions capture CLI likewise does not accept a caller-selected `gh` path or
resolve `gh` from inherited `PATH`. It selects from a closed absolute-path set,
records invoked path, realpath, binary SHA-256, and version, then records exact
absolute-path `gh api` argv and derives GitHub-Actions-owned check-suite plus
workflow/run/job/check identities, matching job/check status and conclusion, and
job-step count for every declared pair.
A zero-step `skipped` job is a non-execution, not a second run. More than one
actual execution of any declared pair for the exact candidate is a provenance
conflict, not "latest wins"; publication remains blocked instead of blessing a
rerun. Billing annotations still open the circuit even on a zero-step job.

Optional auxiliary feedback checks are declared without restating the primary:

```json
{
  "workflow": ".github/workflows/verify.yml",
  "required_jobs": ["verify"],
  "repair_feedback_checks": [
    {
      "workflow": ".github/workflows/binding.yml",
      "job": "binding"
    }
  ]
}
```

Each auxiliary workflow must exist, own the named job, and pin external actions
to immutable SHAs. It need not copy the primary workflow's event/cost profile.
The primary pair is implicitly first and must not be duplicated in the array.

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
  "schema": "github-actions-publish-snapshot/v5",
  "repository": {
    "full_name": "owner/private-repository",
    "repository_id": 123456,
    "owner_login": "owner",
    "private": true
  },
  "branch": {
    "name": "agent/feature",
    "head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "pull_request": {
    "number": 42,
    "state": "draft",
    "head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "last_published_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "last_published_at": "2026-08-12T05:00:00Z",
    "feedback": null
  },
  "actions": {
    "circuit": "closed",
    "observed_at": null,
    "blocker": null,
    "checks": []
  },
  "captured_at": "2026-08-12T05:10:00Z"
}
```

The intent and local verification receipt are separate inputs. Exit `0` with an
`ALLOW` decision authorizes exactly the named operation. Exit `2` is a policy
BLOCK and exit `64` is malformed/unavailable evidence. Any nonzero exit stops
before `git push`.

New capture emits observation v4, transport v6, and snapshot v5. Observation
v3 and transport v5 remain readable but carry unknown step provenance, so they
cannot dismiss a skipped check from rerun ambiguity. The replay adapter also
keeps the prior single-workflow v2/v4/v4 shapes readable for existing dual-origin
receipts. Publication admission accepts a v4 snapshot only when it
contains no CI check capable of authorizing a repair; legacy CI feedback must be
recaptured as v5 so workflow/job provenance is explicit.
