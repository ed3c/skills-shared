# mem0 Module

## Trigger

Use only when prior project decisions, incident history, user preferences, or task continuity can reduce rediscovery cost and the memory namespace/provenance policy is explicit.

## Non-trigger

Do not use for current repository truth, secrets, mutable credentials, live PR state, or when namespace/provenance/freshness cannot be established.

## Purpose

Retrieve a small provenance-bearing hint set that the core procedure verifies against current documents, source, tests, and receipts.

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

## Inputs

Exact project subject, bounded continuity question, namespace, maximum results, privacy policy, and current repository routes.

## Outputs and effects

Prior-decision/context hints with record identity, provenance, timestamp, privacy class, confidence, conflict state, and required readback. Default effect is read-only; memory never becomes implementation truth on its own.

## Fallback

Read current `AGENTS.md`, `CONTEXT.md`, ADRs, issues/PR receipts when available, source files, and deterministic tests.

## Evidence class and freshness

Memory is context candidate evidence. Any repository claim recalled from memory must be checked against current routed documents or source before it enters an accepted report.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source truth, evidence states, privacy boundaries, and completion.

## Consumer-owned values

Deployment, model/embedding keys, namespaces, retention/deletion policy, production writeback, personal data, and live receipts remain outside this shared module.
