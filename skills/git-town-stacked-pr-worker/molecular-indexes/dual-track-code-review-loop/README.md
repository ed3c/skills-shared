# Molecular index — Dual-Track Code Review Loop

This terminal index tracks `#517` (parent) and its currently open child lanes.
GitHub remains authoritative for mutable issue/PR state; this file does not
embed a mutable head SHA and is not GitHub's live state.

## Problem DAG

```text
#517 [DTCR] generalize dual-track code-review and auto-refactor loop
 ├─ #518  C0 contract ── ADMITTED
 ├─ #519  D1 deterministic fact-plane contracts ── schemas landed
 │    ├─ adapters/tree-sitter/    LANDED (live receipt)
 │    ├─ adapters/sqlite-ledger/  LANDED (planted mutations)
 │    ├─ #547 D1-SCIP adapter     BLOCKED_ON_PROVIDER
 │    └─ #549 D1-BUF adapter      BLOCKED_ON_PROVIDER
 ├─ #521  M1 semantic-context plane
 │    └─ #550 M1-C adapter        BLOCKED
 ├─ #522  X1 synthesis/closure compiler   CLOSED (landed and closed via PR #563)
 ├─ #523  R1 single-repo refactor protocol   landed in-tree (issue state on GitHub)
 ├─ #524  R2 cross-repo Expand & Contract
 ├─ #525  E1 independent Shadow / mutations / closure denominator
 ├─ #526  D2 docs/AGENTS/prompts/routing convergence (this convergence)   CLOSED via PR #563
 ├─ #527  B1 bootstrap profile
 └─ #528  L1 live consumer canary / Local Handoff
        ↓
docs/traceability/dual-track-code-review-loop/{README,AGENTS,ISSUE_DAG.json,
LOCAL_HANDOFF_EXECUTION_QUEUE.json}
```

Child issues are evidence-linked lanes, not Git parents of `#517`, unless a
concrete branch has actually consumed another branch's unmerged bytes.

## Molecular atom

| Atom | Issue / publication | Relation | Owns | Current ceiling |
|---|---|---|---|---|
| `C0` | `#518` | `CONTRACT` | source-packet/candidate/violation/refactor/change-unit/verification/closure/disposition schemas | admitted |
| `D1` | `#519` | `CONTRACT + TWO ADAPTERS` | 16 D1/M1 interface schemas; tree-sitter + sqlite-ledger adapters | schemas landed, adapters green in committed suite |
| `M1` | `#521` | `CONTRACT` | optional semantic-context/organizational-memory plane | open, adapter (`#550`) blocked |
| `X1` | `#522` | `SYNTHESIS` | dual-track synthesis + problem-closure compiler | landed (`synthesis/` + three schemas, suite-counted); closed via PR #563 |
| `R1`/`R2` | `#523`/`#524` | `PROTOCOL` | bounded single-repo and cross-repo refactor protocols | R1 landed in-tree (`refactor/` + four contracts, suite-counted; issue state on GitHub); R2 open, start-dependent on `X1` |
| `E1` | `#525` | `INDEPENDENT SHADOW` | mutations and evidence-closure denominator | open |
| `D2` | `#526` | `CONVERGENCE` | README/AGENTS/SESSION-prompt/traceability navigation (this atom) | `DTCR_DOCS_PROMPTS_TRACE_READY`; closed via PR #563 |
| `B1` | `#527` | `BOOTSTRAP` | immutable thin-binding profile for new repositories | open, start-dependent on `D2` |
| `L1` | `#528` | `LIVE CANARY` | real consumer canary and final Local Handoff admission | open, completion-dependent on `R1`/`R2`/`E1`/`B1` |

This is a wide sibling fan-out under one parent rather than a serial chain:
`M1`/`D1` are siblings after `C0`, and `#547`/`#549`/`#550` are provider-bound
adapter lanes that do not gate `D2`'s own doc convergence.

## Closure State Machine (parent `#517`)

```text
CONTRACTS_ADMITTED (C0, D1 schemas, M1 schema)
→ DETERMINISTIC_ADAPTERS_LANDED (tree-sitter, sqlite-ledger)
→ DOCS_AND_ROUTES_CONVERGED (D2, this atom)
→ SYNTHESIS_COMPILED (X1)
→ PROTOCOLS_IMPLEMENTED (R1, R2)
→ INDEPENDENT_SHADOW_CLOSED (E1)
→ BOOTSTRAP_ADDED (B1)
→ LIVE_CANARY_RUN_AND_ADMITTED (L1)
```

## Data flow

```text
Issue #517 fan-out
     │
C0/D1/M1 schemas + refused-claims.json
     │
tree-sitter / sqlite-ledger adapters ──→ committed selftest.py, run-all.sh
     │
D2 convergence (this atom) ──→ docs/traceability/dual-track-code-review-loop/*
     │
X1 synthesis (landed) → R1/R2 protocols → E1 Shadow → B1 bootstrap → L1 canary
```

## Evidence boundary

An open child issue is not implementation evidence for the parent. A landed
adapter's selftest is evidence for that adapter's own capability class only,
never for the synthesis compiler, the refactor protocols, or Local Handoff. A
still-open issue (`#525`, awaiting its own implementation) is not advanced by
this index mentioning it, and a closed one (`#522`, closed via PR #563) was
closed by its receipt on GitHub, never by an index row. Merge, release, registry admission and Human legal/rights
clearance remain separate Human-owned transitions this index cannot reach.
