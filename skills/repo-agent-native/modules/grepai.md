# grepai Module

## Trigger

Use when the task asks for concept/intent-oriented code discovery, exact text search is producing too much noise, and grepai has a healthy index for the exact repository.

## Non-trigger

Do not use for a tiny known file/symbol, when the index identity/freshness cannot be established, or as source-truth evidence.

## Assumptions

```text
grepai executable/source identity known
exact repository/workspace selected
index exists
watcher/index freshness checked
embedding provider boundary known
network/privacy policy admitted
```

## State machine

```text
SEMANTIC DISCOVERY REQUESTED
→ EXECUTABLE/PROJECT IDENTIFIED
→ INDEX HEALTH CHECKED
→ QUERY BOUNDED
→ CANDIDATES RETURNED
→ CURRENT SOURCE READ BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
WRONG_WORKSPACE
INDEX_ABSENT
INDEX_STALE
EMBEDDING_PROVIDER_UNAVAILABLE
RESULT_SOURCE_MISSING
RESULT_CONTRADICTS_SOURCE
```

## Inputs and outputs

Input: natural-language query, bounded repository scope, result budget.

Output: candidate repository-relative paths/symbols and optional call hints. The module does not output accepted invariants directly.

## Fallback

Use `git ls-files`, `git grep`, `rg`, direct file reads, and the host compiler/LSP/tests.

## Evidence boundary

grepai is a `B+` candidate lane. Upgrade only after current source read-back. Record index/project identity and source-readback count.

## Core laws

`../SKILL.md` remains authoritative for source anchoring, negative invariants, evidence states, permissions, and completion.
