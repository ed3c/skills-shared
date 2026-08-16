# `skills/` directory contract

This directory contains canonical shared Skill bodies and deliberately repo-owned examples recorded by [`../registry.json`](../registry.json). The registry is the classification authority; directory presence alone does not decide whether a Skill is shared.

## Procedural core and domain-instance separation

Every non-trivial Skill follows this ownership model:

```text
skills/<name>/
├── README.md          navigation, ownership, state-machine map
├── SKILL.md           procedural generalization: workflow, method, laws
├── references/        reusable host-neutral contracts/templates
├── modules/           domain instances/examples loaded on demand
├── scripts/           executable mechanisms
├── tests/             positive, hollow, mutation, integration controls
├── evals.json         machine-readable eval inventory when used
└── cases.json         deterministic routing/case inventory when used
```

A small Skill may contain only `SKILL.md`. When a Skill grows domain examples or executable surfaces, add the nearest READMEs and keep the layers separate.

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

1. `README.md` — purpose, state machines, data flows, evidence boundary.
2. `SKILL.md` — portable procedure.
3. `references/README.md` — generic contracts.
4. `modules/README.md` — on-demand domain examples.
5. `scripts/README.md` — I/O, exits, network and mutation boundaries.
6. `tests/README.md` and `evals.json`/`cases.json` — positive and negative controls.
7. Exact issue/PR — one admitted change and Human boundary.

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
- [`agentic-tech-lead-orchestration`](agentic-tech-lead-orchestration/README.md) — candidate contract-first DAG, deterministic code-intelligence roles, bounded parallel Workers, tournament selection, and Stacked PR handoff. Directory presence is not registry admission.

## Delivery methods

| Skill | Owns | Does not own |
|---|---|---|
| [`dual-forge-repository-loop`](dual-forge-repository-loop/README.md) | cross-forge state machine, local-main-first ordering, SHA/ancestry receipts, GitHub reconciliation gate | forge-specific mechanics, credentials, semantic merge authority |
| [`github-delivery-loop`](github-delivery-loop/README.md) | artifact/receipt binding, GitHub observation, Actions publication, merge preflight | implementation correctness, Git Town graph, Human merge |
| [`forgejo-delivery-loop`](forgejo-delivery-loop/README.md) | localhost Forgejo routing, line/receipt binding, deterministic outbox/recovery, safe operation boundaries | consumer registry values, credentials, arbitrary remote changes, Human merge |
| [`git-town-stacked-pr-worker`](git-town-stacked-pr-worker/README.md) | portable branch/worktree/sync method | consumer config, branches, CI, push/merge/promotion |

## Evidence boundary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Documentation can describe a target mechanism. It cannot promote a host tool, service, browser/device session, provider, model run, or release to `PASS`.

## Change rules

- Update `registry.json` when classification changes.
- Update the nearest README when a governed directory or state machine appears.
- Define evals/cases before implementation.
- Keep procedural core and domain instances decoupled.
- Preserve one writer per branch and disjoint path leases for parallel Workers.
- Keep machine paths, credentials, sessions, and live receipts out of shared bodies.
- Do not create empty directories only to match a planned architecture.
