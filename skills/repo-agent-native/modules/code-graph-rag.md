# Code-Graph-RAG Module

## Trigger

Use when the task needs cross-language dependency, call/data-flow, architecture-impact, or hidden-coupling analysis that exact search and symbol operations cannot answer efficiently.

## Non-trigger

Do not start a graph stack for a small local scope, when graph freshness/project identity is unknown, or when source read-back cannot be performed.

## Purpose

Return provenance-carrying graph paths and impact candidates for direct source, test, and manifest readback.

## Assumptions

```text
graph provider/version known
exact repository/project selected
graph build subject identified
freshness checked against current source
query budget bounded
```

## State machine

```text
GRAPH ANALYSIS REQUESTED
→ PROVIDER/GRAPH IDENTIFIED
→ SUBJECT/FRESHNESS CHECKED
→ QUERY BOUNDED
→ EDGES/PATHS RETURNED
→ ENDPOINT SOURCE READ BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
WRONG_PROJECT
GRAPH_ABSENT
GRAPH_STALE
INCOMPLETE_GRAPH
SOURCE_CHANGED
EDGE_NOT_REPRODUCIBLE
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Exact subject, seed symbols/files, relation/data-flow question, edge kinds, direction/depth limits, language scope, result budget, and freshness observation.

## Outputs and effects

Bounded candidate nodes, edges, paths, impact sets, source provenance, graph identity, completeness warnings, and next readback actions. Effects are read-only. A graph edge is never an accepted invariant until its relevant endpoints and relations are checked against current source or a stronger runtime control.

## Fallback

Use `git`, `rg`, direct reads, symbol/LSP analysis, compiler diagnostics, and targeted tests.

## Evidence class and freshness

Graph output is `B+` candidate evidence. Freshness plus source read-back may upgrade specific relations; graph query success alone is not PASS.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source anchoring, evidence, effects, repair bounds, and completion.

## Consumer-owned values

Containers, graph/vector databases, ports, credentials, indexes, mutation endpoints, network policy, and live provider receipts remain outside this shared module.
