# Repository control-plane profile

The canonical `repository-control-plane-profile/v1` composes shared procedure bodies without copying them into consumer repositories.

```text
shared-skills-infra
→ procedural-shadow-runtime
→ agentic-tech-lead-orchestration
→ spatial-loop-systems-engineering
→ git-town-stacked-pr-worker
→ dual-forge-repository-loop
```

## Attach

From a clean `skills-shared` checkout, run:

```bash
python3 skills/shared-skills-infra/scripts/repository_control_plane.py \
  profile-check

python3 skills/shared-skills-infra/scripts/repository_control_plane.py \
  attach --consumer <consumer-repository>
```

`attach` writes only thin consumer material:

```text
<consumer>/.agents/control-plane/profile.json
<consumer>/.agents/control-plane/requirements.json
<consumer>/.agents/bindings/repository-control-plane.json
```

The binding itself is rendered by the existing `shared_skills.py sync` mechanism and therefore content-binds canonical Skill bodies without vendoring them.

## Verify

```bash
python3 skills/shared-skills-infra/scripts/repository_control_plane.py \
  verify --consumer <consumer-repository>
```

Verification refuses project-local body copies, profile drift, closure drift, and stale generated binding bytes. It does not prove that any host loaded the Skill or that any Agent/runtime executed it.

## Offline unfinished-issue monitor plan

Prepare a JSON array of issue identities and dependencies, then run:

```bash
python3 skills/shared-skills-infra/scripts/repository_control_plane.py \
  monitor-plan --issues <issue-packet.json>
```

The plan rejects duplicate issue identities and cycles. It returns deterministic dependency waves only; it never merges, resolves conflicts, changes visibility, or invokes a provider.

## Runtime ownership

- Git Town is one user-scoped runtime capability. Its installer remains `NOT_IMPLEMENTED` until `runtime-env` owns an immutable, receipt-producing implementation.
- Forgejo is one host-scoped service. The default profile records its live state as `NOT_EXERCISED`; a running service requires a separate exact-subject runtime receipt.
- Credentials, provider sessions, local service endpoints, worktrees, repository remotes, issue/PR identities, and runtime receipts stay outside the canonical profile.

## Migration

1. Remove project-local copies of any shared control-plane Skill; keep repo-owned material only in bindings/modules owned by the consumer.
2. Bind the consumer to a clean canonical `skills-shared` subject.
3. Run `profile-check`.
4. Run `attach` against the consumer worktree.
5. Review the three generated thin files and commit them in the consumer repository using its normal delivery policy.
6. Run `verify` on the exact consumer head.
7. Run host-specific cold-start/runtime canaries separately; do not infer them from attachment success.

## Rollback

Rollback is consumer-owned and byte-scoped:

1. restore the previous committed `.agents/control-plane/` and `.agents/bindings/repository-control-plane.json` files, or remove the new binding if the consumer had no previous profile;
2. rebind to the previous immutable `skills-shared` subject;
3. rerun the existing `shared_skills.py sync --check` and control-plane `verify`;
4. preserve any failed runtime receipts as historical evidence rather than deleting them.

Rollback never changes repository visibility, credentials, provider state, or merge authority.

## Evidence boundary

A green profile/attachment suite establishes only deterministic composition, thin binding, drift/refusal behavior, and offline monitor-plan behavior for the exact repository bytes. It does **not** establish Git Town installation, a running Forgejo service, multi-Agent execution, independent Shadow execution, dual-forge publication, CI success, merge, release, or production safety.
