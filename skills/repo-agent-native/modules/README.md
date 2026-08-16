# repo-agent-native Modules

`modules/` contains optional capability or domain instances. The portable procedure remains in `../SKILL.md`; stable cross-domain reference material belongs in `../references/`.

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

## Current files and classification

| File | Role | State |
|---|---|---|
| `extraction-methodology.md` | stable cross-domain inference method | retained on demand |
| `codebase-mastery-methodology.md` | optional deep analysis mode | retained behind explicit trigger |
| `specs-as-code-prompt.md` | optional output template | retained on demand; no execution authority |
| `grepai.md` | fuzzy intent candidate discovery | read-only and source-readback gated |
| `serena.md` | interactive symbol/reference/diagnostic candidates | project-health and readback gated |
| `scip.md` | compiler-derived Def/Ref/type relation candidates | exact-subject and coverage gated |
| `tree-sitter.md` | AST/CST ranges, signatures and skeletonization | exact-byte structural lane |
| `sqlite-code-index.md` | rebuildable normalized code projection | subject-bound, non-authoritative store |
| `compiler-truth-context-funnel.md` | composed intent → semantics → structure → context route | bounded composition; no evidence promotion |
| `blindspot-hybrid.md` | cross-lane event ledger and coverage law behind `NO_FLOW` | absence is a coverage claim, never a provider miss |
| `mem0.md` | episodic memory provider contract | optional projection, never source truth |
| `canonical-terms.md` | refactor terminology preservation | audit-only |
| `semantic-loss-ledger.md` | immutable baseline-to-current mapping | audit-only |

`code-graph-rag.md` was removed from the active surface. The decision and re-admission boundary are recorded in [`../references/CODE_GRAPH_RAG_RETIREMENT.md`](../references/CODE_GRAPH_RAG_RETIREMENT.md).

Consumer-specific paths, provider endpoints, namespaces, credentials, mutable health, and live receipts remain in the consumer repository. There is deliberately no consumer-named module here.

## Compiler-truth context funnel

```text
natural-language question
→ grepai or deterministic search: candidate seeds
→ current source: read-back boundary
→ SCIP / Serena / native LSP: semantic candidates
→ Tree-sitter: exact-byte ranges and skeletons
→ SQLite: normalized subject-bound projection
→ bounded target/dependency/callsite/test context
→ source-anchored core procedure
```

Each stage preserves its own evidence ceiling. The composition cannot turn search success, an index edge, a parse tree, or a database row into a fact by itself.

## Provider-module data flow

```text
core capability request
→ module trigger match
→ provider/project/producer identity
→ subject + health + freshness + coverage check
→ bounded query or parse
→ candidate output
→ current source read-back
→ accept at admitted evidence level / downgrade / fallback
```

The fallback path returns to deterministic repository-owned mechanisms. Provider absence cannot become PASS.

## Decoupling laws

A module may not:

- override source-code SSOT or evidence-state rules;
- make an optional provider mandatory for the core;
- widen filesystem, network, shell, memory-write, merge, or publication authority;
- contain machine-local paths, consumer branches/remotes, secrets, sessions, or live receipts;
- turn a search/index/AST/database/memory hit into an accepted fact without required read-back;
- become passive context for tasks whose trigger does not match;
- claim language/indexer coverage it did not observe.

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

A module change includes positive trigger coverage, non-trigger coverage, ambiguity/staleness/coverage/contradiction controls, context budget, source read-back behavior, fallback, affected consumers, and rollback identity.
