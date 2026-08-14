# Repository profile — Git Town Stacked-PR Worker

> Copy this template into the consuming repository. The completed profile is repo-owned. Replace every required placeholder; unresolved placeholders are `ABSENT` and block Worker execution.

## Identity

```yaml
schema: git-town-stacked-pr-worker/repo-profile/v1
repository:
  full_name: <REPO_FULL_NAME>
  immutable_identity: <REPO_IDENTITY>
  default_branch: <MAIN_BRANCH>
  perennial_branches:
    - <PERENNIAL_BRANCH>
  allowed_remote_name: <ALLOWED_REMOTE_NAME>
  allowed_remote_url_pattern: <CREDENTIAL_FREE_REMOTE_PATTERN>
```

`immutable_identity` should be a stable repository ID or another repository-approved identity, not only a mutable display name.

## Authority documents

```yaml
authority:
  agents: <AGENTS_PATH>
  architecture: <ARCHITECTURE_PATH>
  git_governance: <GIT_GOVERNANCE_DOC>
  harness: <HARNESS_DOC>
  path_ownership: <PATH_OWNERSHIP_DOC_OR_MANIFEST>
  git_town_admission: <GIT_TOWN_ADMISSION_DOC>
  issue_template: <ISSUE_TEMPLATE_PATH>
  pull_request_template: <PR_TEMPLATE_PATH>
```

## Git Town admission

```yaml
git_town:
  version: <EXACT_VERSION>
  source_repository: <SOURCE_REPOSITORY>
  immutable_release: <TAG_COMMIT_OR_RELEASE_ID>
  platform: <PLATFORM>
  architecture: <ARCHITECTURE>
  executable_sha256: <SHA256_OR_HOST_OWNED_RECEIPT_REF>
  provenance_ref: <PROVENANCE_REF>
  direct_license: <SPDX_ID>
  direct_license_sha256: <SHA256>
  sbom_or_transitive_review: <PASS_FAIL_ABSENT_NOT_EXERCISED_AND_REF>
  notices_review: <PASS_FAIL_ABSENT_NOT_EXERCISED_AND_REF>
  legal_approval: <PASS_FAIL_ABSENT_NOT_EXERCISED_AND_REF>
```

Do not use `latest` as an executable identity. A direct permissive license does not complete the transitive/legal fields automatically.

## Synchronization policy

```yaml
sync:
  feature_strategy: <rebase_or_repo_approved_strategy>
  perennial_strategy: <ff-only_or_repo_approved_strategy>
  default_scope: stack
  non_interactive: true
  auto_resolve: false
  default_push: false
  allow_all_stacks: false
  timeout_seconds: <POSITIVE_INTEGER>
  dry_run_required: true
  post_sync_ancestry_check: true
  rerun_evals_after_sync: true
```

Explain every deviation from the safe defaults:

```text
<DEVIATIONS_AND_REASONS_OR_NONE>
```

## Worktree and lease policy

```yaml
workers:
  primary_checkout_mutation: denied
  linked_worktree_required: true
  worktree_root: <HOST_OWNED_LOGICAL_ROOT_OR_SELECTOR>
  branch_lease_root: <HOST_OWNED_LOGICAL_ROOT_OR_SELECTOR>
  repository_lease: <required_or_policy>
  lease_ttl_seconds: <POSITIVE_INTEGER>
  sibling_path_overlap: denied
  preserve_blocked_worktree: true
```

Do not commit machine-specific worktree roots when repository policy keeps them host-owned. The tracked profile may store a logical selector or placeholder resolved by trusted host configuration.

## Receipt policy

```yaml
receipts:
  root: <RECEIPT_ROOT>
  schema: git-town-stacked-pr-worker/receipt/v1
  append_only: true
  max_stream_bytes: <POSITIVE_INTEGER>
  secret_values: denied
  absolute_secret_paths: denied
  task_packet_digest_required: true
  before_after_graph_required: true
  cleanup_lane_required: true
```

## Background policy

```yaml
background:
  enabled: <true_or_false>
  max_iterations: <POSITIVE_INTEGER>
  interval_seconds: <POSITIVE_INTEGER>
  no_push: true
  stop_on_blocked_state: true
  stop_on_task_packet_change: true
  stop_on_lease_loss: true
  stop_on_conflict: true
  stop_on_failed_eval: true
```

## Publication policy

```yaml
publication:
  enabled: <true_or_false>
  task_packet_authorization_required: true
  explicit_cli_flag: <PUBLISH_FLAG>
  environment_guard_name: <PUBLISH_GUARD_NAME>
  environment_guard_expected_value: <PUBLISH_GUARD_VALUE>
  allowed_remote: <ALLOWED_REMOTE_NAME>
  protected_branch_rewrite: denied
  post_push_fetch_and_verify: true
```

The expected guard value is not a secret. Do not put a token in this field.

## Prompt suppression

```yaml
unattended_environment:
  GIT_TERMINAL_PROMPT: "0"
  GIT_EDITOR: ":"
  GIT_SEQUENCE_EDITOR: ":"
  GCM_INTERACTIVE: "Never"
```

Additional host variables may be named, but values must not enter receipts or logs.

## Required task packet fields

```yaml
task_packet:
  required:
    - issue_id
    - goal
    - non_goals
    - base_branch
    - parent_branch
    - head_branch
    - stack_class
    - allowed_paths
    - excluded_paths
    - dependencies
    - parallel_safe_siblings
    - required_evals
    - negative_or_mutation_controls
    - evidence_boundary
    - cleanup_contract
    - rollback_subject
    - human_owned_operations
```

## Required eval commands

```yaml
evals:
  commands:
    - <COMMAND_OR_TYPED_ENTRYPOINT>
  live_git_town_canary: <COMMAND_OR_NOT_EXERCISED>
  conflict_canary: <COMMAND_OR_NOT_EXERCISED>
  publication_canary: <COMMAND_OR_NOT_EXERCISED>
```

Commands must be fixed/typed entrypoints. Do not expose arbitrary trailing shell through MCP or a task packet.

## Forbidden paths and data

```yaml
forbidden:
  paths:
    - <FORBIDDEN_PATH_PATTERN>
  data_classes:
    - credentials
    - tokens
    - private_keys
    - env_values
    - cookies
    - browser_profiles
    - device_sessions
    - host_keyrings
    - unbounded_model_output
```

## Human-owned operations

```yaml
human_owned:
  - semantic_conflict_resolution
  - git_town_continue_skip_undo_ship
  - merge_or_merge_queue_admission
  - branch_protection_or_permission_change
  - legal_or_license_acceptance
  - secret_or_credential_setup
  - release_promotion
  - production_deployment
  - destructive_or_drifted_rollback
```

## Validation checklist

- [ ] no required placeholder remains unresolved;
- [ ] repository identity and remote are exact and credential-free;
- [ ] Git Town version is immutable and policy evidence is referenced;
- [ ] feature/perennial strategies match branch-protection policy;
- [ ] default sync is non-interactive, no-auto-resolve, bounded and no-push;
- [ ] worktree/branch/path leases are defined;
- [ ] background loop is bounded and stops on blocked states;
- [ ] publication has two explicit guards plus post-push verification;
- [ ] evals include planted conflicts and disagreement controls;
- [ ] receipts exclude secret values and bind exact subjects;
- [ ] Human Admit boundaries are unchanged;
- [ ] rollback is immutable and drift-aware.