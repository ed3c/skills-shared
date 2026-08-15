# PRECHECK mode

Use PRECHECK when a material transition is high-risk or difficult to reverse.

Typical triggers: production migration, payment/financial mutation, trust/security boundary changes, kernel/virtualization changes, destructive tests, permission widening, production deployment, or another Human-admitted critical path.

Run the complete Constraint-First A–L packet for the risky boundary before crossing it. Reversible exploration outside that boundary may continue.

PRECHECK returns exactly one material-boundary gate:

```text
BLOCKED
READY_FOR_PROTOTYPE
READY_FOR_IMPLEMENTATION
```

It does not create `PRODUCTION_ACCEPTANCE`; Human or organizational authority remains required where applicable.