# repo-agent-native Modules

`modules/` contains optional tool or domain instances. The portable procedure remains in `../SKILL.md`; stable cross-domain reference material belongs in `../references/`.

## Module contract

Every module must state:

```text
Trigger
Non-trigger
Purpose
Assumptions
Required repository/document routes
Required capability and provider identity
Inputs
Outputs and effects
Evidence class and freshness
Fallback
Core laws that remain authoritative
Consumer-owned values
```

## Module selection state machine

```text
TASK RECEIVED
→ PORTABLE SKILL TRIGGER MATCHED
→ MODULE CANDIDATES DISCOVERED
→ MODULE TRIGGERS EVALUATED
    ├── none required → CORE ONLY
    ├── exactly one primary + compatible helpers → LOAD BOUNDED SET
    └── conflicting primary modules → BLOCK
→ ASSUMPTIONS/HEALTH VERIFIED
→ BOUNDED MODULE CONTEXT LOADED
→ CORE PROCEDURE CONTINUES
→ MODULE AND CORE EVIDENCE RECORDED
```

Failure states:

```text
MODULE_TRIGGER_AMBIGUOUS
MODULE_ASSUMPTION_ABSENT
MODULE_LAW_OVERRIDE
MODULE_CONTEXT_STALE
MODULE_CONTEXT_TOO_LARGE
PROVIDER_IDENTITY_ABSENT
SECRET_OR_SESSION_EXPOSURE
NO_FALLBACK
```

## Current files and intended classification

| File | Current role | Migration decision |
|---|---|---|
| `extraction-methodology.md` | stable cross-domain method | candidate to move to `references/` in the portable-core child PR |
| `codebase-mastery-methodology.md` | optional deep analysis mode | retain as an explicit domain/mode module with trigger |
| `specs-as-code-prompt.md` | optional output/prompt instance | retain as an explicit module or template; do not preload |
| `grepai.md` | planned provider module | child PR |
| `serena.md` | planned provider module | child PR |
| `code-graph-rag.md` | planned provider module | child PR |
| `mem0.md` | planned provider module | child PR |
| `bettor-arena.md` | planned consumer binding example | consumer-specific values remain in Bettor, not here |

No planned file is created empty in this contract PR.

## Decoupling laws

A module may not:

- override source-code SSOT or evidence-state rules;
- make an optional provider mandatory for the core;
- widen filesystem, network, shell, memory-write, merge, or publication authority;
- contain machine-local paths, consumer branches/remotes, secrets, sessions, or live receipts;
- turn a search/graph/memory hit into an accepted fact without the required read-back;
- become passive context for tasks whose trigger does not match.

## Promotion and demotion

```text
repeated domain observation
→ common invariant identified
→ cross-domain evals remove provider/domain assumptions
→ governance PR
→ promote to SKILL.md or references/
```

```text
portable text found to depend on one tool/domain
→ define trigger, assumptions, fallback, and evals
→ prove core works without it
→ governance PR
→ demote to module
```

Copying text alone is not a placement decision.

## Change contract

A module change includes positive trigger coverage, non-trigger coverage, ambiguity/staleness/contradiction controls, context budget, source read-back behavior, fallback, affected consumers, and rollback identity.
