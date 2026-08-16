# grepai Intent Anchor Module

## Trigger

Use when a task begins with an architectural or behavioral intent rather than a known file/symbol, exact text search is noisy, and grepai has a healthy index for the exact repository. A consumer may also expose the same bounded read-only search/call-hint surface through MCP while a Serena-backed Agent is executing.

## Non-trigger

Do not use for a tiny known file or symbol, when workspace/index/freshness/embedding identity cannot be established, as a replacement for SCIP or Tree-sitter, or as source-truth evidence.

## Purpose

Return bounded fuzzy intent anchors that seed exact semantic, structural, symbol, source-readback, and test lanes.

```text
natural-language intent
→ grepai path/symbol anchors and optional call hints
→ SCIP relations + Tree-sitter AST skeleton
→ Serena symbol read/diagnostic/edit planning
→ current source read-back
→ targeted test when behavioral
```

`grepai` answers “where should the exact investigation start?” It does not answer “which indexed relation is exact?”, “what is the AST shape?”, or “did the behavior execute correctly?”

## Assumptions

```text
grepai executable/source identity known
exact repository/workspace selected
index exists and subject/freshness are observed
embedding provider/model boundary known
network/privacy policy admitted
MCP transport and tool allowlist known when exposed at runtime
query/result budget bounded
```

## State machine

```text
INTENT UNKNOWN
→ EXECUTABLE/WORKSPACE IDENTIFIED
→ INDEX HEALTH/FRESHNESS CHECKED
→ BOUNDED INTENT QUERY
→ ANCHORS / CALL HINTS
→ EXACT LANE HANDOFF
→ CURRENT SOURCE READ-BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
WRONG_WORKSPACE
INDEX_ABSENT
INDEX_STALE
EMBEDDING_PROVIDER_UNAVAILABLE
MCP_TOOL_NOT_ALLOWLISTED
RESULT_SOURCE_MISSING
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Natural-language intent, exact subject identity, bounded paths/exclusions, result budget, provider/index health, embedding/privacy boundary, and runtime MCP policy when applicable.

## Outputs and effects

Candidate repository-relative paths/symbols, intent labels, indexed subject/freshness, optional call hints, and the required next exact/readback action. Default effect is read-only. Index updates, embeddings, MCP transport, network access, and provider lifecycle are consumer/runtime effects and are not performed by this module.

## Fallback

Use `git ls-files`, `git grep`, `rg`, direct reads, compiler/LSP/SCIP/Tree-sitter routes, and targeted tests.

## Evidence class and freshness

grepai remains a `B+` candidate lane. Source read-back is mandatory before a repository claim is admitted. Call hints remain candidates until exact relations and source endpoints are checked.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative. `blindspot-hybrid.md` owns the composite golden-loop contract.

## Consumer-owned values

Install path, command/transport, index location, embedding model, credentials, network policy, MCP tool names/permissions, live health, and index update/delete authority remain outside this module.
