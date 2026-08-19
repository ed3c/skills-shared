# `git-town-stacked-pr-worker`

Portable method for coordinating multiple Worker Agents with Git Town, isolated linked worktrees, eval-first task packets, bounded no-push synchronization, molecular issue/PR traceability, explicit multi-parent convergence, and Human Admit. This Skill does not own a consumer repository's branches, `.git-town.toml`, CI, remotes, receipts, merge, release, or promotion.

## Read order

1. [`SKILL.md`](SKILL.md) — portable operating law.
2. This README — State Machines, DAG rules, data flow and current Molecular index.
3. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) — Worker instruction body.
4. [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) — publication/no-push boundary.
5. [`references/ADOPTION.md`](references/ADOPTION.md), [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md), [`references/EVALS.md`](references/EVALS.md), [`references/COMPLETION_REPORT.template.md`](references/COMPLETION_REPORT.template.md).
6. [`references/TECH_LEAD_FAN_OUT.md`](references/TECH_LEAD_FAN_OUT.md) and [`references/FAN_OUT_CONTRACT.schema.json`](references/FAN_OUT_CONTRACT.schema.json).
7. [`references/MOLECULAR_STACK_INDEX.md`](references/MOLECULAR_STACK_INDEX.md), `references/molecular-stack-index.schema.json`, example and checker.
8. [`modules/domain-profile.md`](modules/domain-profile.md) only when a concrete forge/carrier must be selected.
9. `evals.json`, `scripts/`, `tests/`.
10. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) for proof-carrying refactor contracts.
11. [`../github-delivery-loop/README.md`](../github-delivery-loop/README.md) for GitHub publication/merge State Machines.
12. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md) and [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md) for current closure/control-plane subjects.
13. current issue/PR/workflow/Git subjects before mutation.

## Ownership

```text
Git Town
  branch hierarchy + parent-first synchronization

Shared Skill
  portable Worker method + fan-out/eval/Molecular traceability contracts

Consumer repository
  branch graph + worktrees + leases + commands + CI + publication guards

Tech Lead
  semantic task DAG, writer/lease admission, one convergence owner

Independent Shadow
  same-subject applicability/contradiction/evidence-ceiling findings; no second writer

Human / trusted operator
  semantic conflict + force-push admission + merge + legal acceptance + release + rollback
```

## Worker State Machine

```text
TASK_ABSENT
→ TASK_ADMITTED
→ WORKTREE_READY
→ LOCAL_ITERATION
→ SYNCING
    ├── NO_CHANGE
    ├── SYNCED_LOCAL
    ├── BLOCKED_DIRTY
    ├── BLOCKED_CONFLICT
    ├── BLOCKED_ANCESTRY
    ├── BLOCKED_TIMEOUT
    └── FAILED_TOOL
→ LOCALLY_GREEN
→ PR_PUBLISHED
→ MERGE_OWNED_OUTSIDE_WORKER
```

A blocked state preserves worktree, branch and recovery evidence. It never silently continues.

## Molecular delivery State Machine

```text
ISSUE_CONTRACTED
→ PATH_AND_BRANCH_LEASED
→ BRANCH_CREATED
→ LOCAL_IMPLEMENTATION
→ LOCAL_EVALS_GREEN
→ PR_DRAFT / PR_OPEN
→ EXACT_HEAD_CHECKS_OBSERVED
→ READY_FOR_HUMAN_ADMIT
→ MERGED
```

Allowed tracked states include `PLANNED`, `BRANCH_CREATED`, `PR_DRAFT`, `PR_OPEN`, `BLOCKED`, `READY_FOR_HUMAN_ADMIT`, `MERGED`, `CLOSED_NOT_PLANNED`, `EXTERNAL_OPEN`. Branch names, issue closure, documentation PASS, prior green runs, or merge-side effects do not substitute for exact node state.

## Synchronization boundary

Unattended sync is conceptually:

```bash
git town sync \
  --stack \
  --non-interactive \
  --no-auto-resolve \
  --no-push
```

Consumer wrappers own exact Git Town artifact admission, dirty/rebase/merge preflight, one active branch/path/resource writer, bounded timeout/log budget, receipts/BLOCKED markers, post-sync ancestry and explicit publication guards. `git town sync` exit `0` proves synchronization only.

## DAG relation vocabulary

### `SIBLING`

Path/resource-disjoint work that consumes only a common admitted base. Do not serialize it for visual convenience.

```text
main
├── sibling-A
├── sibling-B
└── sibling-C
```

### `TRUE_CHILD`

A child consumes a named unmerged parent contract/code/proof/document artifact. The branch base must reflect that dependency.

```text
main
└── contract
    └── implementation
        └── consumer
```

### `CONVERGENCE`

One owner consumes several admitted prerequisite artifacts and updates shared indexes/integration/e2e surfaces. A convergence commit may have multiple sibling parents. That records consumption without making the siblings children of each other.

### `PROCESS_DEPENDENCY`

Ordering without Git ancestry, for example waiting for an audit/receipt before Human Admit.

### `EXTERNAL_EVIDENCE`

Independent runtime/Shadow/provider receipt lane. It owns no implementation paths unless it is itself implementing code.

### `HISTORICAL`

Immutable admitted/rejected/forensic subject retained for lineage, not current mutable authority.

## Molecular atom contract

Each implementation atom records:

```text
issue / PR
relation class
branch + common base or true parent
owns_paths
consumes_artifacts / provides_artifacts
one writer/resource lease
evals + negative controls
exact-head hosted/runtime evidence
terminal classification
remaining evidence ceiling
rollback
Human-owned operations
successor/convergence owner
```

The machine index and `assert_molecular_stack_index.py` reject hidden multi-parent convergence, fake serial siblings, overlapping writer leases, self-embedded mutable open heads, review-only atoms used as parents, external evidence owning Stack paths, false merged state and widened merge/release authority.

## Current Codex control-plane Molecular index — #375–#380

Current common base observed for the hardened sibling epoch:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Relation | Current exact head | Provides | Deterministic denominator | Remaining ceiling |
|---|---|---|---|---|---|---|
| `A-CODEX` | `#375 / #451` | `SIBLING` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact session/result contract, clean-worktree subject preflight, SDK runner, post-turn writable-lease readback | `4 positive / 14 mutations`; own Skill Suites + Shared Skills Infra green | live SDK `NOT_EXERCISED`; independent acceptance still required |
| `A-GH-DAG` | `#376 / #452` | `SIBLING` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection, repo/default-branch/visibility + issue-state + closing-PR-reference preflight, non-destructive readback | `6 positive / 17 mutations`; own Skill Suites + Shared Skills Infra green | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| `A-HERDR` | `#377 / #453` | `SIBLING` | `5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf` | optional pane/workspace/process/native-session/foreground-CWD observer + fallback | `4 positive / 9 mutations` | live Herdr `NOT_EXERCISED` |
| `K-CLOSURE` | `#378 / #454` | `SIBLING` | `32c5425de1cf4f083bd998e81873a86af8771e1e` | source→task/DAG→session/evidence closure schema/checker/renderer | `4 positive / 11 mutations` | real source/provider closure `EVIDENCE_DEPENDENT` |
| `D-TRACE` | `#379 refs / #380` | `SIBLING / DOCUMENTATION` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original control-plane design/trace routing | navigation only | consumed by convergence; no runtime claim |
| `X-CONVERGENCE` | `#379 / #455` | `CONVERGENCE` | read current head from GitHub | exact sibling bytes + shared `run-all`, Agent routes, Shadow relation, Git Town/trace indexes | current final head must rerun Skill Suites + Shared Skills Infra + Skill Eval Contract + Git Town workflow | static/deterministic scope only; Human Admit/merge/release separate |

Current hardened-parent convergence refresh:

```text
5d21ecab137cb26586ef1636dc279ee29733e913
parents:
  35874af7a6d04783983b05c8f1b1e402471b4451  prior #455 epoch
  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  #451 current
  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  #452 current
```

The final mutable #455 head is never self-embedded in this README. Read it from GitHub after every convergence edit.

### Historical convergence epoch 1

The earlier implementation convergence remains immutable lineage:

```text
c0f6979f80038394350aea724c598c8dba5ac338
parents:
  ccef97dedd7ea8b1873e3afa130ca82b8eabb413
  339ae874b070fb3a8a5fa89b0241d90434257e99  historical #451
  b5295df681d6471b19775db38860b2d151339879  historical #452
  5b6e58d1e7e9e127123dbb4a9189b98e5ff973cf
  32c5425de1cf4f083bd998e81873a86af8771e1e
union tree 37cb2c56e7dfc939cacaa0f65cf8f9b0f8318b22
```

Then `af427a13...` consumed PR #380 documentation and `35874af7...` refreshed current-main-at-that-time. That epoch passed all four hosted workflows and received a Shadow static verdict, but it became `HISTORICAL` when #451/#452 moved. Green evidence never follows a moving parent automatically.

Rejected first candidates are preserved:

```text
#444 → #451
#445 → #452
#446 → #453
#447 → #454
```

They are `HISTORICAL / REJECTED`, not alternate merge candidates.

### Current control-plane data flow

```text
A-CODEX ─┐
A-GH-DAG ├─ exact current sibling bytes ─┐
A-HERDR ─┤                               │
K-CLOSURE┘                               ├→ X-CONVERGENCE (#379/#455)
D-TRACE ─── documentation sibling ───────┘       │
                                                  ├→ unconditional shared ATL suite
                                                  ├→ independent Shadow readback
                                                  ├→ repository-wide hosted workflows
                                                  └→ Human Admit for static scope

live Codex / live GitHub mutation / live Herdr / real source-provider closure
  = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
  ≠ Git children of X-CONVERGENCE
```

## Required shared convergence gates

The convergence subject contains the sibling bytes first; then `agentic-tech-lead-orchestration/tests/run-all.sh` unconditionally executes:

```text
6 Draft-2020-12 schemas
problem-closure example
Codex selftest        4 / 14
GitHub DAG selftest   6 / 17
Herdr selftest        4 / 9
closure selftest      4 / 11
closure checker + Markdown non-authority marker
existing ATL suite
```

No required test may be hidden behind `if file exists`.

Hosted final-head denominator:

```text
Skill Suites
Shared Skills Infra
Skill Eval Contract
Git Town Stacked PR Worker (offline-contract + live-canary)
```

An earlier green head is historical after any consumed sibling head moves.

## Human-owned operations / rollback

```text
semantic conflict resolution       HUMAN
force update / force push          HUMAN / repository policy
unmanaged GitHub blocker deletion  HUMAN or separately admitted policy
merge                              HUMAN / repository merge authority
release / promotion                HUMAN / repository release authority
rollback                           reviewed revert to an exact admitted pre-convergence subject
```

No workflow green state, Shadow agreement, issue close or PR publication substitutes for these operations.

## Publication and merge boundary

```text
local verified batch
→ trusted GitHub snapshot
→ draft / ready publication
→ exact-head checks
→ review
→ Human merge-admit
→ checked-head landing
```

Git Town does not bypass publication or merge gates. Open PR heads are read from GitHub metadata; immutable merged/rejected/convergence ancestors may be recorded durably.

## Conflict policy

Semantic conflict is terminal for unattended execution:

```text
sync conflict
→ BLOCKED_CONFLICT receipt
→ preserve worktree and suspended state
→ Human/recovery assignment
→ reviewed resolution
→ explicit continue
→ full eval replay
```

Workers must not automatically run `git town continue`, `skip`, `undo`, `ship`, semantic conflict edits, force push, merge, permission widening or production rollback.

## Proof-carrying refactor and historical indexes

The current golden proof lineage and cross-Skill adoption state live in [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) and [`../../docs/traceability/TRACEABILITY_INDEX.md`](../../docs/traceability/TRACEABILITY_INDEX.md). Historical consumer snapshots, IBC/CTL delivery lines and other programme indexes remain traceability subjects rather than being duplicated as current mutable state here.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
EVIDENCE_DEPENDENT
HUMAN_ADMIT_REQUIRED
```

A static prompt, schema, Stack graph, deterministic test or hosted workflow cannot by itself prove live Codex/Herdr/GitHub effects, real source/provider closure, model uplift, merge, release or production readiness.

## Adoption checklist

- pin/admit exact Git Town artifact;
- define repository profile and `.git-town.toml`;
- enforce one Worker/branch/worktree and branch/path/resource leases;
- declare consumed/provided artifacts and one convergence owner;
- add machine-readable Molecular Stack index;
- add bounded no-push sync wrappers and receipts;
- run local verification before publication;
- integrate GitHub publication and merge gates;
- plant conflict, dirty, ancestry, timeout, false-child, stale-head and publication controls;
- keep semantic conflict, force push, ship, merge, release and promotion Human-owned.
