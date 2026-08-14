# Live Git Town Canary

## Scope

This lane exercises the exact admitted Git Town release inside disposable local repositories. It proves more than static prompt inspection and less than consumer or publication admission.

Pinned release:

```text
Git Town                 24.0.0
Linux amd64 Debian asset git-town_linux_intel_64.deb
Linux amd64 Debian SHA   1535999a402e08c721538473808429eeb71beb929ef51a1438ba007434951dd7
checksums.txt SHA        7532377166cb59dc01c74f86e3a71c54ba9567a461313a5d203a1ea99c571b24
direct license marker    MIT License
legal acceptance         HUMAN_ADMIT_REQUIRED
```

The workflow downloads public release artifacts only. It does not receive repository write credentials.

## Positive canary

```text
disposable main
└── parent
    └── stale child
```

The canary:

1. creates one local bare remote;
2. establishes the branch graph with the admitted executable;
3. adds a new parent commit after the child exists;
4. opens the child in a linked isolated worktree;
5. executes `sync --stack --dry-run --non-interactive --no-auto-resolve --no-push`;
6. proves dry-run did not move local refs;
7. executes bounded local synchronization;
8. proves parent ancestry, unchanged `main`, clean worktree, and unchanged bare-remote refs.

Fixture-only pushes establish baseline refs before the no-push assertion. Git Town synchronization never publishes.

## Conflict canary

```text
parent changes shared line
child changes same shared line
→ sync
→ non-zero exit
→ unmerged path
→ suspended rebase state
→ unchanged remote refs
```

The test command log rejects automatic:

```text
continue
skip
undo
ship
```

The Harness removes the disposable directory after assertions. It does not semantically resolve the planted conflict.

## Receipt

`git-town-live-canary-receipt/v1` binds:

- exact candidate SHA;
- exact tool and release checksums;
- observed license bytes digest and marker;
- required CLI flags;
- dry-run immutability;
- post-sync ancestry;
- protected `main`;
- no-push remote immutability;
- conflict fail-closed state;
- Human-owned legal and merge boundaries.

## Evidence boundary

```text
exact public artifact checksum       PASS when workflow is green
disposable linked-worktree sync      PASS when workflow is green
stale-child ancestry repair          PASS when workflow is green
semantic conflict fail-closed        PASS when workflow is green
network publication                  NOT_EXERCISED
real consumer repository             NOT_EXERCISED
multi-Worker scheduler               NOT_EXERCISED
organization legal acceptance        HUMAN_ADMIT_REQUIRED
merge / ship                         HUMAN_ADMIT_REQUIRED
release promotion / rollback         HUMAN_ADMIT_REQUIRED
```

A green canary applies only to its exact candidate workflow and disposable fixture.
