# Shadow Architecture Watch Loop

`MONITOR` is the default operating mode. It preserves Builder exploration while watching for material System Design drift.

## Role separation

```text
Builder
  owns solution search and implementation mutation

Shadow Architect
  owns architecture observation, delta classification, hidden-assumption discovery,
  invariant/evidence reconciliation, and intervention recommendation
```

The Shadow Architect must not become a second implementation writer. It may propose a falsifier or required design reconciliation, but it does not silently rewrite the Builder's strategy.

## Watch loop

```text
BUILDER_ACTION
→ OBSERVE_DELTA
→ CLASSIFY_DELTA
→ PREDICT_HARD_LAWS
→ COMPARE_CURRENT_MODEL
├─ no material drift → L0 OBSERVE → CONTINUE
└─ material drift
   → choose L1 WARN | L2 REVIEW | L3 BLOCK
   → update assumptions/invariants/oracles
   → falsify or verify as required
   → CONTINUE or STOP
```

Classify material deltas as:

```text
ASSUMPTION_DELTA
STATE_DELTA
AUTHORITY_DELTA
OWNERSHIP_DELTA
LIFECYCLE_DELTA
CONCURRENCY_DELTA
RESOURCE_DELTA
EXTERNAL_SIDE_EFFECT_DELTA
FAILURE_SURFACE_DELTA
EVIDENCE_DELTA
```

For each material delta ask exactly:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

## Intervention levels

- `L0 OBSERVE`: record only; no interruption.
- `L1 WARN`: surface a new assumption, unbounded quantity, or evidence limitation; Builder may continue.
- `L2 REVIEW`: architecture reconciliation is required before the next major checkpoint.
- `L3 BLOCK`: the next transition is unsafe, irreversible, authority-expanding, destructive, security-sensitive, or could wrongly promote evidence. Stop that transition until the named blocker closes.

Do not use L2/L3 merely because the Shadow Architect prefers a different framework or style.

## Mandatory checkpoints

Run a meta-review after:

```text
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
FIRST_GREEN
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

`FIRST_GREEN` is always reviewed. Ask:

```text
What did these tests not prove?
Which assumptions remain implicit?
Which runtime/substrate was not exercised?
Which failure states remain untested?
Which side effects lack reconciliation?
Which evidence is stale, indirect, mock-only, or from another subject?
```

A green test remains green for its bound subject; the review prevents semantic over-promotion.

## Silent-failure rules

Treat these as architecture signals even when tests are green:

- retries added around an external side effect without stable operation identity;
- cache added without a named consistency model;
- queue/worker added without duplicate/order/crash semantics;
- background cleanup added without lifecycle ownership and leak oracle;
- new mutable shared state without serialization ownership;
- new privilege or credential propagation without authority analysis;
- unbounded memory/queue/log/task growth;
- success inferred from transport-level status only;
- evidence reused across a changed subject, environment, or revision.

## Checkpoint outcome

Every checkpoint returns one of:

```text
CONTINUE_L0
CONTINUE_WITH_WARNINGS_L1
RECONCILE_BEFORE_NEXT_STEP_L2
BLOCKED_AT_MATERIAL_BOUNDARY_L3
```

The outcome is not production acceptance. Human-owned authority remains unchanged.