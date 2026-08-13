# mem0 Module

## Trigger

Use only when prior project decisions, incident history, user preferences, or task continuity can reduce rediscovery cost and the memory namespace/provenance policy is explicit.

## Non-trigger

Do not use for current repository truth, secrets, mutable credentials, live PR state, or when namespace/provenance/freshness cannot be established.

## Assumptions

```text
provider identity known
namespace and subject matched
privacy policy admitted
provenance and timestamp available
retrieval budget bounded
```

## State machine

```text
MEMORY CONTEXT REQUESTED
→ PROVIDER/NAMESPACE IDENTIFIED
→ PRIVACY/FRESHNESS CHECKED
→ RETRIEVAL BOUNDED
→ CANDIDATES RETURNED
→ CURRENT DOCUMENT/SOURCE CHECK
→ ACCEPT AS CONTEXT / DOWNGRADE / DISCARD
```

Failure states:

```text
PROVIDER_ABSENT
NAMESPACE_MISMATCH
PROVENANCE_ABSENT
STALE_MEMORY
PRIVACY_POLICY_ABSENT
MEMORY_CONFLICTS_WITH_SOURCE
SOURCE_CHANGED
```

## Inputs and outputs

Input: bounded continuity question and repository/task identity.

Output: prior-decision/context candidates with provenance and timestamps. Memory never becomes implementation truth on its own.

## Fallback

Read current `AGENTS.md`, `CONTEXT.md`, ADRs, issues/PR receipts when available, source files, and deterministic tests.

## Evidence boundary

Memory is context candidate evidence. Any repository claim recalled from memory must be checked against current routed documents or source before it enters an accepted report.

## Core laws

`../SKILL.md` remains authoritative for source truth, evidence states, privacy boundaries, and completion.