# Implementation preflight — #413 / #414–#418

This file is the Tech Lead + Shadow Architect preparation boundary before deterministic implementation expands beyond the projection schemas.

## Exact upstream dependency

```text
PR #412
head observed: 9408efd28a3123aed3afd8d7f037ddfee1d1684b
provides: Spatial Loop ICPG + static Shadow projection + Tech Lead case obligations
        ↓ TRUE_CHILD by consumed unmerged contract
PR #419
provides: Knowledge Graph method/docs/trace contract
        ↓ TRUE_CHILD while machine schemas consume PR #419 contract
PR #420 / #414 machine-contract branch
provides: complete v7.2 prompt + projection schemas + Shadow design review
```

Refresh mutable PR heads before decision-grade use. The values above are observations, not permanent truth.

## Frozen terminal work packets

```text
KG-C2/P1 #414
  owns:
    references/SYSTEM_PROMPT_V7_2.md
    references/SHADOW_REVIEW_V7_2.md
    references/intent-projection.schema.json
    references/artifact-projection.schema.json
    references/trace-graph.schema.json
    references/IMPLEMENTATION_PREFLIGHT.md
    references/NEGATIVE_CONTROL_MATRIX.md
    future checker/schema mutation fixtures
  provides:
    complete reusable v7.2 prompt
    machine projection contract

KG-E1 #414
  owns future deterministic schema/semantic checker + mutation fixtures
  consumes KG-C2/P1 machine contracts

KG-K1/E2 #415
  owns future case→task/issue→Stack/document binding and reverse-trace checker
  consumes #414 only if implementation imports/validates the machine schema bytes

KG-K2/E3 #416
  owns future traversal/authority/freshness/evidence-ceiling checker
  consumes #414/#415 only when actual machine bytes are required

KG-D2/X1 #417
  one convergence owner for final root/skills routing, shared indexes and release-facing prompt documentation after terminal artifacts stabilize
  must route to `SYSTEM_PROMPT_V7_2.md`; it must not create a second full prompt

KG-X1 #418
  EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
  no Stack paths by default
```

Issue order is not Git ancestry. #415 and #416 remain siblings unless their eventual implementation consumes unmerged parent artifacts.

## Shadow Architect preflight questions

Before admitting a Worker:

1. Is the exact ICPG digest referenced rather than copied into a second denominator?
2. Does every implementation-oriented artifact trace to Intent + ICPG case IDs?
3. Is any semantic/process edge being misrepresented as `TRUE_CHILD`?
4. Does every `TRUE_CHILD` name a consumed unmerged artifact?
5. Are mutable Issue/PR/branch/workflow projections marked refresh-before-decision?
6. Can README/card/prose override verifier/receipt/Git truth? If yes, BLOCK.
7. Can a lower evidence layer be promoted by merge/model agreement? If yes, BLOCK.
8. Is reverse implementation→case→Intent traversal required, not optional?
9. Does every edge support a declared query/decision/authority/evidence use?
10. Is live #418 evidence still separate from deterministic fixtures?
11. Does any Agent need to compose v7.1 + delta manually? If yes, prompt packaging is incomplete.
12. Does any root/convergence document duplicate the full prompt instead of routing to one canonical artifact? If yes, BLOCK prompt divergence.

## Admission states

```text
CONTRACT_PREPARED
→ MACHINE_SCHEMAS_PRESENT
→ FULL_V7_2_PROMPT_PRESENT
→ SHADOW_PROMPT_REVIEW_PRESENT
→ PROMPT_DESIGN_STAGE_COMPLETE
→ SCHEMA_VALIDATION_NOT_YET_EXECUTED
→ SEMANTIC_CHECKER_NOT_YET_IMPLEMENTED
→ MUTATION_CONTROLS_NOT_YET_EXERCISED
→ LIVE_RETRIEVAL_NOT_EXERCISED
→ HUMAN_ADMIT_REQUIRED
```

Do not collapse these states into one completion percentage.

## Prompt-design stage exit — reached on PR #420 candidate

This stage is considered complete as a **design artifact stage** when:

- the full standalone v7.2 prompt exists;
- a fresh Agent no longer needs to manually combine v7.1 + delta;
- v7.1 Evidence/Narrative/Action baseline is preserved;
- Intent, ICPG bridge, Artifact Projection, authority, freshness, evidence ceiling, exact Stack relation semantics and bidirectional traversal are all normative parts of the prompt;
- AGENTS/README route to one canonical full prompt artifact;
- Shadow review explicitly lists the remaining executable risks;
- #414–#418 retain distinct deterministic/live/Human evidence lanes.

These conditions are now represented by repository bytes on the PR #420 candidate branch. File presence proves design packaging only.

## Next stage exit

The next deterministic stage is complete only when:

- schema validation executes on an exact subject;
- semantic trace checker exists;
- all required negative controls are executable and observed;
- exact-head receipt records terminal dispositions;
- no prompt rewrite is required unless a failing control exposes a contract defect.

This stage does **not** prove schema validation, checker PASS, GraphRAG quality, continuous Shadow runtime, merge or release.
