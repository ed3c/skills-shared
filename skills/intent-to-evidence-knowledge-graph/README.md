# `intent-to-evidence-knowledge-graph`

Portable semantic-projection and traceability method for connecting human-readable knowledge cards to the canonical Spatial Loop Intent–Case–Proof Graph (ICPG), Tech Lead task ownership, Git Town Molecular Stack delivery, governed Agent documentation and exact-subject evidence.

This Skill does not replace Spatial Loop, Tech Lead, Git Town, GitHub/Git, verifiers or receipts. It composes their identities into an authority-aware graph so a human or GraphRAG query can traverse `why → what must remain true → who owns it → where it landed → what proves it` without inventing a second source of truth.

## Read order

1. `AGENTS.md`
2. `SKILL.md`
3. `references/SYSTEM_PROMPT_V7_2.md` — canonical complete Zettelkasten v7.2 prompt
4. `references/SHADOW_REVIEW_V7_2.md`
5. `references/TRACE_GRAPH_CONTRACT.md`
6. `references/intent-projection.schema.json`, `artifact-projection.schema.json`, `trace-graph.schema.json`
7. `scripts/check_trace_graph.py`
8. `references/case-delivery-binding.schema.json`
9. `scripts/check_case_delivery_binding.py`
10. `tests/run-all.sh`, `tests/mutation_proof.py`, `tests/delivery_binding_mutation_proof.py`
11. `references/IMPLEMENTATION_PREFLIGHT.md`
12. `references/NEGATIVE_CONTROL_MATRIX.md`
13. Spatial Loop ICPG reference/schema/checker
14. Tech Lead `case_obligations` task contract/checker
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
│   ├── case-delivery-binding.schema.json
│   ├── IMPLEMENTATION_PREFLIGHT.md
│   └── NEGATIVE_CONTROL_MATRIX.md
├── scripts/
│   ├── check_trace_graph.py
│   │   └── projection / authority / freshness / evidence-ceiling gate
│   └── check_case_delivery_binding.py
│       └── canonical case denominator → task/issue/Stack/doc ownership gate
└── tests/
    ├── run-all.sh
    ├── mutation_proof.py
    ├── delivery_binding_mutation_proof.py
    ├── build_exact_head_fixture.py
    ├── build_exact_head_delivery_fixture.py
    └── fixtures/
        ├── valid-trace-graph.json
        ├── authority-snapshot.json
        ├── delivery-task-contract.json
        ├── valid-case-delivery-binding.json
        └── delivery-trace-graph.json

.github/workflows/intent-to-evidence-knowledge-graph.yml
└── dedicated exact-head deterministic CI arrival + replayable receipts
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
→ #414_PROJECTION_GATE_ASSERTED
→ TECH_LEAD_CASE_OBLIGATIONS_BOUND
→ REQUIRED_CASE_DENOMINATOR_FROZEN
→ CASE_TO_TASK_BRANCH_OWNER_ASSERTED
→ ISSUE_AND_STACK_NODE_BOUND
→ PATH_LEASES_ASSERTED
→ GOVERNED_DOCUMENTS_BOUND
→ IMPLEMENTATION_REVERSE_TRACE_ASSERTED
→ ONE_CONVERGENCE_OWNER_ASSERTED
→ #415_DELIVERY_BINDING_GATE_ASSERTED
→ BIDIRECTIONAL_TRAVERSAL_READY_FOR_#416
→ #417_CONVERGENCE
→ #418_LIVE_RETRIEVAL_NOT_EXERCISED
→ HUMAN_ADMIT_REQUIRED
```

Failure states include duplicate case truth, fabricated artifact identity, stale mutable state, false Git ancestry, false serial dependency, duplicate/unowned case, path-lease overlap, missing convergence owner, orphan implementation, broken reverse trace, missing governed-document route, authority inversion, evidence laundering, unresolved blocking case, connectivity inflation and divergent prompt authority.

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
        │ exact case_obligations
        ▼
Tech Lead Task / Issue DAG                [EXECUTION OWNERSHIP]
required case denominator → branch owner → path lease → one convergence owner
        │ delivery binding
        ▼
Git Town Molecular Stack                  [DELIVERY TOPOLOGY]
SIBLING / TRUE_CHILD / CONVERGENCE / PROCESS_DEPENDENCY /
EXTERNAL_EVIDENCE / HISTORICAL
        │ touches / protects / documents / verifies
        ▼
Repository Artifact Graph
AGENTS / README / SKILL / schema / code / test / workflow
        │ exact-subject proof
        ▼
Evidence Graph                            [TRUTH CEILING]
verifier → workflow → receipt → Shadow verdict → Human Admit
```

Semantic relations never create Git ancestry. Issue order never creates Git ancestry. Retrieval relevance never grants execution authority.

## Tech Lead + Issue DAG

```text
#407 ICPG program
└─ #408/#409/#410 deterministic ICPG + monitor + Tech Lead ownership preparation
   └─ PR #412 ICPG implementation candidate
      └─ #413 Knowledge Graph integration program
         └─ PR #419 portable method + trace contract
            └─ PR #420 #414 machine contracts + complete v7.2 prompt
               ├─ #437/#438/#439 exact-head #414 deterministic evidence [CLOSED]
               └─ #415 case→task→issue→Stack/document binding
                  └─ PR #450 TRUE_CHILD of PR #420
                     ├─ #448 exact-head #415 receipt lane
                     └─ #449 durable docs / Git Town index convergence

#416 authority-aware traversal + reverse-trace/evidence gate
#417 one final routing/index convergence owner
#411 live continuous Spatial Shadow       EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
#418 live multi-hop GraphRAG/Shadow canary EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

#416 is not automatically a child of #449. It becomes a Git child of the machine leaf whose unmerged contracts it actually consumes. Issue order is not ancestry.

## Molecular Stack decomposition

```text
PR #412 ICPG contract/Shadow/Tech Lead ownership preparation
└─ PR #419 KG-C1/D1 portable Knowledge Graph contract
   └─ PR #420 KG-C2/P1 #414 projection contracts + v7.2 prompt
      └─ PR #450 KG-K1/E2 #415 case-delivery binding [TRUE_CHILD]
         ├─ #448 exact-head receipt                 [EVIDENCE]
         └─ #449 docs/index child                   [CONVERGENCE]

#416 future traversal leaf should branch from the exact machine parent it consumes.
#417 final program convergence remains separate.
#418 live retrieval canary = EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY.
```

PR #450 is a `TRUE_CHILD` because it consumes the unmerged Intent/Artifact/Trace projection contracts and deterministic checker from PR #420. The relation is caused by artifact consumption, not by issue numbering.

## End-to-end data flow

```text
Article / PDF / code / issue / prompt
→ evidence-constrained semantic cards
→ Intent projection
→ canonical Spatial Loop ICPG read
→ exact ICPG digest + admitted case IDs
→ Tech Lead case_obligations
→ frozen required-case denominator
→ exactly one branch owner per required case
→ Issue identity + path lease
→ Git Town Stack relation with provided/consumed artifacts
→ branch/commit/file/AGENTS/README/SKILL projections
→ case/invariant reverse trace
→ one convergence owner
→ deterministic #414 + #415 gates
→ exact-head workflow receipts
→ #416 authority/freshness/traversal gate
→ GraphRAG query
→ refresh mutable external artifacts before decision use
→ Shadow review
→ Human Admit for promotion/merge/release
```

## Deterministic #414 projection gate

`check_trace_graph.py` exits:

```text
0   PASS
2   BLOCK
64  INPUT_ERROR
```

Executable controls:

```text
NC-01 duplicate ICPG authority       → DUPLICATE_ICPG_AUTHORITY
NC-02 stale mutable PR               → STALE_MUTABLE_SUBJECT
NC-03 prose over receipt             → PROSE_OVER_RECEIPT
NC-17 fabricated artifact identity   → FABRICATED_ARTIFACT_IDENTITY
```

#414 is closed at its deterministic evidence lane. The immutable evidence details live on #414/#437/#438/#439; mutable PR state must still be refreshed before current-state decisions.

## Deterministic #415 delivery-binding gate

`check_case_delivery_binding.py` consumes three independent inputs rather than trusting one self-describing graph:

```text
case-delivery binding candidate
+ canonical Tech Lead task-contract/v1
+ Intent-to-Evidence Trace Graph
→ deterministic ownership/Stack/reverse-trace verdict
```

It verifies:

- task contract digest and task identity;
- `case_obligations.case_graph_ref` + SHA-256 binding;
- exact required-case denominator;
- exactly one branch owner per required case;
- no unknown/unowned case;
- exact Tech Lead branch and write-lease binding;
- issue ownership for each branch;
- one convergence owner;
- `TRUE_CHILD`/`CONVERGENCE` consumed artifacts come from the declared parent;
- `SIBLING` does not consume parent artifacts;
- parallel path leases are disjoint;
- bound ArtifactProjections exist and reverse-trace to the exact Intent + case;
- governed AGENTS/README/SKILL projections expose a protection/document-routing edge;
- implementation-oriented artifacts are not orphaned from case ownership.

Executable controls:

```text
NC-04              → FALSE_GIT_ANCESTRY
NC-05              → FALSE_SERIAL_DEPENDENCY
NC-06              → CASE_UNOWNED
NC-07              → REVERSE_TRACE_INCOMPLETE
CASE-DUPLICATE     → DUPLICATE_CASE_OWNER
CASE-CONVERGENCE   → MISSING_CONVERGENCE_OWNER
PATH-OVERLAP       → PATH_LEASE_OVERLAP
```

The exact-head receipt is owned by #448. A repository-wide workflow failure on the same head remains a blocker even if this dedicated gate is green.

## Exact-head deterministic arrival

`.github/workflows/intent-to-evidence-knowledge-graph.yml` checks out the exact PR head, runs the #414 and #415 positive/mutation gates, binds repository/ref/head/authority observation time, and uploads the evidence directory.

A workflow definition, skipped draft job, stale receipt or dedicated PASS beside a repository-wide FAIL is not enough for stage closure.

## Standard traversal contracts

### Why → implementation → proof

```text
Narrative/Concept
→ Intent
→ ICPG Case
→ Invariant
→ Tech Lead task/branch owner
→ Issue
→ Stack PR
→ File/AGENTS/README
→ Oracle
→ Receipt
```

### Implementation → why

```text
File/PR
→ owned case binding
→ Tech Lead task/issue
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
V7_1_SEMANTIC_BASELINE                   PRESERVED
ICPG_NON_DUPLICATION                     #414 DETERMINISTICALLY GUARDED
PROJECTION_AUTHORITY/FRESHNESS            #414 DETERMINISTICALLY GUARDED
CASE_DENOMINATOR/BRANCH_OWNERSHIP          #415 IMPLEMENTED
STACK_ARTIFACT_CONSUMPTION                #415 IMPLEMENTED
DOCUMENT→CASE / IMPLEMENTATION→INTENT      #415 IMPLEMENTED
#415_EXACT_HEAD_DEDICATED_GATE             EXERCISED; CURRENT-HEAD RECHECK REQUIRED AFTER DOC ROUTING PATCH
REPOSITORY_DOCUMENT_ROUTING                REPAIRED; CURRENT-HEAD WORKFLOWS MUST CONFIRM
#416_TRAVERSAL/AUTHORITY_GRAPH             NOT_IMPLEMENTED
#418_LIVE_GRAPHRAG_SHADOW                  NOT_EXERCISED
HUMAN_ADMIT                                REQUIRED
```

Implementation presence is not exact-head execution evidence. Current-state workflow conclusions are read from GitHub authority, not this README.

## Evidence ceiling

```text
Spatial ICPG contract/checker/routes              IMPLEMENTED_ON_PARENT_PR_412
Spatial Shadow/static prompt projection            IMPLEMENTED_ON_PARENT_PR_412
Tech Lead ICPG denominator/ownership gate          IMPLEMENTED_ON_PARENT_PR_412
Knowledge Graph portable method/trace contract     IMPLEMENTED_ON_PR_419
Complete Zettelkasten v7.2 system prompt           IMPLEMENTED_ON_PR_420
#414 projection schemas/checker/mutations          DETERMINISTIC_EXACT_HEAD_EVIDENCE_RECORDED
#415 case-delivery schema/checker/mutations        IMPLEMENTED_ON_PR_450
#415 dedicated exact-head evidence                 EXERCISED_ON_PRIOR_HEAD; RECHECK_CURRENT_HEAD
repository-wide route/guard contract               RECHECK_CURRENT_HEAD
#449 durable Git Town/docs convergence             PLANNED
#416 traversal/authority controls                  NOT_IMPLEMENTED
#417 global convergence                            PLANNED
#418 live GraphRAG multi-hop canary                NOT_EXERCISED
#411 live continuous Spatial Shadow                NOT_EXERCISED
merge/release/promotion                            HUMAN_ADMIT_REQUIRED
```

## Next frontier

```text
re-run current PR #450 head through:
  Intent-to-Evidence exact-head gate
  Shared Skills Infra
  Skill Eval Contract
→ require all relevant gates terminal green
→ #448 evidence closure
→ freeze PR #450 machine/docs bytes
→ #449 Git Town canonical index child
→ decompose #416 from actual consumed #415 bytes, sibling to #449 unless it consumes #449 docs
→ #417 convergence
→ #418 live GraphRAG/Shadow canary
→ Human Admit
```
