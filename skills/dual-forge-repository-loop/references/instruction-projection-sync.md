# Modular instruction projection and local/cloud synchronization

This contract prevents `skills-shared`, repository `AGENTS.md`, repository `CLAUDE.md`, and local global `~/.claude/CLAUDE.md` from becoming independent copies of the same law.

## Authority planes

```text
skills-shared
  instruction-projection.json
  = canonical machine-readable law
          |
          +----------------------+-----------------------+
          |                      |                       |
          v                      v                       v
repo AGENTS.md             repo CLAUDE.md        ~/.claude/CLAUDE.md
cross-host procedure       Claude adapter        local host projection
committed                  committed             host-owned / not committed
          |                      |                       |
          +----------- repo binding --------------+      |
                         |                                |
                         v                                v
                  GitHub Actions check             local sync receipt
                  repo-visible evidence            local-only evidence
```

The three projections are generated views. They are not co-equal sources of truth.

## Document design rules

### `AGENTS.md`

`AGENTS.md` remains the repository-level cross-host procedure. Repository-specific architecture, read order, invariants, test commands, and ownership rules stay outside the managed block. The shared block only owns runtime identity and dual-forge delivery laws.

### Repository `CLAUDE.md`

Repository `CLAUDE.md` is a Claude host adapter. It SHOULD point Claude to `AGENTS.md` for cross-host repository law and keep Claude-specific trigger/routing behavior outside the managed block. It MUST NOT fork or restate the canonical shared runtime/delivery law outside the managed block.

### Global `~/.claude/CLAUDE.md`

The global file is local host policy. It may contain user-wide Claude preferences and local host routing. The managed shared block provides runtime identity, worktree/Forgejo boundaries, and sync requirements. It is never committed to a consumer repository.

## Synchronization state machine

```text
CANONICAL_OBSERVED
  -> PROJECTION_RENDERED
  -> REPO_FILES_BOUND
  -> REPO_BINDING_WRITTEN
  -> REPO_CHECK_PASS
  -> CLOUD_CHECK_ELIGIBLE

local extension:
REPO_CHECK_PASS
  -> GLOBAL_CLAUDE_RENDERED
  -> GLOBAL_RECEIPT_WRITTEN
  -> LOCAL_CHECK_PASS

cross-plane convergence:
CLOUD_CHECK_ELIGIBLE + LOCAL_CHECK_PASS
  -> SAME_CANONICAL_COMMIT_AND_MODULE_DIGEST
  -> SYNCHRONIZED_FOR_DUAL_FORGE_WORK
```

Cloud and local lanes are intentionally asymmetric. GitHub Actions cannot inspect a developer's home directory; local Claude/Codex cannot claim an Actions run without GitHub evidence.

## Canonical identity

Every projection is bound to both:

```text
skills-shared exact commit SHA
instruction-projection.json SHA-256
```

A matching version string alone is insufficient. If either identity changes, old projections are stale.

## Managed block rules

The only replaceable region is:

```text
<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->
...
<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->
```

Synchronization MUST preserve all bytes outside the marker region except normal file creation when the file did not exist. Malformed or duplicate markers are an input error and must fail closed.

## Runtime-aware operation

Before mutation, classify the runtime using `runtime-identity.md` and the canonical JSON projection. Runtime identity is not model identity.

```text
CHATGPT_GITHUB_CONNECTOR
  -> GitHub connector operations only; no local/Actions claims

GITHUB_ACTIONS
  -> exact-run CI workspace; no developer worktree/Forgejo authority

CLAUDE_CODE_LOCAL / CODEX_CLI_LOCAL
  -> local git/worktree capability after checkout/remotes/ownership proof

CHATGPT_DESKTOP_WORKTREE
  -> only after actual Desktop-created worktree binding

UNKNOWN
  -> read/diagnose only; irreversible delivery blocked
```

## Local sync command

From a checked-out `skills-shared` repository:

```bash
python3 skills/dual-forge-repository-loop/scripts/sync_instruction_projections.py \
  --module skills/dual-forge-repository-loop/references/instruction-projection.json \
  --canonical-commit "$(git rev-parse HEAD)" \
  --mode write \
  --repo-root /path/to/consumer-repo \
  --include-global
```

Check without mutation by replacing `--mode write` with `--mode check`.

Local global state is recorded in:

```text
~/.claude/.skills-shared-projection-receipt.json
```

This receipt is host-owned and must not be committed.

## Repository binding

Each consumer repository receives:

```text
.skill-bindings/instruction-projection.json
```

It records the exact canonical repository/commit/module digest and the final repository projection digests. The global Claude lane remains `NOT_EXERCISED` in the committed binding because a repository cannot prove a developer's home-directory state.

## Cloud verification

A consumer GitHub workflow may run the same checker against repository files after materializing the canonical module at the bound commit. If a private canonical repository cannot be fetched under current credentials, report `ABSENT`/provider blocker; do not treat skipped freshness verification as PASS.

A repo-local structural check may still verify that both managed blocks and the binding agree, but that is weaker evidence than independently fetching the canonical module.

## Concurrency law

Parallel cloud/local work is admitted only when:

- each mutable branch has one writer;
- shared external mutable resources have an explicit lease owner;
- each worker starts from an exact base SHA;
- publication re-observes current GitHub state;
- final Actions evidence is bound to the exact publication candidate.

Instruction synchronization does not override these delivery laws; it ensures every runtime reads the same laws before acting.
