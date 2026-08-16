# SQLite Code Index Module

## Trigger

Use when subject-bound symbols, edges, tests, source ranges, and context-plan metadata need a small local projection that supports deterministic SQL and bounded graph traversal.

## Non-trigger

Do not use SQLite as a source of repository truth, as an unbounded global memory store, or when the database subject/freshness cannot be matched to the requested commit and tree.

## Purpose

Materialize a rebuildable, inspectable projection of normalized SCIP and Tree-sitter observations without introducing a second heuristic code graph.

## Assumptions

```text
schema version pinned
exact repository/commit/tree recorded
producer identities and coverage recorded
foreign keys and integrity checks enabled
projection rebuild path available
database path/effects admitted by the consumer
```

## State machine

```text
PROJECTION REQUESTED
→ SCHEMA/PRODUCERS IDENTIFIED
→ SUBJECT VERIFIED
→ TRANSACTIONAL INGEST
→ INTEGRITY + COVERAGE CHECKED
→ BOUNDED SQL/BFS QUERY
→ ENDPOINT SOURCE READ BACK
→ ACCEPT / REBUILD / FALLBACK
```

Failure states:

```text
SCHEMA_MISMATCH
SUBJECT_MISMATCH
PRODUCER_IDENTITY_ABSENT
STALE_PROJECTION
FOREIGN_KEY_VIOLATION
UNVERIFIED_EDGE
UNBOUNDED_QUERY
CORRUPT_DATABASE
SOURCE_CHANGED
```

## Inputs

Schema and producer identities, exact subject, normalized files/symbols/edges/tests/ranges, source-readback state, traversal limits, output budget, and explicit database destination.

## Outputs and effects

A rebuildable SQLite projection, integrity report, bounded impact candidates, associated tests, source-range references, and query receipt. The only write effect is the consumer-authorized projection file; it cannot mutate source, provider state, task state, or Human Admit.

## Evidence class and freshness

Rows inherit the lowest evidence ceiling of their producer and source-readback state. Database integrity is not semantic correctness. Every query receipt binds schema, producer, repository, commit, tree, coverage, and database digest.

## Fallback

Rebuild from current normalized observations, or use in-memory bounded maps/direct source reads. A missing or stale projection is `ABSENT`/`STALE_PROJECTION`, never PASS.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source anchoring, claim promotion, effects, completion, and rollback boundaries.

## Consumer-owned values

Database path, retention, encryption, cleanup, concurrency/locking policy, producer adapters, migrations, resource caps, and live receipts remain outside this module.
