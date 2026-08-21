# Molecular index — Issue closure drift

This terminal index tracks Issue #551 and Draft PR #552. GitHub remains authoritative for mutable PR state; this file does not embed a mutable head SHA.

## Problem DAG

```text
historical closed Issues
├─ #312  Phase-1 landed / Phase-2 transferred
├─ #403  PR #404 closed-unmerged / consumed by later admitted convergence
├─ #505  direct deterministic repair landed through PR #507
└─ #366  cross-repo consumer landing through website-design-compiler PR #53
        ↓
#551 closure-drift contract
        ↓
#552 schema + semantic gate + audited packets + CI arrival
```

The four historical Issues are evidence cases, not Git parents of #551/#552.

## Molecular atom

| Atom | Issue / PR | Relation | Owns | Current ceiling |
|---|---|---|---|---|
| `C` | `#551 / #552` | `CONTRACT + IMPLEMENTATION CANDIDATE` | Issue closure schema, disposition vocabulary, repository-qualified PR/landing identities | static bytes |
| `K` | `#551 / #552` | same bounded candidate | deterministic closure checker | deterministic semantics after exact-head execution |
| `E` | `#551 / #552` | same bounded candidate | positive/mutation controls for unresolved acceptance, convergence indirection, cross-repo identity, evidence promotion | deterministic controls after execution |
| `D` | `#551 / #552` | documentation/index projection | closure-audit README/AGENTS, audited packets, this index | navigation only |
| `CI` | `#551 / #552` | external execution arrival | `Issue Closure Contract` workflow | exact-head GitHub Actions receipt only |

This is intentionally one bounded implementation PR rather than fake serial child branches: the files are one small authority boundary and do not justify invented Git ancestry.

## Closure State Machine

```text
ISSUE_DEFINED
→ ACCEPTANCE_FROZEN
→ IMPLEMENTATION_BOUND
→ EVIDENCE_BOUND
→ RESIDUAL_CLASSIFIED
→ LANDING_BOUND
→ SHADOW_REVIEWED
→ CLOSURE_ELIGIBLE
→ CLOSED
```

## Data flow

```text
GitHub Issue + acceptance
          │
GitHub PR / merge / tree ─┐
cross-repo landing ───────┼→ closure-audit/issue-*.json
successor ownership ──────┘              │
                                         ├→ Draft-2020-12 shape gate
                                         ├→ semantic closure gate
                                         ├→ planted mutation controls
                                         └→ exact-head Actions → Shadow → Human Admit
```

## Audited dispositions

```text
#312  SCOPE_TRANSFERRED
#403  CONSUMED_BY_CONVERGENCE
#505  DIRECTLY_LANDED
#366  DIRECTLY_LANDED / CROSS_REPOSITORY
```

## Evidence boundary

A closed Issue is not implementation evidence by itself. A closed-unmerged PR is not landing evidence. A PR number without repository identity is ambiguous. A deterministic green packet does not prove live/provider/production state. Draft PR #552 must remain non-admitted until its exact current head receives the required CI and independent Shadow readback; merge/release remain separate Human authority transitions.
