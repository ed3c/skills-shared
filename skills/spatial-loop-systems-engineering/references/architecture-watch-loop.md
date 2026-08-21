# Shadow Architecture Watch Loop

`MONITOR` is the default operating mode. It preserves Builder exploration while watching for material System Design, intent, case-coverage and evidence drift.

## Role separation

```text
Builder
  owns solution search and implementation mutation

Shadow Architect
  owns architecture/case observation, delta classification, hidden-assumption discovery,
  semantic-preservation/invariant/evidence reconciliation, and intervention recommendation
```

The Shadow Architect must not become a second implementation writer. It may propose a falsifier, required case, or design reconciliation, but it does not silently rewrite the Builder's strategy.

## Watch loop

```text
BUILDER_ACTION
→ OBSERVE_DELTA
→ CLASSIFY_DELTA
→ PREDICT_HARD_LAWS_AND_CASE_OBLIGATIONS
→ COMPARE_CURRENT_MODEL_AND_CASE_GRAPH
├─ no material drift → L0 OBSERVE → CONTINUE
└─ material drift
   → choose L1 WARN | L2 REVIEW | L3 BLOCK
   → update assumptions/invariants/cases/oracles
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
PROCEDURAL_GROUNDING_DELTA
INTENT_INTERPRETATION_DELTA
SCOPE_REDUCTION_DELTA
USE_CASE_DELTA
EDGE_CASE_DELTA
SEMANTIC_PARITY_DELTA
CASE_COVERAGE_DELTA
CASE_ORACLE_DELTA
SOURCE_BEHAVIOR_DISPOSITION_DELTA
```

`PROCEDURAL_GROUNDING_DELTA` means a relevant searched/installed Skill procedure was newly discovered, omitted from the implementation Harness, reduced to prose, executed without evidence, or contradicted by runtime observation. When this class is material, compose [`procedural-grounding-shadow-plane.md`](procedural-grounding-shadow-plane.md).

The intent/case delta classes are governed by [`intent-case-proof-graph.md`](intent-case-proof-graph.md). They apply whenever the task has explicit or inferred source behavior, use/edge cases, migration/copy/refactor semantics, or implementation-discovered branches that can narrow the user's actual objective.

For every material delta ask:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
```

For an intent/case/semantic delta additionally ask:

```text
Which intent or source behavior made this path necessary?
Which existing or new case covers it?
Which semantic axis changed?
Which oracle can detect its loss?
Did this change silently narrow scope?
```

For a procedural-grounding delta additionally ask:

```text
Which exact Skill source and procedure span applies?
Was it only discovered, mentioned, planned, encoded, executed, or observed?
What proof mode does the procedure require?
Would a bounded context fork add actionable coverage now?
Which smallest assertion or negative control closes the gap?
```

## Case-delta trigger surfaces

Treat these code/system changes as candidate case deltas even when existing tests remain green:

```text
new or removed branch/validation
new or removed state/transition
new error type or error mapping
retry/timeout/cancellation change
background/async/concurrency introduction
schema/version compatibility path
new authority/permission check
new external side effect
cache/persistence/default/fallback change
ordering or idempotency change
source behavior removed or substituted
```

A short prompt does not authorize the Builder to collapse applicable semantic axes. For copy/migrate/port/replace/sync/merge/refactor/rewrite work, a compatibility path cannot silently substitute for control/decision logic, state/data, failure/recovery, lifecycle/concurrency, side-effect/idempotency, authority, observability, or resource/performance obligations when those axes are material.

## Intervention levels

- `L0 OBSERVE`: record only; case bindings and proof obligations remain closed.
- `L1 WARN`: surface a new assumption, candidate case, unbounded quantity, evidence limitation, or non-critical procedure gap; Builder may continue.
- `L2 REVIEW`: architecture/case reconciliation is required before the next major checkpoint. Use when a required case/oracle is missing, source-behavior disposition changed, or prompt interpretation narrowed semantics without authority.
- `L3 BLOCK`: stop a material/irreversible transition when an `UNKNOWN_BLOCKING` case/behavior remains, source logic is being implicitly dropped, a critical required case lacks an oracle, authority is widened, destructive/security-sensitive behavior is unbound, or evidence/coverage would be falsely promoted.

Do not use L2/L3 merely because the Shadow Architect prefers a different framework, Skill, abstraction, or style.

## Mandatory checkpoints

Run a meta-review after:

```text
SKILL_DISCOVERY when external/retrieved procedures are material
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
NOVELTY_OR_DIVERGENCE when model/runtime/Skill behavior conflicts
FIRST_GREEN
BEFORE_COMMIT when a critical procedure or case proof owns commit eligibility
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
Which required Skill procedures exist only in prose?
Which critical procedures require an executed assertion or negative control?
Which declared intent/source behaviors have no required case?
Which required cases have no implementation binding or oracle?
Did compatibility remain green while semantic parity regressed?
Did the implementation create a new branch/state/error/fallback absent from the case graph?
```

A green test remains green for its bound subject; the review prevents semantic over-promotion. `FIRST_GREEN` cannot erase an unresolved required case or `UNKNOWN_BLOCKING` member.

`BEFORE_PR_OR_PUBLICATION` additionally requires recomputing the case-graph coverage lanes against current implementation/evidence subject. The checker is:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_case_graph.py \
  check path/to/case-graph.json
```

## Bounded context-fork rule

A procedural fork is admitted only when it closes a named procedure/evidence gap at the current checkpoint and fits the repository multi-Agent runtime budget.

```text
exact task/runtime/context subject
+ reviewed Skill source and procedure atoms
+ independent uncertainty or critical gap
+ bounded fork/depth/token/no-progress policy
+ expected actionable Context Capsule
→ fork admitted
```

The fork returns a source-grounded action/assertion/probe/blocker capsule, not a private reasoning trace. The parent runtime receives no payload when the capsule is stale, low-fidelity, low-relevance, duplicative, over budget, or conflicts with higher authority.

## Silent-failure rules

Treat these as architecture/case signals even when tests are green:

- retries added around an external side effect without stable operation identity;
- cache added without a named consistency model;
- queue/worker added without duplicate/order/crash semantics;
- background cleanup added without lifecycle ownership and leak oracle;
- new mutable shared state without serialization ownership;
- new privilege or credential propagation without authority analysis;
- unbounded memory/queue/log/task/context-fork growth;
- success inferred from transport-level status only;
- evidence reused across a changed subject, environment, or revision;
- a Skill procedure counted as implemented because the model mentioned it;
- an execution-required procedure credited without a command/tool/runtime receipt;
- a verifier trusted without an executed planted defect;
- an external Skill executed because it ranked well or installed successfully;
- a raw fork transcript injected into the parent context instead of a bounded capsule;
- prompt brevity treated as permission to drop a semantic axis;
- source behavior removed without an explicit disposition;
- `DROP_EXPLICIT`, `DEFER_EXPLICIT`, `INTENTIONAL_CHANGE`, or scope reduction without an admitted decision record;
- compatibility-only success used to claim copy/migration semantic parity;
- a required case omitted from Tech Lead task ownership or convergence ownership;
- a newly reachable implementation branch/state/error/fallback absent from current case accounting;
- case coverage percentage trusted from prose instead of recomputed from the denominator.

## Checkpoint outcome

Every checkpoint returns one of:

```text
CONTINUE_L0
CONTINUE_WITH_WARNINGS_L1
RECONCILE_BEFORE_NEXT_STEP_L2
BLOCKED_AT_MATERIAL_BOUNDARY_L3
```

The outcome is not production acceptance. Human-owned authority remains unchanged. Static/deterministic monitor controls establish only the declared repository bytes; live continuous Shadow execution remains `NOT_EXERCISED` until an exact-subject runtime receipt exists.
