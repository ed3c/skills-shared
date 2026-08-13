# Semantic retrieval module

## Trigger

Use when exact identifiers are unknown, naming is inconsistent, the codebase is large, or meaning-based candidates can reduce the deterministic search space.

## Non-trigger

Do not use semantic retrieval to prove absence, to replace direct source readback, or when the index subject/freshness cannot be established.

## Inputs

```text
natural-language intent
repository scope
provider identity and version from consumer binding
index subject, included paths, and freshness observation
result budget
```

Concrete providers may include local semantic-search or embedding-backed code indexes. Product choice remains consumer-owned.

## Process

1. Verify provider health, repository identity, indexed path scope, embedding/index version, and freshness.
2. Query for a small candidate set.
3. Record score/rank only as retrieval metadata, not truth confidence.
4. Re-open each load-bearing candidate from current repository bytes.
5. Cross-check callers, configuration, tests, and negative paths using deterministic search or symbol tools.

## Outputs

```text
provider observation
query
ranked candidate paths/symbols
index subject/freshness
readback actions
unresolved candidates
```

## Evidence ceiling

An unread semantic hit is `B+` and remains a candidate. It may become `A` only after the relevant current source body is read; an empty result never proves absence.

## Fallback

Use file listing, exact search, regular expressions, and direct source read. Record `CAPABILITY_UNHEALTHY` or the provider-specific absence without blocking the zero-index procedure unless the task explicitly requires semantic coverage.

## Authoritative laws

The Core laws on candidates, absence boundaries, source references, provider fallbacks, and evidence ceilings remain authoritative.
