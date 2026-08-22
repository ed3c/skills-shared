# Spatial Loop #407 integration and closure state

This directory is the current zero-context closeout route for the `#407` Intent–Case–Proof Graph (ICPG) program. It records integration state and handoff only. Machine contracts, exact Git subjects, GitHub issue/PR metadata, workflow receipts and runtime receipts remain authoritative over this document.

## Current authority

```text
program issue           #407
static implementation   #408 / #409 / #410
live evidence           #411
source PR               #412 (GitHub `CLOSED`, not merged; superseded by #419 per the #560 portfolio wave, commit `c27f8c3` on main — see docs/traceability/github-portfolio-control/decisions.json)
refresh carrier         #513  HISTORICAL / merged only into a temporary branch
main observed           5341885f26b5e8e7baf5087a4d661e324f878242 (2026-08-22 reconciliation)
integration checkpoint  32c049ca11d741e81023857aaf77b46cddce925e (now an ancestor of main)
admitted publication    superseding replayed carrier — terminal merge c27f8c3
receipt                 data/handoff/spatial-407/publication-provenance-receipt.json
```

`#513` exists only to consume current `main` into the #412 candidate without mutating `main`. It is not an implementation atom and must not be counted as feature evidence.

The #412 branch is no longer an open candidate: GitHub reports `state=CLOSED` (not merged; its final head `e679aed9` is not reachable from `main` and is retained as forensic evidence), and main commit `c27f8c3` ("merge(#419,#412): land the replayed ICPG bridge carrier (supersedes #412 bytes)") shows its content landed via #419 instead. Re-read #419's/main's exact head before citing this program as live. The integration checkpoint above proved that main-observed-at-`88ce642` bytes and the #407 implementation could coexist at that point; it does not describe current main.

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
| Short prompt suppresses semantic obligations | #407/#408 | deterministic contract + mutations implemented | admitted on main `5341885f` (receipt); residual checker hardening on #408 |
| Compatibility migration silently drops source decision logic | #408 | differential semantic-loss canary implemented | admitted on main `5341885f`; future live consumer evidence remains separate |
| Implementation discovers a new case but Shadow leaves it at L0 | #409 | literal-deletion falsifiers implemented; falsifier-strength residuals recorded on #409 | live independent runtime #411 |
| FIRST_GREEN erases unresolved case/oracle obligations | #409 | literal-deletion checkpoint falsifier implemented; strength residuals recorded on #409 | live independent runtime #411 |
| Tech Lead decomposes from prompt and drops frozen required cases | #410 | denominator/owner gate implemented | admitted on main `5341885f`; future live Worker receipt separate |
| Stale case graph accepted by task admission | #410 | exact graph readback/digest/denominator controls implemented | admitted on main `5341885f` (receipt) |
| Static fixtures represented as continuous Shadow proof | #411 | explicitly forbidden | exact live canary required |
| All unknown unknowns claimed exhausted | #407 | explicitly not claimed | permanently bounded by declared case basis / discovery lane |

## Close / merge policy

At the static boundary:

```text
#408  close only after #412-equivalent bytes land on main and exact-main readback is green
#409  close only for STATIC monitor-contract scope after the same admission; #411 retains live scope
#410  close only after Tech Lead + Molecular traceability bytes land on main
#411  KEEP OPEN until exact live independent Shadow receipt exists
#407  CLOSED per closure packet (closure-audit/issue-407.json): a program issue may close with a
      named residual owner; #411 stays the NOT_EXERCISED residual owner until its own receipt exists
```

A source branch PASS, Draft/Ready state, temporary carrier merge, or issue comment cannot substitute for main admission.

2026-08-22 state note: main admission is now PERFORMED (see Current authority above), so #408/#409/#410 have entered their close-eligible state; the closes themselves stay human-owned. #407 was auto-closed on 2026-08-21 (commit-reference), briefly reopened for lacking a closure record, then closed again under the landed closure packet `closure-audit/issue-407.json`, which names #411 as the program's NOT_EXERCISED residual owner.

## Evidence ceiling

```text
ICPG contract / checker / semantic mutations        ADMITTED_ON_MAIN 5341885f
Shadow static case-delta contract                    ADMITTED_ON_MAIN 5341885f
Tech Lead ICPG denominator / ownership gate          ADMITTED_ON_MAIN 5341885f
current-main compatibility checkpoint                OBSERVED / HISTORICAL
main admission                                       PERFORMED — superseding carrier merge c27f8c3;
                                                     receipt data/handoff/spatial-407/publication-provenance-receipt.json
live Worker consuming frozen ICPG                    NOT_EXERCISED
continuous independent Shadow case monitoring        NOT_EXERCISED / #411
universal unknown-unknown discovery                  NOT_CLAIMED
production / release / promotion                     HUMAN_ADMIT_REQUIRED
```

## Local Handoff

The authoritative Local Handoff queue for the remaining admission/runtime work is:

`../../agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json`

Read that queue together with current #407 and #411 GitHub state. Queue presence proves only that continuation has been specified; it does not prove execution.