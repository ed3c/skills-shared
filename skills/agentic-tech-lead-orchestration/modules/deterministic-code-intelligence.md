# Deterministic code-intelligence adapter

## Trigger

Use when task decomposition, impact analysis, or context slicing requires cross-file symbol relations and structural source boundaries.

## Non-trigger

Do not claim exact impact when the SCIP index subject, indexer identity, build policy, language coverage, or current-source readback is absent. Do not build a second code-graph-rag graph.

## Purpose

Combine SCIP Def/Ref/type/call candidates with SQLite subject and edge storage, then use Tree-sitter for AST/CST boundaries, skeletons, snippets, and syntax validation.

## Assumptions

The consumer declares exact commit/tree, indexer and version, build/config digest, covered languages/paths, unsupported constructs, SQLite schema version, Tree-sitter grammar identities, and freshness observation.

## State machine

```text
subject → index identity → coverage → SCIP ingest → SQLite normalize
→ seed traversal → source readback → Tree-sitter slice → EXACT | DEGRADED | BLOCKED
```

Failure states: `INDEX_ABSENT`, `INDEX_SUBJECT_MISMATCH`, `INDEX_STALE`, `COVERAGE_UNKNOWN`, `UNSUPPORTED_LANGUAGE`, `EDGE_NOT_REPRODUCIBLE`, `GRAMMAR_ABSENT`, `PARSE_ERROR`, `SCHEMA_DRIFT`.

## Inputs

Seed symbols/files, relation kinds, depth/result budgets, required tests, and context-slicing policy.

## Outputs and effects

Read-only normalized nodes/edges, coverage warnings, related tests, and provenance-carrying source slices. Persistent SQLite writes are consumer-controlled cache/projection effects.

## Evidence class and freshness

`EXACT` is allowed only for the recorded subject and covered constructs after readback. Partial or unsupported regions are `DEGRADED` or `BLOCKED`; they cannot prove absence.

## Fallback

Use Git, exact search, direct reads, compiler/LSP diagnostics, and targeted tests. Report the reduced evidence ceiling.

## Core laws that remain authoritative

`../SKILL.md` owns evidence states, no-double-graph, bounded traversal, Worker limits, and Human boundaries.

## Consumer-owned values

Indexer commands, compilers, grammars, database paths, schemas, caches, generated-code policy, credentials, runtime receipts, and cleanup remain consumer-owned.
