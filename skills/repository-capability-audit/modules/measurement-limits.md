# Measurement limits

What the contribution accounting in [`../evals/live-source-contribution.md`](../evals/live-source-contribution.md) can and cannot decide. Read this before quoting any number from it.

## The two layers answer different questions

```text
Layer A  removing a semantic procedure claim changes a deterministic
         executable-fixture outcome
         -> the procedure is necessary for the committed cases

Layer B  removing a rule from the Skill text changes what a live
         language-model Agent does on a held-out repository
         -> the text is load-bearing for a model
```

A Layer A pass cannot promote a Layer B state. The 13 retained rules each have a deciding Layer A delta and a Layer B state of `NOT_EXERCISED`; those two facts are compatible and neither implies the other.

## Overlap is why there is no total

Several source Skills map to one retained rule, and one source claim can carry several obligations. So each source gets a pair of bounds rather than a share:

```text
lower bound   supported claims that no other source names
upper bound   every supported claim, shared ones included
```

The gap between them is credit the current evidence cannot split. Closing it needs grouped or factorial ablations — remove two sources' claims together, and separately — which have not run. Until then, adding two sources' fractions double-counts every shared rule.

## What the numbers are not

- not a Shapley value, and not any other axiomatic credit allocation;
- not a percentage of prose effectiveness, and not a model-weight attribution;
- not comparable across sources by size: a source with 3 claims and one with 16 are answering the same question over different denominators;
- not a total: the four denominators in the report are four different questions.

## Saturation limits the corpus, not just the sample

Eight of fourteen measured metrics have zero within-arm variance on this corpus (`evals/matrix-slice1-result.json`). A metric that does not move cannot carry a treatment signal, and adding repetitions cannot unsaturate it — only a harder case set can. So an absent effect on those metrics is not evidence of an absent effect.

## Absence has several distinct shapes

```text
NOT_EXERCISED         no run was attempted
INSUFFICIENT_SAMPLE   runs exist and do not reach the preregistered scale
INVALID_EXPERIMENT    runs exist and their matching or receipts do not hold
LIVE_NOT_SUPPORTED    a valid experiment found no deciding delta
```

Only the last is a result. Collapsing the first three into it would read as a finding where there is none. `LIVE_NOT_SUPPORTED` also does not delete a rule from the deterministic core: Layer A may still require it for executable correctness, so removal is a separate scope review.

## Expiry

Every state here is bound to the exact subject that produced it. A state expires when the Skill core or module digests, the model or provider version, the Agent harness, the runtime, the evaluator digest, or the corpus moves. A stale receipt cannot prove the new subject.
