# Tool Routing

The procedural core works with deterministic source tools alone. Optional tools are selected by capability and health, not by installation popularity.

## Routing order

```text
Tier 0  git + rg + repository-relative direct read
Tier 1  semantic candidate search
Tier 2  symbol/LSP/AST analysis
Tier 3  graph/data-flow analysis
Tier M  episodic/project memory
Tier X  compiler/tests/public-port/runtime controls
```

Tier X is not a later truth level; it is the behavioral lane used when the claim concerns executable behavior.

## Tool health state machine

```text
CAPABILITY REQUESTED
→ PROVIDER DISCOVERED
→ EXACT PROVIDER IDENTITY RECORDED
→ PROJECT/INDEX/GRAPH/NAMESPACE MATCHED
→ FRESHNESS AND SCOPE CHECKED
→ QUERY EXECUTED
→ RESULT READ BACK AGAINST SOURCE
→ RESULT ACCEPTED OR DOWNGRADED
```

Failure states:

```text
PROVIDER_ABSENT
PROVIDER_UNREACHABLE
WRONG_PROJECT
STALE_INDEX
INCOMPLETE_GRAPH
UNSUPPORTED_LANGUAGE
NAMESPACE_MISMATCH
SOURCE_CHANGED
RESULT_CONTRADICTS_SOURCE
OUTPUT_LIMIT
```

Every failure has a named Tier 0 fallback unless the task specifically requires the missing capability.

## Current candidate providers

| Capability | Current candidate | Strength | Cost/risk | Default role |
|---|---|---|---|---|
| semantic search/call hints | grepai | local semantic search, watcher, MCP | embedding/index freshness; call hints require read-back | optional candidate lane |
| symbol/refactor/diagnostics | Serena LSP backend | broad language support, symbol operations, diagnostics | project/language-server health; overlapping basic tools | preferred optional symbol lane |
| graph/data flow | Code-Graph-RAG | Tree-sitter, Memgraph, structural/data-flow graph | heavier Docker/database/runtime footprint | optional deep graph lane |
| lightweight graph alternative | codebase-memory-mcp | single-binary persistent graph candidate | requires independent accuracy/security eval | A/B competitor |
| lightweight semantic alternative | Semble | focused agent code search candidate | requires independent recall/precision eval | A/B competitor |
| episodic/personal memory | mem0 OSS | user/session/agent memory and SDKs | LLM/embedding cost, privacy, conflicts; hosted claims may exceed OSS | optional memory lane |
| temporal relational memory | Graphiti | real-time knowledge graph memory | different operational model; not a drop-in personal memory store | A/B competitor |

## Commercial exclusion

GitNexus is not admitted for the commercial core while the upstream repository is licensed under PolyForm Noncommercial. Repository popularity does not override license policy.

## grepai module trigger

Use when intent-based discovery can reduce candidate search cost and a current index for the exact repository is healthy. Do not use its result as an accepted fact without direct source read-back.

## Serena module trigger

Use when symbol identity, references, diagnostics, or a symbol-aware edit is needed and the configured project/language backend matches the exact repository. Disable overlapping basic shell/file tools when the host already owns them.

## Graph module trigger

Use when a task genuinely requires cross-language dependency, data-flow, dead-code, or architectural graph analysis that Tier 0/Tier 2 cannot answer efficiently. Do not start a heavyweight graph stack for a small local scope.

## Memory module trigger

Use only for prior decisions, preferences, incident history, or task continuity. Retrieve a bounded number of records and verify any repository claim against current documents/source. Production writes require explicit policy and are outside the offline Skill eval.

## Tool receipt

A run records:

```text
provider and version/commit when known
capability requested
project/index/graph/namespace identity
freshness observation
query budget
result count
source read-back count
fallback taken
warnings and exclusions
```

Provider presence and query success are not source-truth PASS.
