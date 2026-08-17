# `skills/` directory contract

This directory contains canonical shared Skill bodies and deliberately repo-owned examples recorded by [`../registry.json`](../registry.json). The registry is the classification authority; directory presence alone does not decide whether a Skill is shared.

## Procedural core and domain-instance separation

Every non-trivial Skill follows this ownership model:

```text
skills/<name>/
├── AGENTS.md          mandatory Agent read order and local authority contract when needed
├── README.md          navigation, ownership, state-machine map, DAG and data flow
├── SKILL.md           procedural generalization: workflow, method, laws
├── references/        reusable host-neutral contracts/templates
├── modules/           domain instances/examples loaded on demand
├── scripts/           executable mechanisms
├── tests/             positive, hollow, mutation, integration controls
├── evals.json         machine-readable eval inventory when used
└── cases.json         deterministic routing/case inventory when used
```

A small Skill may contain only `SKILL.md`. When a Skill grows domain examples, executable surfaces, a proof registry, or multiple state machines, add the nearest `AGENTS.md` and READMEs and keep the layers separate.

### `AGENTS.md`

Owns the mandatory read order, writer/path leases, evidence vocabulary, stop conditions, completion report and Human/trusted-operator boundary for the governed directory. It does not replace schemas, scripts, receipts, issues, PR metadata or Git history.

### `SKILL.md`

Owns the generalized procedure and stop conditions. It must not contain consumer branch names, local paths, credentials, live provider state, or product-specific topology.

### `references/`

Owns reusable generic contracts, templates, schema explanations, and assertion vocabulary. References may be selected by the procedure but remain domain-neutral.

### `modules/`

Owns worked examples and domain/repository/provider interpretations. A module is loaded only when its trigger matches. A module cannot silently become global passive context or override the core procedure.

### `scripts/`, `tests/`, `evals.json`, `cases.json`

Own deterministic behavior and falsifiable evidence. Markdown navigation cannot substitute for these authorities.

## Common document routes

Complex Skills and consumer repositories use the same route semantics defined in [`../docs/architecture/DOCUMENT_ROUTING.md`](../docs/architecture/DOCUMENT_ROUTING.md): root entry, Agent procedure, context, architecture, docs index, nearest README, machine authority, and traceability/evidence.

## Reading a complex Skill

1. nearest `AGENTS.md` — mandatory procedure and authority.
2. `README.md` — purpose, state machines, DAGs, data flows, evidence boundary and current handoff.
3. `SKILL.md` — portable procedure.
4. `references/README.md` — generic contracts.
5. `modules/README.md` — on-demand domain examples.
6. `scripts/README.md` — I/O, exits, network and mutation boundaries.
7. `tests/README.md` and `evals.json`/`cases.json` — positive and negative controls.
8. Exact issue/PR — one admitted change, parent graph, current head and Human boundary.

When a Skill has many tracked mechanism files, do **not** duplicate a hand-maintained list into procedural prose. Use the executable current-tree route:

```bash
python3 scripts/check_skill_entry_routes.py --skill <name> --print-index
```

The governed Skill set is declared in `../evals/skill-entry-routes.json`. The command indexes current repository bytes under `scripts/`, `references/`, and `modules/`, so a newly added mechanism becomes discoverable without waiting for a second handwritten basename list to be updated. CI rejects a missing common route or a governed Skill whose owned mechanism surface becomes undiscoverable.

## Proof-carrying Skill refactors

Every material Skill refactor follows [`skill-refactor-proof-loop`](skill-refactor-proof-loop/README.md). “Material” includes monolith-to-module splits, provider/domain decoupling, moved assertion routes, changed runtime entrypoints, changed state-machine ownership, or a new evidence ceiling.

The minimum refactor contract is:

```text
freeze OLD_CANONICAL bytes
freeze REFACTOR_AS_LANDED bytes
retain at least one REPAIRED_CANDIDATE
bind protected old strengths
prove current entrypoint → mechanisms → tests → suite → CI arrival
separate structural, executable-contract, hermetic-task, live-runtime and delivery layers
run matched tasks on the same base/tree/contracts/tests/budget/carrier when claiming L3+
retain failed/stale/blocked/cancelled/superseded attempts in the denominator
prove cleanup and non-widening authority
register eligible golden proofs without copying their implementation
```

A shorter or more generic `SKILL.md` is not evidence of preservation. Missing old strengths, dead routes, unfair comparisons, fixture-to-live promotion, incomplete denominator, residue, or artificial Stack ancestry fail closed.

## Cross-Skill composition

```text
shared Skill body
→ registry classification
→ user-scope projection or immutable bundle
→ consumer requirements/binding
→ runtime contract binding
→ bettor composition/acceptance
→ consumer receipt
```

Shared Skills may reference another method, but consumer selection remains explicit. Shared bodies do not create consumer branches, remotes, secrets, or live runtime state.

## Worked method patterns

- [`knowledge-continuity`](knowledge-continuity/README.md) — procedural continuity loop, generic routing reference, and on-demand cross-repository example.
- [`spatial-loop-systems-engineering`](spatial-loop-systems-engineering/README.md) — pre-implementation state-space, hard-invariant, substrate-capability, teardown, and verification contract for kernel/hardware-bound work.
- [`dual-forge-repository-loop`](dual-forge-repository-loop/README.md) — GitHub ingress/Actions plus local Forgejo worktree implementation, local-main-first integration, GitHub conflict/issue reconciliation, and exact-head publication.
- [`agentic-tech-lead-orchestration`](agentic-tech-lead-orchestration/README.md) — candidate contract-first DAG, deterministic code-intelligence roles, bounded parallel Workers, tournament selection, and Stacked PR handoff. Registry admission is a separate governance fact from directory presence.
- [`skill-refactor-proof-loop`](skill-refactor-proof-loop/README.md) — frozen old/as-landed/repaired treatments, old-strength retention, executable reachability, matched hermetic/live A/B layers, golden-proof registration, and no evidence promotion.

## Delivery methods

| Skill | Owns | Does not own |
|---|---|---|
| [`dual-forge-repository-loop`](dual-forge-repository-loop/README.md) | cross-forge state machine, local-main-first ordering, SHA/ancestry receipts, reconciliation gate | forge-specific mechanics, credentials, semantic merge authority |
| [`github-delivery-loop`](github-delivery-loop/README.md) | artifact/receipt binding, remote observation, publication, merge preflight | implementation correctness, stack graph, Human merge |
| [`forgejo-delivery-loop`](forgejo-delivery-loop/README.md) | local forge routing, line/receipt binding, deterministic outbox/recovery, safe operation boundaries | consumer registry values, credentials, arbitrary remote changes, Human merge |
| [`git-town-stacked-pr-worker`](git-town-stacked-pr-worker/README.md) | portable branch/worktree/sync method | consumer config, branches, CI, push/merge/promotion |

## Evidence boundary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

Documentation can describe a target mechanism. It cannot promote a host tool, service, browser/device session, provider, model run, delivery transition or release to `PASS`.

## Change rules

- Update `registry.json` when classification changes.
- Update the nearest `AGENTS.md` and README when a governed directory, state machine, DAG, data flow or authority boundary appears.
- Define evals/cases and protected old strengths before implementation.
- Apply the proof-carrying refactor protocol to material Skill refactors.
- Keep procedural core and domain instances decoupled.
- Preserve one writer per branch and disjoint path leases for parallel Workers.
- Use a child branch only when it consumes unmerged parent bytes/contracts; path-disjoint work remains sibling work.
- Keep machine paths, credentials, sessions, and live receipts out of shared bodies.
- Do not create empty directories only to match a planned architecture.
