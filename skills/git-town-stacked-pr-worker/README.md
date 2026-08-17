# `git-town-stacked-pr-worker`

This Skill defines the portable method for using Git Town with multiple Worker Agents, isolated worktrees, eval-first task packets, bounded unattended synchronization, molecular traceability, and Human Admit. It does not own a consumer repository's branches, `.git-town.toml`, CI, remotes, receipts, merge, or promotion.

## Read order

1. [`SKILL.md`](SKILL.md) — portable operating law.
2. This README — directory map, State Machines, DAG rules, data flow, molecular Stack index, and GitHub delivery integration.
3. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) — reusable Worker instruction body.
4. [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) — publication and no-push boundary.
5. [`references/ADOPTION.md`](references/ADOPTION.md) — consumer adoption path.
6. [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md) — repository-owned values.
7. [`references/EVALS.md`](references/EVALS.md) — eval design before implementation.
8. [`references/COMPLETION_REPORT.template.md`](references/COMPLETION_REPORT.template.md) — required Worker report.
9. [`references/TECH_LEAD_FAN_OUT.md`](references/TECH_LEAD_FAN_OUT.md) and [`references/FAN_OUT_CONTRACT.schema.json`](references/FAN_OUT_CONTRACT.schema.json) — bounded fan-out for TOURNAMENT, COOPERATIVE, SERIAL_STACK and HYBRID, checked by `scripts/check_fanout_contract.py`.
10. [`evals.json`](evals.json), `scripts/`, and `tests/`.
11. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) for proof-carrying Skill refactor Stack contracts.
12. [`../github-delivery-loop/README.md`](../github-delivery-loop/README.md) for GitHub publication and merge State Machines.

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
│   ├── COMPLETION_REPORT.template.md
│   ├── TECH_LEAD_FAN_OUT.md
│   └── FAN_OUT_CONTRACT.schema.json
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
  portable Worker method + prompt + eval and traceability design

Consumer repository
  branch names + parent graph + worktree/receipt roots + wrapper + CI + publication guard

Human / trusted operator
  semantic conflict resolution + merge + legal acceptance + promotion + rollback
```

## Worker State Machine

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

Control states:

```text
PLANNED
BRANCH_CREATED
PR_DRAFT
PR_OPEN
EXACT_HEAD_GREEN
BLOCKED
READY_FOR_HUMAN_ADMIT
MERGED
CLOSED_NOT_PLANNED
EXTERNAL_OPEN
```

A branch name, issue close, PR merge event, documentation PASS, or old workflow run cannot substitute for the exact node state. Open PR heads are read from GitHub PR metadata. Only an immutable merged commit may be recorded as a durable merged head.

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

`git town sync` exit `0` proves only that synchronization completed. It does not prove implementation correctness, tests, review, release readiness, provider availability, or Human Admit.

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

Use a child only when the child requires the parent's unmerged contract, implementation, proof artifact, or documentation bytes:

```text
main
└── contract/v1
    └── adapter/v1
        └── consumer/v1
```

The child records the exact artifacts it consumes. A parent name without consumed bytes is a false dependency.

### Terminal leaf

A terminal leaf is the smallest PR that delivers one accepted behavior with its tests and evidence. It does not absorb unrelated cleanup, central index work, or newly discovered scope.

### Convergence leaf

After prerequisite leaves are stable, a separate convergence/index PR updates shared indexes, links, coverage, traceability, and final acceptance. It has one owner. Additional verified inputs may converge into it without inventing multiple Git parents.

### Process dependency and external evidence

A task may wait for an admitted standard or receive independent runtime evidence without being a Git child:

```text
PROCESS_DEPENDENCY
EXTERNAL_EVIDENCE
```

These edges are traceable but do not change branch ancestry.

## Molecular issue and PR packet

Every Worker task defines before implementation:

```text
goal
non-goals
issue(s)
PR and branch
base branch / parent PR
exact-head source
allowed and forbidden paths
consumed parent artifacts/contracts
provided artifacts/contracts
evals and negative controls
workflow state
terminal classification
remaining evidence ceiling
timeout and cleanup
rollback subject
Human Admit boundary
```

Missing fields are `ABSENT`. The Worker does not guess them.

## Standard machine-readable Stack index

A proof-carrying Skill refactor uses the contract under [`../skill-refactor-proof-loop/references/refactor-proof-stack.schema.json`](../skill-refactor-proof-loop/references/refactor-proof-stack.schema.json).

Required node fields:

| Field | Meaning |
|---|---|
| `issues` | issue contract identities; each issue has one node owner |
| `pull_request` | publication identity or `null` before publication |
| `branch` / `base_branch` | Git topology; a true child base equals its parent branch |
| `stack_class` | root, true child, sibling, convergence, planned follow-up, or external evidence |
| `owns_paths` | molecular path lease; external evidence owns none |
| `consumes_artifacts` | exact parent or process inputs |
| `provides_artifacts` | outputs available to downstream nodes |
| `evals` / `negative_controls` | falsifiable acceptance |
| `workflow` | exact execution state and source |
| `head` | open heads read from GitHub; merged heads are immutable |
| `terminal_classification` | implemented, partial, blocked, planned, external, merged, or not planned |
| `remaining_evidence` | explicit ceiling, never silently discarded |
| `rollback` | recoverable subject/action |
| `human_admit` | authority still outside Worker control |

The deterministic checker rejects a child without consumed parent bytes, a path-disjoint sibling serialized as a child, multiple convergence owners, stale self-embedded open heads, merged state without immutable evidence, external evidence owning Stack paths, duplicate issue/PR ownership, and widened force-push/ship/merge/release authority.

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

Git Town never bypasses `ci_publish_gate.py` or `merge_gate.py`. Publication and merge are separate State Machines with separate evidence.

## Current proof-carrying Skill refactor Stack

Canonical machine graph: [`../skill-refactor-proof-loop/references/refactor-proof-stack.json`](../skill-refactor-proof-loop/references/refactor-proof-stack.json).

```text
Epic #318

#307/#309 → PR #308
└─ #312 → PR #315
   └─ #319 → PR #323
      └─ #320 → PR #324
         └─ #321 → agent/321-refactor-proof-stack-index
            └─ #322 planned adoption audit after the standard is Human-admitted
```

Node index:

| Node | Issue | PR | Stack class | Branch → base | Owned outcome | Current state source |
|---|---|---|---|---|---|---|
| Tech Lead causal repair | `#307/#309` | `#308` | root | `fix/307-tech-lead-runtime-reachability` → `main` | task/schema/semantic/capability causal gates and frozen treatments | GitHub PR metadata |
| Hermetic golden proof | `#312` | `#315` | true child | `agent/312-tech-lead-real-task-ab` → PR #308 branch | matched worktrees/processes/checkpoint/tournament/global-objective proof | GitHub PR metadata |
| Portable proof contract | `#319` | `#323` | true child | `agent/319-skill-refactor-proof-contract` → PR #315 branch | `skill-refactor-proof-loop`, schemas, registry, mutation controls | GitHub PR metadata |
| Agent docs and State Machines | `#320` | `#324` | true child | `agent/320-refactor-proof-agent-docs` → PR #323 branch | root/nearest Agent contracts, directory State Machines, DAG/data flow | GitHub PR metadata |
| Molecular convergence/index | `#321` | pending publication | convergence | `agent/321-refactor-proof-stack-index` → PR #324 branch | machine Stack graph, Git Town template, traceability index | branch created; workflow `NOT_EXERCISED` |
| Cross-Skill adoption audit | `#322` | none | planned follow-up | no branch until admission | adoption ledger and deduplicated migration backlog | `PLANNED` |

Independent evidence lanes are not Git children:

```text
#231 live scheduler lifecycle
#232 independent Shadow/global objective
#234 real Git Town + dual-forge delivery
#256 exact-subject code-intelligence/executor adapters
```

They may raise the golden proof from L3 to L4/L5 only when receipts bind the same treatment, repository, task graph, budget, carrier and acceptance subjects.

## Historical `skills-shared` Stack index

The historical Skill Eval implementation line was reviewed as:

```text
#32 → #33 → #34 → #35 → #36 → #39 → #42 → #46
```

The terminal leaf for the Actions-cadence consumer change was #46. The reusable publication policy was issue #43 / PR #44, developed as a separate policy line and then consumed by the workflow stack.

Issue #78 was an earlier independent documentation leaf based on then-current `main`; it was not forced under the runtime stack because it consumed only merged bytes. A later automated documentation checker remains a separate child.

See [`../github-delivery-loop/modules/traceability-index.md`](../github-delivery-loop/modules/traceability-index.md).

## Four-repository documentation sibling set

The shared document-routing work was deliberately **not** a serial Stack:

```text
parent contract: ed3c/bettor-arena#35

main in each repository
├── skills-shared#85             procedural/domain routing method
├── runtime-env#30               runtime-contract route binding
├── agent-shield-monorepo#78     product/reference-consumer route binding
└── bettor-arena#37              integration/acceptance route binding

all four merged
└── bettor-arena#38              exact merged index + cold-start convergence
```

Why these are siblings:

- each writes only documentation in its own repository;
- none consumes another sibling's unmerged bytes;
- each can be reviewed and merged independently;
- serializing them would create artificial ancestry and stale-green churn.

Why `bettor-arena#38` is a convergence leaf:

- it requires the exact merged commit/tree of all four siblings;
- it owns cross-repository link/role assertion comparison;
- it owns the fresh cold-start Agent audit;
- its branch must not be created before those inputs exist.

Exact candidate heads and current evidence states are recorded in [`../../docs/traceability/TRACEABILITY_INDEX.md`](../../docs/traceability/TRACEABILITY_INDEX.md). PR metadata remains publication authority.

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
force push
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
HUMAN_ADMIT_REQUIRED
```

The shared prompt and Stack graph can be statically reviewed. They cannot prove that a host has the admitted Git Town executable, that a real rebase ran, that a remote push succeeded, that a provider executed, or that Human Admit occurred.

## Source-proposal boundary

External architecture proposals may describe cloud/local runtimes and synchronization. Git Town source repair does not adopt timestamp-based `newest` or `prefer-beta` overwrites. Source changes use one writer, exact ancestry, reviewable commits, evals, and checked publication.

## Adoption checklist

- pin and admit the exact Git Town artifact in the consumer environment;
- create the repository profile;
- define `.git-town.toml` and parent graph;
- add one-Worker/one-worktree and branch/path leases;
- declare consumed/provided artifacts and one convergence owner;
- add the machine-readable molecular Stack index;
- add bounded no-push sync wrappers and receipts;
- integrate consumer local verification;
- integrate `github-delivery-loop` publication and merge gates;
- plant conflict, dirty-state, ancestry, timeout, false-child, stale-head and publication negative controls;
- keep semantic conflict, force push, ship, merge, release and promotion Human-owned.
