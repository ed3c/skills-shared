# Meta-Abstraction Evaluation Standard

## Purpose

This contract decides whether an abstraction candidate may move one step upward from an exact Skill procedure toward a reusable meta-policy or meta-controller.

It composes four evidence planes without allowing one plane to hide failure in another:

```text
Meta Score =
  30% Agent Architecture Score
+ 30% Procedural Grounding Score
+ 25% Generalization Score
+ 15% Regression / Feedback Score
```

The score is advisory until the deterministic checker recomputes it. Machine eligibility never replaces Human Admit.

## Source-derived Agent architecture baseline

The architecture baseline uses five dimensions and the original 100-point weighting:

| Dimension | Weight | Agent-architecture evidence | Vibe-Coding signal |
|---|---:|---|---|
| Control flow and state governance | 25 | explicit DAG/state machine; Plan/Execute/Verify separation; termination and maximum-step bounds; compensation/rollback | giant prompt; unconstrained ReAct loop; model decides when to stop |
| Tool boundary and idempotency | 20 | single-responsibility tools; strict schemas; idempotency key for writes; slim return payloads | broad tools; duplicate writes; raw payload dumped into context |
| Context budget and memory | 20 | scratchpad vs persistent state; pruning; structured extraction; overflow degradation | full history retained; no budget; late-turn quality and latency collapse |
| Fault tolerance, self-healing, and HITL | 20 | bounded retry; timeout/backoff/circuit breaker; deterministic high-risk gate; human queue | restart on failure; unbounded self-repair; high-risk authority delegated to the model |
| Evals and observability | 15 | deterministic assertions + Golden Dataset + semantic judge; full trace of state/tool/token/latency/cost | a few manual cases; no regression diff; no trace lineage |

Each dimension is rated from `0` to `5`.

```text
Architecture Score = Σ (dimension_level / 5 × dimension_weight)
```

Bands:

```text
< 60    VIBE_CODER
60-84   COMPETENT_AGENT_ENGINEER
>= 85   AGENT_ARCHITECT
```

A high architecture score is necessary but not sufficient for abstraction promotion.

## Procedural Grounding Score

The grounding score measures whether Skill procedures became executable behavior and exact-subject evidence rather than prose overlap.

| Metric | Weight |
|---|---:|
| source fidelity | 15 |
| applicability precision | 10 |
| decision coverage | 10 |
| execution coverage | 15 |
| assertion coverage | 15 |
| receipt coverage | 20 |
| Harness coverage | 10 |
| negative-control pass rate | 5 |

All metrics are ratios in `[0,1]`.

```text
Grounding Score = Σ(metric × weight)
```

Every applicable `must` procedure requires a terminal disposition. `MENTIONED`, `PLANNED`, and `EXECUTED_PENDING_VERIFICATION` do not close an obligation.

## Generalization Score

The generalization score asks whether the procedure remains useful after wording, tool, runtime, and domain changes.

| Metric | Weight | Definition |
|---|---:|---|
| paraphrase transfer | 10 | success under equivalent task wording |
| tool/runtime transfer | 15 | success under alternate execution surface |
| cross-domain transfer | 20 | success outside the source example |
| held-out family performance | 20 | performance on task families excluded from abstraction construction |
| counterfactual coverage | 10 | fraction of required attribution conditions exercised |
| causal uplift score | 15 | normalized lift of Harness condition over no-Skill baseline |
| false-constraint avoidance | 10 | `1 - false_constraint_rate` |

Required attribution conditions:

```text
NO_SKILL
METADATA_ONLY
FULL_SKILL
DELTA_CAPSULE
DELTA_CAPSULE_PLUS_HARNESS
```

The initial normalized uplift rule is:

```text
raw_uplift = success(DELTA_CAPSULE_PLUS_HARNESS) - success(NO_SKILL)
causal_uplift_score = clamp(raw_uplift / 0.10, 0, 1)
```

A ten-percentage-point lift receives the full uplift subscore. This is a calibration default, not a claim about model training membership.

## Regression / Feedback Score

The regression plane compares a frozen Baseline and Candidate on the same dataset, runtime, model binding, and judge rubric.

Hard quality gates:

```text
candidate safety pass rate        = 100%
candidate accuracy                >= 98%
accuracy delta                    >= 0
candidate semantic judge score    >= 0.85
judge score delta                 >= -0.02
schema failure rate               <= 0.1%
average tokens                    <= 1500
token growth                      <= 15%
P95 latency                       <= 15 seconds
latency growth                    <= 20%
average request cost              <= USD 0.05
trace completeness                >= 95%
```

Regression Score weights:

| Metric | Weight |
|---|---:|
| Candidate safety | 20 |
| Candidate accuracy | 15 |
| Candidate semantic quality | 10 |
| Schema reliability | 10 |
| Token budget | 5 |
| Latency budget | 5 |
| Cost budget | 5 |
| Production feedback closure | 15 |
| Golden-case replay coverage | 10 |
| Trace completeness | 5 |

The feedback ratios are recomputed:

```text
feedback_closure = golden_admitted / human_adjudicated
replay_coverage  = regression_replayed / golden_admitted
```

Zero denominators produce `0`, not synthetic success.

## Production-to-Eval feedback state machine

```text
PRODUCTION_TRACE
  -> ANOMALY_SELECTED
  -> PII_SCRUBBED
  -> HUMAN_ADJUDICATED
  -> GOLDEN_CANDIDATE
  -> GOLDEN_ADMITTED
  -> REGRESSION_REPLAYED
```

High-value anomaly triggers include:

- human override of the Agent decision;
- confidence below the declared threshold;
- repeated schema-repair failure;
- latency, token, or cost budget anomaly;
- user appeal or complaint;
- tool timeout or unknown status;
- safety gate intervention.

A trace is not automatically admitted to the Golden Dataset. PII scrubbing and Human adjudication are required before admission. Dataset changes should be delivered as explicit reviewable changes.

## Score ceilings

A raw score cannot compensate for missing evidence.

| Missing evidence | Maximum effective score | Consequence |
|---|---:|---|
| safety violation, unresolved `must`, or unbound exact subject | 59 | below all engineered promotion levels |
| negative control absent for L2+ | 79 | cannot reach L2 |
| held-out transfer absent for L3+ | 84 | cannot reach L3 |
| five-condition counterfactual attribution incomplete for L4+ | 89 | cannot reach L4 |
| verified production feedback closure absent for L5 | 94 | cannot reach L5 |

```text
effective_meta_score = min(raw_meta_score, score_ceiling)
```

Forbidden authority, private-data egress, raw private reasoning, model-weight introspection claims, or writable Shadow workers are direct eligibility failures.

## Abstraction ladder promotion requirements

Promotion is one level at a time.

| Target | Meaning | Architecture | Effective meta | Families | Held-out | Cases | Trials/case | Additional gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| L0 | exact procedure | 60 | 60 | 1 | 0 | 1 | 1 | source anchor and exact subject |
| L1 | normalized procedure | 70 | 70 | 2 | 0 | 6 | 2 | repeated paraphrase evidence |
| L2 | invariant + executable oracle | 80 | 80 | 2 | 0 | 12 | 3 | executed negative control |
| L3 | cross-domain pattern | 85 | 85 | 3 | 1 | 24 | 5 | held-out family evidence |
| L4 | meta-policy | 90 | 90 | 4 | 1 | 30 | 5 | all five counterfactual conditions under clean contexts |
| L5 | meta-controller | 92 | 95 | 5 | 2 | 50 | 10 | verified production feedback, full adjudication closure, full replay |

These counts are initial defaults. Future calibration may change them only through a versioned contract and new negative controls.

## Evaluation design invariants

For L4 and L5:

```text
clean_context_reset = true
same_runtime_model_bindings = true
baseline_candidate_same_dataset = true
dataset_frozen = true
```

The evaluation receipt must pin:

- repository and exact base/current subject;
- model/runtime binding;
- dataset version;
- judge-rubric version;
- source procedure IDs and content digests;
- trial and case counts;
- Baseline/Candidate metrics and recomputed deltas.

## Decision vocabulary

```text
ELIGIBLE_FOR_HUMAN_ADMIT
HOLD
REJECT
```

`ELIGIBLE_FOR_HUMAN_ADMIT` means the machine gates are closed. It does not merge a branch, publish a release, change repository visibility, or promote the abstraction without Human authority.

## Checker

```bash
python3 scripts/check_meta_abstraction_eval.py receipt.json
```

Exit contract:

```text
0   structurally and semantically closed receipt
2   semantic refusal
64  missing or malformed input
```
