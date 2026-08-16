# Vector-store adapter

## Trigger

Use LanceDB when reusable AST chunks, examples, documents, or prior source slices need local semantic retrieval beyond the immediate task packet.

## Non-trigger

Do not use vector rows as source truth, graph authority, type truth, absence proof, task state, or durable decision authority.

## Purpose

Store provenance-carrying chunks keyed to repository subject and optional SCIP symbol identifiers.

## Assumptions

Table/schema version, embedding identity, dimension, source subject, chunker policy, covered paths, retention, privacy, and cleanup are declared.

## State machine

```text
source slice → provenance/digest → embedding → LanceDB row
→ bounded query → candidate → source readback → accept / drift / discard
```

Failure states: `TABLE_ABSENT`, `SCHEMA_DRIFT`, `EMBEDDING_DRIFT`, `SUBJECT_DRIFT`, `CHUNK_DRIFT`, `CROSS_REPOSITORY_LEAK`, `READBACK_FAILED`.

## Inputs

Subject-bound chunks and query, filters, result cap, and readback policy.

## Outputs and effects

Candidate rows with source path/range/digest/symbol and score. Writes are optional cache/projection effects.

## Evidence class and freshness

Candidate evidence only; stale rows remain `DRIFTED`, not matches.

## Fallback

Use grepai or deterministic exact search/direct reads without vector persistence.

## Core laws that remain authoritative

`../SKILL.md` owns source authority, evidence states, no absence from misses, privacy, and context provenance.

## Consumer-owned values

Database path, embedding service, retention, encryption, schema migration, backup, credentials, and receipts remain consumer-owned.
