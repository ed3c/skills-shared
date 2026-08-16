# Repository Control Plane: one host runtime, thin repository attachments

Governance and implementation are tracked by `skills-shared#267`. The missing host-owned Git Town installer and doctor workload are tracked separately by `runtime-env#36`; this split prevents a consumer attachment from claiming a host tool was installed.

## Decision

A new repository must not vendor the central Skill bodies and must not reinstall Git Town or create another Forgejo service. It attaches to a reusable control plane through immutable identifiers and small consumer-owned files.

```text
skills-shared                     runtime-env / host
(method and composition plane)    (toolchain and service plane)
          │                                  │
          │ exact Skill binding              │ exact profile/workload binding
          └────────────────┬─────────────────┘
                           ▼
                 consumer repository
          requirements + control binding + receipts
```

The composition order is fixed:

```text
shared-skills-infra
→ procedural-shadow-runtime       # Shadow Architect role
→ agentic-tech-lead-orchestration # issue → contract/DAG/leases
→ spatial-loop-systems-engineering
→ git-town-stacked-pr-worker
→ dual-forge-repository-loop
```

This order separates responsibilities. Shadow admission cannot be replaced by a branch tool, a Git Town Stack cannot prove spatial invariants, and a dual-forge receipt cannot prove that a Worker respected the task contract.

## Ownership boundary

| Plane | Canonical owner | Installation scope | Consumer stores |
|---|---|---:|---|
| Skill bodies and composition profile | `skills-shared` | one canonical checkout per user | names, digests, exact source commit |
| `runtime-env` CLI | `runtime-env` | one stable user launcher | exact runtime-env commit and IDs |
| Git Town | `runtime-env` | one user-scoped binary | executable/probe IDs and receipts |
| Forgejo | `runtime-env` / host operator | one host service | endpoint variable name, profile/workload IDs, reconciliation receipts |
| Repository policy and adapters | consumer repository | repository-local | paths, remotes, commands, issue identities, runtime receipts |

A consumer must never contain a second `SKILL.md` body for a selected shared Skill. A project-level symlink or a single-file forwarder is a pointer; a directory with additional body files is shadowing and fails verification.

## Thin files in a consumer

`repository_control_plane.py attach` creates only two desired-state source files:

```text
.agents/shared-skills.requirements.json
.agents/repository-control-plane.json
```

`shared_skills.py sync` then creates the immutable generated Skill binding:

```text
.agents/bindings/repository-control-plane.json
```

The files contain no Skill body, credential value, local absolute path, shell command, browser session, mutable branch ref, or live execution claim.

The four machine contracts are versioned beside the profile:

```text
repository-control-plane-profile.schema.json
repository-control-plane-consumer-binding.schema.json
github-open-issues-snapshot.schema.json
repository-control-plane-monitor-plan.schema.json
```

The Python runtime still uses only the standard library. CI installs a pinned JSON Schema validator to prove the schemas themselves and validate generated consumer/monitor documents.

## Attach a new repository

Run from the canonical `skills-shared` checkout. The runtime-env commit must be an exact 40- or 64-hex commit.

```bash
RCP=skills/shared-skills-infra/scripts/repository_control_plane.py
SHARED=skills/shared-skills-infra/scripts/shared_skills.py
CONSUMER=/path/to/new-repository
RUNTIME_ENV_COMMIT=<exact-runtime-env-commit>

python3 "$RCP" profile-check

# Dry-run first. No file is written without --apply.
python3 "$RCP" attach \
  --target-root "$CONSUMER" \
  --consumer-repository-id owner/repository \
  --runtime-env-commit "$RUNTIME_ENV_COMMIT"

python3 "$RCP" attach \
  --target-root "$CONSUMER" \
  --consumer-repository-id owner/repository \
  --runtime-env-commit "$RUNTIME_ENV_COMMIT" \
  --apply

# Resolve selected Skill names to the clean canonical commit and content digests.
python3 "$SHARED" sync \
  --requirements "$CONSUMER/.agents/shared-skills.requirements.json" \
  --target-root "$CONSUMER" \
  --apply

python3 "$RCP" verify --target-root "$CONSUMER"
```

`verify` returns:

```text
0   thin attachment and immutable Skill closure are structurally valid
2   drift, shadow copy, mutable identity, or policy violation
3   source attachment or generated binding is absent / NOT_EXERCISED
64  malformed input
```

A structural `PASS` does not prove that Git Town or Forgejo executed. Host capabilities remain `NOT_EXERCISED` until their exact-subject receipts exist.

## Unfinished-issue monitor

The portable monitor is deliberately read-only. A host adapter retrieves the current GitHub issue snapshot; the central script only normalizes it into a deterministic controller plan.

Accepted snapshot shapes:

```json
[
  {
    "number": 42,
    "title": "Implement contract",
    "state": "open",
    "labels": ["status:in-progress"],
    "blocked_by": [41]
  }
]
```

```bash
python3 "$RCP" monitor-plan \
  --target-root "$CONSUMER" \
  --issues /path/to/github-open-issues.json \
  --output /path/to/monitor-plan.json
```

Every open issue receives the same six-phase controller chain and remains `NOT_EXERCISED`. `blocked_by` and blocked/in-progress labels affect routing state, not evidence state. The monitor cannot merge, resolve conflicts, change visibility, install host software, or write GitHub by itself.

## One-time host setup

The host has three reusable assets:

1. the canonical `skills-shared` checkout and user surfaces, wired with `shared_skills.py install`;
2. the stable `runtime-env` launcher, installed once under `~/.local/bin`;
3. one Forgejo service and credential broker for all consumer repositories.

The existing Forgejo profile/workload is reused:

```text
profile  forgejo-delivery-keychain-local
workload forgejo-delivery-loop
probe    credential-canary
```

The default profile currently records the Git Town setup entrypoint as `NOT_IMPLEMENTED`. This is intentional: a PATH lookup or documentation statement is not a pinned installer receipt. `runtime-env#36` owns the follow-up: install a checksum-verified binary once at user scope, update one stable launcher atomically, and emit a metadata-only receipt. Consumer repositories must not implement their own installers.

## Migration from copied setup

For each existing repository:

1. inventory project-local copies of the six selected Skill names;
2. preserve differentiated repo-owned adapters, fixtures, paths, remotes, and receipts;
3. remove or archive only duplicate canonical bodies;
4. run `shared_skills.py install --project <repo>` for local host pointers;
5. run `repository_control_plane.py attach --apply`;
6. run `shared_skills.py sync --apply`;
7. verify no shadow copies and record missing runtime lanes as `NOT_EXERCISED`;
8. run live Git Town, Forgejo, Worktree, and dual-forge canaries only through admitted host adapters.

## Rollback

Rollback is deletion of the generated attachment files plus restoration of the prior consumer commit. It must not delete the central checkout, uninstall user tools, stop the shared Forgejo service, erase receipts, or restore copied Skill bodies.

```text
consumer rollback != host teardown
consumer detach   != canonical Skill deletion
structural PASS   != live runtime PASS
```
