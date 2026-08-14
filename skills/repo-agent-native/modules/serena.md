# Serena Module

## Trigger

Use when the task requires symbol identity, references, diagnostics, or symbol-aware edits and the configured Serena/LSP project matches the exact repository.

## Non-trigger

Do not use for a tiny known file, when project/language-server health is unknown, or as a substitute for source read-back.

## Purpose

Produce bounded symbol/reference candidates and diagnostics while keeping edits and truth admission under the host and core procedure.

## Assumptions

```text
provider identity known
exact project selected
language backend healthy
workspace/source revision matched
requested operation is supported
```

## State machine

```text
SYMBOL CAPABILITY REQUESTED
→ PROVIDER/PROJECT IDENTIFIED
→ LANGUAGE HEALTH CHECKED
→ SYMBOL QUERY BOUNDED
→ CANDIDATES RETURNED
→ CURRENT SOURCE READ BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
WRONG_PROJECT
UNSUPPORTED_LANGUAGE
LANGUAGE_SERVER_UNHEALTHY
SYMBOL_AMBIGUOUS
SOURCE_CHANGED
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Exact subject, symbol/query intent, repository-relative scope, read-only or edit-planning mode, diagnostics budget, and provider-health observation.

## Outputs and effects

Candidate declarations, references, diagnostics, or an edit proposal with source locations. Default effect is read-only; an edit requires separate host authority and source readback.

## Fallback

Use `git grep`, `rg`, direct reads, the host compiler/LSP, and deterministic tests.

## Evidence class and freshness

Serena/LSP evidence is `A-` only when structured relation and source read-back agree. Without read-back it is a candidate lane, not source truth.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source anchoring, effects, permissions, repair bounds, and completion.

## Consumer-owned values

Project onboarding, Serena configuration, language servers, disabled tools, edit permissions, credentials, and live health remain outside this shared module.
