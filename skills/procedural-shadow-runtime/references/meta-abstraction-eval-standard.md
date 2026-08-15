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

The score is advisory until deterministic checkers recompute it. Machine eligibility never replaces Human Admit.

## Source-derived Agent Architecture baseline

The source matrix defines five dimensions and the original 100-point weights:

| Dimension | Weight | Positive controls | Vibe-Coding signals |
|---|---:|---|---|
| Control flow and state governance | 25 | explicit DAG/state machine; Plan/Execute/Verify separation; terminal and maximum-step bounds; compensation or safe pause | giant prompt; model decides termination; query-fail retry loop |
| Tool boundary and idempotency | 20 | single-responsibility tools; strict schemas; idempotent writes; slim outputs | broad manage tool; duplicate writes; raw payload dump |
| Context budget and memory | 20 | scratchpad/durable-state separation; pruning and structured extraction; token budget and overflow fallback | retain full history; no cleanup or budget |
| Fault tolerance, self-healing, and HITL | 20 | timeout/backoff/circuit breaker; bounded schema repair; deterministic high-risk gate and Human queue | crash/restart on tool error; high-risk authority delegated to model |
| Evals and observability | 15 | deterministic assertions + Golden Dataset + semantic judge; full trace; CI Baseline/Candidate regression | a few manual cases; no measurable prompt/model regression |

Bands remain:

```text
< 60    VIBE_CODER
60-84   COMPETENT_AGENT_ENGINEER
>= 85   AGENT_ARCHITECT
```

## Implementation calibration: atomic executable scoring

The source defines dimension weights and qualitative controls, but does not assign numeric points to each bullet. Version `agent-architecture-rubric/v1` therefore uses this explicit calibration:

1. each source-derived positive control becomes a stable criterion atom;
2. positive controls share their dimension weight equally;
3. every Vibe signal maps to the positive controls it contradicts;
4. a detected Vibe signal makes those mapped points unavailable;
5. `deduction_points` reports unavailable points and is not an arbitrary second subtraction;
6. critical non-idempotent writes and model-owned high-risk authority impose a score ceiling of `59`.

The machine authority is:

```text
references/agent-architecture-rubric.json
references/agent-architecture-eval-receipt.schema.json
scripts/agent_architecture_common.py
scripts/check_agent_architecture_eval.py
```

Architecture scoring procedure:

```text
versioned rubric
-> exact runtime/repository subject
-> all positive criteria
-> all Vibe signals
-> executable evidence
-> terminal states
-> contradiction refusal
-> dimension points
-> safety ceiling
-> effective 100-point score
-> band
```

Allowed evidence modes:

```text
STATIC_ASSERTION
RUNTIME_PROBE
TRACE_ASSERTION
NEGATIVE_CONTROL
```

`VERIFIED` and `NOT_DETECTED` require executable evidence bound to the exact subject. `NOT_EXERCISED` earns no points and cannot produce a `PASS` architecture receipt. Prose-only evidence is rejected.

The Meta-Abstraction receipt embeds a closed `agent-architecture-eval/v1` receipt. Free-form `0..5` dimension ratings are no longer authoritative.

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

Initial calibration:

```text
raw_uplift = success(DELTA_CAPSULE_PLUS_HARNESS) - success(NO_SKILL)
causal_uplift_score = clamp(raw_uplift / 0.10, 0, 1)
```

A ten-percentage-point lift receives the full uplift subscore. This is a versioned calibration default, not evidence of training-data membership.

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

Feedback ratios:

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

- Human override of the Agent decision;
- confidence below the declared threshold;
- repeated schema-repair failure;
- latency, token, or cost budget anomaly;
- user appeal or complaint;
- tool timeout or unknown status;
- safety-gate intervention.

A trace is not automatically admitted. PII scrubbing and Human adjudication are required, and dataset changes remain explicit reviewable changes.

## Score ceilings

A raw score cannot compensate for missing evidence.

| Missing evidence | Maximum effective score | Consequence |
|---|---:|---|
| safety violation, unresolved `must`, or unbound exact subject | 59 | below all engineered promotion levels |
| negative control absent for L2+ | 79 | cannot reach L2 |
| held-out transfer absent for L3+ | 84 | cannot reach L3 |
| five-condition attribution incomplete for L4+ | 89 | cannot reach L4 |
| verified production feedback closure absent for L5 | 94 | cannot reach L5 |

```text
effective_meta_score = min(raw_meta_score, score_ceiling)
```

Forbidden authority, private-data egress, raw private reasoning, model-weight introspection claims, or writable Shadow workers are direct eligibility failures.

The embedded architecture receipt applies its own safety ceilings before entering the Meta Score.

## Abstraction-ladder promotion requirements

Promotion is one level at a time.

| Target | Meaning | Architecture | Effective meta | Families | Held-out | Cases | Trials/case | Additional gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| L0 | exact procedure | 60 | 60 | 1 | 0 | 1 | 1 | source anchor and exact subject |
| L1 | normalized procedure | 70 | 70 | 2 | 0 | 6 | 2 | repeated paraphrase evidence |
| L2 | invariant + executable oracle | 80 | 80 | 2 | 0 | 12 | 3 | executed negative control |
| L3 | cross-domain pattern | 85 | 85 | 3 | 1 | 24 | 5 | held-out family evidence |
| L4 | meta-policy | 90 | 90 | 4 | 1 | 30 | 5 | all five attribution conditions under clean contexts |
| L5 | meta-controller | 92 | 95 | 5 | 2 | 50 | 10 | verified production feedback, full adjudication closure, full replay |

Counts are initial defaults. Change them only through a versioned contract and new negative controls.

## Evaluation-design invariants

For L4 and L5:

```text
clean_context_reset = true
same_runtime_model_bindings = true
baseline_candidate_same_dataset = true
dataset_frozen = true
```

The receipt must pin:

- repository and exact base/current subject;
- architecture-rubric bytes and atomic evidence;
- model/runtime binding;
- dataset version;
- judge-rubric version;
- source procedure IDs and content digests;
- trial and case counts;
- Baseline/Candidate metrics and recomputed deltas.

## Domain decoupling

The e-commerce dispute case is one task family under `modules/ecommerce-dispute/`.

Its USD 500 boundary, logistics timeout, vision evidence, refund/voucher tools, and cost/latency constants do not enter the universal rubric. The domain runner loads a consumer adapter and emits deterministic case receipts that can support generic criterion IDs.

```text
generic architecture criterion
-> domain mapping
-> executable case
-> assertion result
-> evidence artifact
-> architecture receipt
-> meta receipt
```

A semantic judge may score explanation quality, but it cannot overrule deterministic HITL, idempotency, timeout, or safety assertions.

## Decision vocabulary

```text
ELIGIBLE_FOR_HUMAN_ADMIT
HOLD
REJECT
```

`ELIGIBLE_FOR_HUMAN_ADMIT` means machine gates are closed. It does not merge, release, change visibility, or promote without Human authority.

## Checkers

```bash
python3 scripts/check_agent_architecture_eval.py architecture-receipt.json
python3 scripts/check_meta_abstraction_eval.py meta-receipt.json
```

Exit contract:

```text
0   structurally and semantically closed
2   semantic/assertion refusal
64  missing or malformed input
```
