# Serena Module

## Trigger

Use when the task requires symbol identity, references, diagnostics, or symbol-aware edits and the configured Serena/LSP project matches the exact repository.

## Non-trigger

Do not use for a tiny known file, when project/language-server health is unknown, or as a substitute for source read-back.

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

## Inputs and outputs

Input: symbol/query intent, repository-relative scope, result budget.

Output: candidate declarations, references, diagnostics, or edit locations. These are structured candidates until source read-back confirms the relevant claim.

## Fallback

Use `git grep`, `rg`, direct reads, the host compiler/LSP, and deterministic tests.

## Evidence boundary

Serena/LSP evidence is `A-` only when structured relation and source read-back agree. Without read-back it is a candidate lane, not source truth.

## Core laws

`../SKILL.md` remains authoritative for source anchoring, effects, permissions, repair bounds, and completion.