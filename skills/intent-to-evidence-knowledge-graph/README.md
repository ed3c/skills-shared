# `intent-to-evidence-knowledge-graph`

Portable semantic-projection and traceability method for connecting human-readable knowledge cards to the canonical Spatial Loop Intent–Case–Proof Graph (ICPG), Tech Lead task ownership, Git Town Molecular Stack delivery, governed Agent documentation and exact-subject evidence.

This Skill does not replace Spatial Loop, Tech Lead, Git Town, GitHub/Git, verifiers or receipts. It composes their identities into an authority-aware graph so a human or GraphRAG query can traverse `why → what must remain true → who owns it → where it landed → what proves it` without inventing a second source of truth.

## Read order

1. `AGENTS.md`
2. `SKILL.md`
3. `references/SYSTEM_PROMPT_V7_2.md` — complete reusable Zettelkasten v7.2 system prompt
4. `references/SHADOW_REVIEW_V7_2.md` — Shadow Architect design review and remaining executable risks
5. `references/TRACE_GRAPH_CONTRACT.md`
6. `references/intent-projection.schema.json`
7. `references/artifact-projection.schema.json`
8. `references/trace-graph.schema.json`
9. `references/IMPLEMENTATION_PREFLIGHT.md`
10. `references/NEGATIVE_CONTROL_MATRIX.md`
11. Spatial Loop ICPG reference/schema/checker
12. Tech Lead case obligations/task DAG
13. Git Town Molecular Stack index
14. exact current external artifact subjects and receipts

`references/SYSTEM_PROMPT_V7_2_DELTA.md` remains a maintenance/history aid. A fresh Agent must not need to compose v7.1 + delta manually; `SYSTEM_PROMPT_V7_2.md` is the canonical complete prompt artifact for this branch.

## Directory map → State Machine ownership

```text
skills/intent-to-evidence-knowledge-graph/
├── AGENTS.md
│   └── Agent read order, prompt ownership, authority/freshness/evidence stop conditions
├── README.md
│   └── State Machine, DAG, data flow, issue/Stack ownership and evidence ceiling
├── SKILL.md
│   └── portable projection/traversal laws + canonical prompt routing
└── references/
    ├── SYSTEM_PROMPT_V7_2.md
    │   └── complete reusable Evidence-First + Intent-to-Evidence Graph system prompt
    ├── SHADOW_REVIEW_V7_2.md
    │   └── independent architecture/design review and executable residual risks
    ├── TRACE_GRAPH_CONTRACT.md
    │   └── node classes, edge types, authority classes, freshness and proof propagation
    ├── SYSTEM_PROMPT_V7_2_DELTA.md
    │   └── v7.1 → v7.2 maintenance delta; not the canonical runtime prompt
    ├── intent-projection.schema.json
    │   └── Intent → exact ICPG digest/case IDs contract
    ├── artifact-projection.schema.json
    │   └── external artifact identity/authority/freshness/evidence projection contract
    ├── trace-graph.schema.json
    │   └── exact typed trace and Git-topology relation contract
    ├── IMPLEMENTATION_PREFLIGHT.md
    │   └── Tech Lead terminal packets, relation classes and stage boundary
    └── NEGATIVE_CONTROL_MATRIX.md
        └── required deterministic false-ancestry/freshness/authority/evidence/prompt-divergence controls
```

The full prompt and machine schemas now exist. Deterministic checker/runtime validation and mutation execution remain owned by #414–#416 and are not implied by file presence.

## Primary State Machine

```text
SOURCE_OR_ARTIFACT_BOUND
→ SEMANTIC_CARD_CONTEXT_BOUND
→ INTENT_PROJECTION_BOUND
→ ICPG_SUBJECT_BOUND
→ ICPG_DIGEST_AND_CASE_IDS_ASSERTED
→ ARTIFACT_PROJECTIONS_BOUND
→ AUTHORITY_CLASSES_ASSERTED
→ EXECUTION_EDGE_TYPES_ASSERTED
→ BIDIRECTIONAL_TRACE_ASSERTED
→ FRESHNESS_REQUIREMENTS_ASSERTED
→ EVIDENCE_CEILING_PROPAGATED
→ GRAPH_QUERY_ROUTES_READY
→ SHADOW_GRAPH_REVIEW
→ SYSTEM_PROMPT_V7_2_DESIGNED
→ MACHINE_SCHEMAS_PRESENT
→ PROMPT_DESIGN_STAGE_COMPLETE
→ READY_FOR_DETERMINISTIC_CHECKER_IMPLEMENTATION
→ LIVE_RETRIEVAL_NOT_EXERCISED
```

Failure states include duplicate case truth, fabricated artifact identity, stale mutable state, false Git ancestry, orphan implementation, broken reverse trace, authority inversion, evidence laundering, unresolved blocking case, connectivity inflation and divergent prompt authority.

## Graph layers and ownership

```text
Semantic Knowledge Plane
N/C/Q/D/E/T/S/P/R/G/V/X/K cards
        │ semantic projection
        ▼
Intent Projection Plane
human desired outcome / non-goals / invariants / acceptance
        │ exact digest + case IDs only
        ▼
Spatial Loop ICPG                         [CANONICAL CASE AUTHORITY]
Intent Atom → Semantic Axis → Case → State Path/Invariant → Oracle
        │ case ownership
        ▼
Tech Lead Task / Issue DAG                [EXECUTION OWNERSHIP]
required case denominator → task/branch owner → one convergence owner
        │ implementation relation
        ▼
Git Town Molecular Stack                  [DELIVERY TOPOLOGY]
SIBLING / TRUE_CHILD / CONVERGENCE / PROCESS_DEPENDENCY /
EXTERNAL_EVIDENCE / HISTORICAL
        │ touches / documents / verifies
        ▼
Repository Artifact Graph
AGENTS / README / SKILL / schema / code / test / workflow
        │ exact-subject proof
        ▼
Evidence Graph                            [TRUTH CEILING]
verifier → workflow → receipt → Shadow verdict → Human Admit
```

The semantic graph and delivery graph are joined by typed bridges. A semantic relation never creates Git ancestry.

## Tech Lead + Issue DAG

```text
#407 ICPG program
└─ #408/#409/#410 deterministic ICPG + monitor + Tech Lead ownership preparation
   └─ PR #412 draft exact implementation candidate
      └─ #413 Knowledge Graph integration program consumes ICPG candidate contract
         └─ PR #419 portable method + trace contract
            └─ PR #420 #414 machine contracts + complete v7.2 prompt
               ├─ #414 deterministic checker/mutations next
               ├─ #415 case→task→issue→Stack/document binding
               ├─ #416 authority-aware traversal + reverse-trace checker
               └─ #417 final root/routing/Molecular convergence

#411 live continuous Spatial Shadow       EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
#418 live multi-hop GraphRAG/Shadow canary EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

Issue order is not Git ancestry. #415/#416 remain siblings unless their implementation actually consumes another leaf's unmerged bytes/contracts. #417 is the one convergence/index owner after terminal artifact identities stabilize; it must route to the canonical prompt rather than recreate it.

## Molecular Stack decomposition

```text
PR #412 ICPG contract/Shadow/Tech Lead ownership preparation
└─ PR #419 KG-C1/D1 portable Knowledge Graph contract
   └─ PR #420 KG-C2/P1 #414 machine schemas + complete v7.2 prompt
      ├─ KG-E1 #414 deterministic checker/mutation implementation
      ├─ KG-K1/E2 #415 case→task/issue→Stack/AGENTS binding
      ├─ KG-K2/E3 #416 traversal/authority/freshness/reverse-trace controls
      └─ KG-D2/X1 #417 one convergence owner after exact artifacts stabilize

#418 live retrieval canary = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY.
```

A future implementation becomes `TRUE_CHILD` only when it consumes an unmerged parent artifact. Documentation/index convergence never manufactures ancestry.

## End-to-end data flow

```text
Article / PDF / code / issue / prompt
→ evidence-constrained semantic cards
→ Intent projection
→ read canonical Spatial Loop ICPG
→ exact ICPG digest + admitted case IDs
→ Tech Lead case_obligations + task/issue ownership
→ Git Town Molecular Stack atoms
→ branch/commit/file/AGENTS/README/SKILL projections
→ oracle/test/workflow/receipt projections
→ authority + freshness + evidence-ceiling checks
→ bidirectional traversal index
→ GraphRAG query
→ refresh mutable external artifacts before decision use
→ answer with exact authority/evidence ceiling
→ Shadow review
→ Human Admit when promotion/merge/release is requested
```

## Standard traversal contracts

### Why → implementation → proof

```text
Narrative/Concept
→ Intent
→ ICPG Case
→ Invariant
→ Task/Issue
→ Stack PR
→ File/AGENTS/README
→ Oracle
→ Receipt
```

### Implementation → why

```text
File/PR
→ Task/Issue
→ ICPG Case
→ Invariant
→ Intent
→ Narrative/Concept
```

### Agent context route

```text
target path
→ nearest AGENTS
→ parent/root routing
→ target Skill
→ current Issue/PR
→ exact ICPG/evidence subject
```

### Gap propagation

```text
UNKNOWN_BLOCKING case
→ owning task/issue
→ blocked Stack/convergence nodes
→ blocked Intent closure
```

## Prompt authority

```text
canonical full prompt:
references/SYSTEM_PROMPT_V7_2.md

maintenance-only delta:
references/SYSTEM_PROMPT_V7_2_DELTA.md
```

Root docs, consumers and #417 convergence should route to the canonical prompt. A copied decision-active full prompt is a governance/traceability defect because it can diverge from the reviewed contract.

## Shadow Architect design verdict

`references/SHADOW_REVIEW_V7_2.md` records:

```text
FULL_V7_2_SYSTEM_PROMPT                  PASS_AS_DESIGN_ARTIFACT
STANDALONE_PROMPT_PACKAGING              PASS_AS_DESIGN_ARTIFACT
V7_1_SEMANTIC_BASELINE                   PRESERVED
ICPG_NON_DUPLICATION                     SPECIFIED
INTENT_TO_EVIDENCE_TRACE                 SPECIFIED
AUTHORITY/FRESHNESS/EVIDENCE_CEILING     SPECIFIED
BIDIRECTIONAL_GRAPH_TRAVERSAL            SPECIFIED
PROMPT_DIVERGENCE_CONTROLS               SPECIFIED
DETERMINISTIC_CHECKER                    NOT_IMPLEMENTED
MUTATION_EXECUTION                       NOT_EXERCISED
LIVE_GRAPHRAG_SHADOW                     NOT_EXERCISED
HUMAN_ADMIT                              REQUIRED
```

Design PASS is not execution PASS.

## Evidence ceiling

Current branch state:

```text
Spatial ICPG contract/checker/routes              IMPLEMENTED_ON_PARENT_PR_412
Spatial Shadow/static prompt projection            IMPLEMENTED_ON_PARENT_PR_412
Tech Lead ICPG denominator/ownership gate          IMPLEMENTED_ON_PARENT_PR_412
Knowledge Graph portable method/trace contract     IMPLEMENTED_ON_PR_419
Complete Zettelkasten v7.2 system prompt           IMPLEMENTED_ON_PR_420
Intent/Artifact/Trace machine schemas              IMPLEMENTED_ON_PR_420
Shadow v7.2 design review                           IMPLEMENTED_ON_PR_420
Prompt-design packaging stage                      STAGE_COMPLETE_AS_DESIGN_ARTIFACT
Deterministic semantic checker                     NOT_IMPLEMENTED
Negative mutation execution                        NOT_EXERCISED
Live GraphRAG multi-hop canary                      NOT_EXERCISED / #418
Live continuous Spatial Shadow                      NOT_EXERCISED / #411
merge/release/promotion                             HUMAN_ADMIT_REQUIRED
```

Do not lift these states based on documentation presence.

## Next deterministic frontier

No additional prompt redesign is admitted before executable work unless a deterministic checker/mutation exposes a contract defect.

```text
complete v7.2 prompt + schemas
→ deterministic schema validation
→ semantic trace checker
→ negative controls
→ exact-head deterministic receipt
→ #415/#416 terminal implementation leaves
→ #417 convergence
→ #418 live GraphRAG/Shadow canary
→ Human Admit
```
