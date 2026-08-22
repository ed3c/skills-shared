# Spatial-Loop System Spec Packet

Use this packet before core implementation. Delete no section merely because its
answer is unknown; record `ABSENT`, `NOT_IMPLEMENTED`, or `NOT_EXERCISED`.

## 1. Subject

```text
Subject ID:
Repository/path or artifact:
Revision:
SHA-256 digest:
Configuration digest:
Environment identity:
Owner:
Date:
```

## 2. Objective and non-goals

```text
Objective:
Risk class: LOW | MEDIUM | HIGH | CRITICAL
Non-goals:
Forbidden claims:
Human acceptance authority:
```

## 3. Claims, assumptions, and unknowns

| ID | Type | Statement | Owner | Falsifier/discovery method | Impact | State | Evidence |
|---|---|---|---|---|---|---|---|

## 4. Intent–Case–Proof sidecar

For copy/migrate/port/replace/sync/merge/refactor/rewrite work, and whenever behavior preservation or scope completeness is material, bind a `spatial-loop-case-graph/v1` sidecar. Short prompt wording does not authorize semantic reduction.

```text
Prompt / source behavior
→ Intent Atom
→ Semantic Axis
→ Use / Edge Case
→ Invariant or State Path
→ Implementation Binding
→ Oracle / Negative Control
→ Exact-subject Evidence
```

Record at least:

| ID | Kind | Statement / classification | Disposition / owner | Case / implementation | Oracle | Evidence state |
|---|---|---|---|---|---|---|

Required semantic axes for migration-like work are considered explicitly and either marked applicable or explicitly not applicable with rationale: interface compatibility, control/decision logic, data/state semantics, failure/recovery, lifecycle/concurrency, side effects/idempotency, authority/permission, observability/error contract, and resource/performance behavior where material.

Every source behavior has exactly one disposition:

```text
PRESERVE_EXACT
PRESERVE_OBSERVABLE
ADAPT_WITH_COMPATIBILITY
INTENTIONAL_CHANGE
DEFER_EXPLICIT
DROP_EXPLICIT
UNKNOWN_BLOCKING
```

`INTENTIONAL_CHANGE`, `DEFER_EXPLICIT`, `DROP_EXPLICIT`, and explicit scope reduction require a named authority decision. `UNKNOWN_BLOCKING` blocks the dependent material transition. Runtime state machines may cycle; the ICPG provenance graph may not.

Machine authority: [`case-graph.schema.json`](case-graph.schema.json) plus [`../scripts/check_case_graph.py`](../scripts/check_case_graph.py). This section is navigation only.

## 5. Spatial topography

### Realms

| ID | Trust | Authority | Entry conditions | Exit conditions |
|---|---|---|---|---|

### Boundaries

| ID | From | To | Mechanism | Enforcement owner | Blast radius | Failure behavior |
|---|---|---|---|---|---|---|

### Flows

| ID | From | To | Payload/ownership | Transport | Ordering | Backpressure | Failure semantics |
|---|---|---|---|---|---|---|---|

## 6. Lifecycle state machine

```text
Initial state:
Terminal states:
Illegal transitions:
Cancellation path:
Crash path:
Recovery path:
```

| Transition ID | From | To | Trigger | Preconditions | Postconditions | Evidence |
|---|---|---|---|---|---|---|

## 7. Hard invariants

| ID | Statement | Scope | Owner | Enforcement | Oracle | Failure state |
|---|---|---|---|---|---|---|

For concurrent systems also record ownership, synchronization order, memory
visibility, cancellation semantics, and race/deadlock oracle.

## 8. Capability matrix

| ID | Capability | Required | Probe | State | Evidence | Consequence if absent |
|---|---|---|---|---|---|---|

## 9. Resource envelope

| ID | Realm | Kind | Limit | Unit | Enforcement | Observation | Exceed action | Lifecycle-owned |
|---|---|---|---|---|---|---|---|---|

## 10. Failure/collision matrix

| ID | Fault | Collision window | Detection | Containment | Reconciliation | Oracle |
|---|---|---|---|---|---|---|

## 11. Teardown symmetry

| Resource | Acquire transition | Release transition | Crash path | Leak oracle |
|---|---|---|---|---|

## 12. Reconciliation loops

| ID | Observes | Desired state | Diff | Actuator | Convergence | Stop condition |
|---|---|---|---|---|---|---|

## 13. Performance budgets

| Metric | Target | Unit | Percentile | Load model | Environment identity | Measurement | Repetitions |
|---|---|---|---|---|---|---|---|

Leave the table empty only when the objective contains no performance claim.

## 14. Verification lanes

| ID | Required | Lane | Preconditions | Stimulus | Oracle | Negative control | Status | Evidence |
|---|---|---|---|---|---|---|---|---|

When an ICPG sidecar is required, report its independent coverage values rather than one aggregate score:

```text
Intent Coverage
Source Behavior Disposition Coverage
Required Case Coverage
Implementation Binding Coverage
Oracle Coverage
Executed Evidence Coverage
Unknown Blocking Count
```

Execution coverage is not correctness. `READY_FOR_PUBLICATION_REVIEW` requires every required case to have subject-bound `PASS` evidence.

## 15. Implementation gate

```text
Status: BLOCKED | READY_FOR_PROTOTYPE | READY_FOR_IMPLEMENTATION
Claim level: DESIGN_ONLY | PROTOTYPE_ONLY | IMPLEMENTATION_CANDIDATE
Blocking unknown IDs:
Allowed actions:
Forbidden claims:
Rationale:
```

There is no Agent-declared production-ready state.

## Field skeleton (intentionally invalid until populated)

This skeleton is a field map, not a passing fixture. It must fail the checker
until every required array, reference, oracle, and gate field is populated.

```json
{
  "schema": "spatial-loop-system-contract/v1",
  "subject": {
    "id": "system-id",
    "revision": "exact-revision",
    "digest": "sha256:<64 lowercase hex>"
  },
  "objective": {
    "statement": "One exact objective.",
    "non_goals": ["One explicit non-goal."],
    "risk_class": "HIGH"
  },
  "assumptions": [],
  "unknowns": [],
  "realms": [],
  "boundaries": [],
  "flows": [],
  "states": {
    "nodes": [],
    "initial": "",
    "terminal": [],
    "transitions": []
  },
  "invariants": [],
  "capabilities": [],
  "resources": [],
  "failures": [],
  "teardown": [],
  "reconciliation_loops": [],
  "performance_budgets": [],
  "verification": [],
  "implementation_gate": {
    "status": "BLOCKED",
    "claim_level": "DESIGN_ONLY",
    "blocking_unknowns": [],
    "allowed_actions": [],
    "forbidden_claims": [],
    "rationale": ""
  },
  "human_admit": []
}
```

The complete system-contract field rules are enforced by
`../scripts/check_system_contract.py`; ICPG sidecar rules are enforced by
`../scripts/check_case_graph.py`. Markdown is navigation, not a second schema authority.

## Case-delta obligations (ICPG sidecar)

A spec packet that copies, migrates, ports, replaces, or otherwise preserves existing
behavior carries the Shadow case-delta obligations from `architecture-watch-loop.md`:

```text
delta classes   INTENT_INTERPRETATION_DELTA, SCOPE_REDUCTION_DELTA, USE_CASE_DELTA,
                EDGE_CASE_DELTA, SEMANTIC_PARITY_DELTA, CASE_COVERAGE_DELTA,
                CASE_ORACLE_DELTA, SOURCE_BEHAVIOR_DISPOSITION_DELTA
monitor asks    Which intent/source behavior made this path necessary?
                Which existing or new case covers it?
                Which semantic axis changed?
                Which oracle can detect its loss?
                Did this change silently narrow scope?
intervention    L0 OBSERVE · L1 WARN · L2 REVIEW · L3 BLOCK
checkpoints     ARCHITECTURE_CHOICE, FIRST_VERTICAL_SLICE, FIRST_GREEN,
                BEFORE_COMMIT (when critical case proof owns eligibility),
                BEFORE_PR_OR_PUBLICATION
```

The packet's `implementation_gate` cannot claim readiness while a required case, its
oracle, or its source-behavior disposition is unresolved at the current checkpoint.
