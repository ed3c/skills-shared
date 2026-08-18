# Repository Control-Plane Profile

The canonical `repository-control-plane-profile/v1` composes shared procedure bodies without copying them into consumer repositories.

```text
shared-skills-infra
→ procedural-shadow-runtime
→ agentic-tech-lead-orchestration
→ spatial-loop-systems-engineering
→ git-town-stacked-pr-worker
→ dual-forge-repository-loop
```

## Bootstrap a new modular consumer

Use the atomic bootstrap for a repository that does not yet have the standard multi-hop routes and thin binding:

```bash
python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py \
  --consumer <consumer-repository> \
  --repository-id <owner/repo> \
  --apply

python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py \
  --consumer <consumer-repository> \
  --repository-id <owner/repo> \
  --check
```

Read [`CONSUMER_BOOTSTRAP.md`](CONSUMER_BOOTSTRAP.md) for generated surfaces, State Machine, atomic rollback, Shadow controls, and evidence ceiling.

## Attach an already-routed consumer

```bash
python3 skills/shared-skills-infra/scripts/repository_control_plane.py profile-check
python3 skills/shared-skills-infra/scripts/repository_control_plane.py attach --consumer <consumer-repository>
python3 skills/shared-skills-infra/scripts/repository_control_plane.py verify --consumer <consumer-repository>
```

`attach` writes only:

```text
<consumer>/.agents/control-plane/profile.json
<consumer>/.agents/control-plane/requirements.json
<consumer>/.agents/bindings/repository-control-plane.json
```

The binding is rendered by `shared_skills.py sync` and content-binds canonical Skill bodies without vendoring them.

## Offline unfinished-issue monitor plan

```bash
python3 skills/shared-skills-infra/scripts/repository_control_plane.py \
  monitor-plan --issues <issue-packet.json>
```

The planner rejects duplicates, missing dependency closure, and cycles. It never merges, resolves conflicts, changes visibility, or invokes providers.

## Runtime ownership

- Git Town remains a user-scoped runtime capability. Installation is `NOT_IMPLEMENTED` until `runtime-env` owns a pinned receipt-producing installer.
- Forgejo remains host-scoped. A running service requires an exact runtime receipt.
- Credentials, sessions, endpoints, worktrees, remotes, issue/PR identities, and live receipts stay outside the canonical profile.

## Migration and rollback

1. Remove or classify project-local copies of shared Skill names.
2. Bind a clean immutable `skills-shared` subject.
3. Bootstrap or attach the consumer.
4. Review thin files and commit them under consumer delivery policy.
5. Run exact-head deterministic checks.
6. Run host-specific cold-start/runtime canaries separately.

Rollback restores the previous committed consumer subject and its thin generated files. It never changes visibility, credentials, provider state, merge authority, or production state.

## Evidence boundary

Green bootstrap/attachment evidence establishes deterministic composition, thin binding, drift/refusal behavior, route closure, and rollback identity for exact bytes. It does not establish host discovery, Git Town installation, Forgejo service state, multi-Agent execution, CI success in another repository, merge, release, or production safety.
