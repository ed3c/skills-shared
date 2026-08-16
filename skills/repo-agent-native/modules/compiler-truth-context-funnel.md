# Compiler-Truth Context Funnel Module

## Trigger

Use when a brownfield task begins as natural-language intent and needs a high-purity, exact-subject context bundle for planning, one Worker, or a bounded parallel fan-out.

## Non-trigger

Do not compose the funnel for a tiny known edit, when exact subject identity is absent, when source read-back is impossible, or merely because optional providers are installed.

## Purpose

Route fuzzy intent through deterministic evidence stages without duplicating graph stores:

```text
intent
→ optional grepai candidate seeds
→ direct source read-back
→ SCIP/Serena semantic relations
→ Tree-sitter ranges and skeletons
→ SQLite subject-bound projection
→ bounded context bundle + receipt
```

The name describes the preferred semantic lane, not a claim of universal compiler completeness.

## Assumptions

```text
one immutable repository/commit/tree subject
question and included/excluded scope declared
provider/index/grammar identities observable when used
source read-back mandatory before promotion
coverage and degradation states explicit
context and traversal budgets bounded
```

## State machine

```text
INTENT RECEIVED
→ EXACT SUBJECT + SCOPE LOCKED
→ CANDIDATE SEEDS DISCOVERED
→ SOURCE READ BACK
→ SEMANTIC EDGES EXPANDED
→ STRUCTURAL SLICES BUILT
→ SUBJECT-BOUND PROJECTION QUERIED
→ CONTEXT BUDGET APPLIED
→ RECEIPT + UNRESOLVED STATES EMITTED
```

Failure states:

```text
SUBJECT_ABSENT
INTENT_ANCHOR_AMBIGUOUS
SOURCE_READBACK_MISSING
SEMANTIC_COVERAGE_PARTIAL
STRUCTURAL_PARSE_DEGRADED
PROJECTION_SUBJECT_MISMATCH
CONTEXT_BUDGET_EXCEEDED
PROVIDER_CONTRADICTS_SOURCE
NO_DETERMINISTIC_FALLBACK
```

## Inputs

Exact subject and scope, natural-language question, deterministic search seeds, optional provider health, requested relation classes, traversal limits, context-class budgets, test-discovery policy, and named exclusions.

## Outputs and effects

A context bundle whose sections are typed as target full source, direct dependency skeletons, downstream call-site snippets, related tests, manifests/configuration, unresolved edges, coverage warnings, and producer/source references. Effects are read-only except an explicitly consumer-owned SQLite projection and receipt.

## Evidence class and freshness

The bundle carries per-item evidence; composition does not raise it. Intent/semantic results remain candidates until source read-back. Compiler-derived relations are limited to declared language/indexer coverage. Structural slices bind exact bytes. SQLite proves only projection integrity and subject identity.

## Fallback

Use `git ls-files`, `git grep`, `rg`, direct reads, repository compilers/LSPs and targeted tests. Emit a smaller bundle and explicit unavailable relation classes rather than silently substituting heuristic edges.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative. Optional providers cannot waive source read-back, absence boundaries, permission/effect limits, assertions, or Human Admit.

## Consumer-owned values

Provider/indexer/parser configuration, project routes, database/receipt paths, token budgets, model routing, worktrees, credentials, privacy policy, and live evidence remain outside this shared module.
