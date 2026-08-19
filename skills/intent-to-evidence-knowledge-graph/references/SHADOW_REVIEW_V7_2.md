# Shadow Architect Review — Zettelkasten v7.2

Subject: `SYSTEM_PROMPT_V7_2.md`

## Review objective

Verify that v7.2 preserves the v7.1 knowledge-compilation baseline while adding a non-duplicative Intent-to-Evidence trace layer that composes Spatial Loop ICPG, Tech Lead ownership, Git Town Stack topology, AGENTS/README routing and exact evidence.

## Findings

### PASS — v7.1 baseline preserved

The prompt retains evidence-first compilation, source dependency awareness, epistemic separation, anti-fragmentation, action honesty, narrative richness, stable identity, typed links, idempotency and explicit completion states.

### PASS — full prompt is standalone

A fresh Agent can use `SYSTEM_PROMPT_V7_2.md` directly. It no longer needs to manually combine the v7.1 prompt with a delta file. `SYSTEM_PROMPT_V7_2_DELTA.md` is maintenance/history only, preventing two runtime prompt authorities.

### PASS — Intent is first-class without replacing source evidence

Implementation-oriented subjects require an Intent projection, but source evidence remains independently anchored. Issue/PR/source artifacts do not become substitutes for the desired outcome.

### PASS — ICPG remains canonical case authority

The prompt explicitly forbids a second exhaustive case denominator. It requires exact ICPG subject/digest/case IDs and treats missing ICPG as a knowledge gap rather than silently reconstructing case truth.

### PASS — delivery graph is not hidden in cards

Issue, Task, PR, Branch, Commit, File, AGENTS, README, SKILL, Test, Workflow, Receipt and Human Admit are Artifact Projection node classes with external identities and authority/freshness semantics.

### PASS — Git ancestry semantics protected

`SIBLING`, `TRUE_CHILD`, `CONVERGENCE`, `PROCESS_DEPENDENCY`, `EXTERNAL_EVIDENCE`, `HISTORICAL` are explicit topology relations. `TRUE_CHILD` requires an actual consumed unmerged artifact; issue order, semantic dependency and process order are insufficient.

### PASS — retrieval cannot escalate authority

The prompt states retrieval relevance is not execution authority and requires exact external readback for mutable decision-critical artifacts.

### PASS — evidence ceiling is explicit

L0–L5 is propagated across claims. PR merge, model agreement, prose or semantic relevance cannot upgrade live/runtime/delivery evidence.

### PASS — bidirectional trace required

Both `Intent → implementation → evidence` and `implementation → case/invariant → Intent` are hard requirements and quality gates.

### PASS — no graph-density objective

Every edge must support a declared decision, causal, implementation, authority, evidence, retrieval or contradiction use. Connectivity inflation is a failure mode.

### PASS — explicit denominator != unknown unknowns

The prompt forbids presenting frozen ICPG coverage as universal all-edge-case completeness; live Shadow/runtime/incident feedback remains the unknown-unknown discovery lane.

## Remaining deterministic risks

These are not prompt-design blockers; they belong to #414–#416 executable controls:

1. machine schema refs must be validated in the actual repository runtime;
2. checker must reject duplicate ICPG truth rather than relying only on prose;
3. stale mutable artifact detection needs deterministic fixtures;
4. false TRUE_CHILD and false serial sibling mutations must fail;
5. reverse-trace completeness needs a graph assertion;
6. authority precedence and evidence-ceiling laundering need executable negative controls;
7. Graph utility/no-connectivity-inflation needs a machine representation of edge purpose;
8. live #418 GraphRAG/Shadow quality remains NOT_EXERCISED.

## Stage verdict

```text
FULL_V7_2_SYSTEM_PROMPT                  PASS_AS_DESIGN_ARTIFACT
STANDALONE_PROMPT_PACKAGING              PASS_AS_DESIGN_ARTIFACT
V7_1_SEMANTIC_BASELINE                   PRESERVED
ICPG_NON_DUPLICATION                     SPECIFIED
INTENT_TO_EVIDENCE_TRACE                 SPECIFIED
AUTHORITY/FRESHNESS/EVIDENCE_CEILING     SPECIFIED
BIDIRECTIONAL_GRAPH_TRAVERSAL            SPECIFIED
DETERMINISTIC_CHECKER                    NOT_IMPLEMENTED
MUTATION_EXECUTION                       NOT_EXERCISED
LIVE_GRAPHRAG_SHADOW                     NOT_EXERCISED
HUMAN_ADMIT                              REQUIRED
```

The prompt-design stage is complete. The next Tech Lead frontier is executable checker/tests, not another prompt rewrite unless a deterministic control proves the current prompt contract insufficient.
