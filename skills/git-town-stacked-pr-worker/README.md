# `git-town-stacked-pr-worker`

This Skill defines the portable method for using Git Town with multiple Worker Agents, isolated worktrees, eval-first task packets, bounded unattended synchronization, and Human Admit. It does not own a consumer repository's branches, `.git-town.toml`, CI, remotes, receipts, merge, or promotion.

## Read order

1. [`SKILL.md`](SKILL.md) — portable operating law.
2. This README — directory map, state machine, data flow, and integration with GitHub delivery.
3. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) — reusable Worker instruction body.
4. [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) — publication and no-push boundary.
5. [`references/ADOPTION.md`](references/ADOPTION.md) — consumer adoption path.
6. [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md) — repository-owned values.
7. [`references/EVALS.md`](references/EVALS.md) — eval design before implementation.
8. [`references/COMPLETION_REPORT.template.md`](references/COMPLETION_REPORT.template.md) — required Worker report.
9. [`evals.json`](evals.json), `scripts/`, and `tests/`.
10. [`../github-delivery-loop/README.md`](../github-delivery-loop/README.md) for GitHub publication and merge state machines.

## Directory map

```text
skills/git-town-stacked-pr-worker/
├── README.md
├── SKILL.md
├── SYSTEM_PROMPT.md
├── PUBLICATION_POLICY.md
├── evals.json
├── references/
│   ├── ADOPTION.md
│   ├── REPO_PROFILE.template.md
│   ├── EVALS.md
│   └── COMPLETION_REPORT.template.md
├── scripts/               portable method checks/helpers
└── tests/                 positive, hollow and policy controls
```

The consumer repository materializes the operational layer:

```text
consumer-repo/
├── .git-town.toml
├── AGENTS.md / CLAUDE.md
├── docs/git/
├── scripts/git-town/
├── data/git-town/receipts/
├── issue/PR task packets
└── isolated linked worktrees
```

Those consumer files must not be copied back into the shared Skill as if they were universal.

## Core ownership

```text
Git Town
  branch hierarchy + parent-first synchronization

Shared Skill
  portable Worker method + prompt + eval design

Consumer repository
  branch names + parent graph + worktree/receipt roots + Bash wrapper + CI + publication guard

Human / trusted operator
  semantic conflict resolution + merge + legal acceptance + promotion + rollback
```

## Worker state machine

```text
TASK_ABSENT
    │ admitted issue/task packet
    ▼
TASK_ADMITTED
    │ one branch + one linked worktree + one writer lease
    ▼
WORKTREE_READY
    │ local implementation and commits
    ▼
LOCAL_ITERATION
    │ bounded sync, no push, no auto-resolve
    ▼
SYNCING
    ├── NO_CHANGE
    ├── SYNCED_LOCAL
    ├── BLOCKED_DIRTY
    ├── BLOCKED_CONFLICT
    ├── BLOCKED_ANCESTRY
    ├── BLOCKED_TIMEOUT
    └── FAILED_TOOL

SYNCED_LOCAL
    │ consumer local evals
    ▼
LOCALLY_GREEN
    │ github-delivery publication gate
    ▼
PR_PUBLISHED
    │ review + Human Admit
    ▼
MERGE_OWNED_OUTSIDE_WORKER
```

Stable Worker outcomes are defined in `SKILL.md`. A blocked state preserves worktree and recovery evidence; it does not silently continue.

## Synchronization command boundary

The unattended form is conceptually:

```bash
git town sync \
  --stack \
  --non-interactive \
  --no-auto-resolve \
  --no-push
```

The consumer wrapper additionally owns:

```text
exact Git Town version and artifact admission
dirty/rebase/merge preflight
branch writer lease
path lease
timeout
log budget
receipt
BLOCKED marker
post-sync ancestry check
optional explicit double-guard publication
```

`git town sync` exit `0` proves only that synchronization completed. It does not prove tests, review, release readiness, or provider availability.

## Branch graph rules

### Sibling branches

Use sibling branches when work is path-disjoint and does not consume unmerged bytes:

```text
main
├── docs/architecture
├── tests/negative-controls
└── scripts/cost-gate
```

Serializing these changes would create artificial waiting and wider conflict surfaces.

### True child branches

Use a child only when the child requires the parent's unmerged contract or implementation:

```text
main
└── contract/v1
    └── adapter/v1
        └── consumer/v1
```

### Terminal leaf

A terminal leaf is the smallest PR that delivers one accepted behavior with its tests and evidence. It should not absorb unrelated cleanup, index work, or newly discovered scope.

### Convergence leaf

After independent siblings are reviewed or merged, a separate convergence/index PR may update shared indexes, links, coverage, and final acceptance. This avoids multiple Workers editing the same central file.

## Molecular issue and PR packet

Every Worker task defines before implementation:

```text
goal
non-goals
parent branch/PR
allowed paths
forbidden paths
provided/required contracts
evals
negative controls
evidence state and receipt path
timeout and cleanup
rollback subject
Human Admit boundary
```

Missing fields are `ABSENT`. The Worker does not guess them.

## Integration with `github-delivery-loop`

```text
Git Town Worker
→ local commits and parent-first rebase
→ local consumer evals
→ exact-HEAD local verification receipt
→ trusted GitHub snapshot
→ publication gate
→ draft / ready / one batched repair
→ GitHub checks
→ review
→ owner merge-admit
→ merge preflight and checked-head landing
```

Git Town never bypasses `ci_publish_gate.py` or `merge_gate.py`. Publication and merge are separate state machines with separate evidence.

## Current `skills-shared` Stack index

The historical Skill Eval implementation line was reviewed as:

```text
#32 → #33 → #34 → #35 → #36 → #39 → #42 → #46
```

The terminal leaf for the Actions-cadence consumer change was #46. The reusable publication policy was issue #43 / PR #44, developed as a separate policy line and then consumed by the workflow stack.

Issue #78 is an independent documentation leaf based on current `main`; it is not forced under the runtime stack because it consumes only merged bytes. A later automated documentation checker is a separate child.

See [`../github-delivery-loop/modules/traceability-index.md`](../github-delivery-loop/modules/traceability-index.md).

## Publication policy

Local commits and GitHub publications are different events. For private repositories:

```text
many local commits
→ one locally verified batch
→ initial draft publication
→ ready-for-review publication
→ one batched repair per actionable feedback subject
```

Background sync remains no-push. See [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) and the GitHub delivery cost-control module.

## Conflict policy

Semantic conflict is a terminal unattended state:

```text
sync conflict
→ BLOCKED_CONFLICT receipt
→ preserve worktree and Git Town suspended state
→ dedicated Human/recovery assignment
→ reviewed resolution
→ explicit continue
→ full eval replay
```

The Worker must not automatically run:

```text
git town continue
git town skip
git town undo
git town ship
semantic conflict edits
merge
permission widening
production rollback
```

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

The shared prompt can be statically reviewed. It cannot prove that a host has the admitted Git Town executable, that a real rebase ran, that a remote push succeeded, or that Human Admit occurred.

## Source-proposal boundary

The external PDF `科技巨頭開源授權與AI框架v2.pdf` proposes cloud/local runtimes and synchronization. Git Town source repair deliberately does not adopt timestamp-based `newest` or `prefer-beta` source overwrites. Source changes use one writer, exact ancestry, reviewable commits, evals, and checked publication.

## Adoption checklist

- pin and admit the exact Git Town artifact in the consumer environment;
- create the repository profile;
- define `.git-town.toml` and parent graph;
- add one-Worker/one-worktree and branch/path leases;
- add bounded no-push sync wrappers and receipts;
- integrate consumer local verification;
- integrate `github-delivery-loop` publication and merge gates;
- plant conflict, dirty-state, ancestry, timeout, and publication negative controls;
- keep merge/promotion human-owned.
