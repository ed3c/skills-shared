---
name: agentic-tech-lead-orchestration
description: |
  Portable Agentic Tech Lead procedure for compiling a request into typed task contracts, extracting invariants and unknowns, building only true dependency edges, admitting bounded workers with disjoint leases, verifying each result independently, selecting among candidate implementations, converging shared state, and handing off a reviewable stack. Concrete code-intelligence providers, parsers, symbol tools, executors, vector projections, schedulers, and consumer commands are domain modules.
---

# Agentic Tech Lead Orchestration

<!-- PORTABLE_CORE_START -->

## Contract

The core owns task-contract compilation, invariant extraction, true dependency DAGs, capability-plan compilation, worker/attempt identity, lease admission, independent verification, candidate comparison, convergence ownership, global-objective retention, and delivery handoff. Concrete tool/runtime implementations live in `modules/domain-profile.md`.

The core owns two independent admission layers:

1. a two-stage task-packet gate: `scripts/check_task_contract_schema.py` validates shape against `references/task-contract.schema.json`, then `scripts/assert_task_contract.py` evaluates semantic/hard-law assertions and emits a receipt;
2. a capability-causality gate: `scripts/assert_capability_dag.py` validates `references/capability-plan.schema.json` plus receipts shaped by `references/capability-receipts.schema.json`, then enforces predecessor closure, trigger/selection consistency, identity binding, and receipt-gated admission to downstream states.

Structural core/domain separation is a third assertion and cannot substitute for either admission layer. A Markdown module link proves reachability only; it does not prove runtime execution or authorize the next state.

## State machine

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ CAPABILITY_PLAN_COMPILED
→ CAPABILITY_PLAN_ASSERTED
→ CONTEXT_ADMITTED
→ TASK_DAG_COMPILED
→ TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_ASSERTED
→ DELIVERY_HANDOFF
```

`references/t0-t10-causal-map.json` is the machine-readable compatibility map from the former T0–T10 stages to these portable states and capability transitions.

## Hard laws

- **CORE-LAW-001 — contracts before workers.** Freeze exact subject, invariants, task inputs/outputs, dependencies, acceptance criteria, negative controls, budgets, authority, and capability triggers before fan-out.
- **CORE-LAW-002 — dependency edges must be real and writers disjoint.** A dependency exists only when a task consumes another task's unmerged contract/bytes/state; active writers may not overlap path/resource leases.
- **CORE-LAW-003 — worker/provider output is candidate evidence.** Results require exact-source readback and owning assertions; self-report, index hits, graph edges, or process exit zero cannot become correctness `PASS` by themselves.
- **CORE-LAW-004 — modules cannot widen authority.** Capability modules may implement retrieval/execution but cannot fabricate dependencies, weaken oracles, suppress failures/dissent, or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — convergence preserves the global objective.** Candidate selection and shared-state integration happen only after prerequisites are verified; local task success cannot override frozen repository/system invariants.
- **CORE-LAW-006 — capability transitions are receipt-gated.** A selected module can contribute to a downstream state only when its frozen trigger matches, every selected predecessor is closed by an identity-matched receipt, predecessor output states are consumed, and an admissible receipt for the same task/subject/module closes the transition. Plan presence, installation, or fixture evidence cannot self-promote to live runtime `PASS`.

## Procedure

1. Bind exact repository/system/task subject, objective, non-goals, constraints, and Human-owned operations.
2. Extract system invariants, interfaces, unknowns, evidence requirements, rollback conditions, and shared-state owners.
3. Compile a provider-neutral capability plan from the frozen task needs using `modules/domain-profile.md`. Record one transition per capability with trigger evidence, selection state, predecessor transitions, required input states, produced state, downstream admission state, fallback, and authority ceiling.
4. Validate the capability plan structurally before executing a module:

   ```bash
   python3 skills/agentic-tech-lead-orchestration/scripts/assert_capability_dag.py \
     --contract <task-contract.json> \
     --plan <capability-plan.json> \
     --receipts <capability-receipts.json>
   ```

   Structural validation may use an empty receipt set. It proves only plan topology and contracts.
5. Execute only the modules whose frozen trigger selects them. Every invocation emits a capability receipt bound to task id, exact subject, transition id, module path, attempt id, input states, output state, evidence digest, evidence kind, readback state, and authority ceiling. Non-selected modules stay unloaded.
6. Before admitting a downstream state that depends on capability execution, run the cumulative causal gate:

   ```bash
   python3 skills/agentic-tech-lead-orchestration/scripts/assert_capability_dag.py \
     --contract <task-contract.json> \
     --plan <capability-plan.json> \
     --receipts <capability-receipts.json> \
     --admit-state <STATE>
   ```

   In normal runtime this accepts only `LIVE` receipts. `FIXTURE` receipts are valid solely with `--fixture-mode` in deterministic tests and can never authorize production state advancement.
7. Admit `CONTEXT_ADMITTED` only after every selected capability required at or before that state is closed or an explicitly admitted fallback receipt closes the optional transition. A `REQUIRED` capability has `fallback=STOP` and fails closed.
8. Compile the task DAG from admitted context, then run the two-stage task gate in order:
   - `python3 scripts/check_task_contract_schema.py --contract <task-contract.json>`;
   - `python3 scripts/assert_task_contract.py --contract <task-contract.json> --receipt <receipt.json>`.
   Any non-zero result blocks dispatch. Preserve both verdicts with the exact task subject.
9. Admit parallel workers only when scopes are disjoint and prerequisites/capabilities are satisfied; otherwise choose bounded serial/single-worker execution.
10. Build each Worker packet from the frozen contract and `references/fanout-prompt.md`; modules may add bounded invocation details but may not replace the contract envelope.
11. Before `ATTEMPTS_EXECUTED`, require the cumulative capability gate to close any selected executor transition. Execute attempts with unique identities, observable artifacts, bounded retries, and no private-reasoning requirement.
12. Verify every result independently; stale/wrong-subject/out-of-lease results fail closed and remain in the denominator.
13. Before `CANDIDATES_COMPARED`, close any selected tournament transition. Compare valid candidates on frozen correctness, risk, cost, reviewability, and rollback criteria rather than model preference.
14. Converge shared indexes/contracts/state through one explicit owner after prerequisites are verified.
15. Assert both local task oracles and the frozen global objective. Before `DELIVERY_HANDOFF`, close any selected delivery transition; merge/release/promotion remain Human/repository authority.

## Module selection

Load `modules/domain-profile.md` only when concrete code-intelligence providers, parsers, symbol/executor tools, projections, schedulers, runtime carriers, or consumer commands must be bound. That profile is the only provider-specific router. Selection must be materialized in a capability plan, not inferred ad hoc during execution.

For each selected module, the runtime chain is:

```text
frozen predecessor states / predecessor receipts
→ trigger predicate + evidence
→ REQUIRED | OPTIONAL_SELECTED
→ exact module path
→ identity-bound invocation
→ capability receipt
→ cumulative causal assertion
→ downstream state admission
```

A module may never activate itself merely because a tool is installed. `NOT_APPLICABLE` transitions produce no module receipt. Optional fallback must itself be recorded as a receipt; silent substitution is forbidden.

## Executable assertions

Four assertion surfaces have distinct authority and all must stay reachable:

```bash
# Refactor/boundary integrity. Does not admit a task or capability.
python3 scripts/check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration

# Capability plan / receipt causal DAG. Default admission requires LIVE receipts.
# Contracts: references/capability-plan.schema.json + references/capability-receipts.schema.json
python3 skills/agentic-tech-lead-orchestration/scripts/assert_capability_dag.py \
  --contract <task-contract.json> \
  --plan <capability-plan.json> \
  --receipts <capability-receipts.json> \
  --admit-state <STATE>

# Task Stage 1: Draft 2020-12 packet shape.
python3 skills/agentic-tech-lead-orchestration/scripts/check_task_contract_schema.py \
  --contract <task-contract.json>

# Task Stage 2: semantic/hard-law assertions and receipt.
python3 skills/agentic-tech-lead-orchestration/scripts/assert_task_contract.py \
  --contract <task-contract.json> \
  --receipt <receipt.json>
```

Exit contract:

```text
0   the named gate passed for the declared subject/evidence mode
2   input was evaluable and the named gate found a contract/causal violation
64  usage/JSON/required input invalid or absent where supported
70  assertion mechanism, schema, or validator unavailable/invalid
```

A capability-gate `0` in `--fixture-mode` proves checker behavior only. A live state admission requires identity-matched `LIVE` receipts and still does not prove downstream correctness, mergeability, or Human Admit.

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`. Provider/tool implementation, module selection, fixture validation, and live runtime execution remain distinct evidence classes.

## Stop and handoff

Stop on missing system contract, invalid capability plan, false trigger/selection state, absent/cyclic predecessor, receipt identity mismatch, missing required live receipt, unadmitted fallback, failed schema gate, failed semantic task-contract assertion, false task dependency graph, overlapping leases, failed oracle, stale result, unresolved safety dissent, unavailable required capability, budget exhaustion, or Human-owned merge/release/promotion.

Handoff includes task DAG, capability plan, selected/non-selected module states, capability receipts and evidence kinds, causal-admission receipts/results, task schema-gate state, semantic task-contract receipt, attempts, leases, verified results, rejected candidates, convergence subject, global-objective receipt, residual `NOT_EXERCISED` lanes, and next delivery authority.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Existing deterministic task-graph/evidence mechanisms remain reusable; product-specific adapters must stay outside the portable core.
