# GitHub PR CADG adapter

Trigger-selected adapter for material GitHub pull requests. The portable CADG
packet stays in `human-led-agentic-engineering`; this module owns only GitHub
event binding, content-manifest recomputation, exact-head receipt emission and
the independent-Shadow boundary.

## State Machine

```text
PR_READY_EVENT_BOUND
→ CHANGED_PATHS_CLASSIFIED
    ├── non-material + no packet → NOT_APPLICABLE
    └── material or packet
         → PACKET_VALIDATED
         → DECLARED_DELTA_RECONCILED
         → CODE_MANIFEST_RECOMPUTED
         → EXACT_PR_SUBJECT_BOUND
         → SHADOW_BOUND_OR_NOT_EXERCISED
         → HUMAN_ADMISSION_BOUND_OR_REQUIRED
         → ADMISSION_RECEIPT_EMITTED
```

## Data flow

```text
GitHub PR event + checked-out head
+ changed file list
+ consumer packet under .agents/cadg/packets/
+ optional independent Shadow/Human receipts
→ zero-network core checker
→ delta-path content manifest
→ exact PR base/head/tree receipt
→ artifact / later convergence
```

`CODE`, `CADG`, `SHADOW` and `HUMAN` are separate fields. This adapter never
turns GitHub status, CI green, packet prose or Builder self-review into a later
lane. The receipt is generated outside the Git tree to avoid self-reference.
