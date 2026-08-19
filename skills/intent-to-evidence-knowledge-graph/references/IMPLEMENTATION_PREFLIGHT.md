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
#414 machine-contract branch
```

Refresh mutable PR heads before decision-grade use. The values above are observations, not permanent truth.

## Frozen terminal work packets

```text
KG-C2/E1 #414
  owns:
    references/intent-projection.schema.json
    references/artifact-projection.schema.json
    references/trace-graph.schema.json
    future checker/schema mutation fixtures
  provides:
    machine projection contract

KG-K1/E2 #415
  owns future case→task/issue→Stack/document binding and reverse-trace checker
  consumes #414 only if implementation imports/validates the machine schema bytes

KG-K2/E3 #416
  owns future traversal/authority/freshness/evidence-ceiling checker
  consumes #414/#415 only when actual machine bytes are required

KG-D2/X1 #417
  one convergence owner for system prompt, routing and shared indexes after terminal artifacts stabilize

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

## Admission states

```text
CONTRACT_PREPARED
→ MACHINE_SCHEMAS_PRESENT
→ SCHEMA_VALIDATION_NOT_YET_EXECUTED
→ SEMANTIC_CHECKER_NOT_YET_IMPLEMENTED
→ MUTATION_CONTROLS_NOT_YET_IMPLEMENTED
→ LIVE_RETRIEVAL_NOT_EXERCISED
→ HUMAN_ADMIT_REQUIRED
```

Do not collapse these states into one completion percentage.

## Stage exit

This preparation stage is complete when:

- #414–#418 have explicit owners and relation classes;
- nearest AGENTS/README/SKILL explain the architecture without chat history;
- machine projection schemas exist for Intent, Artifact and trace edges;
- false ancestry/freshness/authority/evidence/reverse-trace controls are enumerated before checker implementation;
- the next Worker can begin deterministic checker/tests without redefining graph semantics.

This stage does **not** prove schema validation, checker PASS, GraphRAG quality, continuous Shadow runtime, merge or release.
