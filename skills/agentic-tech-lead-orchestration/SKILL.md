---
name: agentic-tech-lead-orchestration
description: |
  Portable Agentic Tech Lead procedure for compiling a request into typed task contracts, extracting invariants and unknowns, building only true dependency edges, admitting bounded workers with disjoint leases, verifying each result independently, selecting among candidate implementations, converging shared state, and handing off a reviewable stack. Concrete code-intelligence providers, parsers, symbol tools, executors, vector projections, schedulers, and consumer commands are domain modules.
---

# Agentic Tech Lead Orchestration

<!-- PORTABLE_CORE_START -->

## Contract

The core owns task-contract compilation, invariant extraction, true dependency DAGs, worker/attempt identity, lease admission, independent verification, candidate comparison, convergence ownership, global-objective retention, and delivery handoff. Concrete tool/runtime implementations live in `modules/domain-profile.md`.

## State machine

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ TASK_DAG_COMPILED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_ASSERTED
→ DELIVERY_HANDOFF
```

## Hard laws

- **CORE-LAW-001 — contracts before workers.** Freeze exact subject, invariants, task inputs/outputs, dependencies, acceptance criteria, negative controls, budgets, and authority before fan-out.
- **CORE-LAW-002 — dependency edges must be real and writers disjoint.** A dependency exists only when a task consumes another task's unmerged contract/bytes/state; active writers may not overlap path/resource leases.
- **CORE-LAW-003 — worker/provider output is candidate evidence.** Results require exact-source readback and owning assertions; self-report, index hits, graph edges, or process exit zero cannot become correctness `PASS` by themselves.
- **CORE-LAW-004 — modules cannot widen authority.** Capability modules may implement retrieval/execution but cannot fabricate dependencies, weaken oracles, suppress failures/dissent, or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — convergence preserves the global objective.** Candidate selection and shared-state integration happen only after prerequisites are verified; local task success cannot override frozen repository/system invariants.

## Procedure

1. Bind exact repository/system/task subject, objective, non-goals, constraints, and Human-owned operations.
2. Extract system invariants, interfaces, unknowns, evidence requirements, rollback conditions, and shared-state owners.
3. Compile typed task packets with true dependency edges, path/resource scope, budgets, independent oracles, and negative controls.
4. Admit parallel workers only when scopes are disjoint and prerequisites/capabilities are satisfied; otherwise choose bounded serial/single-worker execution.
5. Select optional retrieval/execution capabilities only through `modules/domain-profile.md`; direct source and deterministic controls remain authoritative.
6. Execute attempts with unique identities, observable artifacts, bounded retries, and no private-reasoning requirement.
7. Verify every result independently; stale/wrong-subject/out-of-lease results fail closed and remain in the denominator.
8. Compare competing valid candidates on frozen correctness, risk, cost, reviewability, and rollback criteria rather than model preference.
9. Converge shared indexes/contracts/state through one explicit owner after prerequisites are verified.
10. Assert both local task oracles and the frozen global objective before producing a stacked/delivery handoff.

## Module selection

Load `modules/domain-profile.md` only when concrete code-intelligence providers, parsers, symbol/executor tools, projections, schedulers, runtime carriers, or consumer commands must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`. Provider/tool implementation and live runtime execution remain distinct.

## Stop and handoff

Stop on missing system contract, false dependency graph, overlapping leases, failed oracle, stale result, unresolved safety dissent, unavailable required capability, budget exhaustion, or Human-owned merge/release/promotion. Handoff includes task DAG, attempts, leases, verified results, rejected candidates, convergence subject, global-objective receipt, and next delivery authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Existing deterministic task-graph/evidence mechanisms remain reusable; product-specific adapters must stay outside the portable core.
