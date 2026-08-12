# `skills/` directory contract

This directory contains canonical shared Skill bodies and deliberately repo-owned examples recorded by [`../registry.json`](../registry.json). The registry is the classification authority; directory presence alone does not decide whether a Skill is shared.

## Shape of a Skill

A small Skill may contain only:

```text
skills/<name>/
└── SKILL.md
```

A complex executable Skill should use:

```text
skills/<name>/
├── README.md          navigation, directory ownership, state-machine map
├── SKILL.md           portable Agent behavior authority
├── evals.json         machine-readable eval inventory
├── modules/           explanatory mechanisms and decision records
├── scripts/           executable public/private mechanisms
└── tests/             good, hollow, mutation, and integration controls
```

`README.md` is required when a Skill has multiple state machines, executable scripts, or a non-trivial test tree. It must not duplicate an API or schema that already has a machine-readable owner.

## Reading a complex Skill

1. `README.md` — purpose, state machines, data flows, current evidence boundary.
2. `SKILL.md` — rules that an Agent must follow.
3. `modules/README.md` — mechanism documents and which state machine each owns.
4. `scripts/README.md` — inputs, outputs, exit semantics, network and mutation boundaries.
5. `tests/README.md` and `evals.json` — positive and negative controls.
6. Exact issue/PR — one admitted change and its Human Admit boundary.

## Cross-Skill composition

Shared Skills compose through explicit references and consumer bindings, not private imports between Skill directories.

```text
shared Skill body
→ registry classification
→ user-scope projection or immutable bundle
→ consumer requirements/binding
→ consumer-owned runtime configuration
→ consumer receipt
```

A Skill may reference another Skill's method, but the consumer repository decides whether both are selected. Shared Skills do not create consumer branches, remotes, secrets, or live runtime state.

## Delivery pair

Two Skills form the Git delivery pair:

| Skill | Owns | Does not own |
|---|---|---|
| [`github-delivery-loop`](github-delivery-loop/README.md) | artifact/receipt binding, GitHub state snapshot, Actions publication admission, merge preflight | implementation correctness, Git Town branch graph, Human merge decision |
| [`git-town-stacked-pr-worker`](git-town-stacked-pr-worker/README.md) | portable branch/worktree/sync method and Worker prompt | consumer `.git-town.toml`, branch names, CI, push authority, merge/promotion |

The consumer repository joins them:

```text
issue + path lease + evals
→ Git Town isolated Worker
→ local implementation and verification
→ github-delivery publication gate
→ reviewed PR
→ Human Admit
```

## Evidence boundary

Use exact evidence states:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

Documentation may describe a target mechanism. It cannot promote a package, host tool, external service, browser session, provider, or model run to `PASS`.

## Change rules

- Update `registry.json` when classification changes.
- Update the nearest README when a new governed directory or state machine appears.
- Define evals before implementation.
- Preserve one writer per branch and disjoint path leases for parallel Workers.
- Keep machine paths, credentials, browser/device sessions, and live receipts out of shared bodies.
- Do not create empty directories only to match a planned architecture.
