# `intent-to-evidence-knowledge-graph`

Portable semantic-projection and traceability method for connecting human-readable knowledge cards to the canonical Spatial Loop Intent–Case–Proof Graph (ICPG), Tech Lead task ownership, Git Town Molecular Stack delivery, governed Agent documentation and exact-subject evidence.

This Skill does not replace Spatial Loop, Tech Lead, Git Town, GitHub/Git, verifiers or receipts. It composes their identities into an authority-aware graph so a human or GraphRAG query can traverse `why → what must remain true → who owns it → where it landed → what proves it` without inventing a second source of truth.

## Read order

1. `AGENTS.md`
2. `SKILL.md`
3. `references/SYSTEM_PROMPT_V7_2.md` — canonical complete Zettelkasten v7.2 prompt
4. `references/SHADOW_REVIEW_V7_2.md`
5. `references/TRACE_GRAPH_CONTRACT.md`
6. `references/intent-projection.schema.json`
7. `references/artifact-projection.schema.json`
8. `references/trace-graph.schema.json`
9. `scripts/check_trace_graph.py`
10. `tests/run-all.sh` and `tests/mutation_proof.py`
11. `references/IMPLEMENTATION_PREFLIGHT.md`
12. `references/NEGATIVE_CONTROL_MATRIX.md`
13. Spatial Loop ICPG reference/schema/checker
14. Tech Lead case obligations/task DAG
15. Git Town Molecular Stack index
16. exact current external artifact subjects and receipts before current-state decisions

`references/SYSTEM_PROMPT_V7_2_DELTA.md` is maintenance/history only. Fresh Agents route directly to `SYSTEM_PROMPT_V7_2.md`.

## Directory map → runtime ownership

```text
skills/intent-to-evidence-knowledge-graph/
├── AGENTS.md
│   └── read order, authority/freshness/evidence stop rules
├── README.md
│   └── State Machine, DAG, data flow, Stack ownership and evidence ceiling
├── SKILL.md
│   └── portable graph laws + canonical prompt route
├── references/
│   ├── SYSTEM_PROMPT_V7_2.md
│   ├── SHADOW_REVIEW_V7_2.md
│   ├── TRACE_GRAPH_CONTRACT.md
│   ├── intent-projection.schema.json
│   ├── artifact-projection.schema.json
│   ├── trace-graph.schema.json
│   ├── IMPLEMENTATION_PREFLIGHT.md
│   └── NEGATIVE_CONTROL_MATRIX.md
├── scripts/
│   └── check_trace_graph.py
│       ├── Draft 2020-12 schema gates
│       ├── Intent↔ICPG digest/case subset checks
│       ├── external artifact identity checks
│       ├── mutable authority-snapshot freshness checks
│       ├── authority-class checks
│       └── evidence-ceiling anti-laundering checks
└── tests/
    ├── run-all.sh
    ├── mutation_proof.py
    ├── build_exact_head_fixture.py
    └── fixtures/
        ├── valid-trace-graph.json
        └── authority-snapshot.json

.github/workflows/intent-to-evidence-knowledge-graph.yml
└── dedicated exact-head deterministic CI arrival + replayable receipt upload
```

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
→ DETERMINISTIC_CHECKER_IMPLEMENTED
→ #414_MUTATION_CONTROLS_IMPLEMENTED
→ EXACT_HEAD_CI_ROUTE_IMPLEMENTED
→ WAIT_EXACT_HEAD_RECEIPT
→ #415/#416_TERMINAL_LEAVES
→ #417_CONVERGENCE
→ #418_LIVE_RETRIEVAL_NOT_EXERCISED
→ HUMAN_ADMIT_REQUIRED
```

Failure states include duplicate case truth, fabricated artifact identity, stale mutable state, false Git ancestry, orphan implementation, broken reverse trace, authority inversion, evidence laundering, unresolved blocking case, connectivity inflation and divergent prompt authority.

## Graph layers and authority

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

Semantic relations never create Git ancestry. Retrieval relevance never grants execution authority.

## Tech Lead + Issue DAG

```text
#407 ICPG program
└─ #408/#409/#410 deterministic ICPG + monitor + Tech Lead ownership preparation
   └─ PR #412 ICPG implementation candidate
      └─ #413 Knowledge Graph integration program
         └─ PR #419 portable method + trace contract
            └─ PR #420 #414 machine contracts + complete v7.2 prompt
               ├─ #438 deterministic checker + #414 mutation subset
               ├─ #437 dedicated exact-head CI arrival
               ├─ #439 exact-head receipt publication after real run
               ├─ #415 case→task→issue→Stack/document binding
               ├─ #416 authority-aware traversal + reverse trace
               └─ #417 one final routing/index convergence owner

#411 live continuous Spatial Shadow       EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
#418 live multi-hop GraphRAG/Shadow canary EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

`#438`, `#437`, and `#439` are work/evidence ownership for #414; they do not create new semantic graph authority. #415/#416 become Git children only if they consume unmerged parent bytes. Issue order alone never creates ancestry.

## Molecular Stack decomposition

```text
PR #412 ICPG contract/Shadow/Tech Lead ownership preparation
└─ PR #419 KG-C1/D1 portable Knowledge Graph contract
   └─ PR #420 KG-C2/P1 #414 machine schemas + v7.2 prompt
      ├─ KG-E1 #438 checker + executable #414 mutations       [same PR leaf currently]
      ├─ KG-CI #437 exact-head deterministic arrival          [evidence route]
      ├─ KG-R1 #439 exact-head receipt                         [evidence route]
      ├─ KG-K1/E2 #415 case→task/issue→Stack/AGENTS binding   [future terminal leaf]
      ├─ KG-K2/E3 #416 traversal/authority/reverse trace      [future terminal leaf]
      └─ KG-D2/X1 #417 one convergence owner

#418 live retrieval canary = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY.
```

The current #438 implementation stays inside PR #420 because it is still #414 scope and directly modifies the same machine-contract leaf. A new Git child is unnecessary until a later task has an independent review/ownership boundary.

## End-to-end data flow

```text
Article / PDF / code / issue / prompt
→ evidence-constrained semantic cards
→ Intent projection
→ canonical Spatial Loop ICPG read
→ exact ICPG digest + admitted case IDs
→ Tech Lead case_obligations + task/issue ownership
→ Git Town Molecular Stack atoms
→ branch/commit/file/AGENTS/README/SKILL projections
→ oracle/test/workflow/receipt projections
→ deterministic schema + semantic gate
→ authority snapshot freshness check
→ evidence-ceiling propagation
→ bidirectional traversal index
→ GraphRAG query
→ refresh mutable external artifacts before decision use
→ answer with exact authority/evidence ceiling
→ Shadow review
→ Human Admit for promotion/merge/release
```

## Deterministic #414 gate

`check_trace_graph.py` exits:

```text
0   PASS
2   BLOCK — contract/semantic violation
64  INPUT_ERROR — invalid/missing runtime contract input
```

Current executable mutation subset:

```text
NC-01 duplicate ICPG authority       → DUPLICATE_ICPG_AUTHORITY
NC-02 stale mutable PR               → STALE_MUTABLE_SUBJECT
NC-03 prose over receipt             → PROSE_OVER_RECEIPT
NC-17 fabricated artifact identity   → FABRICATED_ARTIFACT_IDENTITY
```

The broader NC-04…NC-16 matrix remains owned by #415/#416/#417/#418 as documented in `NEGATIVE_CONTROL_MATRIX.md`.

## Exact-head deterministic arrival

`.github/workflows/intent-to-evidence-knowledge-graph.yml` is dedicated to this Skill and checks out:

```text
${{ github.event.pull_request.head.sha || github.sha }}
```

On a non-draft PR it runs `tests/run-all.sh`, binds repository/ref/PR/head into a generated projection fixture, requires `receipt.subject.sha == expected PR head`, and uploads the generated evidence directory.

A workflow definition or skipped draft job is not PASS. #439 closes only after a real runner executes the current head with non-empty steps.

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

Root docs and #417 convergence route here; they must not fork a second decision-active prompt.

## Shadow Architect current verdict

```text
FULL_V7_2_SYSTEM_PROMPT                  PASS_AS_DESIGN_ARTIFACT
STANDALONE_PROMPT_PACKAGING              PASS_AS_DESIGN_ARTIFACT
V7_1_SEMANTIC_BASELINE                   PRESERVED
ICPG_NON_DUPLICATION                     SPECIFIED + NC-01 EXECUTABLE
INTENT_TO_EVIDENCE_TRACE                 SPECIFIED
AUTHORITY/FRESHNESS/EVIDENCE_CEILING     PARTIALLY_EXECUTABLE_IN_#414
ARTIFACT_IDENTITY                        EXECUTABLE_IN_#414
DETERMINISTIC_CHECKER                    IMPLEMENTED_ON_PR_420
#414_MUTATION_SUBSET                     IMPLEMENTED_ON_PR_420
EXACT_HEAD_CI_ROUTE                      IMPLEMENTED_ON_PR_420
EXACT_HEAD_RECEIPT                       PENDING_REAL_RUN / #439
LIVE_GRAPHRAG_SHADOW                     NOT_EXERCISED / #418
HUMAN_ADMIT                              REQUIRED
```

Implementation presence is not exact-head execution evidence.

## Evidence ceiling

```text
Spatial ICPG contract/checker/routes              IMPLEMENTED_ON_PARENT_PR_412
Spatial Shadow/static prompt projection            IMPLEMENTED_ON_PARENT_PR_412
Tech Lead ICPG denominator/ownership gate          IMPLEMENTED_ON_PARENT_PR_412
Knowledge Graph portable method/trace contract     IMPLEMENTED_ON_PR_419
Complete Zettelkasten v7.2 system prompt           IMPLEMENTED_ON_PR_420
Intent/Artifact/Trace machine schemas              IMPLEMENTED_ON_PR_420
Deterministic #414 checker                          IMPLEMENTED_ON_PR_420
NC-01/02/03/17 executable mutation code            IMPLEMENTED_ON_PR_420
Dedicated exact-head CI route                      IMPLEMENTED_ON_PR_420
Local hermetic authoring check                      PASS_FOR_AUTHORED_BYTES; NOT_GITHUB_HEAD_EVIDENCE
GitHub exact-head deterministic receipt             PENDING / #439
#415 delivery/reverse-trace controls                NOT_IMPLEMENTED
#416 traversal/authority controls                   NOT_IMPLEMENTED
#417 convergence                                    PLANNED
#418 live GraphRAG multi-hop canary                  NOT_EXERCISED
#411 live continuous Spatial Shadow                  NOT_EXERCISED
merge/release/promotion                              HUMAN_ADMIT_REQUIRED
```

## Next frontier

```text
mark PR #420 ready for one exact-head run
→ inspect real job steps + uploaded receipt
→ close #437/#438/#439 and parent #414 only if current head passes
→ freeze #414 artifacts
→ decompose #415/#416 from actual consumed bytes
→ #417 convergence
→ #418 live GraphRAG/Shadow canary
→ Human Admit
```
