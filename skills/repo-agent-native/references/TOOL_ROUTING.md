# Tool Routing

The procedural core works with deterministic source tools alone. Optional tools are selected by capability, exact subject and health—not installation popularity.

## Routing order

```text
Tier 0  git + rg + repository-relative direct read
Tier 1  semantic intent candidates
Tier 2a interactive symbol/LSP diagnostics
Tier 2b compiler-derived semantic index
Tier 3  syntax structure and skeletonization
Tier 4  subject-bound normalized projection
Tier M  episodic/project memory
Tier X  compiler/tests/public-port/runtime controls
```

Tier X is a behavioral evidence lane, not a later retrieval tier.

## Tool health state machine

```text
CAPABILITY REQUESTED
→ PRODUCER/PROVIDER DISCOVERED
→ EXACT IDENTITY RECORDED
→ PROJECT + SUBJECT + COVERAGE MATCHED
→ FRESHNESS/SCOPE CHECKED
→ QUERY/PARSE EXECUTED
→ RESULT READ BACK AGAINST SOURCE
→ RESULT ACCEPTED OR DOWNGRADED
```

Failure states:

```text
PROVIDER_ABSENT
PROVIDER_UNREACHABLE
WRONG_PROJECT
STALE_SUBJECT
PARTIAL_LANGUAGE_COVERAGE
UNSUPPORTED_LANGUAGE
NAMESPACE_MISMATCH
SOURCE_CHANGED
RESULT_CONTRADICTS_SOURCE
OUTPUT_LIMIT
```

Every failure has a Tier-0 fallback unless the task specifically requires the missing relation class.

## Current capability routes

| Capability | Current route | Strength | Cost/risk | Default role |
|---|---|---|---|---|
| semantic intent search | grepai | local concept search, watcher, MCP | embedding/index freshness; negative results incomplete | optional seed lane |
| interactive symbols/diagnostics | Serena/LSP | definitions, references, diagnostics, edit planning | project/server health and language variance | optional interactive lane |
| compiler semantic relations | SCIP indexers | stable global symbols, Def/Ref/type edges | build/config/language coverage; batch index cost | preferred impact-edge lane when healthy |
| syntax/skeletons | Tree-sitter | tolerant AST/CST ranges and structural queries | no cross-file type inference | structural slicing lane |
| normalized graph/projection | SQLite | embedded, inspectable, transactional, rebuildable | schema/subject/producer drift | deterministic storage/query lane |
| episodic context | mem0 or admitted memory provider | prior decisions and incident context | privacy, freshness and conflicts | optional memory lane |

The composed route is [`../modules/compiler-truth-context-funnel.md`](../modules/compiler-truth-context-funnel.md). The Code-Graph-RAG retirement decision is [`CODE_GRAPH_RAG_RETIREMENT.md`](CODE_GRAPH_RAG_RETIREMENT.md).

## Selection rules

### grepai

Use to turn fuzzy intent into a small candidate set. Record exact workspace/index identity, cap results, and read every promoted result from current source.

### Serena

Use for interactive symbol/reference/diagnostic operations when the exact project and language backend are healthy. Treat edit output as a proposal unless the host separately grants mutation authority.

### SCIP

Use for compiler-derived cross-file relations when the exact commit/tree, indexer and language/path coverage are known. Do not describe partial coverage as 100% completeness.

### Tree-sitter

Use for exact-byte ranges, signatures, imports, snippets and skeletons. Do not infer type identity or runtime behavior from syntax alone.

### SQLite

Use only as a subject-bound projection of normalized observations. Database integrity proves the projection shape, not repository semantics. Refuse subject mismatch and rebuild stale stores.

### Memory

Use only for prior decisions, preferences, incident history or continuity. Current repository authority wins conflicts; writes require a separate policy.

## Commercial exclusion

GitNexus is not admitted for the commercial core while the upstream repository is licensed under PolyForm Noncommercial. Popularity does not override license policy.

## Tool receipt

A run records:

```text
producer/provider version or commit
capability requested
repository/commit/tree
project/index/grammar/schema identity
language and path coverage
freshness observation
query/depth/byte budget
result count
source read-back count
fallback taken
warnings and exclusions
```

Provider presence, query success, parse success and database integrity are not source-truth PASS.
