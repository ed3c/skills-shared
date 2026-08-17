---
name: agentic-tech-lead-orchestration
description: |
  Portable Agentic Tech Lead procedure for compiling a request into typed task contracts, extracting invariants and unknowns, building only true dependency edges, admitting bounded workers with disjoint leases, verifying each result independently, selecting among candidate implementations, converging shared state, and handing off a reviewable stack or zero-context local execution queue. Concrete code-intelligence providers, parsers, symbol tools, executors, vector projections, schedulers, and consumer commands are domain modules.
---

# Agentic Tech Lead Orchestration

<!-- PORTABLE_CORE_START -->

## Contract

The core owns task-contract compilation, invariant extraction, true dependency DAGs, worker/attempt identity, lease admission, independent verification, candidate comparison, convergence ownership, global-objective retention, delivery handoff, and typed local-runtime handoff compilation. Concrete tool/runtime implementations live in `modules/domain-profile.md`.

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
→ LOCAL_HANDOFF_COMPILED when unresolved work requires local/runtime-host evidence
→ LOCAL_HANDOFF_EXECUTED by the admitted consumer/runtime authority
```

## Hard laws

- **CORE-LAW-001 — contracts before workers.** Freeze exact subject, invariants, task inputs/outputs, dependencies, acceptance criteria, negative controls, budgets, and authority before fan-out.
- **CORE-LAW-002 — dependency edges must be real and writers disjoint.** A dependency exists only when a task consumes another task's unmerged contract/bytes/state; active writers may not overlap path/resource leases.
- **CORE-LAW-003 — worker/provider output is candidate evidence.** Results require exact-source readback and owning assertions; self-report, index hits, graph edges, or process exit zero cannot become correctness `PASS` by themselves.
- **CORE-LAW-004 — modules cannot widen authority.** Capability modules may implement retrieval/execution but cannot fabricate dependencies, weaken oracles, suppress failures/dissent, or widen filesystem/network/secret/merge authority.
- **CORE-LAW-005 — convergence preserves the global objective.** Candidate selection and shared-state integration happen only after prerequisites are verified; local task success cannot override frozen repository/system invariants.
- **CORE-LAW-006 — handoff is executable state, not prose.** Work that cannot be completed in the current host/session must be compiled into a typed Local Handoff Execution Queue. Each item binds entry condition, exact subject, runtime/command lane, receipt contract, exit condition, and next item. Consumer issue IDs, commands, provider names, and runtime paths remain opaque consumer data.
- **CORE-LAW-007 — handoff cannot launder evidence or authority.** Static/synthetic evidence cannot satisfy a live/runtime receipt; issue UI state cannot prove completion; no handoff item may infer merge, issue close, queue advance, promotion, provider activation, rollback, permission change, or semantic-conflict resolution.

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
11. If any remaining item requires a different physical host, local-only runtime, private forge, signed-in carrier, device, provider session, or Human admission, compile `references/local-handoff-queue.schema.json` rather than leaving narrative TODOs.
12. For each handoff item, bind `entry → exact subject/capability prerequisites → command/runtime lane → durable receipt → exit PASS condition → next item`. Only one item is `ACTIVE`; successors remain `BLOCKED_BY_PREDECESSOR` until the predecessor exit receipt validates.
13. Preserve unresolved live lanes as `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, or `HUMAN_ADMIT_REQUIRED`; never upgrade them from static/synthetic evidence.
14. A local handoff executor must stop on stale subject, missing capability, invalid receipt, failed cleanup, Human-owned transition, or predecessor mismatch. It may advance only the consumer-owned handoff instance after a validated exit receipt; shared core does not mutate consumer issues or repositories.

## Local Handoff Execution Queue

Use this only when the current session has reached a real host/runtime boundary. Do not manufacture a handoff for work that can still be verified in the current environment.

Required queue item shape:

```text
entry condition
→ exact subject/runtime prerequisite
→ command/runtime lane
→ receipt contract
→ exit condition
→ next item
```

The consumer instance must additionally name rollback/cleanup boundaries and Human-owned operations. Commands must be concrete argv/cwd/timeout contracts; placeholders are invalid. Receipt paths must be durable and path-safe, and may not contain secrets, session material, machine-local credentials, or private reasoning.

Portable schema and assertion:

```bash
python3 scripts/assert_local_handoff_queue.py \
  --queue references/example-local-handoff-queue.json
python3 scripts/assert_local_handoff_queue.py \
  --queue references/example-local-handoff-queue.json --selftest
```

## Module selection

Load `modules/domain-profile.md` only when concrete code-intelligence providers, parsers, symbol/executor tools, projections, schedulers, runtime carriers, or consumer commands must be bound.

## Executable assertion

```bash
python3 scripts/check_skill_core_boundaries.py --skill agentic-tech-lead-orchestration
```

## Evidence states

Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED`. Provider/tool implementation and live runtime execution remain distinct.

## Stop and handoff

Stop on missing system contract, false dependency graph, overlapping leases, failed oracle, stale result, unresolved safety dissent, unavailable required capability, budget exhaustion, or Human-owned merge/release/promotion. Handoff includes task DAG, attempts, leases, verified results, rejected candidates, convergence subject, global-objective receipt, and next delivery authority. When the next authority is a local/runtime host, also include the validated Local Handoff Execution Queue so a zero-context executor can begin from its single `ACTIVE` item without re-deriving architecture.

<!-- PORTABLE_CORE_END -->

## Domain specialization

See [modules/domain-profile.md](modules/domain-profile.md). Existing deterministic task-graph/evidence mechanisms remain reusable; product-specific adapters must stay outside the portable core.
