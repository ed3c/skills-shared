# Private GitHub Actions publication boundary

`github-delivery-loop` treats a local commit and a GitHub Actions publication as two different events. Local commits are cheap, frequent, and stay inside the Worker worktree. A remote push is admitted only when it buys a new review or verification fact.

## Why this exists

A private repository can bill one runner minute even when a job finishes in a few seconds. During the 2026-08-12 `skills-shared` incident, at least 28 different PR heads triggered `Skill Eval Contract` in about 19 minutes. Later jobs did not start because GitHub reported an account payment or spending-limit blocker. That state is `ACTIONS_BILLING_BLOCKED`, not test `FAIL`, CI `PASS`, or a reason to create no-op commits.

```text
local edit / commit / rebase
        │
        ├─ exact-HEAD local verification receipt
        ├─ trusted GitHub observation / snapshot
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

Everything else is a local checkpoint. Do not push after every commit, after every Agent turn, or merely to test whether billing recovered.

## Evidence-production pipeline

The publication gate does not accept hand-written success JSON. Two independently generated inputs meet at the gate:

```text
consumer-owned fixed command contract
        │
        ▼
local_verification.py (zero network)
        │
        ├─ local-verification.receipt.json
        └─ local-verification.evidence.json

trusted `gh api` capture lane
        │
        ├─ github-observation.json
        ▼
github_actions_snapshot.py
        └─ github-state.snapshot.json

receipt + snapshot + publication intent
        ▼
ci_publish_gate.py evaluate
        └─ ALLOW or BLOCK
```

### Local verification contract

A consumer repository owns a small contract:

```json
{
  "schema": "github-delivery-local-verification-contract/v1",
  "repository_id": 1326262274,
  "inherit_env": ["PATH"],
  "commands": [
    {
      "id": "delivery-skill-tests",
      "argv": ["bash", "skills/github-delivery-loop/tests/run-all.sh"],
      "cwd": ".",
      "timeout_seconds": 120,
      "max_output_bytes": 65536
    }
  ]
}
```

The contract is not a shell script. Every command is an argv array. The verifier rejects empty commands, shell strings such as `bash -c`, absolute or machine-local paths, inherited environment names outside the safe allowlist, dirty worktrees, repository-ID mismatch, timeout, nonzero exit and output-budget overflow.

```bash
python3 skills/github-delivery-loop/scripts/local_verification.py verify \
  --repo-root /absolute/path/to/repo \
  --contract /path/to/local-verification.contract.json \
  --repository-id 1326262274 \
  --receipt /path/to/local-verification.receipt.json \
  --evidence /path/to/local-verification.evidence.json
```

The compact receipt is consumed by `ci_publish_gate.py`:

```json
{
  "schema": "github-delivery-local-verification/v1",
  "repository_id": 1326262274,
  "head_sha": "<exact clean local HEAD>",
  "status": "PASS",
  "verified_at": "<RFC3339>",
  "evidence_sha256": "<SHA-256 of the detailed evidence>",
  "commands": ["delivery-skill-tests"]
}
```

The sidecar records the exact Git tree, contract digest, per-command argv/cwd, exit, timeout, duration, stdout/stderr byte counts and hashes. It records no environment values and no unbounded streams.

### Trusted GitHub observation and snapshot

`github_actions_snapshot.py capture` is the only network lane:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py capture \
  --repository OWNER/REPO \
  --branch <HEAD_BRANCH> \
  --check-name <STABLE_JOB_CHECK_NAME> \
  --observation-output /path/to/github-observation.json \
  --output /path/to/github-state.snapshot.json
```

It uses fixed `gh api` argv only and performs no mutation. It resolves exact private repository identity, zero or one open PR, exact PR head, exact stable check name, conclusion and annotations.

Replay is zero-network:

```bash
python3 skills/github-delivery-loop/scripts/github_actions_snapshot.py replay \
  --observation /path/to/github-observation.json \
  --check-name <STABLE_JOB_CHECK_NAME> \
  --output /path/to/github-state.snapshot.json
```

The producer fails closed on public repositories, multiple open PRs, stale-head checks, incomplete checks, malformed annotations and unknown API state. V1 derives actionable CI feedback only. Review feedback needs a separate explicit adapter; it is never guessed from general PR text.

### Billing circuit breaker

When the exact check annotation says no runner started because recent account payments failed or the spending limit must be increased, the snapshot contains:

```json
{
  "circuit": "billing-open",
  "observed_at": "2026-08-12T05:03:00Z",
  "blocker": "billing-or-spending-limit",
  "latest_check": null
}
```

The gate returns `BLOCK billing-circuit-open`. Forbidden responses are rerun, no-op commit, another checkpoint push, weakening the trusted check, or reporting the unstarted job as repository test `FAIL`/`PASS`. An owner-authored recovery receipt admits one later attempt; it does not prove a runner will start.

## Zero-network publication gate

```bash
python3 skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root /absolute/path/to/repo \
  --snapshot /path/to/github-state.snapshot.json \
  --verification /path/to/local-verification.receipt.json \
  --verification-evidence /path/to/local-verification.evidence.json \
  --intent initial-pr \
  --json
```

```text
0   ALLOW
2   BLOCK by publication policy
64  malformed/missing evidence or local Git failure
```

Repository identity is the immutable numeric ID; `owner/name` is a display alias. A CI repair is not admitted when its check belongs to an older SHA, is missing, or is not actionable. Feedback is bound to one exact PR head and can be consumed once.

## Private-repository workflow pattern

```yaml
name: Skill Eval Contract

on:
  pull_request:
    types: [ready_for_review, synchronize, reopened]
  workflow_dispatch:

concurrency:
  group: skill-eval-contract-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  contract:
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

Keep default-branch verification separate and thin. Create the PR as draft, work and rebase locally, mark ready once, batch actionable repairs, cancel obsolete runs, upload diagnostics only on failure/manual execution, and keep physical model/browser/mobile/provider matrices manual, scheduled or release-only.

## Git Town and Worker Agents

`git town sync --stack --non-interactive --no-auto-resolve --no-push` remains a local ancestry operation. The publication gate runs after local sync and local evals, before any push.

```text
Worker worktree
→ local commits
→ git town sync --no-push
→ local verification receipt for exact HEAD
→ trusted GitHub snapshot
→ CI publication gate
→ one admitted push
```

Conflict, dirty state, missing receipt, stale HEAD, ambiguous PR identity, billing circuit or old feedback stops publication. None authorizes an alternate API, force push, workflow rerun or hidden checkpoint.

## Claim boundary

This mechanism controls publication cadence and produces the exact evidence required by that decision. It does not guarantee GitHub billing availability, remote workflow success, model/provider affordability or merge approval. GitHub remains the distribution-origin witness; deterministic generation and frequent iteration stay on local or Forgejo/self-hosted workers.
