# GitHub Delivery State Machines

This document maps the independent state machines coordinated by `github-delivery-loop`. The separation is load-bearing: local implementation success, Git synchronization, GitHub publication, CI, review, and merge are different observations with different owners.

## 1. Evidence vocabulary

```text
PASS                 subject was exercised and accepted by its owning verifier
FAIL                 subject was exercised and rejected
ABSENT               required subject or input does not exist
NOT_IMPLEMENTED      mechanism does not exist
NOT_EXERCISED        mechanism exists but no current subject-bound execution exists
SKIPPED_BY_POLICY     execution was deliberately not requested by an admitted policy
```

Do not collapse these states into `success`, `green`, or `done`.

---

## 2. Delivery-line state machine

**Owner:** `github_delivery.py` and `delivery_sync*`

**Purpose:** bind one local implementation artifact to GitHub tracking and publication evidence without invading the implementation loop.

### Inputs

- `.github-delivery/registry.json` line;
- materialized artifact path;
- implementation receipt;
- publication attestation;
- optional trusted GitHub snapshot;
- exact export source commit and tree.

### States

```text
UNREGISTERED
    │ register one line
    ▼
REGISTERED
    │ artifact exists
    ▼
MATERIALIZED
    │ implementation receipt validates
    ▼
RECEIPT_VALID
    │ publication attestation validates
    ▼
PUBLICATION_ATTESTED
    │ trusted sync derives metrics/dashboard
    ▼
SYNCED
```

### Failure terminals

```text
UNMATERIALIZED
RECEIPT_MISSING
RECEIPT_INVALID
PUBLICATION_MISSING
PUBLICATION_INVALID
REPOSITORY_ID_DRIFT
EXPORT_TREE_DRIFT
SNAPSHOT_INVALID
SYNC_FAILED
```

### Invariants

- An empty registry is not success.
- Artifact absence is failure, not skip.
- GitHub owner/name is an alias; immutable repository identity is separate.
- Export file count or history shape cannot proxy exact tree identity.
- The delivery line does not prove implementation correctness; it proves the artifact/receipt/publication binding.

---

## 3. Local-verification state machine

**Owner:** `local_verification.py`

**Purpose:** create a receipt for a clean exact local Git HEAD using a consumer-owned fixed-command contract.

### Inputs

- clean repository and exact `HEAD`;
- repository numeric identity;
- fixed argv arrays;
- safe inherited-environment allowlist;
- timeout and output budget;
- expected command set.

### States

```text
CONTRACT_ABSENT
    │ load and validate fixed command contract
    ▼
CONTRACT_VALID
    │ verify clean exact Git HEAD
    ▼
HEAD_BOUND
    │ execute every command without shell interpolation
    ▼
COMMANDS_EXECUTED
    │ all required commands exit 0 and evidence is bounded
    ▼
LOCAL_VERIFIED
```

### Failure terminals

```text
DIRTY_WORKTREE
STALE_HEAD
UNSAFE_COMMAND
UNSAFE_ENVIRONMENT
TIMEOUT
OUTPUT_BUDGET_EXCEEDED
COMMAND_FAILED
RECEIPT_WRITE_FAILED
```

### Output

```text
github-delivery-local-verification/v1 receipt
+ evidence artifact
```

### Human boundary

The consumer decides which commands are necessary. A shared Skill cannot decide that a generic linter proves a domain-specific release.

---

## 4. GitHub-observation state machine

**Owner:** `github_actions_snapshot.py`

**Purpose:** separate live GitHub network observation from the zero-network publication decision.

### Capture lane

```text
CAPTURE_REQUESTED
    │ fixed read-only gh api calls
    ▼
REPOSITORY_OBSERVED
    │ resolve zero or one open PR for branch
    ▼
PR_IDENTITY_OBSERVED
    │ resolve exact stable check name and billing annotations
    ▼
CHECK_STATE_OBSERVED
    │ write raw observation and normalized snapshot
    ▼
SNAPSHOT_EMITTED
```

### Replay lane

```text
SAVED_OBSERVATION
    │ zero-network normalization
    ▼
SNAPSHOT_EMITTED
```

### Failure terminals

```text
REPOSITORY_AMBIGUOUS
PUBLIC_REPOSITORY_UNEXPECTED
MULTIPLE_OPEN_PRS
PR_HEAD_DRIFT
CHECK_NAME_AMBIGUOUS
CHECK_HEAD_STALE
ACTIONS_STATE_UNKNOWN
MALFORMED_BILLING_ANNOTATION
NETWORK_CAPTURE_FAILED
```

### Billing circuit representation

```text
closed
billing-open
unknown
```

`billing-open` means GitHub did not allocate a runner because of account payment/spending state. It does not mean repository tests failed.

---

## 5. CI-publication state machine

**Owner:** `ci_publish_gate.py`

**Purpose:** admit one valuable remote publication rather than converting every local commit into a private-repository Actions run.

### Common preconditions

```text
exact local Git HEAD
+ LOCAL_VERIFIED receipt for that HEAD
+ valid repository/PR/check/billing snapshot
+ one explicit publication intent
```

### Main flow

```text
LOCAL_ITERATION
    │ complete a local batch
    ▼
LOCAL_VERIFIED
    │ trusted GitHub snapshot
    ▼
PUBLICATION_EVALUATED
    │
    ├── BLOCK(reason) ───────────────> REMAIN_LOCAL
    │
    └── ALLOW(one operation)
             │
             ▼
       PUBLICATION_EXECUTED
             │
             ▼
       REMOTE_HEAD_OBSERVED
             │
             ▼
       GITHUB_CHECK_REQUESTED
```

### Allowed intents

#### `initial-pr`

```text
PR_ABSENT
→ ALLOW push-and-create-draft-pr
→ DRAFT_PUBLISHED
```

A draft PR creates review visibility. It does not authorize repeated checkpoint pushes.

#### `ready-for-review`

```text
DRAFT_PUBLISHED
+ exact local verified HEAD
→ ALLOW ready-transition-only
  or push-and-ready-transition
→ READY_PUBLISHED
```

#### `batched-repair`

```text
READY_PUBLISHED
+ new actionable CI/review feedback bound to remote head
+ feedback not previously consumed
+ new local verified HEAD
→ ALLOW one batched repair push
→ REPAIR_PUBLISHED
```

### Billing circuit

```text
CIRCUIT_CLOSED
    │ billing/spending no-runner observation
    ▼
BILLING_CIRCUIT_OPEN
    │ owner-authored recovery receipt later than blocker
    ▼
ONE_RECOVERY_ATTEMPT_ADMITTED
    │ fresh observation
    ├── runner/check observed ──> CIRCUIT_CLOSED
    └── blocker persists ───────> BILLING_CIRCUIT_OPEN
```

### Stable block reasons

Representative reasons include:

```text
invalid-policy-input
local-verification-stale
initial-pr-already-exists
ready-requires-draft-pr
repair-requires-ready-pr
repair-feedback-absent
repair-feedback-already-consumed
repair-ci-check-stale
actions-state-unknown
billing-circuit-open
billing-recovery-invalid
```

### Forbidden transitions

```text
DRAFT_PUBLISHED → checkpoint push
BILLING_CIRCUIT_OPEN → rerun
BILLING_CIRCUIT_OPEN → no-op commit
old SHA success → authorize new SHA
feedback already consumed → second repair push
BLOCK → alternate API bypass
```

---

## 6. GitHub Actions workflow state machine

**Owner:** consumer repository workflow; `github-delivery-loop` only supplies the policy.

The current Skill Eval consumer pattern is:

```text
DRAFT PR opened/updated
→ SKIPPED_BY_POLICY before runner-backed contract job

READY_FOR_REVIEW / reopened / admitted synchronize
→ runner-backed deterministic contract job
→ SUCCESS / FAILURE / CANCELLED / TIMED_OUT

new head on same PR
→ concurrency cancels obsolete in-progress head

push main
→ one deterministic exact-tree integrity run

manual recovery
→ workflow_dispatch
```

Expensive physical model, browser, macOS, mobile, or provider execution is not part of every PR synchronization. It belongs to manual, release, path-specific, or scheduled lanes.

---

## 7. Git Town Worker state machine

**Owner:** consumer repository using `git-town-stacked-pr-worker`.

```text
TASK_ABSENT
    │ issue + goal + non-goals + path lease + evals + parent
    ▼
TASK_ADMITTED
    │ create isolated linked worktree and branch writer lease
    ▼
WORKTREE_READY
    │ local implementation commits
    ▼
LOCAL_ITERATION
    │ bounded parent-first sync, no push, no auto-resolve
    ▼
SYNCING
    ├── no change ──────────────> NO_CHANGE
    ├── successful rebase ──────> SYNCED_LOCAL
    ├── semantic conflict ──────> BLOCKED_CONFLICT
    ├── ancestry drift ─────────> BLOCKED_ANCESTRY
    ├── dirty state ────────────> BLOCKED_DIRTY
    └── timeout/tool failure ───> FAILED_TOOL

SYNCED_LOCAL
    │ local verification
    ▼
LOCALLY_GREEN
    │ CI publication state machine
    ▼
PR_PUBLISHED
```

### Human-owned exits

```text
semantic conflict resolution
git town continue / skip / undo / ship
merge
permission widening
release promotion
production rollback
```

The unattended Worker stops before these operations.

---

## 8. Merge-authority state machine

**Owner:** `merge_gate.py` coordinates; repository owner owns the decision.

```text
PR_OPEN
    │ owner applies merge-admit after current head
    ▼
HEAD_ADMITTED
    │ host preflight executes real policy planes
    ▼
PREFLIGHT_GREEN
    │ refresh GitHub head/check/mergeability
    ▼
LANDING_REQUESTED_WITH_EXPECTED_HEAD
    ├── exact head merged ──────> MERGED
    ├── request accepted/open ──> PENDING (exit 5; do not resubmit)
    ├── existing auto/queue ────> PENDING (exit 5; do not resubmit)
    ├── head moved ─────────────> ADMIT_STALE
    ├── closed without merge ───> MERGE_READBACK_FAILED
    ├── host policy denies ─────> HOST_POLICY_BLOCKED
    ├── GitHub rules deny ──────> GITHUB_BLOCKED
    └── no owner admit ─────────> NOT_ADMITTED
```

### Independent policy planes

```text
Human owner decision
Claude PreToolUse hooks
Codex PreToolUse hooks
Codex sandbox/network profile
Codex execpolicy
GitHub authentication
GitHub branch/repository rules
Required checks and mergeability
Merge API exact-head result
Provider readback of exact head, state, and mergedAt
```

One green plane cannot override a red plane.

---

## 9. Canonical Skill projection state machine

**Owner:** `link-canonical.sh` plus shared-skills governance.

```text
TARGET_ABSENT
    │ create link
    ▼
CANONICAL_LINKED

IDENTICAL_COPY
    │ dry-run plan
    │ move copy to backup; create link
    ▼
CANONICAL_LINKED

DIVERGED_COPY
    └── REFUSED_DIVERGENCE
```

A diverged copy is never silently moved or deleted. Reconciliation is a human decision.

---

## 10. Integrated macro flow

```text
PRD / goal
→ molecular issues with evals and path leases
→ Git Town sibling/child branch graph
→ isolated micro-loop implementation
→ local exact-HEAD verification
→ GitHub publication gate
→ draft/ready/batched-repair publication
→ deterministic GitHub check
→ review
→ owner merge-admit
→ host/GitHub preflight
→ checked-head merge
→ separate release/promotion state machine
```

No single exit code proves the full chain. Each transition must preserve its own subject and evidence.

## 11. Source-proposal boundary

The external PDF `科技巨頭開源授權與AI框架v2.pdf` contains proposed cloud/local runtime, synchronization, mobile, wallet, and security state flows. Those diagrams are source inputs, not states in the current GitHub delivery machines. Any adoption must create a new provider-specific contract, issue, eval, receipt, and Human Admit path.
