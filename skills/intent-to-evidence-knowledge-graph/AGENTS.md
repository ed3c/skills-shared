# AGENTS.md — Intent-to-Evidence Knowledge Graph

This directory owns the portable **semantic projection and multi-hop trace contract** that connects knowledge cards to Spatial Loop ICPG, Tech Lead task ownership, Git Town Stack delivery and exact-subject evidence.

It does **not** own the canonical case denominator, GitHub/Git mutable truth, live provider state, repository merge authority or Human Admit.

## Mandatory read order

Before changing this Skill, read:

1. `README.md` — current topology, State Machine, DAG, data flow and evidence ceiling.
2. `SKILL.md` — portable laws and stop conditions.
3. `references/SYSTEM_PROMPT_V7_2.md` — complete reusable v7.2 compiler prompt and canonical human-facing prompt artifact.
4. `references/SHADOW_REVIEW_V7_2.md` — Shadow Architect design review and residual risks.
5. `references/intent-projection.schema.json`, `artifact-projection.schema.json`, `trace-graph.schema.json` — machine contracts.
6. `scripts/check_trace_graph.py` — deterministic projection/authority/freshness/evidence gate.
7. `tests/run-all.sh` and `tests/mutation_proof.py` — current executable controls and exact-head fixture path.
8. `references/IMPLEMENTATION_PREFLIGHT.md` — Tech Lead stage boundary and work packets.
9. `references/NEGATIVE_CONTROL_MATRIX.md` — controls and current stage owners.
10. `../spatial-loop-systems-engineering/references/intent-case-proof-graph.md` — canonical ICPG semantics.
11. `../agentic-tech-lead-orchestration/README.md` — case ownership, task DAG, leases and convergence.
12. `../git-town-stacked-pr-worker/README.md` — Stack relation semantics and Molecular Stack rules.
13. `references/TRACE_GRAPH_CONTRACT.md` — graph node/edge/authority/freshness/evidence rules.
14. exact issue/PR/ref/SHA/file/workflow/receipt subjects before any current-state claim.

`references/SYSTEM_PROMPT_V7_2_DELTA.md` is maintenance/history only. Do not require a fresh Agent to compose v7.1 + delta manually.

## Current stage

```text
v7.2 prompt design                COMPLETE_AS_DESIGN_ARTIFACT
Intent/Artifact/Trace schemas     IMPLEMENTED_ON_PR_420
#414 deterministic checker        IMPLEMENTED_ON_PR_420
NC-01/02/03/17 mutation code      IMPLEMENTED_ON_PR_420
exact-head CI route               IMPLEMENTED_ON_PR_420 / #437
exact-head deterministic receipt  PENDING_REAL_RUN / #439
#415 delivery/reverse trace       NOT_IMPLEMENTED
#416 traversal/authority gate     NOT_IMPLEMENTED
#417 convergence                  PLANNED
#418 live GraphRAG/Shadow         NOT_EXERCISED
merge/release                     HUMAN_ADMIT_REQUIRED
```

Do not reopen prompt design for wording changes. The current frontier is one real exact-head deterministic run, then #415/#416 decomposition from the actual frozen #414 bytes.

## Prompt ownership

`references/SYSTEM_PROMPT_V7_2.md` is the complete reusable prompt. `SYSTEM_PROMPT_V7_2_DELTA.md` is a maintenance aid only.

Do not fork the full prompt into root docs, Issue bodies or another Skill. Those surfaces route here. If checker/mutation work exposes a real contract defect, update the canonical prompt and record the reason rather than creating an independent variant.

## Non-negotiable boundaries

```text
Knowledge card relevance != execution authority
ICPG projection          != second case denominator
Issue relationship       != Git ancestry
README/AGENTS statement  != verifier/receipt PASS
merged PR                != live-runtime proof
historical snapshot      != current mutable truth
fixture PASS              != live #418 evidence
```

The canonical case graph remains Spatial Loop `spatial-loop-case-graph/v1`. This Skill references exact digest + case IDs; it must not copy or independently regenerate the case denominator.

## Writer / graph ownership

- `skills/intent-to-evidence-knowledge-graph/**`: current Knowledge Graph worker path.
- `.github/workflows/intent-to-evidence-knowledge-graph.yml`: dedicated deterministic arrival for this Skill.
- Spatial Loop ICPG bytes: read-only unless a Spatial Loop issue/branch explicitly owns them.
- Tech Lead task contracts: read-only here; ownership changes belong to the Tech Lead lane.
- Git Town canonical indexes: update only in the designated convergence/index leaf.
- Mutable GitHub/branch/workflow state: refresh from authority before decision use.

## Required trace directions

Every implementation-oriented trace must support both:

```text
Intent → ICPG Case → invariant/proof obligation → task/issue → Stack PR → file → oracle/evidence
```

and:

```text
file/PR → task/issue → ICPG Case → invariant → Intent → semantic card/narrative
```

Missing reverse trace is a graph-integrity failure, not a documentation inconvenience.

## Deterministic #414 gate

`check_trace_graph.py` owns only projection-level semantics already frozen by #414:

- Draft 2020-12 schema validation;
- exact subject SHA assertion when supplied;
- Intent↔ICPG digest/case-subset consistency;
- artifact identity vs observed repository/subject;
- mutable authority snapshot freshness;
- artifact type ↔ authority class compatibility;
- prose-over-receipt and L4/L5 evidence-laundering checks;
- `TRUE_CHILD` consumed-artifact reference existence.

Exit contract:

```text
0   PASS
2   BLOCK
64  INPUT_ERROR
```

Current mutation subset:

```text
NC-01 → DUPLICATE_ICPG_AUTHORITY
NC-02 → STALE_MUTABLE_SUBJECT
NC-03 → PROSE_OVER_RECEIPT
NC-17 → FABRICATED_ARTIFACT_IDENTITY
```

Do not pull #415/#416 semantics into this checker merely to make the mutation count larger.

## Evidence ceiling

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A card, issue, PR, README, model agreement or static graph cannot promote a subject above its exact evidence lane. A local/hermetic authoring run is not the GitHub exact-head receipt; a deterministic receipt is not live #418 GraphRAG evidence.

## Stop conditions

Stop and mark the subject blocked when any of these is true:

- a required ICPG case is projected without exact graph digest/case ID;
- mutable artifact state is stale or no authority snapshot exists for decision use;
- semantic dependency is used to manufacture Git ancestry;
- implementation artifact lacks intent/case lineage;
- prose attempts to override a verifier/receipt;
- lower evidence is promoted by merge status, model agreement or aggregation;
- a graph edge has no declared decision/causal/implementation/authority/evidence/retrieval utility;
- a second decision-active full v7.2 prompt is created;
- checker failure is hidden by documentation-only edits;
- skipped/no-runner CI is being reported as repository PASS;
- live #418 evidence is inferred from deterministic fixtures.

Merge/release/promotion remains Human/repository authority.
