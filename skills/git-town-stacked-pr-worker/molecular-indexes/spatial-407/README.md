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

Implementation carrier — terminal at the 2026-08-22 readback:

```text
PR #412
branch   agent/spatial-intent-case-proof-graph-v1
state    CLOSED_UNMERGED / SUPERSEDED_BY_#419
```

PR #412 is not an open Draft and not a live path writer. Its bytes reached `main` through the replayed #419 route rather than through its own merge, so it closes no atom by itself: an atom advances only on its own receipt at an admitted subject. The reconciled `#412 → #419 → #420 → #450` chain is in [`../codex-v2/README.md`](../codex-v2/README.md).

Historical current-main refresh carrier:

```text
PR #513
relation TRANSPORT_REFRESH / HISTORICAL
purpose  merged current main into the #412 candidate without modifying main
not an implementation atom; terminal with its base
```

## Atom index

| Atom | Issue | Type | Implementation surface | Relation | Deterministic state | Remaining evidence |
|---|---:|---|---|---|---|---|
| `ICPG-C1` | #408 | C | `intent-case-proof-graph.md`, case schema/template | root contract atom | bytes admitted on `main` `5341885f…` | none |
| `ICPG-K1` | #408 | K | `check_case_graph.py` | same #408 terminal leaf | bytes admitted on `main`; owning Spatial suite green | none |
| `ICPG-E1` | #408 | E | case-graph positive/mutation suite | same #408 terminal leaf | semantic-loss and stale/evidence/coverage controls admitted on `main` | none |
| `ICPG-M1` | #409 | K/E | architecture-watch + monitor prompt/spec packet + falsifiers | consumes #408 vocabulary | static monitor contract admitted on `main`; owning Spatial suite green | live independent #411 |
| `ICPG-D1` | #410 | D/K | Tech Lead task contract/gates/readme + this Stack projection | convergence/shared-route atom | Tech Lead owning suite green; denominator/owner gate admitted on `main` | live Worker receipt separate |
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

At the 2026-08-22 readback:

```text
#408 static atom set    bytes admitted on main 5341885f…
#409 static atom set    bytes admitted on main; live responsibility remains #411
#410 static atom set    bytes admitted on main
#411                    OPEN / NOT_EXERCISED — live independent Shadow case-delta canary
#407                    CLOSED / COMPLETED, disposition CONSUMED_BY_CONVERGENCE
                        landed via PR #573 commit 9fe3c6daf53dcdd61123d5d7a4eeedbdf37b5d7c
                        evidence ceiling DETERMINISTIC; residual owner #411
```

Closure packet: [`../../../agentic-tech-lead-orchestration/references/closure-audit/issue-407.json`](../../../agentic-tech-lead-orchestration/references/closure-audit/issue-407.json). #407 closing did not exercise #411: a program issue may close with a named residual owner, and that residual stays `NOT_EXERCISED` until its own receipt exists.

Repository provenance is load-bearing. A connector-authored source tree may be deterministically correct while still ineligible for main until a provenance-compliant publication subject is built and the repository-wide admission gate passes. That is what happened here: PR #412's own provenance blocked it, and the equivalent bytes reached `main` through the replayed #419 route instead.

## Local Handoff

The next execution subject is owned by:

`../../agentic-tech-lead-orchestration/runtime-handoff/spatial-407-local-handoff-queue.json`

That queue contains the publication/provenance item and the dependent live #411 item. Queue state is not execution evidence.