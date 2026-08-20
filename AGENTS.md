# AGENTS.md — skills-shared operating contract

`skills-shared` is the canonical **Instruction / Method Plane** for cross-repository Skills and truth-gated Skill Eval/Evolution. It must not absorb consumer paths, branches, credentials, provider sessions, mutable consumer state or live receipt authority.

## Mandatory bootstrap route

Before mutation, read in order:

1. [`README.md`](README.md) — repository role and integrated overview.
2. [`CONTEXT.md`](CONTEXT.md) — mutable handoff and cross-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership and authority boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — document routes.
5. [`docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md) when issue/PR closure, current integrated state, source/PDF closure or Local Handoff is in scope.
6. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md).
7. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).
8. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md).
9. [`registry.json`](registry.json) and [`skills/README.md`](skills/README.md).
10. The target Skill's nearest `AGENTS.md`, then `README.md`, `SKILL.md`, `references/`, selected `modules/`, `scripts/`, `tests/`, `evals.json`/`cases.json` as applicable.
11. The exact current issue, PR base/head, workflow, runtime and evidence subjects.

For GitHub delivery read [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md). For Git Town/Molecular work read [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md). For a material Skill refactor read [`skills/skill-refactor-proof-loop/AGENTS.md`](skills/skill-refactor-proof-loop/AGENTS.md).

A missing route, issue, implementation target, parent, eval, workflow run or evidence subject is `ABSENT`. Do not reconstruct it from chat history, branch names, another repository, source prose or a prior successful SHA.

## Repository role and authority

```text
skills-shared        portable method / contracts / deterministic evidence law
runtime-env          secret-free runtime contract plane
consumer repository domain composition / mutable runtime / product acceptance
external evidence    source/provider/manual/Human lanes
```

| Authority | Owns |
|---|---|
| `registry.json` | shared versus repo-owned classification |
| `SKILL.md` | portable method and hard law |
| `references/` | reusable generic contracts/templates |
| `modules/` | trigger-selected instances/adapters |
| directory `AGENTS.md` / `README.md` | local route, State Machine, DAG, data flow, handoff |
| verifier/script/test | deterministic transition/evidence for its declared subject |
| issue / PR | bounded change, path lease, relation, evidence ceiling |
| workflow run | execution arrival on one exact subject; never semantic truth alone |
| runtime/provider receipt | only its executed evidence lane |
| Human / trusted operator | semantic conflict, permission/provider admission, merge, release, promotion, rollback |

Markdown is navigation/human projection and must not become a second API, registry, schema, verifier, receipt or merge authority.

## Skill anatomy

```text
AGENTS.md   local read order, writer/authority law, stop/completion packet
README.md   directory ownership, State Machine, DAG, data flow, evidence ceiling
SKILL.md    portable workflow, laws and stop conditions
references/ host-neutral contracts/schemas/templates
modules/    trigger-selected adapters/instances
scripts/    executable mechanisms
 tests/     positive, hollow, mutation and integration controls
```

Consumer branch names, machine paths, credentials, product topology, provider sessions and live consumer state do not belong in portable `SKILL.md`.

## Current public-state law

Current human projection: [`docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md).

The current audit baseline records:

```text
main 249abc47847f8295b1c75c9d4c84457c5126fd89
```

This is an immutable observation, not a floating alias. Re-read current GitHub `main` before every publication/merge decision.

Current unresolved stronger lanes include:

```text
#376 generic Development sidebar link/unlink     RESIDUAL / MANUAL_OR_UNEXPOSED_API
#464 signed-in Codex v2 acceptance               NOT_EXERCISED
#466 real Herdr lifecycle                        NOT_EXERCISED
#467 article/PDF/PRD + provider truth            EVIDENCE_DEPENDENT
release / production                             NOT_PERFORMED
```

The #465 remote canary is a bounded `REMOTE_CANARY_EDGE_ONLY` PASS and cannot proxy any of those lanes.

## Proof-carrying Skill refactors

Material refactors must follow [`skill-refactor-proof-loop`](skills/skill-refactor-proof-loop/README.md).

Before mutation bind:

```text
A   OLD_CANONICAL immutable bytes
B0  REFACTOR_AS_LANDED immutable bytes
B1+ repaired candidate
protected old strengths
same base/tree/contracts/tests/budget/carrier for matched L3+
complete denominator and cleanup policy
true sibling/child/convergence DAG
rollback subject and Human boundary
```

Proof layers are separate:

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A shorter Skill, a link, fixture, local PASS or model claim cannot promote a stronger layer. Failed, stale, blocked, cancelled and superseded attempts stay in the denominator.

## Tech Lead / Shadow closure law

```text
SOURCE_PROPOSAL
→ METHOD_IMPLEMENTED
→ CONSUMER_MECHANISM_IMPLEMENTED
→ DETERMINISTIC_EVIDENCE_VERIFIED
→ LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED
→ HUMAN_ADMITTED
→ RELEASED
```

Tech Lead owns task/capability DAGs, leases, Worker admission and one convergence writer. Shadow independently re-reads the same immutable subject, checks applicability/contradictions/global objective/evidence ceiling and emits findings only; Shadow is never a second mutable state writer.

Issue close, PR merge, workflow green, source prose or model agreement cannot satisfy a later transition.

## DAG and Molecular delivery law

```text
SIBLING             path/resource-disjoint work on common admitted base
TRUE_CHILD          consumes named unmerged parent bytes/contracts
CONVERGENCE         one shared-index/integration owner
PROCESS_DEPENDENCY  ordering without Git ancestry
EXTERNAL_EVIDENCE   independent runtime/source/manual receipt lane
HISTORICAL          immutable prior subject, not current mutable authority
```

Old open programme stacks that no longer bind current main must be classified `RECONSTRUCT_ON_CURRENT_MAIN`, not silently merged/rebased with old green evidence.

Current Molecular terminal index: [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

## Source-document boundary

User-supplied or third-party architecture documents are `SOURCE_PROPOSAL`. Provider, cost, latency, security, licensing, synchronization, mobile, wallet, sandbox, internal-architecture, product-demand and production claims require independent verification and exact-subject receipts before repository truth.

Source closure matrix: [`docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md`](docs/traceability/CURRENT_PUBLIC_REPOSITORY_STATE.md).

## Local Handoff

An exact-subject queue is a continuation contract, not proof of execution. Never mutate an old queue epoch after its bound subject changes.

Current serial local queue:

[`skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json`](skills/agentic-tech-lead-orchestration/references/public-main-local-handoff-queue-2026-08-20.json)

Only true serial work belongs there. Independent #376 manual UI, #466 Herdr and #467 external evidence remain separately owned.

## Evidence vocabulary

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

A job without a runner is not PASS. A policy-skipped job is `SKIPPED_BY_POLICY`. Source prose, package presence, old SHAs or another environment cannot create runtime PASS.

## Publication / merge boundary

```text
local or connector candidate
→ exact changed-file/path lease
→ exact PR base/head
→ owning workflows execute on that head
→ review-thread readback
→ current-main freshness
→ independent Shadow same-subject veto
→ Human/repository merge admission
→ post-merge commit/tree readback
```

Do not auto-resolve semantic conflicts, force-push, ship, merge, release or promote from Worker/model authority.

<!-- BEGIN SHARED RUNTIME IDENTITY -->
## Shared runtime identity and dual-forge preflight
Canonical contract: [`skills/dual-forge-repository-loop/references/runtime-identity-contract.md`](skills/dual-forge-repository-loop/references/runtime-identity-contract.md).
Before mutating delivery state, classify runtime from evidence: `CHATGPT_GITHUB_CONNECTOR | GITHUB_ACTIONS | CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL | CHATGPT_DESKTOP_WORKTREE | UNKNOWN`.
Connector ≠ Actions ≠ local worktree. Local claims require observed checkout/remotes/branch/HEAD; Forgejo requires a resolved local binding; Desktop requires an actually created worktree. `UNKNOWN` fails closed. Runtime, model family and forge authority are separate. One mutable branch has one writer; runtime/HEAD changes require evidence rebinding.
Dual-forge order: `runtime bind → GitHub ingress → local/Forgejo issue+worktree → verified Forgejo PR → local main → GitHub reconciliation → exact-head Actions → GitHub publication`.
Three qualifying failures trigger fresh diagnosis + new worktree; no fourth blind patch.
<!-- END SHARED RUNTIME IDENTITY -->

## Completion contract

Before claiming completion, report:

```text
changed paths and owner
changed route / State Machine / DAG / data flow / authority boundary
procedural core versus module impact
issue/PR relation and current base/head
owning workflows executed versus skipped/not-run
source/PDF/article closure state when applicable
Local Handoff queue or independent external/manual handoff
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED /
SKIPPED_BY_POLICY / EVIDENCE_DEPENDENT / HUMAN_ADMIT_REQUIRED
cleanup and rollback subject
```

Do not claim provider recovery, live model uplift, source truth, GitHub/Forgejo equivalence, release or production success without immutable evidence.