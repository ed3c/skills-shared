# Blindspot Hybrid Module

## Trigger

Use when a brownfield task needs both fuzzy intent discovery and exact structural/semantic confirmation across more than one file, language boundary, or Agent branch, and the consumer can bind provider outputs to one immutable repository subject.

## Non-trigger

Do not load this composite for a tiny known file or symbol, when source read-back cannot be performed, when provider/index identity is unknown, or as a reason to install every provider. The portable core still works with Tier 0 repository tools only.

## Purpose

Compose bounded candidate lanes without collapsing their different evidence classes:

```text
grepai Intent Anchor
        ↓
SCIP indexed symbol/reference relations + Tree-sitter AST skeleton
        ↓
Serena symbol-aware Agent execution / runtime MCP exploration
        ↓
current source read-back + targeted tests
        ↓
SQLite authoritative observation/admission ledger
        ↓
optional LanceDB similarity projection, rebuildable from SQLite
```

`grepai` is not a replacement for SCIP or Tree-sitter. It finds plausible intent anchors and may be exposed as a bounded read-only MCP exploration surface to a Serena-backed Agent. SCIP confirms relations emitted by a language indexer for the pinned subject. Tree-sitter confirms structural shape and captures unsupported/error regions. Serena performs symbol-aware reads, diagnostics, and separately authorized edits. SQLite owns durable evidence state. LanceDB accelerates similarity recall but owns no truth.

## Assumptions

```text
exact repository/commit/tree subject known
provider executable/source identity known when a provider is used
SCIP index subject and language indexer known
Tree-sitter grammar/version known
Serena project and language backend healthy
SQLite path is consumer-owned and local/private by policy
LanceDB namespace, embedding model and rebuild policy known when enabled
source read-back and targeted-test routes available
```

## State machine

```text
QUESTION BOUND
→ INTENT ANCHORS
→ EXACT SEMANTIC RELATIONS
→ AST SKELETON / COVERAGE
→ SERENA SYMBOL EXECUTION
→ SOURCE READ-BACK
→ TEST / RUNTIME OBSERVATION WHEN REQUIRED
→ SQLITE LEDGER COMMIT
→ OPTIONAL LANCEDB PROJECTION
→ BLINDSPOT ASSERTION
    ├── PASS
    ├── SOURCE_READBACK_MISSING
    ├── AST_COVERAGE_MISSING
    ├── VECTOR_PROJECTION_ORPHAN
    ├── TEST_OBSERVATION_FAILED
    └── PROVIDER_SELF_ADMISSION
```

## Inputs

Immutable repository subject, bounded question, included/excluded paths, normalized provider events, provider/index/grammar/project identities, freshness observations, query/result budgets, read-back locations, tests/runtime observations, and consumer storage policy.

## Outputs and effects

The module emits candidate anchors/relations/AST nodes/symbol observations, direct source read-backs, test observations, a deterministic SQLite ledger, optional content-addressed LanceDB projection rows, and a blindspot report. The shared checker writes only the caller-selected SQLite/report paths. Provider invocation, index mutation, vector embedding, edit execution, network access, and MCP transport are consumer/runtime effects and remain outside this package.

## Evidence class and exactness boundary

| Lane | Maximum before read-back | Boundary |
|---|---:|---|
| grepai | `B+` candidate | intent/semantic recall only |
| SCIP | `A-` relation candidate | exact for emitted indexed symbol/reference records on the pinned subject; not whole-program behavior |
| Tree-sitter | `A-` structural candidate | exact parsed tree for admitted grammar/input; error nodes and unsupported semantics remain visible |
| Serena | `A-` symbol candidate | only when project/backend identity and current source read-back agree |
| source read-back | `A` source observation | repository-relative source on the exact subject |
| targeted test/runtime | `A+` behavioral observation | only for the exercised inputs/environment |
| LanceDB | `B` projection | similarity index; deletable and rebuildable, never admission authority |

No provider output self-admits. An accepted repository claim requires source read-back; a behavioral claim additionally requires a targeted test/runtime observation.

## Golden-loop storage law

```text
SQLite = authoritative normalized events, links, admission state, digests
LanceDB = optional vectors keyed to one existing non-vector SQLite event
```

Deleting or rebuilding LanceDB may change retrieval order but may not change admission results. A LanceDB row that points to a missing event, another LanceDB row, a different subject, or mutable provider state is a blindspot.

## Fallback

Use `git ls-files`, `git grep`/`rg`, direct reads, compiler/LSP diagnostics, language-native indexers, and targeted tests. If any optional provider is absent, keep the remaining lanes and record the missing capability; do not fabricate equivalent output.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for subject binding, source anchoring, negative claims, evidence ceilings, effect separation, repair bounds, Human Admit, and completion.

## Consumer-owned values

Install paths, container images, MCP endpoints, index/grammar/project paths, embedding models, databases, credentials, network rules, provider write authority, branch/Agent scheduling, live health, and receipts remain outside this module.
