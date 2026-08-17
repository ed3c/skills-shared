# `skills/` directory contract

This directory contains canonical shared Skill bodies and deliberately repo-owned examples recorded by [`../registry.json`](../registry.json). The registry is the classification authority; directory presence alone does not decide whether a Skill is shared.

## Procedural core and domain-instance separation

Every non-trivial Skill follows this ownership model:

```text
skills/<name>/
├── README.md          navigation, current state, ownership, state/DAG/data-flow map
├── SKILL.md           portable procedure, states, laws, evidence ceilings and handoff
├── references/        reusable host-neutral contracts, schemas and immutable identities
├── modules/           trigger-selected domain/provider/consumer/proof specializations
├── scripts/           executable mechanisms and receipt emitters
├── tests/             positive, hollow, mutation, integration and A/B controls
├── evals.json         machine-readable runnable claim inventory when used
└── cases.json         deterministic routing/case inventory when used
```

A small Skill may contain only `SKILL.md`. When a Skill gains domain examples, schemas or executable surfaces, add the nearest READMEs and keep the layers separate.

### `SKILL.md`

Owns generalized procedure, state ordering, hard laws, evidence ceilings, typed module-selection rules and stop/handoff. It must not contain consumer branch names, local paths, credentials, live provider state, product-specific topology, or live receipts.

### `references/`

Owns reusable generic contracts, templates, schemas, immutable treatment identities and assertion vocabulary. A valid schema is a contract state; it is not runtime PASS.

### `modules/`

Owns worked examples and domain/repository/provider/proof interpretations. A module is loaded only when its frozen trigger matches. It cannot silently become global passive context, replace a core law, self-activate from tool presence, or widen filesystem/network/secret/merge/publication authority.

### `scripts/`, `tests/`, `evals.json`, `cases.json`

Own deterministic behavior and falsifiable evidence. Markdown navigation, module presence, package installation or process exit zero cannot substitute for these authorities.

## Mandatory refactor route

Before moving or generalizing load-bearing content between `SKILL.md`, `modules/`, `references/`, `scripts/`, and `tests/`, use [`procedural-core-refactor`](procedural-core-refactor/README.md).

Required refactor state machine:

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

The standard requires immutable historical treatments, old-strength retention, explicit intermediate regressions, law-to-assertion/test routes, trigger/predecessor/receipt causality, matched A/B when behavior is claimed, global-objective and cleanup closure, exact traceability and Human-owned merge/promotion.

The current worked proof is [`agentic-tech-lead-orchestration`](agentic-tech-lead-orchestration/README.md): A=9/11, B0=6/11, B1=10/11 and B2=11/11 on the deterministic structural/executable rubric, plus a production-shaped linked-worktree/subprocess canary. Its live model/provider/Git Town/Forgejo lanes remain `NOT_EXERCISED`.

## Common document routes

Complex Skills and consumer repositories use the same route semantics defined in [`../docs/architecture/DOCUMENT_ROUTING.md`](../docs/architecture/DOCUMENT_ROUTING.md): root entry, Agent procedure, context, architecture, docs index, nearest README, machine authority, and traceability/evidence.

Every governed README states, as applicable:

```text
read order
current integration state
directory/file owner
inputs and outputs
state machine
DAG dependencies and parallel-vs-serial rule
data flow
assertion owner and receipt route
evidence ceiling
stop/handoff
issue → branch → PR → exact head/tree → CI → proof
```

## Reading a complex Skill

1. `README.md` — purpose, current state, ownership, state machine, DAG and data flow.
2. `SKILL.md` — portable procedure.
3. `references/README.md` — contracts and immutable proof identities.
4. `modules/README.md` — trigger-selected specializations.
5. `scripts/README.md` — inputs, outputs, exits, network and mutation boundaries.
6. `tests/README.md`, `evals.json` and `cases.json` — positive and negative controls.
7. Exact issue/PR/head/CI/receipt — one admitted change and evidence boundary.

When a Skill has many tracked mechanism files, do **not** duplicate a hand-maintained list into procedural prose. Use the executable current-tree route:

```bash
python3 scripts/check_skill_entry_routes.py --skill <name> --print-index
```

The governed Skill set is declared in [`../evals/skill-entry-routes.json`](../evals/skill-entry-routes.json). CI rejects a missing common route or a governed Skill whose owned mechanism surface becomes undiscoverable.

## Cross-Skill composition

```text
shared Skill body
→ registry classification
→ user-scope projection or immutable bundle
→ consumer requirements/binding
→ runtime contract binding
→ composition/acceptance
→ exact consumer receipt
```

Shared Skills may reference another method, but consumer selection remains explicit. Shared bodies do not create consumer branches, remotes, secrets, or live runtime state.

## Worked method patterns

- [`procedural-core-refactor`](procedural-core-refactor/README.md) — canonical Skill-refactor procedure, executable proof contract and Agentic Tech Lead golden-proof module.
- [`knowledge-continuity`](knowledge-continuity/README.md) — procedural continuity loop, generic routing reference and on-demand cross-repository example.
- [`spatial-loop-systems-engineering`](spatial-loop-systems-engineering/README.md) — constraint/state-space method for kernel/hardware-bound work.
- [`dual-forge-repository-loop`](dual-forge-repository-loop/README.md) — GitHub ingress/Actions plus local Forgejo implementation, reconciliation and exact-head publication boundaries.
- [`agentic-tech-lead-orchestration`](agentic-tech-lead-orchestration/README.md) — contract-first task/capability DAG, bounded Workers, tournament, convergence, global objective and typed handoff.

## Delivery methods

| Skill | Owns | Does not own |
|---|---|---|
| [`dual-forge-repository-loop`](dual-forge-repository-loop/README.md) | cross-forge state machine, local-main-first ordering, SHA/ancestry receipts, reconciliation | forge credentials, semantic merge authority |
| [`github-delivery-loop`](github-delivery-loop/README.md) | artifact/receipt binding, remote observation, publication, merge preflight | implementation correctness, stack graph, Human merge |
| [`forgejo-delivery-loop`](forgejo-delivery-loop/README.md) | local forge routing, receipt binding, deterministic outbox/recovery | consumer registry values, credentials, arbitrary remote changes, Human merge |
| [`git-town-stacked-pr-worker`](git-town-stacked-pr-worker/README.md) | portable branch/worktree/sync method and molecular Stack trace | consumer config, branches, CI, push/merge/promotion |

## Evidence boundary

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

Documentation can describe a target mechanism. It cannot promote a host tool, service, browser/device session, provider, model run, Git Town sync, forge publication, release or merge to PASS.

## Change rules

- Invoke `procedural-core-refactor` before changing a shared Skill ownership boundary.
- Update `registry.json` when classification changes.
- Update the nearest README when a governed directory, state machine, DAG, data flow or proof route changes.
- Define evals/cases and planted controls before implementation claims.
- Keep procedural core and domain instances decoupled **and** causally connected through typed triggers and receipts.
- Preserve one writer per branch and disjoint path/resource leases for parallel Workers.
- Use a child PR only when it consumes unmerged parent contracts or bytes; keep path-disjoint work as siblings.
- Keep machine paths, credentials, sessions, live indexes and receipts out of shared bodies.
- Do not create empty directories only to match a planned architecture.
- Keep unresolved live lanes and Human authority visible.
