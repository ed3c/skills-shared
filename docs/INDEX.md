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
| [`traceability/AGENTS.md`](traceability/AGENTS.md) | nearest router for repository-wide traceability, Tech Lead/Shadow closure and Codex control-plane indexes |
| [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) | canonical route names and DR assertions |
| [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) | repository and document-loading state machines |
| [`architecture/DOMAIN_DECOUPLING.md`](architecture/DOMAIN_DECOUPLING.md) | portable core, domain ports, consumer modules/adapters and monotonicity laws |
| [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md) | four-repository roles and data flow |
| [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md) | source → decision → issue → PR → eval → evidence |

## Existing canonical documents

- [`AGENT_INTEGRATION_STATE.md`](AGENT_INTEGRATION_STATE.md) — live Skill Eval/Evolution handoff.
- [`SKILL_EVAL_ROADMAP.md`](SKILL_EVAL_ROADMAP.md) — target phase roadmap.
- [`traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md`](traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md) — generated projection of the cross-Skill refactor-proof adoption ledger; regenerate it with its renderer, never edit it.
- [`traceability/TECH_LEAD_SHADOW_CLOSURE.md`](traceability/TECH_LEAD_SHADOW_CLOSURE.md) — provider-neutral Tech Lead closure states and independent Shadow audit over the same immutable subject.
- [`traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md`](traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE_ADMISSION.md) — admitted #379 static/deterministic convergence subject, exact merge provenance, hosted evidence, consumed sibling publication state, and remaining live evidence owners.
- [`traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md`](traceability/CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md) — #375–#379 pre-admission Codex SDK/GitHub Issue DAG/Herdr/problem-closure State Machine, exact sibling/convergence subjects, rejected epochs, evidence ceilings and cold-start route.
- [`traceability/WAVE3_PARENT_ADMISSION.md`](traceability/WAVE3_PARENT_ADMISSION.md) — #464–#468 fork-time #455 ancestry, Wave‑2/#475 admission, rejected convergence history, current-main freshness and Human-admission boundary.
- [`traceability/WAVE3_LIVE_EVIDENCE.md`](traceability/WAVE3_LIVE_EVIDENCE.md) — Wave‑3 live-evidence carriers, State Machine, deterministic denominator, Local Handoff Queue and current-main convergence rule.
- [`architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md`](architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md) — controlled-language architecture, evidence classes and merged CTL ledger.
- [`../skills/README.md`](../skills/README.md) — Skill directory contract.
- [`../skills/github-delivery-loop/README.md`](../skills/github-delivery-loop/README.md) — GitHub delivery State Machines.
- [`../skills/git-town-stacked-pr-worker/README.md`](../skills/git-town-stacked-pr-worker/README.md) — Stack PR method and Molecular indexes, including #375–#379, #464–#468 and the UCR convergence lineages.
- [`../skills/forgejo-delivery-loop/README.md`](../skills/forgejo-delivery-loop/README.md) — local Forgejo delivery routing and receipts.
- [`../skills/repo-agent-native/README.md`](../skills/repo-agent-native/README.md) — source-anchored invariant extraction and A/B evidence boundary.
- [`../skills/knowledge-continuity/README.md`](../skills/knowledge-continuity/README.md) — continuity and routing method example.
- [`../skills/spatial-loop-systems-engineering/README.md`](../skills/spatial-loop-systems-engineering/README.md) — substrate-bound state-space, invariant, capability, teardown, and verification method.
- [`../skills/agentic-tech-lead-orchestration/README.md`](../skills/agentic-tech-lead-orchestration/README.md) — contract-first multi-branch decomposition, dual DAG, Codex control-plane adapters, Wave‑3 live-evidence carriers, convergence and handoff.
- [`../skills/procedural-shadow-runtime/README.md`](../skills/procedural-shadow-runtime/README.md) — independent same-subject applicability, contradiction, denominator and evidence-ceiling monitor; never a second writer.
- [`../skills/controlled-technical-language-harness/README.md`](../skills/controlled-technical-language-harness/README.md) — controlled-language checking and rewriting with separate deterministic/semantic/Human lanes.
- [`../skills/product-reverse-engineering-loop/README.md`](../skills/product-reverse-engineering-loop/README.md) — evidence-graded product signals and problem closure by lane.
- [`../skills/universal-refactor-controller/README.md`](../skills/universal-refactor-controller/README.md) — capability-preserving complexity-reduction controller, State Machine, cross-owner DAG, bounded canary evidence and Human boundary.
- [`governance/LICENSE_DECISION.md`](governance/LICENSE_DECISION.md) — license decision packet and ready-to-activate drafts. `HUMAN_ADMIT_REQUIRED`; no root `LICENSE` exists yet.

The nearest directory README/AGENTS is the local ownership route. Machine contracts remain authoritative over prose.

These other documents under `docs/` are on the tree and still unrouted here: `architecture/DELIVERY_SHAPE_EXPERIMENT.md`, `architecture/INTENT_BOUND_CONSTRAINT_HARNESS.md`, `architecture/INTENT_PROMOTION.md`, `integration/CURRENT_WORK.md`, `modular-consumer-contract.md`, `prompts/INTENT_BOUND_CONSTRAINT_HARNESS.md`, and `traceability/SKILL_REFACTOR_PROOF_STACK.md`. Each belongs to its own line of work; naming them keeps this section's omissions from reading as completeness. This list is not a measured count; `scripts/check_document_routes.py` remains the executable inventory gate.

An index fails in one direction only: a dead link is found the moment someone follows it, while an omission looks exactly like completeness. `scripts/check_document_routes.py` measures the stated Skill-directory counts off the tree and refuses drift. 14 of 34 skill directories ship a `README.md` and 11 are routed above. The three that ship one and are still unrouted are `codebase-atlas`, `dual-forge-repository-loop`, and `skill-refactor-proof-loop`; each is named here so the omission cannot read as completeness, and each belongs to its own line of work rather than to this change. The remaining 20 directories have no nearest-README route to omit yet. A directory's shared/repo-owned classification remains `ABSENT` until a separate `registry.json` governance change is Human-admitted.
