# Spatial Loop #407 — terminal Molecular Stack index

This is the durable terminal-atom projection for the Spatial Loop Intent–Case–Proof Graph program. Current GitHub metadata and exact Git subjects remain mutable-state authority; this README preserves relation semantics, consumed bytes, evidence ceilings and handoff ownership.

## Program graph

```text
#407  GLOBAL_OBJECTIVE
│
├─ ICPG-C1  #408  C   case-graph contract/schema/reference
├─ ICPG-K1  #408  K   deterministic semantic checker
├─ ICPG-E1  #408  E   positive + semantic-loss/mutation controls
│
├─ ICPG-M1  #409  K/E Shadow intent/case/semantic-parity monitor
│
├─ ICPG-D1  #410  D/K Tech Lead denominator/ownership + Stack traceability
│
└─ ICPG-X1  #411  X   live independent continuous Shadow canary
                      EXTERNAL_EVIDENCE / PROCESS_DEPENDENCY
```

Implementation carrier:

```text
PR #412               CLOSED_NOT_MERGED (2026-08-21); preserved as first-red provenance evidence
branch                agent/spatial-intent-case-proof-graph-v1; final head e679aed9 NOT reachable from main
admitted publication  superseding replayed carrier — terminal merge c27f8c3 → main 5341885f
receipt               data/handoff/spatial-407/publication-provenance-receipt.json
```

Historical current-main refresh carrier:

```text
PR #513
relation TRANSPORT_REFRESH / HISTORICAL
purpose  merge current main into the #412 candidate without modifying main
not an implementation atom
```

## Atom index

| Atom | Issue | Type | Implementation surface | Relation | Deterministic state | Remaining evidence |
|---|---:|---|---|---|---|---|
| `ICPG-C1` | #408 | C | `intent-case-proof-graph.md`, case schema/template | `SIBLING` (root contract atom) | admitted on main `5341885f` | residual checker hardening tracked on #408; close = human |
| `ICPG-K1` | #408 | K | `check_case_graph.py` | `SIBLING` (same #408 terminal leaf) | admitted on main `5341885f`; owning suite green | residual checker hardening tracked on #408; close = human |
| `ICPG-E1` | #408 | E | case-graph positive/mutation suite | `SIBLING` (same #408 terminal leaf) | admitted on main `5341885f`; empty-denominator control added 2026-08-22 | residual control gaps tracked on #408; close = human |
| `ICPG-M1` | #409 | K/E | architecture-watch + monitor prompt/spec packet + falsifiers | `TRUE_CHILD` (consumed #408 vocabulary) | admitted on main `5341885f`; owning suite green | falsifier-strength residuals tracked on #409; live independent #411 |
| `ICPG-D1` | #410 | D/K | Tech Lead task contract/gates/readme + this Stack projection | `CONVERGENCE` (shared-route atom) | admitted on main `5341885f`; denominator/owner gate green | index/lease-control residuals tracked on #410; live Worker receipt separate |
| `ICPG-X1` | #411 | X | live Builder/Shadow canary receipt | `EXTERNAL_EVIDENCE` | `NOT_EXERCISED` | exact host/runtime/model/task canary |

Stack binding for the admitted static atom set (2026-08-22 reconciliation):

```text
issues            #408 #409 #410 static; #411 live
case IDs          NOT_APPLICABLE_WITH_EVIDENCE — no frozen program-level case-graph digest exists;
                  the case vocabulary ships as schema/template/fixture bytes, consumed per task at
                  Tech Lead admission time
branch class      single historical candidate branch agent/spatial-intent-case-proof-graph-v1
parent            main 88ce642a at branch time; admitted via superseding carrier through c27f8c3
owned paths       skills/spatial-loop-systems-engineering/**,
                  skills/agentic-tech-lead-orchestration/** (task-contract/case-obligation surfaces),
                  skills/git-town-stacked-pr-worker/molecular-indexes/spatial-407/**
produced state    MAIN_ADMITTED (static set) / NOT_EXERCISED (ICPG-X1)
oracle            per-atom owning suites + exact-head workflows (Skill Suites 597, Skill Eval Contract 341)
evidence ceiling  deterministic exact-head only; live lanes remain #411
rollback subject  revert of the superseding carrier merges on current main; the queue's compile-time
                  rollback_commit 88ce642a is historical — do not hard-reset to it (see receipt)
```

## State Machine

```text
ATOM_DECLARED
→ PATH_OWNER_BOUND
→ IMPLEMENTATION_BYTES_PRESENT
→ OWNING_ORACLE_GREEN
→ CURRENT_MAIN_RECONCILED
→ REPOSITORY_WIDE_GATES
→ PROVENANCE_ADMISSION
→ READY_FOR_MAIN_ADMIT
→ MERGED_ON_MAIN
→ STATIC_ATOM_CLOSED
```

`ICPG-X1` follows a separate machine:

```text
STATIC_MONITOR_ADMITTED
→ EXACT_LIVE_TASK_BOUND
→ BUILDER_AND_SHADOW_IDENTITIES_SEPARATED
→ CASE_GRAPH_DIGEST_FROZEN
→ SEMANTIC_LOSS_ATTEMPT
→ SHADOW_DELTA_OBSERVED
→ L0-L3_DISPOSITION_RECORDED
→ OWNING_ORACLE_READBACK
→ CLEANUP / UNRESOLVED_CASE_RECOUNT
→ LIVE_CANARY_VERIFIED | HOLD | FAIL
```

## Data flow

```text
Prompt / source behavior
→ ICPG exact digest + REQUIRED_CASE denominator
→ Tech Lead `case_obligations`
→ one implementation or convergence owner per case
→ true task DAG
→ Worker/path/resource leases
→ C/K/E/D terminal atoms
→ independent oracle receipts
→ global case reconciliation
→ main admission
→ #411 external live evidence
```

## Branch relation laws

- `SIBLING`: path/resource-disjoint work on a common admitted base.
- `TRUE_CHILD`: consumes a named unmerged parent contract/bytes/state.
- `CONVERGENCE`: one owner consumes selected sibling outputs or owns a shared index/integration surface.
- `PROCESS_DEPENDENCY`: ordering with no Git ancestry.
- `EXTERNAL_EVIDENCE`: runtime/Shadow/provider receipt with no implementation path ownership by default.
- `HISTORICAL`: prior transport, rejected, admitted or forensic subject that is not current mutable authority.

Case dependency never creates a Git child by itself. PR #513 is explicitly `HISTORICAL/TRANSPORT_REFRESH`; it does not inflate the C/K/E/X denominator.

## Closeout boundary

```text
#408 static atom set    closeable only after equivalent bytes are admitted on main
#409 static atom set    closeable after main admission; live responsibility remains #411
#410 static atom set    closeable after main admission
#411                    remains OPEN / NOT_EXERCISED
#407                    remains OPEN while #411 is a blocking program lane
```

2026-08-22 state note: GitHub auto-closed #407 on 2026-08-21T20:00:25Z when commit `32c049ca` reached `main` (a commit-reference close with no closure-audit record). The boundary above remains law — #407 was reopened in the same reconciliation wave and closes only after #411. The `admitted on main` condition for #408/#409/#410 is now met; receipt: `data/handoff/spatial-407/publication-provenance-receipt.json`. Issue closes stay human-owned.

Repository provenance is load-bearing. A connector-authored source tree may be deterministically correct while still ineligible for main until a provenance-compliant publication subject is built and the repository-wide admission gate passes.

## Local Handoff

The next execution subject is owned by:

`../../../agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json`

That queue contains the publication/provenance item and the dependent live #411 item. Queue state is not execution evidence.