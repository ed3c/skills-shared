# Serena Symbol-Aware Agent Executor Module

## Trigger

Use when a task requires symbol identity, references, diagnostics, bounded symbol-aware edits, or runtime MCP exploration after an intent anchor has narrowed the scope, and the configured Serena project/language backend matches the exact repository.

## Non-trigger

Do not use for a tiny known file, when project/language-server health is unknown, as a replacement for grepai intent discovery, SCIP indexed relations, Tree-sitter AST coverage, current source read-back, or behavioral tests.

## Purpose

Act as the symbol-aware Agent execution lane inside the Blindspot Hybrid loop.

```text
grepai intent anchor
→ SCIP relation candidates + Tree-sitter structural skeleton
→ Serena symbol read / diagnostics / edit proposal / bounded execution observation
→ current source read-back
→ targeted test/runtime observation
→ SQLite ledger
```

Serena may consume bounded grepai MCP exploration results, but it does not inherit their evidence level. Each symbol operation records its own project/backend/subject identity and required read-back.

## Assumptions

```text
provider identity known
exact Serena project selected
language backend healthy
workspace/source revision matched
requested operation is supported
MCP/tool allowlist and effect boundary known
edit authority separately granted when needed
```

## State machine

```text
SYMBOL CAPABILITY REQUESTED
→ PROVIDER/PROJECT IDENTIFIED
→ LANGUAGE HEALTH CHECKED
→ INPUT ANCHORS/RELATIONS BOUND
→ SYMBOL QUERY OR EDIT PROPOSAL BOUNDED
→ CANDIDATES / DIAGNOSTICS / PROPOSAL
→ CURRENT SOURCE READ-BACK
→ TARGETED TEST WHEN BEHAVIORAL
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
PROVIDER_ABSENT
WRONG_PROJECT
UNSUPPORTED_LANGUAGE
LANGUAGE_SERVER_UNHEALTHY
SYMBOL_AMBIGUOUS
MCP_TOOL_NOT_ALLOWLISTED
EDIT_AUTHORITY_ABSENT
SOURCE_CHANGED
AST_COVERAGE_MISSING
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Exact subject, intent anchors, optional SCIP relations/Tree-sitter skeleton, symbol/query intent, repository-relative scope, read-only or edit-planning mode, diagnostics/effect budget, provider health, and runtime MCP policy.

## Outputs and effects

Candidate declarations, references, diagnostics, edit proposals, or bounded execution observations with source locations and provider identity. Default effect is read-only. An edit or execution effect requires separate host authority, path lease, source read-back, targeted verification, and receipt. This shared module does not spawn an Agent, start MCP, or mutate a project.

## Fallback

Use `git grep`, `rg`, direct reads, SCIP/language-native indexes, Tree-sitter/compiler/LSP diagnostics, and deterministic tests.

## Evidence class and freshness

Serena evidence is `A-` only when structured relation, exact project/backend subject, and current source read-back agree. Edit proposals and execution observations additionally require AST/path coverage and targeted verification. Without those controls it remains a candidate lane.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative. `blindspot-hybrid.md` owns composite lane ordering and storage/admission law.

## Consumer-owned values

Project onboarding, Serena configuration, language servers, disabled/enabled tools, MCP transport, edit permissions, credentials, Agent runtime, live health, and receipts remain outside this shared module.
