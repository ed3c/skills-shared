# Code-Graph-RAG Compatibility Retirement Adapter

## Trigger

Use only when reading a legacy consumer binding, historical eval, receipt, issue, or migration record that names `code-graph-rag` and the task must translate that record into the current Blindspot Hybrid contract.

## Non-trigger

Do not select this module for new repository analysis, architecture-impact work, provider installation, graph queries, or Agent execution. New work uses `blindspot-hybrid.md` with bounded grepai, SCIP, Tree-sitter, Serena, SQLite, optional LanceDB, source-readback, and test lanes.

## Purpose

Preserve audit compatibility without keeping Code-Graph-RAG in the active routing surface.

```text
legacy code-graph-rag record
→ bind immutable historical subject/provider identity
→ preserve original evidence ceiling and warnings
→ map only reproducible endpoints/relations to normalized blindspot events
→ current source read-back
→ targeted test when behavioral
→ SQLite ledger
→ retired record retained; no provider resurrection
```

This adapter is a tombstone, not a provider endorsement. It grants no permission to install Memgraph, mutate a graph, query a legacy endpoint, or treat old graph edges as current source truth.

## Assumptions

```text
historical artifact identity known
legacy repository/project/graph subject known when recorded
original bytes or content digest available
current replacement route known
migration is read-only and bounded
```

## State machine

```text
LEGACY REFERENCE OBSERVED
→ HISTORICAL SUBJECT BOUND
→ ORIGINAL CLAIM/EVIDENCE CEILING PRESERVED
→ REPRODUCIBLE ENDPOINTS IDENTIFIED
→ NORMALIZED CANDIDATE EVENTS
→ CURRENT SOURCE READ-BACK
→ ACCEPT / DOWNGRADE / RETIRE UNMAPPED
```

Failure states:

```text
LEGACY_ARTIFACT_ABSENT
HISTORICAL_SUBJECT_UNKNOWN
LEGACY_GRAPH_STALE
EDGE_NOT_REPRODUCIBLE
MIGRATION_WOULD_RAISE_EVIDENCE
PROVIDER_RESURRECTION_REQUESTED
```

## Inputs

Legacy artifact identity, historical subject/provider metadata when available, bounded claims/edges/paths, current exact subject, replacement blindspot event route, and read-back budget.

## Outputs and effects

A read-only migration ledger containing preserved legacy IDs, mapped candidate events, unmapped evidence, current source read-backs, downgrade reasons, and retirement state. No provider, container, graph database, vector database, endpoint, branch, or remote is created or mutated.

## Fallback

Keep the historical record as retired/unmapped and use current deterministic repository discovery, SCIP/Tree-sitter/Serena where admitted, source read-back, and tests.

## Evidence class and freshness

Legacy graph output keeps its original `B+` maximum and becomes stale when its exact graph/source subject cannot be reproduced. Migration never raises evidence. Only current source read-back and current targeted execution can support a new admitted claim.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative. `blindspot-hybrid.md` is the active replacement contract.

## Consumer-owned values

Historical containers, graph/vector stores, ports, credentials, indexes, provider endpoints, network policy, and retained live receipts remain outside this shared adapter.
