# AGENTS.md — Intent-to-Evidence Knowledge Graph

This directory owns the portable **semantic projection and multi-hop trace contract** that connects knowledge cards to Spatial Loop ICPG, Tech Lead task ownership, Git Town Stack delivery and exact-subject evidence.

It does **not** own the canonical case denominator, GitHub/Git mutable truth, live provider state, repository merge authority or Human Admit.

## Mandatory read order

Before changing this Skill, read:

1. `README.md` — current topology, State Machine, DAG, data flow and evidence ceiling.
2. `SKILL.md` — portable laws and stop conditions.
3. `references/SYSTEM_PROMPT_V7_2.md` — complete reusable v7.2 compiler prompt and canonical human-facing prompt artifact.
4. `references/SHADOW_REVIEW_V7_2.md` — Shadow Architect design review and residual risks.
5. `references/intent-projection.schema.json`, `artifact-projection.schema.json`, `trace-graph.schema.json` — projection contracts.
6. `scripts/check_trace_graph.py` — deterministic projection/authority/freshness/evidence gate.
7. `references/case-delivery-binding.schema.json` — #415 case→task/issue/Stack/document binding contract.
8. `scripts/check_case_delivery_binding.py` — Tech Lead case-obligations and delivery ownership checker.
9. `tests/run-all.sh`, `tests/mutation_proof.py`, `tests/delivery_binding_mutation_proof.py` — executable controls and exact-head receipt path.
10. `references/IMPLEMENTATION_PREFLIGHT.md` — Tech Lead stage boundary and work packets.
11. `references/NEGATIVE_CONTROL_MATRIX.md` — controls and current stage owners.
12. `../spatial-loop-systems-engineering/references/intent-case-proof-graph.md` — canonical ICPG semantics.
13. `../agentic-tech-lead-orchestration/references/task-contract.schema.json` and its semantic checker — canonical `case_obligations` ownership contract.
14. `../git-town-stacked-pr-worker/README.md` — Stack relation semantics and Molecular Stack rules.
15. `references/TRACE_GRAPH_CONTRACT.md` — graph node/edge/authority/freshness/evidence rules.
16. exact issue/PR/ref/SHA/file/workflow/receipt subjects before any current-state claim.

`references/SYSTEM_PROMPT_V7_2_DELTA.md` is maintenance/history only. Do not require a fresh Agent to compose v7.1 + delta manually.

## Current stage

```text
v7.2 prompt design                  COMPLETE_AS_DESIGN_ARTIFACT
#414 projection contracts/checker   DETERMINISTIC_EXACT_HEAD_EVIDENCE_RECORDED
#415 case-delivery contract/checker IMPLEMENTED_ON_PR_450
#415 dedicated exact-head gate      EXERCISED_ON_PRIOR_HEAD
repository routing baseline         REPAIRED; CURRENT_HEAD_RECHECK_REQUIRED
#448 #415 evidence closure          WAIT_CURRENT_HEAD_ALL_RELEVANT_GATES
#449 Git Town/docs convergence      PLANNED_CHILD_AFTER_FREEZE
#416 traversal/authority gate       NOT_IMPLEMENTED
#417 convergence                    PLANNED
#418 live GraphRAG/Shadow           NOT_EXERCISED
merge/release                       HUMAN_ADMIT_REQUIRED
```

Do not reopen prompt design for wording changes. Current work is deterministic delivery binding and repository-wide evidence closure.

## Prompt ownership

`references/SYSTEM_PROMPT_V7_2.md` is the complete reusable prompt. `SYSTEM_PROMPT_V7_2_DELTA.md` is a maintenance aid only.

Do not fork the full prompt into root docs, Issue bodies or another Skill. Those surfaces route here. If checker/mutation work exposes a real contract defect, update the canonical prompt and record the reason rather than creating an independent variant.

## Non-negotiable boundaries

```text
Knowledge card relevance != execution authority
ICPG projection          != second case denominator
case binding             != case truth
Issue relationship       != Git ancestry
issue order              != serial dependency
README/AGENTS statement  != verifier/receipt PASS
dedicated gate PASS      != repository-wide clean head
merged PR                != live-runtime proof
historical snapshot      != current mutable truth
fixture PASS              != live #418 evidence
```

The canonical case graph remains Spatial Loop `spatial-loop-case-graph/v1`. This Skill references exact digest + case IDs and consumes Tech Lead `case_obligations`; it must not copy or independently regenerate the case denominator.

## Writer / graph ownership

- `skills/intent-to-evidence-knowledge-graph/**`: current Knowledge Graph worker path.
- `.github/workflows/intent-to-evidence-knowledge-graph.yml`: dedicated deterministic arrival for this Skill.
- `docs/INDEX.md`: repository-wide route inventory; update when this Skill changes measured README routing.
- Spatial Loop ICPG bytes: read-only unless a Spatial Loop issue/branch explicitly owns them.
- Tech Lead task contracts: read-only here; ownership changes belong to the Tech Lead lane.
- Git Town canonical index: #449/#417 only; do not modify it from #450 machine leaf.
- Mutable GitHub/branch/workflow state: refresh from authority before decision use.

## #414 projection gate

`check_trace_graph.py` owns projection semantics already frozen by #414:

- Draft 2020-12 schema validation;
- exact subject SHA assertion;
- Intent↔ICPG digest/case-subset consistency;
- artifact identity vs observed repository/subject;
- mutable authority snapshot freshness;
- artifact type ↔ authority class compatibility;
- prose-over-receipt and L4/L5 evidence-laundering checks;
- `TRUE_CHILD` consumed-artifact reference existence.

Its deterministic controls are NC-01, NC-02, NC-03 and NC-17. #414 is closed at deterministic L2; do not widen it with #415/#416 semantics.

## #415 delivery-binding gate

`check_case_delivery_binding.py` consumes:

```text
case-delivery candidate
+ canonical Tech Lead task-contract/v1 with case_obligations
+ Intent-to-Evidence Trace Graph
```

and must BLOCK when any of these fail:

- canonical task digest/identity;
- exact ICPG graph ref/digest and required-case denominator;
- exactly one branch owner per required case;
- exact task branch/parent/write lease;
- issue ownership per branch;
- one convergence owner;
- TRUE_CHILD/CONVERGENCE artifact consumption from declared parent;
- no parent consumption for SIBLING;
- disjoint path leases for parallel writers;
- bound ArtifactProjection exists and reverse-traces to exact Intent + case;
- AGENTS/README/SKILL projection has a protection/document-routing edge;
- no implementation-oriented artifact is orphaned from a required case.

Executable controls:

```text
NC-04            FALSE_GIT_ANCESTRY
NC-05            FALSE_SERIAL_DEPENDENCY
NC-06            CASE_UNOWNED
NC-07            REVERSE_TRACE_INCOMPLETE
CASE-DUPLICATE   DUPLICATE_CASE_OWNER
CASE-CONVERGENCE MISSING_CONVERGENCE_OWNER
PATH-OVERLAP     PATH_LEASE_OVERLAP
```

A PASS from this dedicated gate is necessary but not sufficient: repository-wide `Shared Skills Infra` and `Skill Eval Contract` failures on the same exact head remain blocking evidence.

## Required trace directions

Every implementation-oriented trace must support both:

```text
Intent → ICPG Case → invariant/proof obligation → task/branch owner → issue → Stack PR → file/doc → oracle/evidence
```

and:

```text
file/doc/PR → owned case binding → task/issue → ICPG Case → invariant → Intent → semantic card/narrative
```

Missing reverse trace is a graph-integrity failure, not a documentation inconvenience.

## Evidence ceiling

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A card, issue, PR, README, model agreement or static graph cannot promote a subject above its exact evidence lane. A local/hermetic authoring run is not a GitHub exact-head receipt; a deterministic receipt is not live #418 GraphRAG evidence.

## Exact-head closure rule

For #415 closure, all decision-relevant gates must describe the same current head:

```text
Intent-to-Evidence Knowledge Graph  PASS
Shared Skills Infra                 PASS
Skill Eval Contract                 PASS
#415 case-delivery receipt          PASS + exact subject SHA
```

If any one is red, fix that real defect and re-run. Never carry a PASS from an older head across a corrective commit.

## Stop conditions

Stop and mark the subject blocked when any of these is true:

- required ICPG case is projected without exact graph digest/case ID;
- `case_obligations` denominator differs from the delivery binding;
- a required case has zero or multiple branch owners;
- task branch/path lease and delivery Stack disagree;
- semantic/issue ordering is used to manufacture Git ancestry;
- implementation artifact lacks Intent/case lineage;
- governed document cannot trace to the case/invariant it protects;
- mutable artifact state is stale or lacks an authority snapshot;
- prose attempts to override a verifier/receipt;
- lower evidence is promoted by merge status, model agreement or aggregation;
- repository-wide route/guard workflow is red on the exact head;
- a second decision-active full v7.2 prompt is created;
- skipped/no-runner CI is being reported as PASS;
- live #418 evidence is inferred from deterministic fixtures.

Merge/release/promotion remains Human/repository authority.
