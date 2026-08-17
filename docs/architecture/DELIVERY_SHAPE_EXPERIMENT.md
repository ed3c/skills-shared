# Delivery shape experiment

> Status: mechanism implemented, two task pairs `PRE_REGISTERED`, experiment
> `NOT_EXERCISED`. The canonical default is unchanged and remains `BLOCKED` —
> see the admission rule.

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

## The pre-registered task pair

Every controlled field above has the same weakness: fixed *after* a result is
seen, it looks identical in the file to one fixed before. So the pairs are
written into a document whose defining property is that it contains no outcome
at all.

```text
evals/fixtures/delivery-shape/task-pair-01-proof-carrying-refactor.json
evals/fixtures/delivery-shape/task-pair-02-closure-reconciliation.json
```

Each is a `delivery-shape-task-pair/v1` body: one requirement, one target, one
evaluator, one carrier, one base commit, one rubric, one budget — and two
planned branch graphs over the *identical* planned file set. Validate one with:

```bash
python3 scripts/measure_delivery_shape.py plan \
  evals/fixtures/delivery-shape/task-pair-01-proof-carrying-refactor.json
```

`plan` refuses, rather than reports, when:

- any outcome-bearing field appears — on the pair, on an arm, or on a planned
  unit. The permitted fields are allowlisted, because a metric added to the
  measurement schema later would arrive here by default under a denylist, and
  the first person to notice would be whoever read a fabricated number as data;
- `requirement_digest` or `reviewer_rubric_digest` does not digest the text
  sitting beside it. Without the text, "identical requirement" is a claim about
  two hex strings nobody can check;
- the arms plan different files. Two arms of one task end at the same tree, and
  a scope difference read as a shape difference is the confounder the whole
  scorer exists to refuse;
- the structural stack rules above are already violated on paper;
- `execution_state` is anything but `NOT_EXERCISED`. A pair that has run is a
  record, and records go through `compare`.

Executing a pair produces a separate `delivery-shape-experiment/v1` record. The
pre-registration is never edited to match what happened — that edit is the one
that would make the whole apparatus decorative.

Both requirements name work this repository has open and has not done, so
neither arm can be written from a remembered solution. Two pairs is the minimum
the admission rule's `task_pairs >= 2` clause can be satisfied with; it is a
floor, not a target.

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
pre-registration checker IMPLEMENTED (18 outcome-leak refusals proven)
fixture/task pair        PRE_REGISTERED (2 pairs)
A execution              NOT_EXERCISED
B execution              NOT_EXERCISED
comparative receipt      NOT_PRODUCED
canonical-default unlock BLOCKED
```

`A execution` and `B execution` stay `NOT_EXERCISED` because populating them
needs live agent carriers doing the real work twice, which nothing local can
produce. The gap between `PRE_REGISTERED` and `NOT_EXERCISED` is the honest
state of this experiment, and writing numbers into it would close the row
without closing the gap.

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
numbers are real and no pair has been executed — and because "we already have
data" is exactly the inference that would turn an observation into an unearned
conclusion. The pre-registered pairs above do not change that: a plan is not a
result either.

One thing the observation does show, without needing a comparison: the largest
single review unit in the stacked groups was 20 changed files, and in the
unstacked group 24. That is not a difference worth a claim.
