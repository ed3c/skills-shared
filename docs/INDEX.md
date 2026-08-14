# Documentation index

## Root routes

| Route | Purpose |
|---|---|
| [`../README.md`](../README.md) | repository entry and current integrated overview |
| [`../AGENTS.md`](../AGENTS.md) | mandatory Agent procedure and completion contract |
| [`../CLAUDE.md`](../CLAUDE.md) | Claude Code thin projection |
| [`../CONTEXT.md`](../CONTEXT.md) | mutable current handoff |
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | stable ownership and invariants |

## Shared same-name routes

| Route | Purpose |
|---|---|
| [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) | canonical route names and DR assertions |
| [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) | repository and document-loading state machines |
| [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) | four-repository roles and data flow |
| [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) | source → decision → issue → PR → eval → evidence |

## Existing canonical documents

- [`AGENT_INTEGRATION_STATE.md`](AGENT_INTEGRATION_STATE.md) — live Skill Eval/Evolution handoff.
- [`SKILL_EVAL_ROADMAP.md`](SKILL_EVAL_ROADMAP.md) — target phase roadmap.
- [`../skills/README.md`](../skills/README.md) — Skill directory contract.
- [`../skills/github-delivery-loop/README.md`](../skills/github-delivery-loop/README.md) — GitHub delivery state machines.
- [`../skills/git-town-stacked-pr-worker/README.md`](../skills/git-town-stacked-pr-worker/README.md) — Stack PR method.
- [`../skills/forgejo-delivery-loop/README.md`](../skills/forgejo-delivery-loop/README.md) — local Forgejo delivery routing and receipts.
- [`../skills/repo-agent-native/README.md`](../skills/repo-agent-native/README.md) — source-anchored invariant extraction and its A/B evidence boundary.
- [`../skills/knowledge-continuity/README.md`](../skills/knowledge-continuity/README.md) — continuity and routing method example.
- [`../skills/spatial-loop-systems-engineering/README.md`](../skills/spatial-loop-systems-engineering/README.md) — substrate-bound state-space, invariant, capability, teardown, and verification method.

The nearest directory README is the local ownership route. Machine contracts remain authoritative over prose.

An index fails in one direction only: a dead link is found the moment someone follows it, while an omission looks exactly like completeness. On this candidate branch, 7 of 24 skills ship a `README.md` and all 7 are routed above; the other 17 have no nearest-README route to omit yet. Adding one without adding its route here recreates the omission.
