# Architecture documentation Agent route

This file governs `docs/architecture/`. It is a conditional router, not a second architecture specification.

## Bootstrap

Read:

1. [`../../AGENTS.md`](../../AGENTS.md) for repository-wide procedure.
2. [`../../README.md`](../../README.md) for repository role.
3. [`../../CONTEXT.md`](../../CONTEXT.md) for current handoff.
4. [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) for stable ownership.
5. [`../INDEX.md`](../INDEX.md) for the complete local route map.

Then load only the topic route that matches the task.

## Conditional topic routes

| Trigger | Read |
|---|---|
| route name, hop order, route assertion | [`DOCUMENT_ROUTING.md`](DOCUMENT_ROUTING.md) |
| state, event, transition, terminal, evidence transition | [`STATE_MACHINES.md`](STATE_MACHINES.md) |
| Skill core, `references/`, `modules/`, consumer binding, adapter, domain boundary | [`DOMAIN_DECOUPLING.md`](DOMAIN_DECOUPLING.md) |
| cross-repository ownership, binding, release or origin | [`../integration/CROSS_REPO_INTEGRATION.md`](../integration/CROSS_REPO_INTEGRATION.md) |
| source-to-issue/PR/eval/receipt lineage | [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md) |

Do not load every architecture document for every task.

## Writer and authority rules

- One issue and one branch own one architecture-document change.
- The nearest README owns local navigation.
- Machine contracts, scripts, verifiers, receipts, workflows and Git history remain execution authorities.
- Current consumer state stays in the consumer repository.
- A source proposal does not become repository truth by being cited here.
- A new stable architecture topic uses the standard filename in every participating repository and is registered in `docs/INDEX.md`.

## Completion packet

Report:

```text
changed routes
changed stable boundary
changed State Machine or dependency direction
machine authority affected or unchanged
relative-link and route checks
exact base/head
remaining non-success states
```
