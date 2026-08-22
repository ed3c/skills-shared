# CADG contracts

This directory owns the compact Context–Assumption–Decision causal-provenance interface for material engineering changes. It composes existing Context Capsule, architecture-watch, Tech Lead, Shadow and Stack owners; it does not duplicate them.

## Files

```text
cadg-packet.schema.json             packet shape and causal backbone
cadg-admission-receipt.schema.json  separate CODE/CADG/SHADOW/HUMAN result shape
controlled-vocabulary.md            terms, evidence lanes and refusal IDs
```

Positive examples are in `../../examples/cadg/`.

## Contract State Machine

```text
SOURCE_BOUND
→ CONTEXT_BOUND
→ ASSUMPTIONS_BOUND
→ DECISION_BOUND
→ DELTA_BOUND
→ CAUSAL_EDGES_BOUND
→ EVIDENCE_LANES_BOUND
→ INTERFACE_LOCKED
```

Schema validation proves shape only. Semantic and causal admission belongs to `../../scripts/check_cadg_packet.py` after the checker atom lands. Live Agent/Shadow, Human admission, merge and release remain separate evidence lanes.

## Two-subject persistence law

A committed forward packet binds an analyzed code manifest that excludes `.agents/cadg/**`; it does not claim to contain its own final Git head. Exact PR base/head/tree belongs to the CI admission receipt. CI recomputes the excluded-path manifest at the checked-out PR head and requires equality before emitting that receipt. Historical packets instead bind one exact Git subject.
