# AGENTS.md — skills-shared operating contract

`skills-shared` is the canonical **Instruction / Method Plane** for cross-repository Skills and the truth-gated Skill Eval/Evolution system. It is not a product monorepo and it must not absorb consumer paths, branches, credentials, provider sessions, or live receipts.

## Mandatory multi-hop read order

Before changing this repository, read in order:

1. [`README.md`](README.md) — repository role and current integrated state.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership and authority boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — same-name document routes.
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md) — shared routing contract and assertions.
6. [`docs/AGENT_INTEGRATION_STATE.md`](docs/AGENT_INTEGRATION_STATE.md) — current Skill Eval/Evolution handoff.
7. [`docs/SKILL_EVAL_ROADMAP.md`](docs/SKILL_EVAL_ROADMAP.md) — target phases; target is not current state.
8. [`registry.json`](registry.json) and [`skills/README.md`](skills/README.md).
9. The target Skill's nearest `README.md`, then `SKILL.md`, `references/`, `modules/`, `scripts/`, `tests/`, and `evals.json`/`cases.json` as applicable.
10. The exact issue, PR base/head, eval contract, and evidence subject.

For GitHub delivery, read [`skills/github-delivery-loop/README.md`](skills/github-delivery-loop/README.md). For local Forgejo delivery, read [`skills/forgejo-delivery-loop/README.md`](skills/forgejo-delivery-loop/README.md). For Git Town/Stacked PR work, read [`skills/git-town-stacked-pr-worker/README.md`](skills/git-town-stacked-pr-worker/README.md).

A missing route, issue, implementation target, parent, eval, or evidence subject is `ABSENT`. Do not reconstruct it from chat history, branch names, another repository, or source prose.

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

`README.md` explains navigation and ownership. `AGENTS.md` defines mandatory procedure. `CLAUDE.md` is a thin host projection. `CONTEXT.md` records mutable current context. `ARCHITECTURE.md` owns stable boundaries. Machine-readable files, scripts, verifiers, receipts, and Git history remain the execution authorities.

## Skill anatomy: procedural core versus domain instances

This separation is load-bearing:

```text
SKILL.md
  = procedural generalization: workflow, method, laws, stop conditions

references/
  = reusable host-neutral contracts, templates, schemas, assertion vocabulary

modules/
  = domain instances, worked examples, provider/repository-specific interpretations
    loaded only when their trigger matches

scripts/ + tests/ + evals.json or cases.json
  = deterministic mechanisms and falsifiable controls
```

Do not put consumer branch names, repository paths, credentials, product topology, or live provider state into a shared `SKILL.md`. Do not make a domain module mandatory passive context for unrelated tasks. If an example becomes a universal law, promote the law into `SKILL.md` through an eval-first governance change; keep the example in `modules/`.

The canonical routing example is under [`skills/knowledge-continuity/`](skills/knowledge-continuity/README.md). `forgejo-delivery-loop` demonstrates the complementary pattern: generic contracts in `references/`, operational/domain details in `modules/`, deterministic route logic in `scripts/`, and consumer-specific line/repository state in `.skill-bindings/`.

## Authority layers

| Authority | Owns |
|---|---|
| `registry.json` | shared versus repo-owned classification |
| `SKILL.md` | portable Agent method and behavior law |
| `references/` | reusable generic contracts and templates |
| `modules/` | on-demand domain instances and examples |
| directory `README.md` | local ownership, state-machine explanation, routes |
| `evals.json` / `cases.json` / `evals/` | machine-readable eval inventory and case contracts |
| deterministic verifier | hard-gate outcome for its declared subject |
| `scripts/` | executable transitions |
| `tests/` | positive, hollow, mutation, and integration controls |
| issue / PR | one admitted change, path lease, parent graph, and evidence boundary |
| Human Admit | merge, promotion, legal/permission expansion, rollback |

Markdown must not become a second API, registry, schema, verifier, receipt, capability unlock, or merge authority.

## Four-repository integration roles

- `skills-shared`: Instruction / Method Plane.
- `runtime-env`: secret-free Runtime Contract Plane.
- `bettor-arena`: Integration / Acceptance Plane and stateless execution gateway.
- `agent-shield-monorepo`: Domain Product / Reference Consumer Plane.

The full data flow is in [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Mutable sibling checkouts and local symlinks are development conveniences, not release identities.

## Codex Desktop handoff and external review

- `codex app <workspace-path>` may open the installed ChatGPT desktop app and the
  named workspace; it does not submit a prompt, create a chat turn, or prove a
  worktree. See the official [CLI command](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-app).
- A `codex://threads/new?...` or `codex://new?...` deep link may prefill composer
  text, path, origin URL, and plugin context, but **does not send the prompt**.
  The operator must submit it; until then fresh diagnosis is
  `FRESH_DIAGNOSIS_HANDOFF_REQUIRED`, not PASS. See official
  [deep links](https://learn.chatgpt.com/docs/reference/commands#deep-links).
- Codex-managed worktrees are created by the ChatGPT desktop app after a Worktree
  chat is selected and its prompt is submitted. Do not invent `EnterWorktree`,
  `ExitWorktree`, `codex worktree`, or `codex -w`. Codex CLI may use
  `codex -C <existing-worktree-path>` only after standard Git worktree path/HEAD
  evidence is bound. See official [worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees).
- A three-failure Desktop packet must name the exact `owner/repo`, request the
  installed GitHub plugin/connector explicitly, include the issue ledger, base/head,
  relevant history, open PRs, failing oracle and logs, and name the PR/branch that
  may receive the solution. A short issue/PR message is not sufficient context.
- `external-verify` resolves external claims through primary sources first.
  `agy`, Codex CLI, Claude Code, or another model may provide cross-family review,
  but never becomes the official truth source by agreeing with a claim.

## Shared versus consumer-owned

Shared here:

- portable Skill procedures;
- reusable method contracts and host-neutral fixtures;
- canonical Skill Eval schemas, adapters, verifier contracts, mutation lineage, and release gates admitted by this repository.

Consumer-owned elsewhere:

- `.git-town.toml`, branch names, worktrees, path leases, repository workflows, remotes, GitHub/Forgejo identities;
- Skills/runtime bindings and product adapters;
- secrets, browser/device sessions, API keys, host tools, live receipts;
- merge, promotion, permission widening, and production rollback.

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
```

A job that never received a runner is `NOT_EXERCISED`; a job deliberately not requested by policy is `SKIPPED_BY_POLICY`. Source prose, diagrams, package presence, license labels, old SHAs, another environment, and green documentation checks cannot create runtime `PASS`.

## GitHub, Forgejo, and Stacked PR delivery

Local commit, remote publication, CI/Actions, review, merge, and release are separate state machines.

- [`github-delivery-loop`](skills/github-delivery-loop/README.md) owns GitHub issue/PR/check/publication and merge-preflight boundaries.
- [`forgejo-delivery-loop`](skills/forgejo-delivery-loop/README.md) owns localhost Forgejo routing, line/receipt binding, deterministic outbox/recovery, and API-safe operation boundaries.
- [`git-town-stacked-pr-worker`](skills/git-town-stacked-pr-worker/README.md) owns the portable branch/worktree/sync method.

One Worker owns one branch and isolated worktree. Independent path-disjoint work is sibling work. A child exists only when it consumes unmerged parent bytes. Terminal implementation leaves stay small; shared index/convergence work is a separate leaf. Unattended synchronization is bounded, non-interactive, no-push, and no-auto-resolve. Semantic conflict, merge, promotion, and rollback remain Human/trusted-operator boundaries.

## Source-document boundary

The attached architecture document is `SOURCE_PROPOSAL`. Its E2B/Firecracker, local/cloud synchronization, mobile, wallet, security, licensing, cost, latency, and recovery claims require independent verification and subject-bound receipts before becoming repository truth.

## Completion contract

Before claiming completion, report:

```text
changed Skill names and paths
changed route/state-machine/authority boundary
procedural core versus domain-module impact
shared/repo-owned classification impact
public interface/schema/workflow impact
evals and positive/hollow/mutation results
exact commit, PR base/head, parent/siblings/terminal leaf
owning workflow execution versus skipped/not-run state
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
rollback subject and Human Admit still required
```

Do not claim merge, promotion, capability unlock, provider recovery, GitHub/Forgejo equivalence, or live runtime success without immutable evidence.

<!-- BEGIN SHARED RUNTIME IDENTITY -->
## Shared runtime identity and dual-forge preflight
Canonical contract: [`skills/dual-forge-repository-loop/references/runtime-identity-contract.md`](skills/dual-forge-repository-loop/references/runtime-identity-contract.md).
Before mutating delivery state, classify runtime from evidence: `CHATGPT_GITHUB_CONNECTOR | GITHUB_ACTIONS | CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL | CHATGPT_DESKTOP_WORKTREE | UNKNOWN`.
Connector ≠ Actions ≠ local worktree. Local claims require observed checkout/remotes/branch/HEAD; Forgejo requires a resolved local binding; Desktop requires an actually created worktree. `UNKNOWN` fails closed. Runtime, model family, and forge authority are separate. One mutable branch has one writer; runtime/HEAD changes require evidence rebinding.
Dual-forge order: `runtime bind → GitHub ingress → local/Forgejo issue+worktree → verified Forgejo PR → local main → GitHub reconciliation → exact-head Actions → GitHub publication`.
Three qualifying failures trigger fresh diagnosis + new worktree; no fourth blind patch.
<!-- END SHARED RUNTIME IDENTITY -->
