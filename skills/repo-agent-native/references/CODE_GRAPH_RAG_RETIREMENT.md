# Code-Graph-RAG retirement decision

## Decision

`code-graph-rag` is removed from the active `repo-agent-native` provider surface. It is not a required module, routing target, context producer, CI dependency, or fallback.

The replacement is a single evidence funnel:

```text
grepai or deterministic search   candidate intent anchors
current source read-back         promotion boundary
SCIP / Serena / native LSP       subject-bound semantic candidates
Tree-sitter                      exact-byte structure and skeletons
SQLite                           rebuildable normalized projection
compiler-truth-context-funnel    bounded context assembly
```

## Why

A second heuristic graph duplicates symbol/edge indexing while carrying a lower and less explicit semantic ceiling. Two competing graphs create freshness, coverage, reconciliation, storage, CI-time, and prompt-authority ambiguity. The active path instead keeps one normalized projection whose producers and coverage are explicit.

## What is not claimed

- SCIP is not universally complete; language/indexer/build coverage is recorded.
- Tree-sitter does not provide cross-file type truth.
- SQLite integrity does not prove semantic correctness.
- grepai search success does not prove a repository fact.
- the funnel does not replace current source, tests, manifests, runtime receipts, or Human Admit.

## Historical references

Git history and consumer decision records may retain the old name so prior receipts remain interpretable. Historical mention is not activation. A provider manifest may be retained as `REJECTED` when a consumer needs an auditable decision trail.

## Re-admission rule

Re-admission requires a new governance issue showing a non-duplicated capability, exact subject and coverage, independent same-subject evaluation, source read-back, bounded resources, cleanup, commercial/license admission, and a reason the deterministic funnel cannot satisfy the task. Popularity or installation alone is insufficient.
