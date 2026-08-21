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
PR #412
branch agent/spatial-intent-case-proof-graph-v1
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
| `ICPG-C1` | #408 | C | `intent-case-proof-graph.md`, case schema/template | root contract atom | implemented on #412 candidate | main admission |
| `ICPG-K1` | #408 | K | `check_case_graph.py` | same #408 terminal leaf | owning Spatial suite green on current-main integration checkpoint | main admission |
| `ICPG-E1` | #408 | E | case-graph positive/mutation suite | same #408 terminal leaf | semantic-loss and stale/evidence/coverage controls implemented | main admission |
| `ICPG-M1` | #409 | K/E | architecture-watch + monitor prompt/spec packet + falsifiers | consumes #408 vocabulary | static monitor contract implemented and owning Spatial suite green | live independent #411 |
| `ICPG-D1` | #410 | D/K | Tech Lead task contract/gates/readme + this Stack projection | convergence/shared-route atom | Tech Lead owning suite green; denominator/owner gate implemented | main admission; live Worker receipt separate |
| `ICPG-X1` | #411 | X | live Builder/Shadow canary receipt | `EXTERNAL_EVIDENCE` | `NOT_EXERCISED` | exact host/runtime/model/task canary |

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

Repository provenance is load-bearing. A connector-authored source tree may be deterministically correct while still ineligible for main until a provenance-compliant publication subject is built and the repository-wide admission gate passes.

## Local Handoff

The next execution subject is owned by:

`../../agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json`

That queue contains the publication/provenance item and the dependent live #411 item. Queue state is not execution evidence.