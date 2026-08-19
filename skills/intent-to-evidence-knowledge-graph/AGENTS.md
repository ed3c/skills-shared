# AGENTS.md — Intent-to-Evidence Knowledge Graph

This directory owns the portable **semantic projection and multi-hop trace contract** that connects knowledge cards to Spatial Loop ICPG, Tech Lead task ownership, Git Town Stack delivery and exact-subject evidence.

It does **not** own the canonical case denominator, GitHub/Git mutable truth, live provider state, repository merge authority or Human Admit.

## Mandatory read order

Before changing this Skill, read:

1. `README.md` — current topology, State Machine, DAG, data flow and evidence ceiling.
2. `SKILL.md` — portable laws and stop conditions.
3. `references/SYSTEM_PROMPT_V7_2.md` — complete reusable v7.2 compiler prompt. This is the canonical human-facing prompt artifact for this branch.
4. `references/SHADOW_REVIEW_V7_2.md` — Shadow Architect design review and remaining executable risks.
5. `../spatial-loop-systems-engineering/references/intent-case-proof-graph.md` — canonical ICPG semantics.
6. `../agentic-tech-lead-orchestration/README.md` — case ownership, task DAG, leases and convergence.
7. `../git-town-stacked-pr-worker/README.md` — exact Stack relation semantics and Molecular Stack rules.
8. `references/TRACE_GRAPH_CONTRACT.md` — node classes, edge vocabulary, authority/freshness/evidence rules.
9. `references/SYSTEM_PROMPT_V7_2_DELTA.md` — historical/maintenance delta explaining what v7.2 adds over v7.1; do not require a fresh Agent to compose the prompt manually from this file.
10. exact issue/PR/ref/SHA/file/workflow/receipt subjects before any current-state claim.

## Prompt ownership

`references/SYSTEM_PROMPT_V7_2.md` is the complete reusable prompt. `SYSTEM_PROMPT_V7_2_DELTA.md` is a maintenance aid only.

Do not fork the full prompt into root docs, Issue bodies or another Skill. Those surfaces should route to the canonical artifact. If deterministic checker/test work finds a contract defect, update the canonical prompt and record the reason rather than creating an independent variant.

## Non-negotiable boundaries

```text
Knowledge card relevance != execution authority
ICPG projection          != second case denominator
Issue relationship       != Git ancestry
README/AGENTS statement  != verifier/receipt PASS
merged PR                != live-runtime proof
historical snapshot      != current mutable truth
```

The canonical case graph remains Spatial Loop `spatial-loop-case-graph/v1`. This Skill may reference its exact digest and case IDs, but must not copy or independently regenerate its denominator as a second authority.

## Writer / graph ownership

- `skills/intent-to-evidence-knowledge-graph/**`: owned by the current Knowledge Graph Worker.
- Spatial Loop ICPG bytes: read-only unless the task is explicitly owned by a Spatial Loop issue/branch.
- Tech Lead task contracts: read-only from this Skill; ownership changes belong to the Tech Lead lane.
- Git Town Stack indexes: updated only by the designated convergence/index leaf.
- Mutable GitHub/branch/workflow state must be refreshed from its authority before decision use.

## Required trace directions

Every implementation-oriented trace must support both:

```text
Intent → ICPG Case → invariant/proof obligation → task/issue → Stack PR → file → oracle/evidence
```

and:

```text
file/PR → task/issue → ICPG Case → invariant → Intent → semantic card/narrative
```

Missing reverse trace is not a documentation inconvenience; it is a graph-integrity failure.

## Evidence ceiling

Use repository proof layers without laundering:

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A card, issue, PR, README, model agreement or static graph cannot promote a subject above its exact evidence lane.

## Stop conditions

Stop and mark the subject blocked when any of these is true:

- a required ICPG case is projected without an exact graph digest/case ID;
- mutable artifact state is stale or cannot be refreshed;
- a semantic `DEPENDS_ON` edge is being used to manufacture Git ancestry;
- an implementation artifact has no intent/case lineage;
- a knowledge card attempts to override a higher-authority verifier/receipt;
- a lower evidence layer is being promoted by prose or aggregation;
- a graph edge exists only to increase connectivity and supports no declared traversal.

Merge/release/promotion remains Human/repository authority.
