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
| [`architecture/AGENTS.md`](architecture/AGENTS.md) | conditional architecture-topic router; does not preload all contracts |
| [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) | canonical route names and DR assertions |
| [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) | repository and document-loading state machines |
| [`architecture/DOMAIN_DECOUPLING.md`](architecture/DOMAIN_DECOUPLING.md) | portable core, domain ports, consumer modules/adapters and monotonicity laws |
| [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) | four-repository roles and data flow |
| [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) | source → decision → issue → PR → eval → evidence |

## Existing canonical documents

- [`AGENT_INTEGRATION_STATE.md`](AGENT_INTEGRATION_STATE.md) — live Skill Eval/Evolution handoff.
- [`SKILL_EVAL_ROADMAP.md`](SKILL_EVAL_ROADMAP.md) — target phase roadmap.
- [`traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md`](traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md) — generated projection of the cross-Skill refactor-proof adoption ledger: per-Skill proven layer and every criterion that is not `PASS`, with its owner issue. Regenerate it with `render_adoption_audit.py`, never edit it.
- [`traceability/TECH_LEAD_SHADOW_CLOSURE.md`](traceability/TECH_LEAD_SHADOW_CLOSURE.md) — Tech Lead closure states and the independent Shadow audit that reviews the same immutable subject without becoming a second state writer. `AGENTS.md` makes reading it a precondition for claiming closure, so an unrouted copy was a route the index required and did not name.
- [`architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md) — controlled-language architecture, evidence classes, the merged CTL ledger, and the CTL 08 convergence record with its selected and rollback bundle identities. Current implementation state stays with the Skill routed below.
- [`../skills/README.md`](../skills/README.md) — Skill directory contract.
- [`../skills/github-delivery-loop/README.md`](../skills/github-delivery-loop/README.md) — GitHub delivery state machines.
- [`../skills/git-town-stacked-pr-worker/README.md`](../skills/git-town-stacked-pr-worker/README.md) — Stack PR method.
- [`../skills/forgejo-delivery-loop/README.md`](../skills/forgejo-delivery-loop/README.md) — local Forgejo delivery routing and receipts.
- [`../skills/repo-agent-native/README.md`](../skills/repo-agent-native/README.md) — source-anchored invariant extraction and its A/B evidence boundary.
- [`../skills/knowledge-continuity/README.md`](../skills/knowledge-continuity/README.md) — continuity and routing method example.
- [`../skills/spatial-loop-systems-engineering/README.md`](../skills/spatial-loop-systems-engineering/README.md) — substrate-bound state-space, invariant, capability, teardown, and verification method.
- [`../skills/agentic-tech-lead-orchestration/README.md`](../skills/agentic-tech-lead-orchestration/README.md) — contract-first multi-branch decomposition, deterministic context, bounded Worker execution, tournament selection, and Stacked PR handoff candidate.
- [`../skills/controlled-technical-language-harness/README.md`](../skills/controlled-technical-language-harness/README.md) — controlled-language checking and rewriting, with the deterministic, calibrated-heuristic, semantic, and Human lanes kept apart.
- [`../skills/product-reverse-engineering-loop/README.md`](../skills/product-reverse-engineering-loop/README.md) — evidence-graded product signals, classified mechanisms, problem closure by lane, and bounded implementation packets, with the user, paid and market lanes left where they belong.
- [`../skills/universal-refactor-controller/README.md`](../skills/universal-refactor-controller/README.md) — capability-preserving complexity-reduction controller, State Machine, cross-owner DAG, bounded canary evidence and Human boundary.
- [`governance/LICENSE_DECISION.md`](governance/LICENSE_DECISION.md) — MIT vs Apache-2.0 decision packet against this repository's real dependency scan and four-repository integration, with ready-to-activate drafts under `governance/drafts/`. `HUMAN_ADMIT_REQUIRED`; no root `LICENSE` exists yet.

The nearest directory README is the local ownership route. Machine contracts remain authoritative over prose.

These other documents under `docs/` are on the tree and still unrouted here: `architecture/DELIVERY_SHAPE_EXPERIMENT.md`, `architecture/INTENT_BOUND_CONSTRAINT_HARNESS.md`, `architecture/INTENT_PROMOTION.md`, `integration/CURRENT_WORK.md`, `modular-consumer-contract.md`, `prompts/INTENT_BOUND_CONSTRAINT_HARNESS.md`, and `traceability/SKILL_REFACTOR_PROOF_STACK.md`. Each belongs to its own line of work; naming them keeps this section's omissions from reading as completeness, the way the skill-README sentence below does. Unlike that sentence this list is not measured off the tree, so it carries no count to be checked against one.

An index fails in one direction only: a dead link is found the moment someone follows it, while an omission looks exactly like completeness. So these numbers are no longer a self-report: `scripts/check_document_routes.py` measures them off the tree on every run and refuses the index when a stated count and the inventory disagree. 14 of 33 skill directories ship a `README.md` and 10 are routed above. The four that ship one and are still unrouted are `codebase-atlas`, `dual-forge-repository-loop`, `procedural-shadow-runtime`, and `skill-refactor-proof-loop`; each is named here so the omission cannot read as completeness, and each belongs to its own line of work rather than to this change. The remaining 19 directories have no nearest-README route to omit yet. A directory's shared/repo-owned classification remains `ABSENT` until a separate `registry.json` governance change is Human-admitted.
