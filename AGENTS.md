# AGENTS.md — skills-shared operating contract

`skills-shared` is the canonical **Instruction / Method Plane** for cross-repository Skills and the truth-gated Skill Eval/Evolution system. It is not a product monorepo and must not absorb consumer paths, branches, credentials, provider sessions, or live receipts.

## Mandatory multi-hop read order

Before changing this repository, read in order:

1. [`README.md`](README.md) — repository role and current integrated state.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership and authority boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — document routes.
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md) — shared routing contract.
6. [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md) — document, Skill, refactor, Tech Lead and publication transitions.
7. [`docs/traceability/TRACEABILITY_INDEX.md`](docs/traceability/TRACEABILITY_INDEX.md) — issue/PR/eval/evidence lineage.
8. [`registry.json`](registry.json) and [`skills/README.md`](skills/README.md).
9. The target Skill's nearest `AGENTS.md`, then `README.md`, `SKILL.md`, `references/`, `modules/`, `scripts/`, `tests/`, and `evals.json`/`cases.json` as applicable.
10. For a material Skill refactor, [`skills/skill-refactor-proof-loop/AGENTS.md`](skills/skill-refactor-proof-loop/AGENTS.md) and its golden registry.
11. The exact issue, PR base/head, eval contract, workflow and evidence subject.

For GitHub delivery, read [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md). For local Forgejo delivery, read [`skills/forgejo-delivery-loop/README.md`](skills/forgejo-delivery-loop/README.md). For Git Town/Stacked PR work, read [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

A missing route, issue, implementation target, parent, eval, workflow run, or evidence subject is `ABSENT`. Do not reconstruct it from chat history, branch names, another repository, source prose, or a prior successful SHA.

## Document-route authority

The standard route names are:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/AGENTS.md
<governed-directory>/README.md
```

`README.md` explains navigation and current topology. `AGENTS.md` defines mandatory procedure and stop conditions. `CLAUDE.md` is a thin host projection. `CONTEXT.md` records mutable current context. `ARCHITECTURE.md` owns stable boundaries. Machine-readable files, scripts, verifiers, receipts, workflows and Git history remain execution authorities.

## Skill anatomy: procedural core versus instances

```text
AGENTS.md
  = local Agent read order, writer/authority contract, completion packet

README.md
  = directory ownership, State Machine, DAG, data flow, evidence ceiling, current handoff

SKILL.md
  = procedural generalization: workflow, method, laws, stop conditions

references/
  = reusable host-neutral contracts, templates, schemas, assertion vocabulary

modules/
  = domain/golden/provider/repository instances loaded only when their trigger matches

scripts/ + tests/ + evals.json or cases.json
  = deterministic mechanisms and falsifiable controls
```

Do not put consumer branch names, machine paths, credentials, product topology, or live provider state into a shared `SKILL.md`. Do not make a domain module passive context for unrelated tasks. If an example becomes a universal law, promote the law through eval-first governance and keep the example in `modules/`.

## Mandatory proof-carrying Skill refactors

A material refactor includes monolith-to-module extraction, provider/domain decoupling, moved assertion routes, changed runtime entrypoints, changed State Machine ownership, or a new evidence ceiling. It must follow [`skill-refactor-proof-loop`](skills/skill-refactor-proof-loop/README.md).

Before mutation, bind:

```text
A   OLD_CANONICAL immutable bytes
B0  REFACTOR_AS_LANDED immutable bytes
B1+ REPAIRED_CANDIDATE bytes
protected old strengths
claimed proof layer
same base/tree/contracts/tests/budget/carrier for matched L3+
complete denominator and cleanup policy
true parent/sibling/convergence DAG
remaining evidence owners and issues
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

A shorter or more generic Skill body is not proof. A file link is not execution. A fixture is not live evidence. A local task PASS cannot hide a failed global objective. Failed, stale, blocked, cancelled and superseded attempts remain in the denominator. Golden proofs are registered by content identity and reference their owner implementation without copying it.

## Authority layers

| Authority | Owns |
|---|---|
| `registry.json` | shared versus repo-owned classification |
| `SKILL.md` | portable Agent method and behavior law |
| `references/` | reusable generic contracts and templates |
| `modules/` | on-demand instances and examples |
| directory `AGENTS.md` / `README.md` | local procedure, ownership, State Machine, DAG, data flow, handoff |
| `evals.json` / `cases.json` / `evals/` | machine-readable eval inventory and contracts |
| deterministic verifier | hard-gate outcome for its declared subject |
| `scripts/` | executable transitions |
| `tests/` | positive, hollow, mutation and integration controls |
| issue / PR | one admitted change, path lease, parent graph and evidence boundary |
| workflow run | execution arrival for one exact checked-out subject; not semantic authority alone |
| Human Admit | semantic conflict, provider/permission expansion, merge, release, promotion, rollback |

Markdown must not become a second API, registry, schema, verifier, receipt, capability unlock, workflow result, or merge authority.

## Four-repository integration roles

- `skills-shared`: Instruction / Method Plane.
- `runtime-env`: secret-free Runtime Contract Plane.
- `bettor-arena`: Integration / Acceptance Plane and stateless execution gateway.
- `agent-shield-monorepo`: Domain Product / Reference Consumer Plane.

The full data flow is in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Mutable sibling checkouts and local symlinks are development conveniences, not release identities.

## Codex Desktop and external-review boundary

- `codex app <workspace-path>` opens the desktop app/workspace; it does not submit a prompt or prove a worktree.
- A Codex deep link may prefill text and context but does not send it. Until a Human submits, state is `FRESH_DIAGNOSIS_HANDOFF_REQUIRED`.
- A desktop Worktree exists only after the app creates it. Do not invent `codex worktree`, `EnterWorktree`, or `ExitWorktree`. Codex CLI may use `-C` only after standard Git worktree path/HEAD evidence exists.
- A three-failure handoff names exact repository, issue ledger, base/head, history, open PRs, failing oracle/logs and the branch allowed to receive the solution.
- External models can review observable artifacts but do not become official truth sources by agreement. Private chain of thought is never required evidence.

## Shared versus consumer-owned

Shared here:

- portable procedures;
- reusable host-neutral contracts and fixtures;
- canonical Skill Eval schemas, adapters, verifier contracts, mutation lineage, refactor-proof registry and release gates admitted by this repository.

Consumer/runtime-owned elsewhere:

- `.git-town.toml`, branches, worktrees, leases, repository workflows, remotes, GitHub/Forgejo identities;
- runtime bindings, product/provider adapters and exact commands;
- secrets, browser/device sessions, API keys, local indexes and live receipts;
- merge, promotion, permission widening, production rollback.

A consumer-local copy of a shared Skill silently shadows the canonical body unless `registry.json` explicitly classifies it as repo-owned.

## Evidence vocabulary

Use these states exactly:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

A job that never received a runner is `NOT_EXERCISED`; a job deliberately not requested by policy is `SKIPPED_BY_POLICY`. Source prose, diagrams, package presence, license labels, old SHAs, another environment and green documentation checks cannot create runtime `PASS`.

## GitHub, Forgejo and molecular PR delivery

Local commit, remote publication, CI/Actions, review, merge and release are separate State Machines.

Every automated commit is bound by [`evals/commit-roles.json`](evals/commit-roles.json) and `scripts/check_commit_roles.py`. `enforced_from` does not move to clear a failure. An unclassified commit is repaired at the endpoint that produced it, never hidden by shortening the subject range.

One Worker owns one branch and isolated worktree. Independent path-disjoint work is sibling work. A child exists only when it consumes unmerged parent bytes/contracts. Terminal implementation leaves stay small; shared index/convergence work is a separate leaf with one owner. Unattended synchronization is bounded, non-interactive, no-push and no-auto-resolve. Semantic conflict, merge, promotion and rollback remain Human/trusted-operator boundaries.

## Current proof-carrying Tech Lead line

```text
PR #308  deterministic task/capability reachability and causal-DAG repair
└─ PR #315 production-shaped matched hermetic real-task proof
   └─ PR #323 canonical refactor-proof contract and golden registry
      └─ documentation/State Machine/DAG leaf
```

Current proven ceiling:

```text
L0 SOURCE_FREEZE              PASS
L1 STRUCTURAL_REACHABILITY    PASS
L2 EXECUTABLE_CONTRACT        PASS
L3 HERMETIC_REAL_TASK         PASS
L4 MATCHED_LIVE_MODEL_RUNTIME NOT_EXERCISED
L5 DELIVERY_AND_HUMAN_ADMIT   HUMAN_ADMIT_REQUIRED
```

A, B1 and B2 produce equivalent deterministic output; B0 is blocked by its absent dispatch route. B2 proves stronger causal/evidence closure, not live model quality. Live owners remain #312 Phase 2 and #231/#232/#234/#256.

## Source-document boundary

User-supplied architecture documents are `SOURCE_PROPOSAL`. Their provider, cost, latency, security, licensing, synchronization, mobile, wallet, sandbox, conflict-repair and production claims require independent verification and exact-subject receipts before becoming repository truth.

## Repository-wide completion review

A completion review starts from the tree, not from the index that describes it. Read in this order:

```text
repository reality readback
→ current integration/closure index
→ nearest directory README
→ code/schema/verifier authority
→ Issue dual DAG
→ Molecular Stack index
→ exact evidence subjects
```

Every repository-wide completion review reports:

```text
actual directory/file existence
implementation state versus admission state
start dependencies versus completion dependencies
cloud/local/private/Human evidence lanes
real-problem closure state
missing Molecular atoms, unexercised Gates, blocked atoms and convergence owners
```

An existing path is never `PLANNED` and an absent path is never implemented. Start-readiness never implies completion-readiness: a completion edge requires the prerequisite's own admitted receipt on the exact subject. A receipt satisfies only the lane it was produced in. Portable contracts and their deterministic gates are [`skills/agentic-tech-lead-orchestration/references/REPOSITORY_CLOSURE_RECONCILIATION.md`](skills/agentic-tech-lead-orchestration/references/REPOSITORY_CLOSURE_RECONCILIATION.md) and [`skills/git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md`](skills/git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md).

## Completion contract

Before claiming completion, report:

```text
changed Skill names and paths
changed route/State-Machine/DAG/data-flow/authority boundary
procedural core versus module impact
shared/repo-owned classification impact
public interface/schema/workflow impact
frozen treatments and protected old strengths for a refactor
evals and positive/hollow/mutation/matched-task results
exact commit, PR base/head, parent/siblings/terminal/convergence leaf
owning workflow execution versus skipped/not-run state
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY / HUMAN_ADMIT_REQUIRED
cleanup and rollback subject
```

Do not claim merge, promotion, capability unlock, provider recovery, GitHub/Forgejo equivalence, live model uplift, or production success without immutable evidence.

<!-- BEGIN SHARED RUNTIME IDENTITY -->
## Shared runtime identity and dual-forge preflight
Canonical contract: [`skills/dual-forge-repository-loop/references/runtime-identity-contract.md`](skills/dual-forge-repository-loop/references/runtime-identity-contract.md).
Before mutating delivery state, classify runtime from evidence: `CHATGPT_GITHUB_CONNECTOR | GITHUB_ACTIONS | CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL | CHATGPT_DESKTOP_WORKTREE | UNKNOWN`.
Connector ≠ Actions ≠ local worktree. Local claims require observed checkout/remotes/branch/HEAD; Forgejo requires a resolved local binding; Desktop requires an actually created worktree. `UNKNOWN` fails closed. Runtime, model family and forge authority are separate. One mutable branch has one writer; runtime/HEAD changes require evidence rebinding.
Dual-forge order: `runtime bind → GitHub ingress → local/Forgejo issue+worktree → verified Forgejo PR → local main → GitHub reconciliation → exact-head Actions → GitHub publication`.
Three qualifying failures trigger fresh diagnosis + new worktree; no fourth blind patch.
<!-- END SHARED RUNTIME IDENTITY -->

## Tech Lead + independent Shadow closure audit

Before claiming that a source proposal, issue program, Skill refactor, consumer integration, physical run, Human admission, or release is closed, read [`docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md`](docs/traceability/TECH_LEAD_SHADOW_CLOSURE.md).

```text
Tech Lead
  → problem/capability/task DAG
  → writer, branch/worktree, path and resource leases
  → one convergence owner
  → Local Handoff Queue when the current runtime cannot execute the next proof

Independent Shadow
  → same immutable subject
  → separate applicability/contradiction/global-objective/evidence-ceiling review
  → findings only; never a second state writer
```

Completion requires separate evidence for `METHOD_IMPLEMENTED`, `CONSUMER_MECHANISM_IMPLEMENTED`, `DETERMINISTIC_EVIDENCE_VERIFIED`, `LIVE_OR_PHYSICAL_EVIDENCE_VERIFIED`, `HUMAN_ADMITTED`, and `RELEASED`. A merged PR, fixture PASS, model agreement, workflow green, source proposal, process dependency, or external evidence lane cannot substitute for a later stage. Consumer snapshots in this repository are dated, non-authoritative navigation aids; refresh the consumer machine queue, Stack index, issue/PR metadata and receipts before acting.
