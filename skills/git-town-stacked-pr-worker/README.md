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
12. [`../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](../../docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md), [`../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md), and [`../../docs/traceability/WAVE3_LIVE_EVIDENCE.md`](../../docs/traceability/WAVE3_LIVE_EVIDENCE.md) for current closure/control-plane subjects.
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

Current authority correction: #455 was Human-admitted and merged as `ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c`; its reviewed candidate and merge share tree `8a75271851f2e9dd47dd3a019c93e4a0f9272d24`. The table and checkpoints below preserve the implementation-candidate lineage that produced that admitted tree. Current mutable repository state must be read from GitHub and [`CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](../../docs/traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md), not inferred from historical wording below.

Historical common base for this sibling epoch:

```text
main@4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

| Atom | Issue / PR | Relation | Selected head | Provides | Deterministic denominator | Remaining ceiling |
|---|---|---|---|---|---|---|
| `A-CODEX` | `#375 / #451` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `86f9e8d940b76cb71b713c098ff09cb68eb4e0c1` | exact session/result contract, clean-worktree subject preflight, SDK runner, post-turn writable-lease readback | `4 / 14`; selected bytes passed shared ATL convergence | live SDK `NOT_EXERCISED`; independent acceptance still required |
| `A-GH-DAG` | `#376 / #452` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `426fb6f6f548f71572d4402e73e0b05ecf6f8aa8` | completion-edge projection, repo/default-branch/visibility + issue-state + closing-PR-reference preflight, non-destructive readback | `6 / 17`; selected bytes passed shared ATL convergence | live mutation/readback `NOT_EXERCISED`; generic development-link ownership beyond closing refs residual |
| `A-HERDR` | `#377 / #456` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123` | exact Git/worktree/pane/workspace/PID/session + PID-start/freshness/liveness + cleanup/residue observer | `4 / 18`; repaired source passed shared ATL convergence | live Herdr `NOT_EXERCISED`; `DONE_CANDIDATE` advisory only |
| `K-CLOSURE` | `#378 / #457` | `SIBLING / CLOSED-UNMERGED / CONSUMED` | `ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34` | frozen denominator/source manifest + exact repo/evidence/receipt subjects + supersession validation | `6 / 22`; selected bytes passed shared ATL convergence | real source/provider closure `EVIDENCE_DEPENDENT` |
| `D-TRACE` | `#379 refs / #380` | `DOCUMENTATION SIBLING / CLOSED-UNMERGED / CONSUMED` | `7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5` | original control-plane design/trace routing | navigation only | consumed by #455; no runtime claim |
| `X-CONVERGENCE` | `#379 / #455` | `CONVERGENCE / HUMAN_ADMITTED / MERGED` | reviewed head `847e56c3418fce920c42d983e84ee44fdc6e8971` | exact selected sibling bytes + shared `run-all`, Agent routes, Shadow relation, Git Town/trace indexes | four exact-head hosted lanes passed before Admit | live lanes remain separate; release not implied |

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

#446/#447 are rejected provenance candidates. #453/#454 are provenance-correct replacements later closed unmerged. The first v3 #456 head is retained as a rejected source-corruption subject and is superseded by `6a2ebcbe...`. All remain `HISTORICAL`, not alternate merge candidates. Green evidence never follows a moving parent automatically.

### Control-plane data flow

```text
A-CODEX ─┐
A-GH-DAG ├─ exact selected candidate bytes ─┐
A-HERDR ─┤                                  │
K-CLOSURE┘                                  ├→ X-CONVERGENCE (#379/#455)
D-TRACE ─── documentation sibling ──────────┘       │
                                                     ├→ unconditional shared ATL suite
                                                     ├→ independent Shadow readback
                                                     ├→ repository-wide hosted workflows
                                                     └→ HUMAN_ADMIT → MERGED

live Codex / live GitHub mutation / live Herdr / real source-provider closure
  = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
  ≠ Git children of X-CONVERGENCE
```

## Required shared convergence gates

The admitted #455 subject contained selected sibling bytes before `agentic-tech-lead-orchestration/tests/run-all.sh` executed:

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

## Wave-3 live-evidence Molecular index — #464–#468

Fork-time parent and selected leaf epoch:

```text
#455 fork head 847e56c3418fce920c42d983e84ee44fdc6e8971
├─ #464 / PR #469  d239d17d1d718f3e5e8c1975307665cae43d3b09  TRUE_CHILD / SIBLING
├─ #465 / PR #470  f4c3215b6c52c2e6106070eaa1121dee1dbd48e3  TRUE_CHILD / SIBLING
├─ #466 / PR #471  9eb70b2b62193b62a28f243de91e51337f1906b3  TRUE_CHILD / SIBLING
└─ #467 / PR #472  44d779a02e1749aa88a502d946646c22af38a026  TRUE_CHILD / SIBLING
         ↓ exact selected bytes
#468 current publication candidate  CONVERGENCE + CURRENT_MAIN_FRESHNESS
```

| Atom | Issue / PR | Deterministic denominator | Live/evidence ceiling |
|---|---|---:|---|
| `A-CODEX-LIVE` | `#464 / #469` | `1 positive / 12 mutations` | live Codex/controller acceptance `NOT_EXERCISED` |
| `A-GH-CANARY` | `#465 / #470` | `1 / 6` | live add/readback/remove `NOT_EXERCISED` |
| `A-HERDR-LIFECYCLE` | `#466 / #471` | `2 / 7` | live Herdr lifecycle `NOT_EXERCISED` |
| `K-SOURCE-COMPILER` | `#467 / #472` | `4 source kinds / 11 mutations` | source/provider truth `EVIDENCE_DEPENDENT` |
| `X-WAVE3` | `#468 / current PR` | 10 control-plane schemas + all Wave‑2/Wave‑3 selftests + queue assertion | static/deterministic infrastructure only until Human Admit |

Immutable fork-time byte integration:

```text
691b342c44c9c6c4e61a9997e778ae4ed6e920d5
└─ tree ba6ef27631546af466284f44af7c81cd347765dd
```

Publication history is intentionally not erased:

```text
#473  historical convergence; document routing passed but ancestry commit-role provenance failed
#480  provenance-complete replay; exact-head evidence became stale when current main moved through admitted #477
current #468 publication subject
      must preserve #477 UCR/workflow/registry bytes,
      consume selected Wave‑3 bytes,
      rerun exact-head Skill Suites + Shared Skills Infra + Skill Eval Contract + Git Town,
      then pass independent Shadow freshness readback before Human Admit
```

Wave‑3 Local Handoff remains a continuation contract for actual live Codex, Herdr and reversible GitHub canary execution. Static queue validation, hosted CI or merge cannot promote those live lanes.

Full current authority transition and State Machine:

- [`../../docs/traceability/WAVE3_PARENT_ADMISSION.md`](../../docs/traceability/WAVE3_PARENT_ADMISSION.md)
- [`../../docs/traceability/WAVE3_LIVE_EVIDENCE.md`](../../docs/traceability/WAVE3_LIVE_EVIDENCE.md)

## Current Spatial Loop ICPG molecular Stack — #407

This index tracks the terminal implementation slices for `spatial-loop-systems-engineering` Intent–Case–Proof Graph work. It is a traceability projection, not a substitute for the canonical machine molecular Stack schema or exact PR metadata.

```text
#407  global objective / program issue
│
├─ ICPG-C1/K1/E1  #408  contract + checker + migration semantic-loss controls
│      branch: agent/spatial-intent-case-proof-graph-v1
│      relation: root terminal implementation leaf
│
├─ ICPG-M1        #409  Shadow intent/case/semantic-parity monitor
│      relation: true child when consuming #408 unmerged contract vocabulary
│
├─ ICPG-D1        #410  Tech Lead task-DAG + Stack/index convergence
│      relation: sibling or convergence according to path ownership;
│                do not serialize merely because issue number is later
│
└─ ICPG-X1        #411  live continuous Shadow runtime canary
       relation: EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY unless harness bytes
                 actually consume an unmerged parent implementation
```

Data flow:

```text
Prompt / source behavior
→ ICPG exact subject + digest
→ required-case ownership
→ Tech Lead task contracts
→ true dependency DAG
→ path/resource leases
→ molecular terminal Workers
→ independent case/oracle receipts
→ one convergence owner
→ global intent/case reconciliation
→ publication review
```

| Atom | Issue | Type | Owns | Stack class | Current state |
|---|---:|---|---|---|---|
| `ICPG-C1` | #408 | `C` | case graph reference/schema | root | implemented on candidate branch |
| `ICPG-K1` | #408 | `K` | deterministic semantic checker | same terminal leaf | implemented on candidate branch |
| `ICPG-E1` | #408 | `E` | positive + semantic-loss/mutation controls | same terminal leaf | implemented; CI/execution receipt pending |
| `ICPG-M1` | #409 | `K/E` | Shadow case-delta contract | child of #408 semantics | implemented contract; live runtime pending |
| `ICPG-D1` | #410 | `D/K` | README/AGENTS/Tech Lead/Stack traceability | convergence by shared-file ownership | partial until full Tech Lead machine binding lands |
| `ICPG-X1` | #411 | `X` | exact-subject independent live Shadow canary | external evidence | `NOT_EXERCISED` |

Hard laws for this Stack:

- every required case has one terminal implementation owner or one explicit convergence owner;
- case dependency does not create a Git child by itself;
- a Git child must name the unmerged parent artifact it consumes;
- path-disjoint case work remains sibling work;
- shared case/index files have one convergence owner;
- terminal Worker PASS cannot close global intent/case coverage;
- live #411 evidence cannot be manufactured from static #408/#409 fixtures;
- merge, release, promotion and semantic conflict remain outside Worker authority.

## Current Intent-to-Evidence Knowledge Graph molecular Stack — #413

This program consumes the unmerged Spatial Loop ICPG contract on draft PR #412. The first implementation branch therefore is a true child of PR #412 by bytes/contracts, not merely because #413 was opened later.

```text
PR #412  Spatial ICPG + Shadow/static projection + Tech Lead case ownership
└─ KG-C1/D1  #414/#413  branch agent/413-knowledge-graph-icpg-bridge
      consumes: spatial-loop-case-graph/v1 contract and Tech Lead case obligations
      provides: Knowledge Graph AGENTS/README/SKILL + trace/prompt contracts
      relation: TRUE_CHILD of PR #412

Planned terminal atoms after contract freeze:
├─ KG-C2/E1  #414  Intent/Artifact projection schemas + deterministic mutations
├─ KG-K1/E2  #415  ICPG case→task/issue→Stack/AGENTS bridge + reverse-trace controls
├─ KG-K2/E3  #416  authority/freshness/traversal checker + GraphRAG query contracts
└─ KG-D2/X1  #417  one system-prompt/docs/Molecular convergence owner

#418 live multi-hop GraphRAG/Shadow canary
  relation: EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
  owns no Stack paths unless a later repair issue explicitly leases them
```

Data flow:

```text
semantic knowledge card
→ Intent projection
→ exact ICPG digest + case IDs
→ Tech Lead case_obligations
→ task/issue owner
→ Molecular Stack atom / PR
→ file + AGENTS/README/SKILL route
→ oracle/test/workflow/receipt
→ authority + freshness + evidence ceiling
→ bidirectional GraphRAG traversal
→ Shadow review
→ Human Admit
```

| Atom | Issue | Type | Owns | Stack class | Current state |
|---|---:|---|---|---|---|
| `KG-C1` | #413/#414 | `C` | semantic projection/ICPG bridge contract | true child of PR #412 | implemented on candidate branch |
| `KG-D1` | #413/#417 | `D` | nearest AGENTS/README/SKILL + current topology | same preparation leaf | implemented on candidate branch |
| `KG-C2` | #414 | `C/E` | machine Intent/Artifact schemas + authority/freshness controls | planned terminal leaf | `NOT_IMPLEMENTED` |
| `KG-K1` | #415 | `K/E` | case→task/issue/Stack/document bindings + reverse trace | planned terminal leaf | `NOT_IMPLEMENTED` |
| `KG-K2` | #416 | `K/E` | authority-aware traversal + evidence-ceiling checker | planned terminal leaf | `NOT_IMPLEMENTED` |
| `KG-D2` | #417 | `D/X` | v7.2 prompt/root routing/final indexes | one convergence owner | `PLANNED` |
| `KG-X1` | #418 | `X` | exact-subject live GraphRAG/Shadow retrieval canary | external evidence | `NOT_EXERCISED` |

Hard laws for this Stack:

- ICPG remains the only canonical case denominator; Knowledge Graph nodes reference digest/case IDs only;
- knowledge/semantic dependencies do not create Git parents;
- #414–#416 become siblings unless one consumes another's unmerged machine contract;
- only #417 owns shared convergence/index updates after terminal artifact identities stabilize;
- mutable GitHub/branch/workflow projections must refresh before decision-grade use;
- cards/README/AGENTS cannot override exact Git/verifier/receipt authority;
- forward trace without reverse implementation→case→Intent trace is incomplete;
- #418 live evidence cannot be manufactured from static/deterministic fixtures;
- merge, release and promotion remain Human/repository authority.

## Integration with `github-delivery-loop`
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
| main landing | `#398` | `#477` | `HUMAN_ADMITTED / MERGED` | preserve concurrent main governance and land one checked-head subject |

PR #462 remains `SUPERSEDED_FORENSIC`; it exposed document-route inventory drift and the connector commit-role endpoint gap. PR #463 repaired that history with CI-authored `agent-macro@ci.invalid` commits and is the immutable semantic source for this landing. PR #476 is `TRANSPORT_ONLY`: it squashed disposable connector-authored construction history into GitHub forge commit `d809f44004bb24b204f78af560366a413db76803`; its tree equals the admitted semantic work tree and it is not a separate capability claim. PR #477 landed on current `main`; it does not import stale UCR Git ancestry or overwrite the admitted #375–#379 Tech Lead/Shadow control-plane bytes.

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