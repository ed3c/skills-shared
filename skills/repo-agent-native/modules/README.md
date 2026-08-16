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
    ├── one provider lane → LOAD THAT MODULE
    ├── fuzzy + exact + structural/symbol lanes needed → BLINDSPOT HYBRID
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
PROVIDER_SELF_ADMISSION
```

## Current files and classification

| File | Role | Current state |
|---|---|---|
| `extraction-methodology.md` | stable cross-domain inference method | retained on demand |
| `codebase-mastery-methodology.md` | optional deep analysis mode | retained behind explicit trigger |
| `specs-as-code-prompt.md` | optional output template | retained on demand; grants no execution authority |
| `blindspot-hybrid.md` | composite grepai + SCIP + Tree-sitter + Serena + SQLite/LanceDB contract | active composite route; source-readback and test gated |
| `grepai.md` | fuzzy Intent Anchor and bounded runtime MCP exploration | active candidate lane; does not replace exact/AST lanes |
| `serena.md` | symbol-aware Agent execution provider contract | active candidate/effect lane; separate edit authority required |
| `code-graph-rag.md` | legacy compatibility retirement adapter | retired from active routing; audit/migration only |
| `mem0.md` | episodic memory provider contract | optional projection, never source truth |
| `canonical-terms.md` | refactor terminology preservation | audit-only |
| `semantic-loss-ledger.md` | immutable baseline-to-current mapping | audit-only |

SCIP, Tree-sitter, SQLite and LanceDB are capability lanes in the Blindspot Hybrid contract. They are not installed or activated by the presence of the module. Consumers own exact binaries/indexers/grammars/databases and live receipts.

## Blindspot Hybrid data flow

```text
question
→ grepai Intent Anchor (optional)
→ SCIP indexed relations + Tree-sitter AST skeleton (optional exact/structural lanes)
→ Serena symbol-aware execution (optional)
→ current source read-back (mandatory for admitted source claims)
→ targeted test/runtime observation (mandatory for behavioral claims)
→ SQLite authoritative ledger
→ optional LanceDB projection
→ deterministic blindspot assertion
```

Provider absence does not fabricate PASS. Tier 0 source discovery remains the fallback.

## Decoupling laws

A module may not:

- override source-code SSOT or evidence-state rules;
- make an optional provider mandatory for the core;
- widen filesystem, network, shell, memory-write, merge, publication, MCP, or Agent authority;
- contain machine-local paths, consumer branches/remotes, secrets, sessions, or live receipts;
- turn a search/index/AST/symbol/vector/memory hit into an accepted fact without required read-back;
- allow LanceDB to become admission authority over SQLite;
- claim SCIP or Tree-sitter proves whole-program runtime behavior;
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
