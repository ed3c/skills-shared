# Spatial Loop #407 integration and closure state

This directory is the current zero-context closeout route for the `#407` Intent–Case–Proof Graph (ICPG) program. It records integration state and handoff only. Machine contracts, exact Git subjects, GitHub issue/PR metadata, workflow receipts and runtime receipts remain authoritative over this document.

## Current authority

```text
program issue           #407
static implementation   #408 / #409 / #410
live evidence           #411
source PR               #412
refresh carrier         #513  HISTORICAL / merged only into a temporary branch
main observed           88ce642a7f198d88019aa8ae19e63631ae4999c2
integration checkpoint  32c049ca11d741e81023857aaf77b46cddce925e
```

`#513` exists only to consume current `main` into the #412 candidate without mutating `main`. It is not an implementation atom and must not be counted as feature evidence.

The #412 branch is mutable until final admission. Always re-read its exact head before a decision. The integration checkpoint above proved that current-main bytes and the #407 implementation can coexist; subsequent closeout commits may move the head.

## Closure State Machine

```text
REQUEST_BOUND
→ ICPG_CONTRACT_IMPLEMENTED                     #408
→ SHADOW_CASE_DELTA_CONTRACT_IMPLEMENTED        #409
→ TECH_LEAD_CASE_OWNERSHIP_GATE_IMPLEMENTED     #410
→ CURRENT_MAIN_REFRESHED                        #513 → checkpoint 32c049c...
→ EXACT_HEAD_SOURCE_SUITES_REVALIDATED
→ GOLDEN_LIVE_CANDIDATES_REBOUND
→ CLOSEOUT_DOCS_AND_HANDOFF_BOUND
→ REPOSITORY_PROVENANCE_GATE
    ├── PASS → READY_FOR_MAIN_ADMIT
    │          → MERGED_ON_MAIN
    │          → STATIC_CHILD_ISSUES_CLOSEABLE
    └── FAIL → LOCAL_HANDOFF_REQUIRED
               → PROVENANCE_COMPLIANT_REBUILD
               → EXACT_HEAD_REPLAY
               → READY_FOR_MAIN_ADMIT

MERGED_ON_MAIN
→ #411 LIVE_SHADOW_CANARY
→ exact-host/runtime receipt
→ LIVE_CANARY_VERIFIED | HOLD | FAIL
```

Static implementation and live Shadow execution are different evidence lanes. `MERGED_ON_MAIN` cannot promote #411.

## Issue and process DAG

```text
#407  global intent/case/proof objective
│
├─ #408  C/K/E
│    ├─ case-graph schema/reference
│    ├─ deterministic semantic checker
│    └─ migration semantic-loss controls
│
├─ #409  M/K/E
│    ├─ intent/case/semantic-parity delta vocabulary
│    ├─ L0-L3 monitor policy
│    └─ FIRST_GREEN / BEFORE_PR falsifiers
│
├─ #410  D/K
│    ├─ ICPG denominator → Tech Lead task contract
│    ├─ one case owner / one convergence owner
│    ├─ true dependency DAG
│    └─ Molecular Stack traceability
│
└─ #411  X
     live independently operating Shadow canary
     EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

Dependency meaning:

```text
#408 → #409   contract vocabulary consumption
#408 → #410   case denominator / ownership contract consumption
#409 → #411   live monitor behavior to exercise
#410 → #411   exact Builder task/case ownership subject to observe
```

These process edges do not manufacture Git ancestry. Path-disjoint work is sibling work; `TRUE_CHILD` exists only when unmerged parent bytes/contracts are consumed.

## Directory ownership and data flow

```text
skills/spatial-loop-systems-engineering/
├── AGENTS.md
│   └── mandatory Agent route and stop laws
├── README.md
│   └── portable topology, State Machines, ICPG and evidence model
├── integration/
│   ├── AGENTS.md
│   └── README.md                ← current #407 closeout / handoff projection
├── references/
│   ├── intent-case-proof-graph.md
│   ├── case-graph.schema.json
│   ├── case-graph-template.json
│   ├── architecture-watch-loop.md
│   ├── system-prompt-monitor-overlay.md
│   └── spec-packet-template.md
├── scripts/
│   └── check_case_graph.py
└── tests/
    ├── case-graph/**
    ├── architecture-watch/**
    ├── refactor-proof/**
    └── universal-entry/**
```

End-to-end data flow:

```text
Prompt / source behavior / article / PDF / PRD
→ explicit source identity and evidence ceiling
→ intent atoms
→ semantic axes
→ use/edge-case denominator
→ source-behavior dispositions
→ invariant / state path
→ implementation binding
→ Tech Lead task + case ownership
→ Worker / Molecular implementation atom
→ oracle + negative control
→ exact-subject evidence
→ Shadow reconciliation
→ global case coverage
→ publication / Human admission boundary
```

An article/PDF is a source, not proof. For the #407 implementation program itself no external article/PDF claim is in the acceptance denominator; the real problem is the observed migration/copy semantic-loss failure mode described in #407. Future article/PDF-backed work must preserve each claim as source evidence and route implementation claims through the same ICPG plus problem-closure evidence lanes rather than promoting prose to runtime truth.

## Real-problem closure matrix

| Problem | Owner | Static state | Remaining proof |
|---|---|---|---|
| Short prompt suppresses semantic obligations | #407/#408 | deterministic contract + mutations implemented | main admission |
| Compatibility migration silently drops source decision logic | #408 | differential semantic-loss canary implemented | main admission; future live consumer evidence remains separate |
| Implementation discovers a new case but Shadow leaves it at L0 | #409 | deterministic monitor falsifiers implemented | live independent runtime #411 |
| FIRST_GREEN erases unresolved case/oracle obligations | #409 | deterministic checkpoint falsifier implemented | live independent runtime #411 |
| Tech Lead decomposes from prompt and drops frozen required cases | #410 | denominator/owner gate implemented | main admission + future live Worker receipt |
| Stale case graph accepted by task admission | #410 | exact graph readback/digest/denominator controls implemented | main admission |
| Static fixtures represented as continuous Shadow proof | #411 | explicitly forbidden | exact live canary required |
| All unknown unknowns claimed exhausted | #407 | explicitly not claimed | permanently bounded by declared case basis / discovery lane |

## Close / merge policy

At the static boundary:

```text
#408  close only after #412-equivalent bytes land on main and exact-main readback is green
#409  close only for STATIC monitor-contract scope after the same admission; #411 retains live scope
#410  close only after Tech Lead + Molecular traceability bytes land on main
#411  KEEP OPEN until exact live independent Shadow receipt exists
#407  KEEP OPEN while #411 or another declared program-level blocking lane remains open
```

A source branch PASS, Draft/Ready state, temporary carrier merge, or issue comment cannot substitute for main admission.

## Evidence ceiling

```text
ICPG contract / checker / semantic mutations        IMPLEMENTED_CANDIDATE
Shadow static case-delta contract                    IMPLEMENTED_CANDIDATE
Tech Lead ICPG denominator / ownership gate          IMPLEMENTED_CANDIDATE
current-main compatibility checkpoint                OBSERVED
main admission                                       PENDING
live Worker consuming frozen ICPG                    NOT_EXERCISED
continuous independent Shadow case monitoring        NOT_EXERCISED / #411
universal unknown-unknown discovery                  NOT_CLAIMED
production / release / promotion                     HUMAN_ADMIT_REQUIRED
```

## Local Handoff

The authoritative Local Handoff queue for the remaining admission/runtime work is:

`../../agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json`

Read that queue together with current #407 and #411 GitHub state. Queue presence proves only that continuation has been specified; it does not prove execution.