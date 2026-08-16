# Tool Routing

The procedural core works with deterministic source tools alone. Optional tools are selected by capability, exact subject, health, and budget—not by installation popularity.

## Routing order

```text
Tier 0  git + rg + repository-relative direct read
Tier I  grepai Intent Anchor / fuzzy semantic discovery
Tier S  SCIP indexed symbol-reference relations
Tier A  Tree-sitter AST skeleton and structural slicing
Tier E  Serena symbol-aware Agent execution / diagnostics
Tier L  SQLite authoritative ledger + optional LanceDB projection
Tier M  episodic/project memory
Tier X  compiler/tests/public-port/runtime controls
```

These are lanes, not a ladder where a later provider automatically has higher truth. Tier X is used whenever the claim concerns executable behavior. Current source read-back is mandatory before a source claim is admitted.

## Tool health state machine

```text
CAPABILITY REQUESTED
→ PROVIDER/INDEX/GRAMMAR/PROJECT DISCOVERED
→ EXACT IDENTITY RECORDED
→ REPOSITORY SUBJECT MATCHED
→ FRESHNESS / SCOPE / PRIVACY CHECKED
→ BOUNDED QUERY
→ NORMALIZED CANDIDATE EVENTS
→ CURRENT SOURCE READ-BACK
→ TARGETED EXECUTION WHEN BEHAVIORAL
→ SQLITE ADMISSION / DOWNGRADE
→ OPTIONAL LANCEDB PROJECTION
```

Failure states:

```text
PROVIDER_ABSENT
PROVIDER_UNREACHABLE
WRONG_PROJECT
WRONG_INDEX_SUBJECT
STALE_INDEX
UNSUPPORTED_LANGUAGE
GRAMMAR_ERROR_REGION
NAMESPACE_MISMATCH
SOURCE_CHANGED
RESULT_CONTRADICTS_SOURCE
OUTPUT_LIMIT
PROVIDER_SELF_ADMISSION
VECTOR_PROJECTION_ORPHAN
```

Every optional-provider failure has a named Tier 0 fallback unless the task specifically requires that missing capability.

## Current candidate providers and mechanisms

| Capability | Candidate | Maximum pre-readback | Default role |
|---|---|---:|---|
| fuzzy intent discovery/call hints | grepai | `B+` | Intent Anchor; optional bounded runtime MCP exploration |
| indexed declarations/references/implementations | SCIP + language indexer | `A-` | exact emitted relations for the pinned indexed subject; not runtime truth |
| AST shape/slicing/error coverage | Tree-sitter + grammar | `A-` | structural skeleton and unsupported/error-region visibility |
| symbol operations/diagnostics/edits | Serena backend | `A-` | symbol-aware Agent executor; effect authority remains separate |
| durable normalized observation/admission | SQLite | ledger authority | authoritative subject-bound event/link/admission store |
| similarity recall | LanceDB | `B` projection | disposable projection keyed to SQLite observation IDs |
| episodic/personal memory | mem0 OSS | memory candidate | prior decisions/preferences; never current source truth |
| behavioral observation | compiler/tests/runtime | task-bound `A+` | only for exercised subject, inputs, and environment |

## Code-Graph-RAG retirement

Code-Graph-RAG is not an active provider route. `modules/code-graph-rag.md` remains only as a compatibility retirement adapter for historical artifacts. New graph/impact questions use the Blindspot Hybrid composition: grepai for intent anchors, SCIP for indexed relations, Tree-sitter for structure, Serena for symbol execution, source read-back/tests for admission, SQLite for authority, and optional LanceDB for recall.

## Commercial exclusion

GitNexus remains excluded from the commercial core while its upstream license is noncommercial. Popularity does not override license policy.

## Lane triggers

### grepai

Use when the question is conceptual and the location is unknown. Do not use it as an accepted fact or as a substitute for SCIP/Tree-sitter.

### SCIP

Use when declarations/references/implementations or cross-file symbol relations are required and an indexer has produced a subject-matched SCIP index. Record language/indexer and uncovered languages.

### Tree-sitter

Use when AST shape, structural slicing, edit boundaries, or unsupported/error-node coverage matters. Record grammar identity and error regions.

### Serena

Use when symbol identity, references, diagnostics, or separately authorized symbol-aware edits/execution are needed. A runtime may expose bounded grepai MCP exploration to Serena, but the evidence classes remain separate.

### SQLite/LanceDB

SQLite stores normalized observations, links, admissions, and digests. LanceDB is optional and rebuildable. A vector row must point to an existing non-vector SQLite event and may not alter admission.

### Memory

Use only for prior decisions, preferences, incident history, or continuity. Verify repository claims against current documents/source.

## Tool receipt

A run records:

```text
provider/mechanism and version/commit when known
capability requested
repository commit/tree
project/index/grammar/namespace identity
freshness observation
query budget and result count
normalized event IDs
source read-back count
test/runtime observation count
SQLite ledger digest
LanceDB projection digest when enabled
fallback taken
warnings and uncovered languages/paths
```

Provider presence, query success, a parsed AST, a vector hit, or a model statement is not source-truth PASS.
