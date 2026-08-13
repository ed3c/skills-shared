# Project memory module

## Trigger

Use when prior decisions, user preferences, incidents, rejected approaches, or cross-session continuity can help select what to inspect or which risk to test.

## Non-trigger

Do not use memory as repository SSOT, to override current source or ADRs, to store secrets/session material, or to auto-apply a remembered preference without current scope validation.

## Inputs

```text
current task and repository identity
user/project/session scope
provider identity and retention policy
allowed memory classes
freshness and provenance requirements
result budget
```

Concrete providers may use a dedicated Agent memory layer, a repository-owned decision store, or another scoped retrieval service.

## Process

1. Query only the relevant user/project/session scope.
2. Require provenance, timestamp, subject identity, and memory class when available.
3. Classify each result as preference, decision, incident, hypothesis, or execution note.
4. Revalidate decisions against current `CONTEXT.md`, ADRs, source, tests, issues, and receipts.
5. When memory conflicts with current authority, current authority wins and the conflict is reported.
6. Write back only admitted, bounded facts with provenance, retention/expiry, and no secrets. Durable project law belongs in repository documents, not memory alone.

## Outputs

```text
memory provider observation
retrieved hints with provenance/freshness
validation result per hint
memory conflicts and winning authority
optional bounded writeback proposal
```

## Evidence ceiling

Memory is a hint (`B+` at best) and never confirms current repository behavior. It can guide search or preserve an incident lead; source/document/runtime readback supplies the evidence.

## Fallback

Continue from repository documents, issue/PR history, source, tests, and receipts. Provider absence does not block source analysis unless the task explicitly requires a historical user preference that is unavailable elsewhere.

## Authoritative laws

The Core laws on memory being advisory, current-subject verification, secret boundaries, source references, and Human Admit remain authoritative.
