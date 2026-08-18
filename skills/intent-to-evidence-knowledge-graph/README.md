# `intent-to-evidence-knowledge-graph`

Portable semantic-projection and traceability method for connecting human-readable knowledge cards to the canonical Spatial Loop Intent–Case–Proof Graph (ICPG), Tech Lead task ownership, Git Town Molecular Stack delivery, governed Agent documentation and exact-subject evidence.

This Skill does not replace Spatial Loop, Tech Lead, Git Town, GitHub/Git, verifiers or receipts. It composes their identities into an authority-aware graph so a human or GraphRAG query can traverse `why → what must remain true → who owns it → where it landed → what proves it` without inventing a second source of truth.

## Read order

1. `AGENTS.md`
2. `SKILL.md`
3. `references/TRACE_GRAPH_CONTRACT.md`
4. `references/SYSTEM_PROMPT_V7_2_DELTA.md`
5. Spatial Loop ICPG reference/schema/checker
6. Tech Lead case obligations/task DAG
7. Git Town Molecular Stack index
8. exact current external artifact subjects and receipts

## Directory map → State Machine ownership

```text
skills/intent-to-evidence-knowledge-graph/
├── AGENTS.md
│   └── Agent read order, authority/freshness/evidence stop conditions
├── README.md
│   └── State Machine, DAG, data flow, issue/Stack ownership and evidence ceiling
├── SKILL.md
│   └── portable projection/traversal laws
└── references/
    ├── TRACE_GRAPH_CONTRACT.md
    │   └── node classes, edge types, authority classes, freshness and proof propagation
    └── SYSTEM_PROMPT_V7_2_DELTA.md
        └── v7.1 → v7.2 knowledge-compiler additions without duplicating ICPG truth
```

Planned deterministic schemas/checkers/mutations are owned by #414–#416 and remain `NOT_IMPLEMENTED` until their exact bytes exist.

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
→ READY_FOR_DETERMINISTIC_GATE
→ LIVE_RETRIEVAL_NOT_EXERCISED
```

Failure states include duplicate case truth, fabricated artifact identity, stale mutable state, false Git ancestry, orphan implementation, broken reverse trace, authority inversion, evidence laundering, unresolved blocking case and connectivity inflation.

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
         ├─ #414 projection schemas + ICPG bridge
         ├─ #415 case→task→issue→Stack/document binding
         ├─ #416 authority-aware traversal + reverse-trace checker
         └─ #417 v7.2 prompt/docs/Molecular convergence

#411 live continuous Spatial Shadow       EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
#418 live multi-hop GraphRAG/Shadow canary EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

#414–#416 are logical work packets; their Git relation must be chosen from actual consumed unmerged artifacts, not from issue numbering. #417 is the convergence/index owner after prerequisite artifact identities stabilize.

## Molecular Stack decomposition

```text
PR #412  ICPG contract/Shadow/Tech Lead ownership preparation [PARENT BY UNMERGED CONTRACT]
└─ K1 #414  Intent + Artifact projection contract
   ├─ K2 #415 implementation/Issue/Stack/AGENTS bridge     sibling or child only if K1 bytes consumed
   └─ K3 #416 traversal/authority/reverse-trace controls  sibling or child only if K1/K2 bytes consumed
      ↓ verified artifacts
   K4 #417 one documentation/system-prompt/index convergence owner

#418 live retrieval canary = EXTERNAL_EVIDENCE, no Stack paths unless a later repair issue is opened.
```

Terminal leaves must own disjoint paths or explicitly consume parent contracts. Documentation/index work does not silently absorb implementation paths.

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

## Evidence ceiling

Current program state at creation of this branch:

```text
Spatial ICPG contract/checker/routes              IMPLEMENTED_ON_PARENT_PR_412
Spatial Shadow/static prompt projection            IMPLEMENTED_ON_PARENT_PR_412
Tech Lead ICPG denominator/ownership gate          IMPLEMENTED_ON_PARENT_PR_412
Knowledge Graph issues #413–#418                  CREATED
Knowledge Graph AGENTS/README/SKILL/contracts     IMPLEMENTATION_IN_PROGRESS
Knowledge Graph deterministic schema/checker       NOT_IMPLEMENTED
Live GraphRAG multi-hop canary                      NOT_EXERCISED / #418
Live continuous Spatial Shadow                      NOT_EXERCISED / #411
merge/release/promotion                             HUMAN_ADMIT_REQUIRED
```

Do not lift these states based on documentation presence.
