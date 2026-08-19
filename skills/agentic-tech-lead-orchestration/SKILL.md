---
name: agentic-tech-lead-orchestration
description: |
  Portable Agentic Tech Lead procedure for compiling an admitted system/case contract into typed task contracts, preserving required use/edge-case obligations, building only true dependency edges, admitting bounded workers with disjoint leases, verifying each result independently, selecting among candidate implementations, converging shared state, and handing off a reviewable stack or zero-context local execution queue. Concrete code-intelligence providers, parsers, symbol tools, executors, vector projections, schedulers, and consumer commands are domain modules.
---

# Agentic Tech Lead Orchestration

<!-- PORTABLE_CORE_START -->

## Contract

The core owns task-contract compilation, invariant and case-obligation preservation, true dependency DAGs, capability-plan compilation, worker/attempt identity, lease admission, independent verification, candidate comparison, convergence ownership, global-objective retention, delivery handoff, and typed local-runtime handoff compilation. Concrete tool/runtime implementations live in `modules/domain-profile.md`.

When the upstream task carries a `spatial-loop-case-graph/v1` Intent–Case–Proof Graph (ICPG), Tech Lead decomposition MUST consume that admitted graph rather than re-derive scope from a shorter natural-language prompt. Every required case in the frozen denominator must be assigned to exactly one branch/Worker owner or to one explicit convergence owner. Local task PASS never closes a missing global case.

The core owns four independent admission layers:

1. a two-stage task-packet gate: `scripts/check_task_contract_schema.py` validates shape against `references/task-contract.schema.json`, then `scripts/assert_task_contract.py` evaluates semantic/hard-law assertions and emits a receipt; the task packet includes an exact case-graph digest and branch→case ownership map;
2. a capability-causality gate: `scripts/assert_capability_dag.py` validates `references/capability-plan.schema.json` plus receipts shaped by `references/capability-receipts.schema.json`, then enforces predecessor closure, trigger/selection consistency, identity binding, and receipt-gated admission to downstream states;
3. a scheduler-lifecycle gate: `scripts/assert_scheduler_lifecycle.py` keeps attempt, lease, checkpoint, result, and terminal-state evidence mechanically distinct from mere task-plan presence;
4. a Local Handoff Execution Queue gate: `scripts/assert_local_handoff_queue.py` validates zero-context continuation after the current session reaches a real host/runtime boundary.

Structural core/domain separation is a fifth assertion and cannot substitute for any admission layer. A Markdown module link proves reachability only; it does not prove runtime execution or authorize the next state.

## State machine

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ CASE_GRAPH_BOUND_OR_EXPLICITLY_NOT_APPLICABLE
→ CASE_OBLIGATIONS_FROZEN
→ CAPABILITY_PLAN_COMPILED
→ CAPABILITY_PLAN_ASSERTED
→ CONTEXT_ADMITTED
→ TASK_DAG_COMPILED
→ TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ CASE_OWNERSHIP_ASSERTED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_AND_CASE_COVERAGE_ASSERTED
→ DELIVERY_HANDOFF

optional continuation when unresolved work requires another physical host/runtime:
DELIVERY_HANDOFF
→ LOCAL_HANDOFF_COMPILED
→ LOCAL_HANDOFF_EXECUTED by the admitted consumer/runtime authority
```

`references/t0-t10-causal-map.json` remains the compatibility map from the former T0–T10 stages to portable capability transitions; it does not override case ownership.

## Hard laws

- **CORE-LAW-001 — contracts before workers.** Freeze exact subject, invariants, case obligations, task inputs/outputs, dependencies, acceptance criteria, negative controls, budgets, authority, and capability triggers before fan-out.
- **CORE-LAW-002 — dependency edges must be real and writers disjoint.** A dependency exists only when a task consumes another task's unmerged contract/bytes/state; active writers may not overlap path/resource leases. Case dependencies do not automatically become Git ancestry dependencies.
- **CORE-LAW-003 — worker/provider output is candidate evidence.** Results require exact-source readback and owning assertions; self-report, index hits, graph edges, or process exit zero cannot become correctness `PASS` by themselves.
- **CORE-LAW-004 — modules cannot widen authority.** Capability modules may implement retrieval/execution but cannot fabricate dependencies, weaken oracles, suppress failures/dissent, omit required cases, or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — convergence preserves the global objective.** Candidate selection and shared-state integration happen only after prerequisites are verified; local task success cannot override frozen repository/system invariants or the frozen required-case denominator.
- **CORE-LAW-006 — capability transitions are receipt-gated.** A selected module can contribute to a downstream state only when its frozen trigger matches, every selected predecessor is closed by an identity-matched receipt, predecessor output states are consumed, and an admissible receipt for the same task/subject/module closes the transition. Plan presence, installation, or fixture evidence cannot self-promote to live runtime `PASS`.
- **CORE-LAW-007 — handoff is executable state, not prose.** Work that cannot be completed in the current host/session must be compiled into a typed Local Handoff Execution Queue. Each item binds entry condition, exact subject, runtime/command lane, receipt contract, exit condition, and next item.
- **CORE-LAW-008 — handoff cannot launder evidence or authority.** Static/synthetic evidence cannot satisfy a live/runtime receipt; issue UI state cannot prove completion; no handoff item may infer merge, issue close, queue advance, promotion, provider activation, rollback, permission change, semantic-conflict resolution, or case closure.
- **CORE-LAW-009 — start-readiness and completion-readiness are two edge classes.** A start edge is closed when the prerequisite is readable and its paths/resources are free. A completion edge is closed only when the prerequisite is admitted by a receipt naming the exact subject and evidence lane. A node whose prerequisites are startable is not thereby completable. A convergence has exactly one declared owner.
- **CORE-LAW-010 — closure lanes do not substitute.** Cloud/static, local-deterministic, private-lineage, live/physical, and Human-admit evidence are independent lanes. A later closure state requires a receipt produced in its own lane.
- **CORE-LAW-011 — required-case denominator cannot shrink during decomposition.** If `case_obligations` is present, its graph digest is immutable for the task packet, every `required_case_id` appears exactly once across branch case owners, every owner names a declared branch, and the convergence owner is declared. Missing, duplicate, stale, or unowned cases block Worker admission.

## Procedure

1. Bind exact repository/system/task subject, objective, non-goals, constraints, and Human-owned operations.
2. Extract system invariants, interfaces, unknowns, evidence requirements, rollback conditions, and shared-state owners. If Spatial Loop supplied an ICPG, bind its exact reference/digest and required-case denominator; do not re-interpret a shorter prompt as authority to remove cases.
3. Compile a provider-neutral capability plan from the frozen task needs using `modules/domain-profile.md`.
4. Validate the capability plan structurally before executing a module.
5. Execute only modules whose frozen trigger selects them and preserve identity-bound receipts.
6. Before admitting a downstream state that depends on capability execution, run the cumulative causal gate; normal runtime requires LIVE receipts.
7. Admit `CONTEXT_ADMITTED` only after every selected required capability is closed or an explicitly admitted fallback closes an optional transition.
8. Compile the task DAG from admitted context and the frozen case denominator. Assign each required case to exactly one branch owner or the single convergence owner. Run the two-stage task gate:
   - `python3 scripts/check_task_contract_schema.py --contract <task-contract.json>`;
   - `python3 scripts/assert_task_contract.py --contract <task-contract.json> --receipt <receipt.json>`.
   Any non-zero result blocks dispatch.
9. Admit parallel workers only when scopes are disjoint and prerequisites/capabilities are satisfied. A case relation alone is not a Git parent edge; use a true child only when unmerged parent bytes/contracts/state are consumed.
10. Build each Worker packet from the frozen contract and `references/fanout-prompt.md`. Include owned case IDs and their acceptance/oracle obligations.
11. Before `ATTEMPTS_EXECUTED`, require the cumulative capability gate to close any selected executor transition. Execute attempts with unique identities, observable artifacts, bounded retries, and no private-reasoning requirement.
12. Verify every result independently; stale/wrong-subject/out-of-lease results fail closed and remain in the denominator.
13. Before `CANDIDATES_COMPARED`, close any selected tournament transition. Compare valid candidates on frozen correctness, case coverage, risk, cost, reviewability, and rollback criteria rather than model preference.
14. Converge shared indexes/contracts/state through the one declared convergence owner after prerequisites are verified.
15. Before `DELIVERY_HANDOFF`, close any selected delivery transition. Assert both local task oracles and the frozen global objective/case denominator. A terminal leaf PASS cannot hide an unowned, unverified, or failed required case. Merge/release/promotion remain Human/repository authority.
16. Classify every unresolved terminal item. Continue in-session when evidence can still be produced here; compile a Local Handoff Execution Queue only for a genuine physical-host, private-forge, signed-in carrier, provider-session, device, or Human-admission boundary.
17. Validate any handoff queue before transfer and preserve exact subject, rollback identity, cleanup requirement, evidence ceiling, and Human-owned operations.

## Module selection

Load `modules/domain-profile.md` only when concrete code-intelligence providers, parsers, symbol/executor tools, projections, schedulers, runtime carriers, or consumer commands must be bound. Selection must be materialized in a capability plan, not inferred ad hoc during execution.

## Executable assertions

```bash
python3 scripts/check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration
python3 skills/agentic-tech-lead-orchestration/scripts/assert_capability_dag.py --contract <task-contract.json> --plan <capability-plan.json> --receipts <capability-receipts.json> --admit-state <STATE>
python3 skills/agentic-tech-lead-orchestration/scripts/check_task_contract_schema.py --contract <task-contract.json>
python3 skills/agentic-tech-lead-orchestration/scripts/assert_task_contract.py --contract <task-contract.json> --receipt <receipt.json>
python3 skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py --queue <local-handoff-queue.json>
```

Exit contract remains `0` pass for the declared gate, `2` semantic/causal failure, `64` invalid/absent input, and `70` unavailable/invalid assertion mechanism where supported.

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`. Case-graph contract closure, task ownership closure, fixture validation, live runtime execution, queue validation, and queue execution remain distinct evidence classes.

## Stop and handoff

Stop on missing system contract, stale/missing required case graph, required-case denominator drift, duplicate/unowned case ownership, invalid capability plan, false trigger/selection state, absent/cyclic predecessor, receipt identity mismatch, failed schema/semantic gate, false task dependency graph, overlapping leases, failed oracle, stale result, unresolved safety dissent, unavailable required capability, budget exhaustion, invalid/stale handoff queue, failed cleanup, or Human-owned merge/release/promotion.

Handoff includes task DAG, frozen case-graph identity and required-case denominator, branch→case ownership, capability plan/receipts, task receipts, attempts, leases, verified results, rejected candidates, convergence subject, global-objective/case-coverage receipt, residual evidence lanes, and next delivery authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Product-specific adapters must stay outside the portable core.