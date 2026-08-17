# AGENTS.md — skills-shared operating contract

`skills-shared` is the canonical **Instruction / Method Plane** for cross-repository Skills and the truth-gated Skill Eval/Evolution system. It is not a product monorepo and it must not absorb consumer paths, branches, credentials, provider sessions, live indexes, or live receipts.

## Mandatory multi-hop read order

Before changing this repository, read in order:

1. [`README.md`](README.md) — repository role and current integrated state.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership and authority boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — document routes.
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md).
6. [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md) — current Skill Eval/Evolution handoff.
7. [`docs/SKILL_EVAL_ROADMAP.md`](docs/SKILL_EVAL_ROADMAP.md) — target phases; target is not current state.
8. [`registry.json`](registry.json) and [`skills/README.md`](skills/README.md).
9. The target Skill's nearest `README.md`, then `SKILL.md`, `references/`, `modules/`, `scripts/`, `tests/`, and `evals.json`/`cases.json` as applicable.
10. The exact issue, PR base/head, eval contract, and evidence subject.

Before changing the ownership boundary of a shared `SKILL.md`, additionally read:

11. [`skills/procedural-core-refactor/README.md`](skills/procedural-core-refactor/README.md).
12. [`skills/procedural-core-refactor/SKILL.md`](skills/procedural-core-refactor/SKILL.md).
13. Its refactor contract, selected proof module, checker, tests and golden-proof ledger.

For GitHub delivery, read [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md). For local Forgejo delivery, read [`skills/forgejo-delivery-loop/README.md`](skills/forgejo-delivery-loop/README.md). For Git Town/Stacked PR work, read [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

A missing route, issue, implementation target, parent, eval, receipt, CI run, or evidence subject is `ABSENT`. Do not reconstruct it from chat history, branch names, another repository, package presence, or source prose.

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
<governed-directory>/README.md
```

`README.md` explains navigation and ownership. `AGENTS.md` defines mandatory procedure. `CLAUDE.md` is a thin host projection. `CONTEXT.md` records mutable current context. `ARCHITECTURE.md` owns stable boundaries. Machine-readable files, scripts, verifiers, receipts, Git objects, PR metadata and workflow jobs remain the execution authorities.

Every governed directory README must state, as applicable:

```text
read order
current integration state
owner directory/file
inputs and outputs
state machine
DAG dependencies and parallel-vs-serial rule
data flow
assertion owner and receipt route
evidence ceiling
stop/handoff condition
issue → branch → PR → exact head/tree → CI → proof trace
```

Markdown must not become a second API, registry, schema, verifier, receipt, capability unlock, runtime invocation, or merge authority.

## Skill anatomy: procedural core versus domain instances

This separation is load-bearing:

```text
SKILL.md
  portable procedural generalization: workflow, states, laws, evidence ceilings,
  stop conditions, typed module-selection rules and handoff

references/
  reusable host-neutral contracts, templates, schemas, immutable treatment identities

modules/
  domain, provider, host, consumer, renderer and worked-proof specializations
  loaded only when a frozen trigger matches

scripts/ + tests/ + evals.json or cases.json
  deterministic mechanisms, receipts, positive/hollow/mutation/A-B controls

README.md / AGENTS.md
  navigation, current integration state, directory/state/DAG/data-flow trace

consumer/runtime repository
  live bytes, credentials, indexes, local paths, worktrees, provider sessions,
  concrete commands and exact runtime receipts
```

Do not put consumer branch names, repository paths, credentials, product topology, or live provider state into a shared `SKILL.md`. Do not make a module passive context for unrelated tasks. A module cannot self-activate because a tool is installed, previously used, preferred by a model, or linked from Markdown.

If an example becomes a universal law, promote the law through an eval-first governance change; keep the example in `modules/`. If a procedural core delegates to a module, preserve the complete route:

```text
frozen need
→ trigger evidence
→ selected module
→ predecessor state/receipt
→ exact invocation/assertion owner
→ identity-bound receipt
→ downstream-state admission
```

Module reachability and module runtime causality are separate gates.

## Mandatory procedural-core refactor standard

Any change that moves, deletes, generalizes, or decouples load-bearing content across `SKILL.md`, `modules/`, `references/`, `scripts/`, or `tests/` **must** use [`procedural-core-refactor`](skills/procedural-core-refactor/README.md).

Required state machine:

```text
REQUEST_BOUND
→ BASELINE_FROZEN
→ OWNERSHIP_CLASSIFIED
→ CORE_EXTRACTED
→ DOMAIN_MODULED
→ ROUTES_WIRED
→ ASSERTIONS_BOUND
→ STRUCTURAL_AB
→ REAL_TASK_AB
→ GOLDEN_PROOF_ADMITTED
→ REGISTRY_INDEXED
→ DELIVERY_HANDOFF
```

Required procedure:

1. Freeze exact old/current Skill, module, script and test bytes plus known strengths/failures before editing.
2. Assign one owner to every load-bearing method, domain instance, contract, assertion, test, navigation atom and live runtime artifact.
3. Keep historical A/B treatments immutable. Never improve a score by rewriting an old arm.
4. Preserve old strengths and keep intermediate regressions visible.
5. Route every stable law to a real checker, positive control and planted violation.
6. Prove entry/module/assertion reachability separately from trigger/predecessor/receipt-gated causality.
7. When behavior or runtime parity/uplift is claimed, run a matched A/B with the same task, base/tree, immutable tests, budgets, carrier, denominator and global objective.
8. Keep structural fixture, synthetic runtime, admitted consumer runtime, live model/provider, delivery-provider and Human admission evidence distinct.
9. Require global-objective and cleanup closure; local task PASS cannot overrule repository/system invariants.
10. Preserve issue, branch, parent/child justification, PR, exact head/tree, CI run/job, receipt digest, evidence ceiling, residual lanes and rollback subject.

The Agentic Tech Lead old/B0/B1/B2 and production-shaped real-task A/B is the current golden proof. It proves deterministic structural and synthetic orchestration closure, not live model quality, provider health, Git Town/Forgejo delivery, merge, release, or production readiness.

A refactor is **not complete** merely because:

- the new body is shorter or provider-neutral;
- body-neutrality or index checks pass;
- a module file exists or is linked;
- a schema or fixture validates;
- a tool is installed;
- a process exits zero;
- an issue or PR exists;
- one local candidate passes.

Completion requires the evidence admitted by the state being claimed. Missing live evidence remains `NOT_EXERCISED` or `INSUFFICIENT_EVIDENCE`.

## Authority layers

| Authority | Owns |
|---|---|
| `registry.json` | shared versus repo-owned classification |
| `SKILL.md` | portable Agent method and behavior law |
| `references/` | reusable generic contracts and immutable proof identities |
| `modules/` | trigger-selected domain/proof specializations |
| directory `README.md` | local ownership, current state, state/DAG/data-flow routes |
| `evals.json` / `cases.json` / `evals/` | machine-readable eval inventory and case contracts |
| deterministic verifier | hard-gate outcome for its declared subject |
| `scripts/` | executable transitions and receipt emitters |
| `tests/` | positive, hollow, mutation, integration and A/B controls |
| issue / PR | one admitted change, path lease, parent graph and evidence boundary |
| runtime/consumer | live providers, paths, secrets, sessions, indexes and receipts |
| Human Admit | merge, promotion, legal/permission expansion, semantic conflict, rollback |

## Four-repository integration roles

- `skills-shared`: Instruction / Method Plane.
- `runtime-env`: secret-free Runtime Contract Plane.
- `bettor-arena`: Integration / Acceptance Plane and stateless execution gateway.
- `agent-shield-monorepo`: Domain Product / Reference Consumer Plane.

The full data flow is in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Mutable sibling checkouts and local symlinks are development conveniences, not release identities.

## Shared versus consumer-owned

Shared here:

- portable Skill procedures;
- reusable method contracts and host-neutral fixtures;
- canonical Skill Eval schemas, adapters, verifier contracts, mutation lineage, release gates and scope-bounded golden proofs admitted by this repository.

Consumer-owned elsewhere:

- `.git-town.toml`, branch names, worktrees, path/resource leases, repository workflows, remotes, GitHub/Forgejo identities;
- Skills/runtime bindings and product adapters;
- secrets, browser/device sessions, API keys, host tools, live indexes and live receipts;
- merge, promotion, permission widening, semantic conflict and production rollback.

A consumer-local copy of a shared Skill silently shadows the canonical body unless `registry.json` explicitly classifies it as repo-owned.

## Evidence vocabulary

Use these states exactly where the owning schema admits them:

```text
IMPLEMENTED
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
INSUFFICIENT_EVIDENCE
CONTESTED
HUMAN_ADMIT_REQUIRED
```

A job that never received a runner is `NOT_EXERCISED`; a job deliberately not requested by policy is `SKIPPED_BY_POLICY`. Source prose, diagrams, package presence, license labels, old SHAs, another environment, green documentation checks, fixture receipts and synthetic canaries cannot create live runtime/model/delivery `PASS`.

## GitHub, Forgejo, and Stacked PR delivery

Local commit, remote publication, CI/Actions, review, merge and release are separate state machines.

Every automated commit is bound by [`evals/commit-roles.json`](evals/commit-roles.json), enforced by `scripts/check_commit_roles.py` over the correct event subject. An agent commit uses the machine-role author for its host and matching `Driven-By` / `Driven-On` trailers. Historical exceptions may be content-addressed but new commits are not repaired by shortening the enforced range.

- [`github-delivery-loop`](skills/github-delivery-loop/README.md) owns GitHub issue/PR/check/publication and merge-preflight boundaries.
- [`forgejo-delivery-loop`](skills/forgejo-delivery-loop/README.md) owns localhost Forgejo routing, line/receipt binding, deterministic outbox/recovery and API-safe operation boundaries.
- [`git-town-stacked-pr-worker`](skills/git-town-stacked-pr-worker/README.md) owns the portable branch/worktree/sync method and molecular Stack index.

One Worker owns one branch and isolated worktree. Independent path-disjoint work is sibling work. A child exists only when it consumes unmerged parent contracts or bytes. Terminal implementation leaves stay small; shared index/convergence work is a separate leaf. Unattended synchronization is bounded, non-interactive, no-push and no-auto-resolve. Semantic conflict, merge, promotion and rollback remain Human/trusted-operator boundaries.

The trace unit is:

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

## Codex Desktop handoff and external review

- `codex app <workspace-path>` may open the desktop app and workspace; it does not submit a prompt, create a chat turn, or prove a worktree.
- A `codex://...` deep link may prefill text and context but does not send it; the operator must submit.
- Codex-managed worktrees exist only after the desktop app creates them. CLI may use `codex -C <existing-worktree-path>` only after standard Git worktree path/HEAD evidence is bound.
- A three-failure packet must name exact repo, issue ledger, base/head, history, open PRs, failing oracle/logs and the branch/PR allowed to receive the solution.
- `external-verify` resolves external claims through primary sources first. Another model may review but cannot become official truth by agreement.

## Shared runtime identity and dual-forge preflight

Canonical contract: [`skills/dual-forge-repository-loop/references/runtime-identity-contract.md`](skills/dual-forge-repository-loop/references/runtime-identity-contract.md).

Classify runtime from evidence:

```text
CHATGPT_GITHUB_CONNECTOR
GITHUB_ACTIONS
CLAUDE_CODE_LOCAL
CODEX_CLI_LOCAL
CHATGPT_DESKTOP_WORKTREE
UNKNOWN
```

Connector ≠ Actions ≠ local worktree. Local claims require observed checkout/remotes/branch/HEAD; Forgejo requires a resolved local binding; Desktop requires an actually created worktree. `UNKNOWN` fails closed. Runtime, model family and forge authority are separate. One mutable branch has one writer; runtime/HEAD changes require evidence rebinding.

Dual-forge order:

```text
runtime bind
→ GitHub ingress
→ local/Forgejo issue + worktree
→ verified Forgejo PR
→ local main
→ GitHub reconciliation
→ exact-head Actions
→ GitHub publication
```

Three qualifying failures trigger fresh diagnosis and a new worktree; no fourth blind patch.

## Source-document boundary

Attached PDFs and external architecture documents are `SOURCE_PROPOSAL` unless their claims are independently verified. Their proposed worktrees, tournament prompts, DAGs, Stacked PRs, code-intelligence tools, runtimes, cost, latency, licensing, recovery and security are candidate requirements—not repository runtime facts.

## Completion contract

Before claiming completion, report:

```text
changed Skill names and paths
changed route/state-machine/authority boundary
procedural core versus domain-module impact
shared/repo-owned classification impact
public interface/schema/workflow impact
evals and positive/hollow/mutation/A-B results
exact commit, PR base/head, parent/siblings/terminal leaf
owning workflow execution versus skipped/not-run state
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
rollback subject and Human Admit still required
```

Do not claim merge, promotion, capability unlock, provider recovery, GitHub/Forgejo equivalence, live model uplift, Git Town execution, or production runtime success without immutable evidence.
