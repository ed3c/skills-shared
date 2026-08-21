# 卡片盒記憶法知識編譯器 v7.2 — Intent-to-Evidence Graph Delta

Apply these additions to v7.1 without weakening Evidence-First, anti-fragmentation, narrative richness, action honesty or source-dependency rules.

## New Runtime fields

```text
ICPG_BRIDGE: REQUIRED_FOR_IMPLEMENTATION_TASKS
ARTIFACT_PROJECTION: ON
AUTHORITY_AWARE_RETRIEVAL: ON
FRESHNESS_CHECK: BEFORE_DECISION_USE
EVIDENCE_CEILING_PROPAGATION: ON
BIDIRECTIONAL_TRACE: REQUIRED
CONNECTIVITY_POLICY: DECISION_RELEVANT_ONLY
```

## New first-class projection: I | Intent

Intent is not an Issue and not a Source. It records the desired outcome that gives implementation artifacts their decision meaning.

Required payload:

```text
Problem
Desired Outcome
Why It Matters
Non-Goals
Invariants
Acceptance Criteria
Prohibited Outcomes
Human Authority Boundary
ICPG Subject
ICPG Digest
Projected Case IDs
Current Closure Ceiling
```

For implementation-oriented work, `Projected Case IDs` must reference the canonical Spatial Loop ICPG. The compiler must not independently enumerate a competing case denominator.

## Artifact Projection

Execution artifacts are first-class graph nodes but remain projections of external authority.

Supported types:

```text
ISSUE TASK PR BRANCH COMMIT FILE AGENTS README SKILL
SCHEMA SCRIPT TEST WORKFLOW RECEIPT SHADOW_VERDICT HUMAN_ADMIT
```

Minimum visible payload when decision-relevant:

```text
Artifact Type
External Identity
Authority Class
Mutable/Immutable
Observed Version
Freshness State
Current Execution/Evidence State
Why It Exists (Intent/Case links)
What It Realizes/Protects
```

Do not copy entire GitHub/Git artifact bodies into cards when an exact external identity is sufficient.

## New Invariants

### I-17 | Intent Is a First-Class Root
Implementation-oriented knowledge must trace to an Intent. Source documents and Issues are not substitutes for the desired outcome.

### I-18 | Knowledge Graph != Delivery Graph
Semantic cards, ICPG cases, Issues, PRs, branches, files and receipts are different node classes. Do not hide a delivery graph inside one D Card.

### I-19 | ICPG Is the Canonical Case Authority
When Spatial Loop ICPG exists, reference exact graph digest/case IDs. Do not create a second exhaustive edge-case graph inside the card compiler.

### I-20 | Execution Edge Semantics Are Exact
Preserve `SIBLING`, `TRUE_CHILD`, `CONVERGENCE`, `PROCESS_DEPENDENCY`, `EXTERNAL_EVIDENCE`, `HISTORICAL`. Generic semantic `DEPENDS_ON` must not create Git ancestry.

### I-21 | Authority-Aware Retrieval
Retrieval relevance never grants execution authority. Markdown/card claims cannot override exact Git/GitHub/verifier/receipt truth for the same subject.

### I-22 | Evidence Ceiling Propagation
The reported closure state cannot exceed the minimum required proof layer across the traversed claim. Never average or narratively upgrade proof layers.

### I-23 | Mutable Artifact Freshness
Issue/PR/open-head/workflow/governing-doc state must be refreshed before decision-grade use. Historical snapshots remain historical until rebound.

### I-24 | No Connectivity Inflation
Every graph edge must support a causal, implementation, authority, evidence, contradiction or declared retrieval traversal. Do not increase link density for its own sake.

### I-25 | Bidirectional Trace Completeness
Implementation-oriented subjects require both `Intent → implementation → evidence` and `implementation → case/invariant → Intent` paths.

## New Typed Links

Add:

```text
TRACKED_BY
OWNS_CASE
REALIZED_BY
TOUCHES
DOCUMENTED_BY
PROTECTS_CASE
DOCUMENTS_INVARIANT
ROUTED_BY
GOVERNED_BY
VERIFIED_BY
PRODUCES
CONSUMES
BLOCKED_BY
UNBLOCKS
ROLLS_BACK_TO
CURRENT_VERSION_OF
HISTORICAL_VERSION_OF
```

Execution topology links remain exact enums and are not interchangeable with semantic links:

```text
SIBLING
TRUE_CHILD
CONVERGENCE
PROCESS_DEPENDENCY
EXTERNAL_EVIDENCE
HISTORICAL
```

## New Compile Phase between Semantic Modeling and Action Compilation

```text
Phase 3.5 | Intent / ICPG / Artifact Trace Binding

1. Decide whether the task is implementation-oriented.
2. Bind/create Intent projection.
3. If an ICPG exists, bind exact subject/digest/case IDs.
4. Project relevant Issues/Tasks/PRs/branches/files/docs/evidence artifacts.
5. Classify authority and mutability.
6. Build forward and reverse trace paths.
7. Reject false Git ancestry and duplicate case truth.
8. Mark mutable artifacts stale until refreshed for decision use.
9. Propagate evidence ceiling.
```

## New GraphRAG Traversal Contracts

```text
Concept/Narrative
→ Intent
→ ICPG Case
→ Invariant
→ Task/Issue
→ Stack PR
→ File/AGENTS/README
→ Oracle
→ Receipt

File/PR
→ Task/Issue
→ ICPG Case
→ Invariant
→ Intent
→ Narrative/Concept

UNKNOWN_BLOCKING Case
→ owning task/issue
→ blocked Stack/convergence
→ blocked Intent closure

target path
→ nearest AGENTS
→ parent/root route
→ Skill
→ current issue/PR
→ exact ICPG/evidence subject
```

## New Quality Gates

```text
QG-25 Intent Traceability
QG-26 ICPG Projection Integrity
QG-27 Delivery Graph Integrity
QG-28 Artifact Authority Integrity
QG-29 Freshness Integrity
QG-30 Evidence Ceiling Integrity
QG-31 Bidirectional Trace Integrity
QG-32 Multi-hop Route Integrity
QG-33 Graph Utility / No Connectivity Inflation
```

Hard failures include fabricated artifact identities, stale decision-critical projections, duplicate ICPG case truth, false Git ancestry, implementation without Intent/Case lineage, missing reverse trace and prose-over-receipt authority inversion.

## Completion Contract additions

For implementation-oriented runs, `DONE` additionally requires:

```text
intent_unmapped = 0
required_case_projection_gaps = 0
implementation_subjects_without_case_lineage = 0
claimed_complete_requirements_without_exact_evidence = 0
stale_decision_critical_artifacts = 0
false_execution_edges = 0
bidirectional_trace_failures = 0
```

ICPG coverage remains lane-specific and must not be collapsed into one percentage. Live GraphRAG retrieval quality, continuous Shadow execution, production safety and unknown-unknown discovery remain separate evidence lanes.
