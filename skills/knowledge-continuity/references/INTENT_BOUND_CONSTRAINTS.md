# knowledge-continuity Intent-Bound Constraints

This adapter maps the existing `Measure → Classify → Repair → Re-measure` procedure to stable meta-intents. It reuses `scripts/check_knowledge_continuity.py`; it does not introduce a second continuity engine.

## Intent map

| Intent | Proof obligation | Deciding lane |
|---|---|---|
| `MI-KC-CANONICAL` | one governed claim has one accepted authority | Human causal review / repository authority receipt |
| `MI-KC-FRESHNESS` | a derived route or projection binds the current subject | exact-subject external receipt |
| `MI-KC-TRACE` | each route hop contains an in-place summary and direct evidence route | existing `KC-01`, `KC-02`, `KC-05` checker controls |
| `MI-KC-AMBIGUITY` | unresolved authority ambiguity blocks acceptance | Human causal review |
| `MI-KC-EVIDENCE` | document presence and prose do not proxy executable or subject-bound evidence | existing checker plus Human causal review |

## Existing evaluator registration

```text
scripts/check_knowledge_continuity.py
  KC-01 external-memory reference
  KC-02 wrong section reference
  KC-03 approximate number
  KC-04 knowledge outsourcing
  KC-05 two hops before evidence
```

The existing checker owns mechanical continuity only. It cannot decide whether a canonical source is semantically correct, whether a projection digest is current, or whether an unresolved cross-file claim should be accepted. Those lanes remain `NOT_IMPLEMENTED` as deterministic checks and require an exact external receipt or Human causal review.

## Repair loop

```text
mechanical break
→ affected intent and rule ID
→ repair local summary or direct route
→ expect rule_violation_count to decrease
→ re-run checker and hollow controls

semantic authority ambiguity
→ BLOCK
→ HUMAN_ADMIT_REQUIRED
```

A repair cannot delete a negative control, weaken a rule, promote an old receipt, or silently choose an authority.

## Evidence boundary

```text
mechanical continuity checker      IMPLEMENTED
positive and hollow controls       IMPLEMENTED
intent/constraint closure          IMPLEMENTED by repository-wide checker
canonical semantic uniqueness      NOT_IMPLEMENTED as deterministic check
projection digest freshness        NOT_IMPLEMENTED as deterministic check
cross-file ambiguity resolution    HUMAN_ADMIT_REQUIRED
consumer route receipts            NOT_EXERCISED
```
