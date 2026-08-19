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
| `A-CODEX` | `#375 / #451` | `SIBLING / UNMERGED CANDIDATE` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact session/result contract, clean-worktree subject preflight, SDK runner, post-turn writable-lease readback | `4 / 14`; selected bytes pass shared ATL suite in convergence | live SDK `NOT_EXERCISED`; independent acceptance still required |
| `A-GH-DAG` | `#376 / #452` | `SIBLING / UNMERGED CANDIDATE` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection, repo/default-branch/visibility + issue-state + closing-PR-reference preflight, non-destructive readback | `6 / 17`; selected bytes pass shared ATL suite in convergence | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| `A-HERDR` | `#377 / #456` | `SIBLING / UNMERGED CANDIDATE` | `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123` | exact Git/worktree/pane/workspace/PID/session + PID-start/freshness/liveness + cleanup/residue observer | `4 / 18`; repaired source passes shared ATL suite in convergence | live Herdr `NOT_EXERCISED`; `DONE_CANDIDATE` advisory only |
| `K-CLOSURE` | `#378 / #457` | `SIBLING / UNMERGED CANDIDATE` | `ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34` | frozen denominator/source manifest + exact repo/evidence/receipt subjects + supersession validation | `6 / 22`; selected bytes pass shared ATL suite in convergence | real source/provider closure `EVIDENCE_DEPENDENT` |
| `D-TRACE` | `#379 refs / #380` | `DOCUMENTATION SIBLING` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original control-plane design/trace routing | navigation only | consumed by convergence; no runtime claim |
| `X-CONVERGENCE` | `#379 / #455` | `CONVERGENCE CANDIDATE` | read current head from GitHub | exact selected sibling bytes + shared `run-all`, Agent routes, Shadow relation, Git Town/trace indexes | final current head must rerun full hosted denominator | static/deterministic scope only; sibling admission/Human merge/release separate |

Current repaired #377 integration checkpoint:

```text
fc40cf833609328ded0141dd8d9629c9a727a159
parents:
  d52ab2aad8e20be0c738e77356f75633813ad444  prior #455 route/index head
  6a2ebcbe87078cecaf67f82f3c9c10643bcc9123  repaired #456 selected candidate
```

Rejected predecessor checkpoint retained for audit:

```text
ed852502437570c7c86bae12c07c16a3f5d37ea8
parents:
  c306b3b4cea797f5f4d1323f8ec7fcd94a94f3ec  prior #455 convergence head
  23b03826b1bf8fe66bd731716466a9349d3242d6  corrupted #456 candidate
  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34  #457 selected candidate
```

The shared ATL suite rejected `ed852502...` because the Herdr script contained a non-printable `U+000F` source corruption and could not import. The #377 owner repaired the source without changing the 4/18 selftest denominator; the repaired integration then passed the shared ATL suite.

Earlier #451/#452 hardening entered through:

```text
5d21ecab137cb26586ef1636dc279ee29733e913
parents:
  35874af7a6d04783983b05c8f1b1e402471b4451  prior #455 epoch
  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1  #451 selected candidate
  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8  #452 selected candidate
```

The final mutable #455 head is never self-embedded in this README. Read it from GitHub after every convergence edit.

### Historical convergence and rejected candidates

```text
c0f6979f80038394350aea724c598c8dba5ac338  epoch-1 union
af427a13a7096df91d74a48c0a4ca6ce3f3e2ac9  epoch-1 + PR #380 documentation
35874af7a6d04783983b05c8f1b1e402471b4451  historical hosted-green convergence
ed852502437570c7c86bae12c07c16a3f5d37ea8  rejected corrupted-Herdr integration

#444 → #451
#445 → #452
#446 → #453 → #456
#447 → #454 → #457
```

#446/#447 are rejected provenance candidates. #453/#454 are provenance-correct replacements later closed unmerged. The first v3 #456 head is retained as a rejected source-corruption subject and is superseded by `6a2ebcbe...`. All remain `HISTORICAL`, not alternate merge candidates. An older hosted-green convergence became historical when selected sibling heads moved; green evidence never follows a moving parent automatically.

### Current control-plane data flow

```text
A-CODEX ─┐
A-GH-DAG ├─ exact selected candidate bytes ─┐
A-HERDR ─┤                                  │
K-CLOSURE┘                                  ├→ X-CONVERGENCE (#379/#455)
D-TRACE ─── documentation sibling ──────────┘       │
                                                     ├→ unconditional shared ATL suite
                                                     ├→ independent Shadow readback
                                                     ├→ repository-wide hosted workflows
                                                     └→ READY_FOR_HUMAN_ADMIT | HOLD | REJECT

live Codex / live GitHub mutation / live Herdr / real source-provider closure
  = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
  ≠ Git children of X-CONVERGENCE
```

## Required shared convergence gates

The convergence subject contains selected sibling bytes first; then `agentic-tech-lead-orchestration/tests/run-all.sh` unconditionally executes:

```text
6 Draft-2020-12 control-plane schemas
problem-closure example
Codex selftest        4 / 14
GitHub DAG selftest   6 / 17
Herdr selftest        4 / 18
closure selftest      6 / 22
closure checker + Markdown non-authority marker
existing ATL suite
```

No required test may be hidden behind `if file exists`.

At repaired integration ancestor `fc40cf83...`, synchronize-triggered hosted gates are:

```text
Skill Suites                         PASS
Shared Skills Infra                  PASS
Git Town Stacked PR Worker           PASS
```

The ATL suite log explicitly records all four control-plane denominators PASS. The final documentation/index head must rerun the synchronize-triggered workflows. `Skill Eval Contract` is `ready_for_review`-triggered and must be explicitly retriggered after the final head stabilizes; absence is never PASS.

An earlier green head is historical after any selected sibling head moves. A final-head hosted PASS does not admit or merge an unmerged sibling and does not raise live evidence.

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
                         └─ Epic #398 current-main landing  PENDING_PUBLICATION
```

| Atom | Issue | PR | Evidence ceiling | Role |
|---|---|---|---|---|
| `C` | `#399` | `#405` | `IMPLEMENTED` | controller + Complexity Delta contract |
| `K/E` | `#400` | `#441` | `LOCAL_DETERMINISTIC_VERIFIED` | composition gate + false-simplification controls |
| `A` | `#401` | `#442` | `STATIC_CONTRACT_VERIFIED` | Skill/repository target adapters |
| `X/LIVE` | `#402` | `#458` | `BOUNDED_CROSS_DOMAIN_REMOTE_VERIFIED` | Skill + ordinary-repository canaries |
| validation | `#402` | `#461` | `REMOTE_REPOSITORY_CI_VERIFIED` | repaired whole-subject hosted receipt |
| `X/D` | `#406` | `#463` | `REMOTE_INTEGRATION_VERIFIED` | registry, CI arrival, Agent routes, corpus and program trace |
| main landing | `#398` | pending publication | `HUMAN_ADMITTED / REVERIFY_ON_CURRENT_MAIN` | preserve concurrent main governance and land one compliant subject |

PR #462 remains `SUPERSEDED_FORENSIC`; it exposed document-route inventory drift and the connector commit-role endpoint gap. PR #463 repaired that history with CI-authored `agent-macro@ci.invalid` commits and is the immutable semantic source for this landing. The landing itself is rebuilt on current `main`; it does not import stale UCR Git ancestry or overwrite the concurrently admitted #375–#379 Tech Lead/Shadow control-plane bytes.

Golden Refactor cases remain bounded. Open ordinary-repository evidence is not promoted by this admission. Live provider/model uplift, production safety, release, promotion and rollback remain separate evidence/Human lanes.

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