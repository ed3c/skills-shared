# Delivery shape experiment

> Status: mechanism implemented, experiment `NOT_EXERCISED`. The canonical
> default is unchanged and remains `BLOCKED` — see the admission rule.

## The question

Does splitting a change into a contract foundation, true children and
path-disjoint siblings improve correctness, reviewability, failure isolation and
rollback scope, without spending an unacceptable amount of CI and rebase churn?

## Why the scorer is mostly refusals

Almost every cheap way to answer produces a well-formed number that is not the
claim:

```text
B produced more pull requests        → so B was better decomposed
B's diffs were smaller per unit      → so B was more reviewable
B's arm ran a newer evaluator        → so B found more defects
B's arm was allowed more retries     → so B converged
a reviewer scored B higher           → so B passed
```

PR count is a property of how the work was cut, not of whether it was cut well.
The owning issue says so outright, so `review_units` is reported and
deliberately excluded from the admission rule.

One metric needed the same treatment, and it was found by a control rather than
by reading: **rollback blast radius falls automatically as units get smaller**.
It covaries with split granularity, so a gain there alone is not evidence — it
is the same claim as "more pull requests" in different units. It is reported
under `covarying_with_split_granularity` and counts only alongside a
reviewability or outcome gain.

## What must be identical across arms

```text
requirement_digest      implementation_target    evaluator_identities
carrier                 fixture_commit           reviewer_rubric_digest
budget                  observed_budget ≤ budget
```

The branch graph is the treatment. Anything else differing makes it one variable
among several, and the comparison answers a question nobody asked.

## Structural rules a stack must satisfy to be measured as one

- a child must consume paths its parent actually touched — a serial chain that
  consumes no parent bytes is not a stack, and declaring it one is the cheapest
  way to make B look decomposed;
- siblings must hold disjoint path leases, or they are not siblings and merging
  them independently is what produces add/add conflicts;
- a convergence unit must name prerequisites, and every one must already be
  merged.

## Admission rule

```text
canonical_default_unlock = BLOCKED unless
    B improves a reviewability or outcome metric
  and B regresses no deterministic outcome
  and B stays within the declared CI and workflow budget
  and task_pairs >= 2
```

The last clause is the evidence boundary, not a formality. A single
hand-selected task pair is mechanism evidence; it cannot establish that one
shape is generally better, so a favourable single pair still leaves the default
where it is.

## Current state

```text
experiment contract      IMPLEMENTED
scorer and controls      IMPLEMENTED (17 refusals proven)
fixture/task pair        ABSENT
A execution              NOT_EXERCISED
B execution              NOT_EXERCISED
comparative receipt      NOT_PRODUCED
canonical-default unlock BLOCKED
```

## Observation, which is not the experiment

`evals/fixtures/delivery-shape/observation-2026-08-14.json` records twenty real
merged pull requests from one day of work here, grouped by the shape they were
delivered in:

```text
group    units  max files  median files  max diff
ibc          5         12           9.0      1763
ctl          5         20           9.0      2598
singles     10         24           4.5      3184
```

These are observations, and `compare` would be wrong to run on them: the tasks
differ, so they are not two arms of anything. They are recorded because the
numbers are real and the experiment's fixture pair does not exist yet — and
because "we already have data" is exactly the inference that would turn an
observation into an unearned conclusion.

One thing the observation does show, without needing a comparison: the largest
single review unit in the stacked groups was 20 changed files, and in the
unstacked group 24. That is not a difference worth a claim.
