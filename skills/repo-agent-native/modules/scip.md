# SCIP Module

## Trigger

Use when the task requires cross-file symbol identity, definition/reference edges, type relationships, or a bounded impact set and an admitted SCIP indexer can bind its output to the exact repository subject.

## Non-trigger

Do not use for a tiny known file, when the project cannot be type-checked far enough to produce a trustworthy index, when requested languages are outside the declared coverage, or as a substitute for current source read-back.

## Purpose

Produce compiler-derived, globally identified semantic candidates that can seed impact traversal and context assembly without relying on heuristic graph construction.

## Assumptions

```text
indexer source/version known
language frontend and configuration identified
exact repository commit/tree declared
index subject and coverage recorded
partial-index behavior understood
query depth and result budget bounded
```

## State machine

```text
SEMANTIC EDGE REQUESTED
→ INDEXER/PROJECT IDENTIFIED
→ SUBJECT + LANGUAGE COVERAGE VERIFIED
→ INDEX PARSED
→ SYMBOL/EDGE QUERY BOUNDED
→ ENDPOINT SOURCE READ BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
INDEXER_UNPINNED
WRONG_PROJECT
STALE_SUBJECT
PARTIAL_LANGUAGE_COVERAGE
TYPECHECK_DEGRADED
SYMBOL_AMBIGUOUS
EDGE_NOT_REPRODUCIBLE
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Exact repository/commit/tree, index identity, declared language and path coverage, seed symbols or source locations, relation kinds, traversal direction/depth, result budget, and source-readback policy.

## Outputs and effects

Subject-bound symbol IDs, definitions, references, type/implementation relations, optional caller/callee candidates, coverage warnings, and source locations. The module is read-only. It does not claim universal semantic completeness and cannot turn an index edge into source truth without read-back.

## Evidence class and freshness

SCIP output is compiler-derived `A-` candidate evidence only for the exact index subject and declared coverage. A relation may be promoted only after current source, manifest, test, or stronger execution evidence reproduces it. Missing language/indexer coverage lowers the ceiling; it is never silently treated as absence.

## Fallback

Use Serena or the repository's native LSP/compiler, `git grep`, `rg`, direct source reads, manifests, and targeted tests. Record which relation classes were no longer available.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source anchoring, evidence states, absence boundaries, effects, completion, and Human Admit.

## Consumer-owned values

Indexer binaries, language frontends, build configuration, cache/index paths, update cadence, coverage declarations, resource limits, and live receipts remain outside this shared module.
