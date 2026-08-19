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
12. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md), [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md), and [`../../docs/traceability/WAVE3_REPLACEMENT_CONVERGENCE.md`](../../docs/traceability/WAVE3_REPLACEMENT_CONVERGENCE.md) for current closure/admission/replacement subjects.
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

One owner consumes several selected prerequisite artifacts and updates shared indexes/integration/e2e surfaces. A convergence commit may have multiple sibling parents. That records byte consumption without making the siblings children of each other and without admitting unmerged candidates by ancestry alone.

### `PROCESS_DEPENDENCY`

Ordering without Git ancestry, for example waiting for an audit/receipt before Human Admit.

### `EXTERNAL_EVIDENCE`

Independent runtime/Shadow/provider receipt lane. It owns no implementation paths unless it is itself implementing code.

### `HISTORICAL`

Immutable admitted/rejected/closed-unmerged/forensic subject retained for lineage, not current mutable authority.

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
candidate/admitted/merged distinction
terminal classification
remaining evidence ceiling
rollback
Human-owned operations
successor/convergence owner
```

The machine index and `assert_molecular_stack_index.py` reject hidden multi-parent convergence, fake serial siblings, overlapping writer leases, self-embedded mutable open heads, review-only atoms used as parents, external evidence owning Stack paths, false merged state and widened merge/release authority.

## Current Codex control-plane Molecular index — #375–#380

Current common base observed for this sibling epoch:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Relation | Current selected head | Provides | Deterministic denominator | Remaining ceiling |
|---|---|---|---|---|---|---|
| `A-CODEX` | `#375 / #451` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact session/result contract, clean-worktree subject preflight, SDK runner, post-turn writable-lease readback | `4 / 14`; bytes admitted through #455 | live SDK `NOT_EXERCISED`; independent acceptance still required |
| `A-GH-DAG` | `#376 / #452` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection, repo/default-branch/visibility + issue-state + closing-PR-reference preflight, non-destructive readback | `6 / 17`; bytes admitted through #455 | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| `A-HERDR` | `#377 / #456` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123` | exact Git/worktree/pane/workspace/PID/session + PID-start/freshness/liveness + cleanup/residue observer | `4 / 18`; bytes admitted through #455 | live Herdr `NOT_EXERCISED`; `DONE_CANDIDATE` advisory only |
| `K-CLOSURE` | `#378 / #457` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34` | frozen denominator/source manifest + exact repo/evidence/receipt subjects + supersession validation | `6 / 22`; bytes admitted through #455 | real source/provider closure `EVIDENCE_DEPENDENT` |
| `D-TRACE` | `#379 refs / #380` | `DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original control-plane design/trace routing | navigation only | consumed by convergence; no runtime claim |
| `X-CONVERGENCE` | `#379 / #455` | `CONVERGENCE / HUMAN_ADMITTED / MERGED` | candidate `847e56c3418fce920c42d983e84ee44fdc6e8971`; merge `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c` | exact selected sibling bytes + shared `run-all`, Agent routes, Shadow relation, Git Town/trace indexes | exact-head hosted denominator PASS before Human Admit | live evidence remains separate |

Post-merge #379 admission detail lives in `docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`; current `main` must still be read live.

### Historical convergence and rejected candidates

```text
c0f6979f80038394350aea724c598c8dba5ac338  epoch-1 union
af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9  epoch-1 + PR #380 documentation
35874af7a6d04783983b05c8f1b1e402471b4451  historical hosted-green convergence
ed852502437570c7c86bae12c07c16a3f5d37ea8  rejected corrupted-Herdr integration
fc40cf833609328ded0141dd8d9629c9a727a159  repaired Herdr integration

#444 → #451
#445 → #452
#446 → #453 → #456
#447 → #454 → #457
```

Failed or closed-unmerged subjects remain `HISTORICAL`, not alternate merge candidates. Green evidence never follows a moving parent automatically.

## Human-owned operations / rollback

```text
semantic conflict resolution       HUMAN
force update / force push          HUMAN / repository policy
unmanaged GitHub blocker deletion  HUMAN or separately admitted policy
sibling admission                  HUMAN / repository policy
merge                              HUMAN / repository merge authority
release / promotion                HUMAN / repository release authority
rollback                           reviewed revert to an exact admitted pre-convergence subject
```

No workflow green state, Shadow agreement, issue close, PR publication or convergence ancestry substitutes for these operations.

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

## Universal refactor controller admission — Epic #398

This is a durable traceability projection, not mutable PR-state authority. Read current GitHub metadata before acting on an open subject.

```text
#399 / PR #405  UCR-C contract
├─ #400 / PR #441  UCR-K/E deterministic gate
└─ #401 / PR #442  UCR-A adapters
       \           /
        #402 / PR #458  UCR-LIVE
           ├─ validation PR #461
           └─ #406 / PR #463  UCR-X/D convergence
                         │
                         └─ #398 / PR #477  current-main landing
```

| Atom | Issue | PR | Evidence ceiling | Role |
|---|---|---|---|---|
| `C` | `#399` | `#405` | `IMPLEMENTED` | controller + Complexity Delta contract |
| `K/E` | `#400` | `#441` | `LOCAL_DETERMINISTIC_VERIFIED` | composition gate + false-simplification controls |
| `A` | `#401` | `#442` | `STATIC_CONTRACT_VERIFIED` | Skill/repository target adapters |
| `X/LIVE` | `#402` | `#458` | `BOUNDED_CROSS_DOMAIN_REMOTE_VERIFIED` | Skill + ordinary-repository canaries |
| validation | `#402` | `#461` | `REMOTE_REPOSITORY_CI_VERIFIED` | repaired whole-subject hosted receipt |
| `X/D` | `#406` | `#463` | `REMOTE_INTEGRATION_VERIFIED` | registry, CI arrival, Agent routes, corpus and program trace |
| main landing | `#398` | `#477` | `HUMAN_ADMITTED / MERGED` | checked-head current-main landing; live provider/model uplift remains separate |

PR #462 remains `SUPERSEDED_FORENSIC`; PR #463 is the immutable semantic source for the UCR convergence, and transport PRs #476/#478 preserve commit-role-clean publication. UCR admission does not replace the Codex control-plane or Wave-3 evidence program.

Golden Refactor cases remain bounded. Open ordinary-repository evidence is not promoted by this admission. Live provider/model uplift, production safety, release, promotion and rollback remain separate evidence/Human lanes.

## Wave-3 live-evidence Molecular replacement index — #464–#479

Wave 3 was forked while #455 was unmerged. Each leaf therefore has real historical `TRUE_CHILD` provenance to #455 exact head `847e56c3418fce920c42d983e84ee44fdc6e8971`; the four leaves consume no bytes from one another and remain siblings. #455 was subsequently Human-admitted, which changes current parent authority without rewriting the fork-time dependency.

```text
#455 fork-time TRUE_PARENT; now HUMAN_ADMITTED / MERGED
├── #464 / PR #469  Codex live-acceptance carrier        TRUE_CHILD / SIBLING
├── #465 / PR #470  GitHub dependency reversible canary TRUE_CHILD / SIBLING
├── #466 / PR #471  Herdr lifecycle carrier             TRUE_CHILD / SIBLING
└── #467 / PR #472  source-claim compiler               TRUE_CHILD / SIBLING
       \             |             |             /
        \____________|_____________|____________/
                     ↓ exact selected bytes
              #468 / PR #473        HISTORICAL / REJECTED_COMMIT_ROLE
              #468 / PR #479        CURRENT CONVERGENCE CANDIDATE
                     ↓
          deterministic exact-head gates
                     ↓
          Local Handoff Queue / runtime
                     ↓
            EXTERNAL_EVIDENCE lanes
```

Selected immutable leaf subjects:

```text
#469 d239d17d1d718f3e5e8c1975307665cae43d3b09
#470 f4c3215b6c52c2e6106070eaa1121dee1dbd48e3
#471 9eb70b2b62193b62a28f243de91e51337f1906b3
#472 44d779a02e1749aa88a502d946646c22af38a026
```

| Atom | Issue / PR | Relation | Owns/provides | Deterministic denominator | Runtime ceiling | Successor |
|---|---|---|---|---|---|---|
| `L-CODEX` | `#464 / #469` | `TRUE_CHILD@fork + SIBLING` | Codex live-result/controller-readback binder | `1 / 12` | signed-in live execution `NOT_EXERCISED` | `#479` |
| `L-GH-CANARY` | `#465 / #470` | `TRUE_CHILD@fork + SIBLING` | reversible one-edge GitHub dependency canary | `1 / 6` | remote canary `NOT_EXERCISED` | `#479` |
| `L-HERDR` | `#466 / #471` | `TRUE_CHILD@fork + SIBLING` | bounded Herdr lifecycle over admitted observer | `2 / 7` | live Herdr `NOT_EXERCISED` | `#479` |
| `L-SOURCE` | `#467 / #472` | `TRUE_CHILD@fork + SIBLING` | Issue/Article/PDF/PRD compiler into problem-closure model | `4 source kinds / 11 mutations` | source truth/provider verification `EVIDENCE_DEPENDENT` | `#479` |
| `X-LIVE-OLD` | `#468 / #473` | `HISTORICAL / REJECTED` | first Wave-3 convergence; functionally green after queue repair | functional/static denominator passed; commit-role rejected accidental `3fe0a79...` | no live claim | superseded by `#479` |
| `X-LIVE` | `#468 / #479` | `CONVERGENCE` | selected leaf bytes + 10 schemas + shared run-all + routes + Shadow + traceability + queue + Molecular index | final exact head must pass all owning workflows | no live lane promoted by static CI; merge/release Human-owned | runtime handoff / Human review |

Path/resource lease law:

```text
#469 owns only Codex live carrier + dedicated test
#470 owns only GitHub live-canary carrier + dedicated test
#471 owns only Herdr lifecycle carrier + dedicated test
#472 owns only source-claim compiler + dedicated test
#479 alone owns Wave-3 shared contracts/run-all/README/AGENTS/Shadow/Git-Town/traceability/queue
```

Wave-3 shared deterministic denominator:

```text
Wave 2 admitted controls remain mandatory
+ 4 Wave-3 Draft-2020-12 contracts
+ Codex live acceptance       1 / 12
+ GitHub reversible canary    1 / 6
+ Herdr lifecycle             2 / 7
+ source-claim compiler       4 source kinds / 11 mutations
+ source compiler → existing problem-closure checker integration
+ asserted Wave-3 Local Handoff Queue
```

Current replacement authority is `docs/traceability/WAVE3_REPLACEMENT_CONVERGENCE.md`; mutable #479 head and current main must be read live. A green #479 hosted suite may establish only static/deterministic live-evidence infrastructure. It cannot turn any `NOT_EXERCISED` or `EVIDENCE_DEPENDENT` lane into PASS.

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

A static prompt, schema, Stack graph, deterministic test or hosted workflow cannot by itself prove live Codex/Herdr/GitHub effects, real source/provider closure, model uplift, sibling admission, merge, release or production readiness.

## Adoption checklist

- pin/admit exact Git Town artifact;
- define repository profile and `.git-town.toml`;
- enforce one Worker/branch/worktree and branch/path/resource leases;
- declare consumed/provided artifacts and one convergence owner;
- distinguish selected candidate ancestry from admitted/merged ancestry;
- add machine-readable Molecular Stack index;
- add bounded no-push sync wrappers and receipts;
- run local verification before publication;
- integrate GitHub publication and merge gates;
- plant conflict, dirty, ancestry, timeout, false-child, stale-head and publication controls;
- keep semantic conflict, force push, ship, merge, release and promotion Human-owned.
