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
9. [`references/TECH_LEAD_FAN_OUT.md`](references/TECH_LEAD_FAN_OUT.md) and [`references/FAN_OUT_CONTRACT.schema.json`](references/FAN_OUT_CONTRACT.schema.json) — bounded multi-branch fan-out for TOURNAMENT, COOPERATIVE, SERIAL_STACK and HYBRID, checked by `scripts/check_fanout_contract.py`.
10. [`evals.json`](evals.json), `scripts/`, and `tests/`.
11. [`../github-delivery-loop/README.md`](../github-delivery-loop/README.md) for GitHub publication and merge state machines.
12. [`../procedural-core-refactor/README.md`](../procedural-core-refactor/README.md) when the Stack changes a shared `SKILL.md` ownership boundary.

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

Issue #78 was an earlier independent documentation leaf based on the then-current `main`; it was not forced under the runtime stack because it consumed only merged bytes. A later automated documentation checker remains a separate child.

See [`../github-delivery-loop/modules/traceability-index.md`](../github-delivery-loop/modules/traceability-index.md).

## Agentic Tech Lead repair Stack — exact molecular trace

This active Stack preserves the old T0–T10 strengths, repairs the modularization regression, runs the matched deterministic task, and then internalizes the refactor method.

```text
main
└─ #307 / PR #308  Tech Lead task/module/causal-DAG repair
   branch: fix/307-tech-lead-runtime-reachability
   exact candidate: 504c18f10d3380be4874a59f7cfad5c290daa93f
   evidence: DETERMINISTIC_FIXTURE
   CI: pending exact-head readback
   │
   └─ #312 / PR #315  production-shaped real-task A/B
      branch: agent/312-tech-lead-real-task-ab
      exact candidate: 403a4f041c5f8c07b0d7c8bb0ef2ccc44ac0f113
      evidence: SYNTHETIC_RUNTIME
      CI: pending exact-head readback
```

The child edge is real: #315 consumes #308's unmerged task gates, capability schemas and causal assertion. #315 is not evidence that Git Town itself ran; it uses a true GitHub branch/PR parent relation and real linked worktrees/processes while the Git Town lane remains `NOT_EXERCISED`.

## Procedural-core refactor standard Stack

```text
main
└─ #327 / PR #330  portable method and typed refactor contract
   branch: refactor/327-procedural-core-standard
   exact candidate: cffa44526d0d3e895256df36c2c7a1628fff49e2
   evidence: STATIC_CONTRACT
   │
   └─ #328 / PR #331  executable assertions + Tech Lead golden proof
      branch: refactor/328-procedural-core-proof
      exact candidate: f65e19c848831f2fcac5ed1f9c66e80b5680243f
      evidence: DETERMINISTIC_FIXTURE + preserved SYNTHETIC_RUNTIME proof
      │
      └─ #329 / convergence PR  AGENTS/README/registry/CI/Stack indexes
         branch: refactor/329-procedural-core-convergence
         exact candidate: assigned by the convergence commit
         evidence: NOT_EXERCISED until exact-head CI
```

These are true child edges:

- #331 imports the unmerged schema and stable `PCR-LAW-*` identities from #330;
- #329 consumes the unmerged checker and golden-proof ledger from #331 before it can admit registry, docs and CI routes.

The convergence leaf owns central files so the contract and proof leaves do not race on `AGENTS.md`, root indexes, `registry.json` or workflow matrices.

## Remaining terminal live lanes

These are not folded into a fake linear Stack because their runtimes/resources differ and they do not consume one another's unmerged implementation bytes:

| Issue | Terminal evidence sought | Current state |
|---|---|---|
| #231 | admitted live multi-Worker scheduler lifecycle and recovery | open; bounded canaries exist, universal/live scope not inferred |
| #232 | independent Shadow enforcement and global-objective retention | `NOT_EXERCISED` for the required independent live mode |
| #234 | actual Git Town commands plus Forgejo/GitHub consumer delivery | `NOT_EXERCISED` |
| #256 | exact-subject grepai/SCIP/Tree-sitter/Serena/SQLite and delivery receipts | partial lanes; completion open |
| #312 Phase 2 | matched clean-context live model/harness A/B | `NOT_EXERCISED` |

The complete trace unit is:

```text
issue
→ branch
→ parent/child justification
→ PR base/head
→ exact candidate head/tree
→ owning CI run/job
→ contract/receipt digest
→ evidence class and ceiling
→ residual lane
→ Human authority
```

An absent CI run stays `NOT_EXERCISED`; a PR link or Markdown claim cannot fill it in.

## Four-repository documentation sibling set

The current shared document-routing work is deliberately **not** a serial Stack:

```text
parent contract: ed3c/bettor-arena#35

main in each repository
├── skills-shared#85             procedural/domain routing method
├── runtime-env#30               runtime-contract route binding
├── agent-shield-monorepo#78     product/reference-consumer route binding
└── bettor-arena#37              integration/acceptance route binding

all four merged
└── bettor-arena#38              exact merged index + Claude/Codex cold-start convergence
```

Why these are siblings:

- each writes only documentation in its own repository;
- none consumes another sibling's unmerged bytes;
- each can be reviewed and merged independently;
- serializing them would create artificial ancestry and stale-green churn.

Why `bettor-arena#38` is a child/convergence leaf:

- it requires the exact merged commit/tree of all four siblings;
- it owns cross-repository link/role assertion comparison;
- it owns the fresh cold-start Agent audit;
- its branch must not be created before those inputs exist.

Exact candidate heads and current evidence states are recorded in [`../../docs/traceability/TRACEABILITY_INDEX.md`](../../docs/traceability/TRACEABILITY_INDEX.md). PR metadata remains the publication authority.

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

The external PDF proposes prompt fan-out into independent worktrees and side-by-side candidate selection; that source motivates the tournament/worktree test shape, but repository truth comes from exact code, assertions and receipts rather than the proposal. The PDF also proposes Contract-First constraints, immutable tests, true DAG edges and Stacked PRs; these remain requirements to prove, not automatic runtime facts.

## Adoption checklist

- pin and admit the exact Git Town artifact in the consumer environment;
- create the repository profile;
- define `.git-town.toml` and parent graph;
- add one-Worker/one-worktree and branch/path leases;
- add bounded no-push sync wrappers and receipts;
- integrate consumer local verification;
- integrate `github-delivery-loop` publication and merge gates;
- plant conflict, dirty-state, ancestry, timeout, and publication negative controls;
- invoke `procedural-core-refactor` before changing another shared `SKILL.md` boundary;
- keep merge/promotion human-owned.
