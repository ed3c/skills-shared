# GitHub Actions publication evals for Git Town Workers

Compose these evals with the base catalog in `EVALS.md`. Each consumer specializes paths, commands,
check names and receipt locations before implementation. A positive assertion without a control that can
turn it red is incomplete.

## GTSP-21 — Canonical publication-gate binding

**Assertion:** the repository profile resolves one canonical `github-delivery-loop` publication gate and
its exact versioned schemas; no consumer-local same-name Skill shadows it.

**Controls:** remove the gate reference, point at a mutable or arbitrary-shell entrypoint, add a local
same-name Skill, or make Claude and Codex resolve different gate bytes. Expected result:
`BLOCKED_POLICY`.

## GTSP-22 — Exact local verification subject

**Assertion:** publication is considered only after fixed local evals produce a PASS receipt for the actual
Git `HEAD` and repository identity.

**Controls:** reuse a receipt for an older SHA, different repository ID, empty command set, malformed digest,
or non-PASS status. Expected result: publication gate exit `64` or policy `BLOCK` according to the typed
consumer adapter; never ALLOW.

## GTSP-23 — Draft publication cadence

**Assertion:** `initial-pr` creates one draft PR; draft checkpoint commits and synchronizations do not request
a runner-backed trusted job. `ready-for-review` is the first normal trusted PR run.

**Controls:** permit a fourth `checkpoint` intent, run the heavy job on PR `opened`, or permit background
`git town sync --push`. Each mutation must turn red.

## GTSP-24 — One batched repair per feedback identity

**Assertion:** a ready PR can publish one complete repair batch only for new actionable CI/review feedback
bound to the exact current remote head.

**Controls:** use feedback from an older head, missing feedback, a non-actionable CI conclusion, or reuse the
same feedback after `consumed_by_sha` is populated. Expected result: BLOCK with a stable reason.

## GTSP-25 — Billing circuit breaker

**Assertion:** account payment/spending-limit evidence that prevented runner allocation opens
`billing-open`; Worker push, rerun, no-op commit and workflow weakening stop until an owner recovery receipt
names the exact blocker and a later timestamp.

**Controls:** omit recovery, use a non-owner, stale timestamp, wrong repository identity, different blocker
time, or treat the unstarted job as PASS/test FAIL. Each mutation must turn red.

## GTSP-26 — Scoped concurrency and stable trusted check

**Assertion:** the deterministic PR workflow uses PR/ref-scoped concurrency with
`cancel-in-progress: true`, retains one stable trusted check for ready PR heads, and preserves one main-tree
integrity run or an explicitly equivalent release gate.

**Controls:** remove cancellation, use a global cross-PR concurrency group, rename the required check without
updating policy, disable the final verifier, or add feature-branch `push` triggers.

## GTSP-27 — Publication evidence separation

**Assertion:** receipts report independently: local sync, local verification, publication decision, remote
publication, remote ancestry, GitHub trusted check, billing circuit and Human Admit.

**Controls:** collapse gate ALLOW into push PASS, push into trusted-check PASS, skipped draft into PASS, or a
GitHub check into merge approval. Each collapse must turn red.

## GTSP-28 — Background no-push invariant

**Assertion:** every unattended iteration uses the version-supported equivalent of:

```bash
git town sync --stack --non-interactive --no-auto-resolve --no-push
```

**Controls:** change `--no-push` to `--push`, invoke raw `git push`, `gh pr ready`, workflow rerun, no-op
commit, merge, `git town ship`, or permission mutation from the supervisor. Expected result:
`BLOCKED_POLICY` and preserved worktree/receipt.

## Evidence ladder

```text
static composition check
→ publication-policy selftest
→ local exact-HEAD receipt canary
→ draft PR no-runner observation
→ ready PR trusted-check observation
→ stale-head / billing-open negative control
→ remote ancestry receipt
→ Human Admit
```

A draft workflow intentionally suppressed by policy is `SKIPPED_BY_POLICY`, not PASS.

A lower lane never proxies a later lane. GitHub Actions account recovery and runner allocation remain
`NOT_EXERCISED` until observed on an exact subject.
