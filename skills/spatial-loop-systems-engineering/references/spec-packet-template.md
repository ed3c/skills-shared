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

## 4. Spatial topography

### Realms

| ID | Trust | Authority | Entry conditions | Exit conditions |
|---|---|---|---|---|

### Boundaries

| ID | From | To | Mechanism | Enforcement owner | Blast radius | Failure behavior |
|---|---|---|---|---|---|---|

### Flows

| ID | From | To | Payload/ownership | Transport | Ordering | Backpressure | Failure semantics |
|---|---|---|---|---|---|---|---|

## 5. Lifecycle state machine

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

## 6. Hard invariants

| ID | Statement | Scope | Owner | Enforcement | Oracle | Failure state |
|---|---|---|---|---|---|---|

For concurrent systems also record ownership, synchronization order, memory
visibility, cancellation semantics, and race/deadlock oracle.

## 7. Capability matrix

| ID | Capability | Required | Probe | State | Evidence | Consequence if absent |
|---|---|---|---|---|---|---|

## 8. Resource envelope

| ID | Realm | Kind | Limit | Unit | Enforcement | Observation | Exceed action | Lifecycle-owned |
|---|---|---|---|---|---|---|---|---|

## 9. Failure/collision matrix

| ID | Fault | Collision window | Detection | Containment | Reconciliation | Oracle |
|---|---|---|---|---|---|---|

## 10. Teardown symmetry

| Resource | Acquire transition | Release transition | Crash path | Leak oracle |
|---|---|---|---|---|

## 11. Reconciliation loops

| ID | Observes | Desired state | Diff | Actuator | Convergence | Stop condition |
|---|---|---|---|---|---|---|

## 12. Performance budgets

| Metric | Target | Unit | Percentile | Load model | Environment identity | Measurement | Repetitions |
|---|---|---|---|---|---|---|---|

Leave the table empty only when the objective contains no performance claim.

## 13. Verification lanes

| ID | Required | Lane | Preconditions | Stimulus | Oracle | Negative control | Status | Evidence |
|---|---|---|---|---|---|---|---|---|

## 14. Implementation gate

```text
Status: BLOCKED | READY_FOR_PROTOTYPE | READY_FOR_IMPLEMENTATION
Claim level: DESIGN_ONLY | PROTOTYPE_ONLY | IMPLEMENTATION_CANDIDATE
Blocking unknown IDs:
Allowed actions:
Forbidden claims:
Rationale:
```

There is no Agent-declared production-ready state.

## Minimal JSON shape

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

The complete field rules are enforced by
`../scripts/check_system_contract.py`; this Markdown template is navigation, not
a second schema authority.
