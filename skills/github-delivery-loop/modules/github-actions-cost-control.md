# Private GitHub Actions publication boundary

`github-delivery-loop` treats a local commit and a GitHub Actions publication as two different events.
Local commits are cheap, frequent, and stay inside the Worker worktree. A remote push is admitted only when
it buys a new review or verification fact.

## Why this exists

A private repository can bill one runner minute even when a job finishes in a few seconds. During the
2026-08-12 `skills-shared` incident, at least 28 different PR heads triggered `Skill Eval Contract` in about
19 minutes. Later jobs did not start because GitHub reported an account payment or spending-limit blocker.
That state is `ACTIONS_BILLING_BLOCKED`, not test `FAIL`, CI `PASS`, or a reason to create no-op commits.

The delivery loop therefore owns an explicit publication gate:

```text
local edit / commit / rebase
        │
        ├─ local verification receipt for exact HEAD
        │
        ▼
zero-network ci_publish_gate.py
        │
        ├─ BLOCK: keep working locally; do not push or rerun
        └─ ALLOW: publish exactly one reviewed boundary
```

## Three admitted publication intents

| Intent | When it is admitted | Result |
|---|---|---|
| `initial-pr` | no PR or remote branch exists; exact local HEAD has a passing local receipt | one push and creation of a **draft** PR |
| `ready-for-review` | the PR is still draft; all planned local commits have been batched | optionally one push, then one ready-for-review transition |
| `batched-repair` | a ready PR has new actionable CI/review feedback bound to its exact remote head | one repair push containing the whole response batch |

Everything else is a local checkpoint. In particular, do not push after every commit, after every Agent turn,
or just to see whether account billing recovered.

## Zero-network gate

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root /absolute/path/to/repo \
  --snapshot /path/to/github-state.snapshot.json \
  --verification /path/to/local-verification.receipt.json \
  --intent initial-pr \
  --json
```

Exit codes:

```text
0   ALLOW
2   BLOCK by publication policy
64  malformed/missing evidence or local Git failure
```

The evaluator never calls GitHub. A trusted sync step captures GitHub state into
`github-actions-publish-snapshot/v1`; the repository Harness produces
`github-delivery-local-verification/v1` for the exact local `HEAD`.

### Snapshot shape

```json
{
  "schema": "github-actions-publish-snapshot/v1",
  "repository": {
    "full_name": "ed3c/skills-shared",
    "repository_id": 1326262274,
    "owner_login": "ed3c",
    "private": true
  },
  "pull_request": {
    "number": 42,
    "state": "ready",
    "head_sha": "<40-hex>",
    "last_published_sha": "<same 40-hex>",
    "last_published_at": "2026-08-12T05:00:00Z",
    "feedback": {
      "id": "check-run:123",
      "kind": "ci",
      "head_sha": "<same 40-hex>",
      "observed_at": "2026-08-12T05:01:00Z",
      "consumed_by_sha": null
    }
  },
  "actions": {
    "circuit": "closed",
    "observed_at": null,
    "blocker": null,
    "latest_check": {
      "head_sha": "<same 40-hex>",
      "conclusion": "failure",
      "completed_at": "2026-08-12T05:01:00Z"
    }
  }
}
```

Repository identity is the immutable numeric ID; `owner/name` is a human-readable alias. A CI repair is not
admitted when the check belongs to an older SHA, is missing, or is not actionable. Review feedback is also
bound to the exact PR head and can be consumed only once.

## Billing circuit breaker

When GitHub reports that no runner started because of payment or spending-limit state, the snapshot must carry:

```json
{
  "circuit": "billing-open",
  "observed_at": "2026-08-12T05:03:00Z",
  "blocker": "billing-or-spending-limit",
  "latest_check": null
}
```

The gate then returns:

```text
BLOCK billing-circuit-open
```

Forbidden responses:

- rerun the workflow;
- push a no-op commit;
- push the next local checkpoint;
- weaken or remove the trusted check;
- report the unstarted job as test `FAIL` or `PASS`.

Only an explicit owner-authored `github-actions-billing-recovery/v1` receipt can close this local circuit, and
its `recovered_at` must be later than the exact blocker timestamp. A recovery receipt admits one new
publication attempt; it does not prove that GitHub will provide a runner.

## Private-repository workflow pattern

The expensive trusted PR job should run after the PR becomes ready and after one admitted repair push—not on
every draft checkpoint.

```yaml
name: Skill Eval Contract

on:
  pull_request:
    types: [ready_for_review, synchronize, reopened]
    paths:
      - 'evals/**'
      - 'mutations/**'
      - 'scripts/**'
      - 'tests/**'
      - '.github/workflows/skill-eval-contract.yml'
  workflow_dispatch:

concurrency:
  group: skill-eval-contract-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  contract:
    name: skill-contract
    if: github.event_name == 'workflow_dispatch' || !github.event.pull_request.draft
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@<pinned-commit>
      - run: python3 -m unittest discover -s tests -v
      - if: failure() || github.event_name == 'workflow_dispatch'
        uses: actions/upload-artifact@<pinned-commit>
        with:
          name: skill-contract-diagnostics
          path: artifacts/
          retention-days: 3
```

Keep default-branch verification separate and thin:

```yaml
on:
  push:
    branches: [main]

# exact merged-tree integrity and publication attestation only;
# do not repeat physical cross-harness/model matrices here.
```

Rules:

1. Create the PR as draft. Draft creation is the first and only pre-review push.
2. Work and rebase locally. Do not use GitHub as a checkpoint store.
3. Mark ready once; that event starts the stable trusted check.
4. After actionable feedback, batch all fixes locally and publish once.
5. Use `concurrency.cancel-in-progress` so an obsolete head cannot continue consuming minutes.
6. Upload diagnostics only on failure/manual execution; release evidence belongs in release/manual workflows.
7. Physical model, cross-harness, browser, mobile, and provider matrices are `workflow_dispatch`, scheduled,
   or release-only. They are never part of every incremental PR push.

## Git Town and Worker Agents

`git town sync --stack --non-interactive --no-auto-resolve --no-push` remains a local ancestry operation.
The publication gate runs **after** local sync and local evals, before any `git push` or Git Town publish mode.
A Worker may commit and rebase repeatedly without creating remote workflow runs.

```text
Worker worktree
→ local commits
→ git town sync --no-push
→ local eval receipt for exact HEAD
→ CI publication gate
→ one admitted push
```

Conflict, dirty state, missing receipt, stale HEAD, ambiguous PR identity, billing circuit, or old feedback all
stop publication. They do not authorize an alternate API, force push, workflow rerun, or hidden checkpoint.

## Claim boundary

This mechanism controls publication cadence and prevents known waste patterns. It does not guarantee that
GitHub billing is available, that the remote workflow passes, or that a provider/model runtime is affordable.
GitHub remains the distribution-origin witness; deterministic generation and frequent iteration should stay on
local or Forgejo/self-hosted workers.
