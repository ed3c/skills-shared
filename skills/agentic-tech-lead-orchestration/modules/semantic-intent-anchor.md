# Semantic intent-anchor adapter

## Trigger

Use grepai when a natural-language requirement cannot yet be mapped to stable repository symbols by exact search.

## Non-trigger

Do not use semantic retrieval as a call graph, type oracle, absence proof, or accepted architecture fact.

## Purpose

Return a small ranked candidate seed set and optionally expose bounded search/trace commands to a Worker inside its sandbox.

## Assumptions

Provider/version, repository namespace, index subject, embedding identity, covered paths, privacy policy, query/result budget, and cleanup behavior are declared.

## State machine

```text
intent → provider health/freshness → bounded search → candidate seed
→ current-source readback → accept seed / downgrade / fallback
```

Failure states: `PROVIDER_ABSENT`, `WRONG_REPOSITORY`, `INDEX_STALE`, `EMBEDDING_DRIFT`, `COVERAGE_GAP`, `SECRET_SHAPED_RESULT`, `ZERO_RESULT_NOT_ABSENCE`.

## Inputs

Natural-language intent, optional exact terms, path/language scope, result cap, and source-readback requirement.

## Outputs and effects

Read-only candidate files/symbols/snippets with score, index subject, and provenance. No accepted impact edge is produced.

## Evidence class and freshness

Always candidate evidence until direct source readback; freshness is tied to the recorded index subject and embedding policy.

## Fallback

Use `git grep`, `rg`, tracked-file discovery, direct reads, and Human clarification.

## Core laws that remain authoritative

`../SKILL.md` owns Search-is-not-truth, source readback, context provenance, privacy, and evidence ceilings.

## Consumer-owned values

MCP configuration, daemon lifecycle, model/embedding endpoint, local paths, namespace, credentials, index, and live receipts remain consumer-owned.
