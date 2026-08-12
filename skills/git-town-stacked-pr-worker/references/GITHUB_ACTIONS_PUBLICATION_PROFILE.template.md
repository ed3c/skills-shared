# Repository profile fragment — GitHub Actions publication

> Compose this fragment with `REPO_PROFILE.md` whenever a Git Town Worker can push a GitHub branch,
> create or update a pull request, transition a draft PR to ready, or trigger a private-repository
> GitHub Actions workflow. The completed profile is repository-owned; the portable policy remains in
> the shared `github-delivery-loop` and `git-town-stacked-pr-worker` Skills.

## Contract

```yaml
schema: git-town-stacked-pr-worker/github-actions-publication-profile/v1

publication:
  enabled: <true_or_false>

  gate:
    skill: github-delivery-loop
    entrypoint: <TYPED_ENTRYPOINT_TO_CI_PUBLISH_GATE>
    snapshot_schema: github-actions-publish-snapshot/v1
    local_verification_schema: github-delivery-local-verification/v1
    decision_schema: github-actions-publish-decision/v1
    recovery_schema: github-actions-billing-recovery/v1

  intents:
    allowed:
      - initial-pr
      - ready-for-review
      - batched-repair
    draft_checkpoint_push: denied
    feedback_reuse: denied

  local_verification:
    exact_head_required: true
    receipt_path_or_selector: <REPOSITORY_OWNED_RECEIPT_SELECTOR>
    required_commands:
      - <FIXED_LOCAL_VERIFICATION_ENTRYPOINT>

  github_snapshot:
    producer: <TRUSTED_SNAPSHOT_ENTRYPOINT>
    repository_identity_required: true
    exact_pr_head_required: true
    latest_check_head_required_for_ci_repair: true

  actions:
    private_repository: <true_or_false>
    draft_pr_runner_policy: no-runner
    obsolete_head_policy: cancel-in-progress
    stable_trusted_check: <STABLE_CHECK_NAME>
    default_branch_integrity_check: <STABLE_MAIN_CHECK_NAME_OR_SAME>
    manual_recovery_path: workflow_dispatch
    success_artifact_policy: no-upload-unless-release

  billing_circuit:
    mode: fail-closed
    blocked_state: billing-open
    owner_recovery_required: true
    recovery_must_postdate_blocker: true
    retry_probe_by_push: denied
    no_op_commit_probe: denied
    workflow_weakening: denied

  background_worker:
    git_town_push: denied
    raw_git_push: denied
    pr_ready_transition: denied
    workflow_rerun: denied

  remote_verification:
    post_push_fetch_required: true
    exact_remote_head_required: true
    ancestry_verification_required: true

  human_owned:
    - billing_recovery_receipt
    - merge_or_merge_queue_admission
    - branch_protection_or_permission_change
    - trusted_check_waiver
    - release_promotion
    - production_deployment
```

## Required invariants

1. `publication.gate.skill` resolves to the canonical shared `github-delivery-loop` body without a
   repository-local shadow copy.
2. `entrypoint` is a fixed typed command, not arbitrary shell and not a mutable remote URL.
3. The three allowed intents are exact and exhaustive. Local checkpoints are not a fourth intent.
4. The local verification receipt binds the actual Git `HEAD`; a receipt for an older SHA is stale.
5. A CI-repair snapshot binds actionable feedback and the latest check to the current remote PR head.
6. Background Git Town synchronization remains local and no-push.
7. `billing-open` blocks push, rerun and no-op commits until an owner recovery receipt names the exact
   blocker and a later recovery time.
8. Gate `ALLOW` permits only the returned operation. It is not merge, release or promotion authority.
9. Remote publication, remote ancestry and the GitHub trusted check remain separate evidence lanes.
10. Secret values, credential-bearing URLs and machine-specific paths do not enter the tracked profile.

## Validation checklist

- [ ] no required placeholder remains unresolved;
- [ ] canonical `github-delivery-loop` resolution is proven;
- [ ] exact gate/schema versions are recorded;
- [ ] only the three portable intents are admitted;
- [ ] local exact-HEAD verification is required;
- [ ] background push and ready transitions are denied;
- [ ] draft PR jobs do not allocate a runner-backed trusted job;
- [ ] obsolete PR heads are cancelled by scoped concurrency;
- [ ] billing recovery remains owner-authored and timestamp-bound;
- [ ] post-push fetch, head and ancestry checks are required;
- [ ] merge, permission widening and promotion remain human-owned.
