# `git-town-stacked-pr-worker`

Portable method for coordinating multiple Worker Agents with Git Town, isolated linked worktrees, eval-first task packets, bounded no-push synchronization, molecular issue/PR traceability, and Human Admit. This Skill does not own a consumer repository's branches, `.git-town.toml`, CI, remotes, receipts, merge, release, or promotion.

## Read order

1. [`SKILL.md`](SKILL.md) — portable operating law.
2. This README — directory ownership, State Machines, DAG rules, data flow and Stack indexes.
3. [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) — reusable Worker instruction body.
4. [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) — publication and no-push boundary.
5. [`references/ADOPTION.md`](references/ADOPTION.md) — consumer adoption path.
6. [`references/REPO_PROFILE.template.md`](references/REPO_PROFILE.template.md) — repository-owned values.
7. [`references/EVALS.md`](references/EVALS.md) — eval design before implementation.
8. [`references/COMPLETION_REPORT.template.md`](references/COMPLETION_REPORT.template.md) — required Worker report.
9. [`references/TECH_LEAD_FAN_OUT.md`](references/TECH_LEAD_FAN_OUT.md) and [`references/FAN_OUT_CONTRACT.schema.json`](references/FAN_OUT_CONTRACT.schema.json) — bounded TOURNAMENT/COOPERATIVE/SERIAL_STACK/HYBRID fan-out.
10. [`modules/domain-profile.md`](modules/domain-profile.md) — host/publication/CI domain bindings, loaded only when a concrete forge or carrier must be selected.
11. [`evals.json`](evals.json), `scripts/`, and `tests/`.
12. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) for proof-carrying Skill refactor contracts and the current golden Stack.
13. [`../github-delivery-loop/README.md`](../github-delivery-loop/README.md) for GitHub publication and merge State Machines.
14. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md) for closure roles and dated consumer snapshots.

## Directory map

```text
skills/git-town-stacked-pr-worker/
├── README.md
├── SKILL.md
├── SYSTEM_PROMPT.md
├── PUBLICATION_POLICY.md
├── evals.json
├── modules/
│   └── domain-profile.md  host/publication/CI domain bindings
├── references/
│   ├── ADOPTION.md
│   ├── REPO_PROFILE.template.md
│   ├── EVALS.md
│   ├── COMPLETION_REPORT.template.md
│   ├── TECH_LEAD_FAN_OUT.md
│   └── FAN_OUT_CONTRACT.schema.json
├── scripts/               portable checks/helpers
└── tests/                 positive, hollow and policy controls
```

Consumer-owned operational surface:

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

Consumer paths, branch names, remotes, credentials and receipts must not be copied into the shared Skill as universal law.

## Core ownership

```text
Git Town
  branch hierarchy + parent-first synchronization

Shared Skill
  portable Worker method + fan-out/eval/traceability contracts

Consumer repository
  branch graph + worktrees + leases + commands + CI + publication guards

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

Allowed tracked states:

```text
PLANNED
BRANCH_CREATED
PR_DRAFT
PR_OPEN
BLOCKED
READY_FOR_HUMAN_ADMIT
MERGED
CLOSED_NOT_PLANNED
EXTERNAL_OPEN
```

A branch name, issue close, merge-side effect, documentation PASS, or prior green run cannot substitute for an exact node state. Open PR heads are read from GitHub PR metadata; only an observed immutable merged commit may be recorded durably.

## Synchronization boundary

The unattended form is conceptually:

```bash
git town sync \
  --stack \
  --non-interactive \
  --no-auto-resolve \
  --no-push
```

The consumer wrapper owns:

```text
exact Git Town artifact/version admission
dirty/rebase/merge preflight
one active branch/path/resource writer
bounded timeout and log budget
receipt and BLOCKED marker
post-sync ancestry check
explicit publication guard
```

`git town sync` exit `0` proves synchronization only. It does not prove implementation, tests, review, provider health, release readiness, or Human Admit.

## DAG and branch rules

### Path-disjoint sibling

Use siblings when no branch consumes another branch's unmerged bytes:

```text
main
├── docs/architecture
├── tests/negative-controls
└── scripts/cost-gate
```

Serializing these is a false dependency.

### True child

A child exists only when it consumes a parent's unmerged contract, code, proof artifact, or documentation bytes:

```text
main
└── contract/v1
    └── implementation/v1
        └── consumer/v1
```

The edge names the consumed artifact. A parent name alone is not causality.

### Terminal leaf

Smallest reviewable behavior plus its tests and evidence. It does not absorb central index work or unrelated cleanup.

### Convergence leaf

One owner updates shared indexes, links, coverage and final traceability after prerequisite artifacts are stable. Verified side inputs may converge without becoming extra Git parents.

### Process dependency / external evidence

A later audit may wait for an admitted standard, and a live runtime may provide evidence, without becoming a Git child:

```text
PROCESS_DEPENDENCY
EXTERNAL_EVIDENCE
```

These edges are traceable and authority-bounded but do not alter branch ancestry.

### Historical subject

An admitted or forensic prior subject can remain relevant without owning current mutable state:

```text
HISTORICAL
```

A historical node records exact head/merge/rollback identity and proven ceiling. It cannot become the current queue, branch writer, or live evidence source by age or documentation reuse.

## Worker task packet

Before implementation, bind:

```text
goal and non-goals
issue(s), PR, branch and base/parent
allowed/read-only/forbidden paths
consumed and provided artifacts/contracts
evals and negative controls
exact-head source and workflow state
terminal classification and remaining evidence
timeout, cleanup and rollback
Human Admit boundary
```

Missing fields are `ABSENT`; Workers do not infer them.

## Standard molecular Stack index

The portable index — atom vocabulary, structural laws, head lifecycle and the update algorithm — is [`references/MOLECULAR_STACK_INDEX.md`](references/MOLECULAR_STACK_INDEX.md), with:

```text
references/molecular-stack-index.schema.json
references/example-molecular-stack-index.json
scripts/assert_molecular_stack_index.py
```

Atoms are `C` contract/schema/interface lock, `K` deterministic core, `A` adapter/provider/substrate, `E` Eval/mutation/fault controls, `X` explicit multi-parent convergence/E2E, and `D` documentation/receipt/handoff. `assert_molecular_stack_index.py` refuses a hidden multi-parent convergence, a path-disjoint sibling serialized as a child, a required atom missing from the index, overlapping writer leases, a self-embedded mutable open PR head, and an atom that owns no paths, oracle or Gate. Its selftest plants all ten controls.

Proof-carrying Skill refactors bind the same shape through their own registry:

```text
skills/skill-refactor-proof-loop/references/refactor-proof-stack.schema.json
skills/skill-refactor-proof-loop/references/refactor-proof-stack.json
skills/skill-refactor-proof-loop/scripts/check_refactor_proof_stack.py
```

Required node fields:

| Field | Meaning |
|---|---|
| `issues` | issue contract identities; one node owns each issue |
| `pull_request` | publication identity or `null` before publication |
| `branch` / `base_branch` | true-child base equals parent branch |
| `stack_class` | root, child, sibling, convergence, planned follow-up, external evidence |
| `owns_paths` | molecular path lease; external evidence owns no Stack paths |
| `consumes_artifacts` / `provides_artifacts` | explicit data dependency |
| `evals` / `negative_controls` | falsifiable acceptance |
| `workflow` | exact execution state and source |
| `head` | open heads read from GitHub; merged heads are immutable |
| `terminal_classification` | implemented, partial, blocked, planned, external, merged, not planned |
| `remaining_evidence` | explicit ceiling |
| `rollback` / `human_admit` | recovery and authority boundary |

The checker rejects missing child artifacts, child/base mismatch, fake serial siblings, multiple convergence owners, duplicate issue/PR ownership, stale self-embedded open heads, false merged state, external evidence owning paths, and widened semantic-conflict/force-push/ship/merge/release/promotion authority.

## Integration with `github-delivery-loop`

```text
local commits and parent-first sync
→ local consumer evals
→ exact-head local receipt
→ trusted GitHub snapshot
→ publication gate
→ draft / ready / one batched repair
→ GitHub checks
→ review
→ owner merge-admit
→ merge preflight and checked-head landing
```

Git Town never bypasses publication or merge gates. Publication and merge are separate State Machines.

## Current proof-carrying Skill refactor Stack

Canonical machine graph: [`../skill-refactor-proof-loop/references/refactor-proof-stack.json`](../skill-refactor-proof-loop/references/refactor-proof-stack.json). Full human trace: [`../../docs/traceability/SKILL_REFACTOR_PROOF_STACK.md`](../../docs/traceability/SKILL_REFACTOR_PROOF_STACK.md).

```text
Epic #318

#307/#309 → PR #308
└─ #312 → PR #315
   └─ #319 → PR #323
      └─ #320 → PR #324
         └─ #321 → PR #325
            └─ #322 planned adoption audit after Human admission
```

| Node | Issue | PR | Stack class | Branch → base | Provides |
|---|---|---|---|---|---|
| Tech Lead causal repair | `#307/#309` | `#308` | root | `fix/307-tech-lead-runtime-reachability` → `main` | task/schema/semantic/capability gates and frozen treatments |
| Hermetic golden proof | `#312` | `#315` | true child | `agent/312-tech-lead-real-task-ab` → PR #308 branch | matched worktree/process/checkpoint/tournament/global-objective L3 proof |
| Portable proof contract | `#319` | `#323` | true child | `agent/319-skill-refactor-proof-contract` → PR #315 branch | shared proof Skill, schemas, registry and mutation controls |
| Agent docs and State Machines | `#320` | `#324` | true child | `agent/320-refactor-proof-agent-docs` → PR #323 branch | root/nearest Agent contracts and directory DAG/data flow |
| Molecular convergence/index | `#321` | `#325` | convergence | `agent/321-refactor-proof-stack-index` → PR #324 branch | machine Stack graph, Git Town standard and traceability |
| Cross-Skill adoption audit | `#322` | none | planned follow-up | no branch before admission | adoption ledger and deduplicated migration backlog |

Independent evidence lanes, not Git children:

```text
#231 live scheduler lifecycle
#232 independent Shadow/global objective
#234 real Git Town + dual-forge delivery
#256 exact-subject GrepAI/SCIP/Tree-sitter/Serena/SQLite adapters
```

They may raise issue #312 from L3 to L4/L5 only with receipts matching treatment, repository, task graph, context, budget, carrier, repetitions and acceptance subjects.

## External consumer Stack snapshot — Bettor order 13

Observed `2026-08-17`. This section is an `EXTERNAL_CONSUMER_SNAPSHOT`, not the consumer's state authority. Refresh the consumer's current issue/PR metadata, exact GitHub/local/Forgejo subjects, machine Stack index and Local Handoff Queue before acting.

Merged implementation/governance subjects:

| Subject | Relation | Proven ceiling |
|---|---|---|
| Bettor PR #81 | `HISTORICAL` | merged Git Town/document governance foundation |
| Bettor PR #153 | `ROOT_AFTER_PREDECESSOR` | deterministic Blindspots ledger |
| Bettor PR #155 | `ROOT_AFTER_PREDECESSOR` | deterministic exact-subject context funnel |
| Bettor PR #156 | `ROOT_AFTER_PREDECESSOR` | planner/fixture Tech Lead, not physical Worker execution |
| Bettor PR #157 | `ROOT_AFTER_PREDECESSOR` | canonical provider/route retirement |
| Bettor PR #158 | `CONVERGENCE` | deterministic closure, no queue advancement |
| Bettor PR #159 | `ROOT_AFTER_PREDECESSOR` | physical-run readiness only |
| Bettor PR #169 | `ROOT_AFTER_PREDECESSOR` | Local Handoff queue contract, not execution |
| Bettor PR #154 | `ROOT_AFTER_PREDECESSOR` | consumer contract adoption, not live Worker execution |

Current process/evidence DAG:

```text
#172 dual-origin reconciliation                  PROCESS_DEPENDENCY / ACTIVE
→ new exact accepted subject
→ #161 runtime rebind and canary                 PROCESS_DEPENDENCY / BLOCKED
→ #146 physical Tech Lead + Shadow run           PROCESS_DEPENDENCY / BLOCKED
→ #140 Human terminal admission                  PROCESS_DEPENDENCY / BLOCKED
→ #68 final convergence/release/rollback         CONVERGENCE / BLOCKED
```

Independent path-disjoint controls:

```text
#173 / PR #176 closure monitor and one queue authority  SIBLING
#174 receipt-status laundering repair                   SIBLING
#175 origin-projection freshness repair                 SIBLING
```

These are not Git children of #172 because they do not consume #172's unmerged bytes. Live Git Town, physical Workers, live carriers/providers, Human admission, release and rollback remain separate evidence/authority lanes.

Full role, State Machine, data-flow and evidence-ceiling details: [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md).

## Historical indexes

The historical Skill Eval implementation line was:

```text
#32 → #33 → #34 → #35 → #36 → #39 → #42 → #46
```

The reusable publication policy was issue #43 / PR #44. Earlier independent documentation leaves were not forced into runtime ancestry when they consumed only merged bytes.

The four-repository documentation change was a sibling set because each repository wrote only its own documentation. `bettor-arena#38` became the convergence owner only after all four merged. Exact historical subjects remain in [`../../docs/traceability/TRACEABILITY_INDEX.md`](../../docs/traceability/TRACEABILITY_INDEX.md).

## Publication policy

```text
many local commits
→ one locally verified batch
→ initial draft publication
→ ready-for-review publication
→ one batched repair per actionable feedback subject
```

Background sync remains no-push. See [`PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md).

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

Workers must not automatically run:

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

A static prompt or Stack graph cannot prove an installed Git Town binary, real rebase, remote push, provider execution, model uplift, merge, or Human Admit.

## Adoption checklist

- pin and admit the exact Git Town artifact;
- define repository profile and `.git-town.toml`;
- enforce one Worker/branch/worktree and branch/path/resource leases;
- declare consumed/provided artifacts and one convergence owner;
- add the machine-readable molecular Stack index;
- add bounded no-push sync wrappers and receipts;
- run local verification before publication;
- integrate GitHub publication and merge gates;
- plant conflict, dirty, ancestry, timeout, false-child, stale-head and publication controls;
- keep semantic conflict, force push, ship, merge, release and promotion Human-owned.
