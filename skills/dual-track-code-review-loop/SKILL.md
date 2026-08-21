---
name: dual-track-code-review-loop
description: |
  Portable procedure for reviewing code with two tracks that are never allowed to substitute for each other: a deterministic track that derives structural facts from an exact commit, and a semantic track that retrieves the organisation's recorded intent and history. The deterministic track can say what the tree does and cannot say why it matters; the retrieval track can say why something mattered once and can never establish that it happened. Findings are nominations, remedies are bounded and written before any file is touched, numbers travel with the benchmark that produced them or do not travel, and merge stays a human operation no evidence combination can reach. Concrete parsers, indexers, graph stores, retrieval engines, languages, providers, forges and live receipts are domain modules and consumer bindings, never part of this body.
---

# Dual-Track Code Review Loop

## Contract

This body owns the two-track separation, the grading of what each track may
assert, the nomination-to-closure state machine, the bounded remedy shapes, and
the refusals that keep a bounded measurement from becoming a guarantee.

It does not own tool selection. A parser, a compiler-backed symbol index, a
queryable graph ledger and a retrieval index are *capability classes*. Which
implementation fills each one is a domain binding, and a stack that worked on
the targets someone ran it on has been observed on those targets and nowhere
else.

The machine half of this contract is in
[`references/schemas/`](references/schemas/); the terms are closed in
[`references/contracts/controlled-vocabulary.md`](references/contracts/controlled-vocabulary.md);
the claims this method refuses to carry, and why, are in
[`references/source-disposition/refused-claims.json`](references/source-disposition/refused-claims.json).

## The two tracks

```text
deterministic track          semantic track
  parser-derived syntax        recorded decisions
  resolved symbol index        incident and failure history
  queryable graph ledger       stated budgets and telemetry

  answers WHAT the tree does   answers WHY it might matter
  grade DETERMINISTIC_FACT     grade SEMANTIC_CONTEXT_CANDIDATE
  reproducible from a commit   ranked by resemblance
```

The tracks meet once, at synthesis, and the meeting is asymmetric on purpose. A
violation's basis must contain at least one deterministic fact. Retrieval may
colour a finding, order it, or argue about its cost. It may never be the reason
the finding exists, because ranking answers which stored text resembles the
query and answers nothing about whether that text is current, was superseded, or
ever bound this subsystem.

The reverse asymmetry is just as load-bearing. A resolved graph edge proves a
dependency exists; it says nothing about whether anyone agreed it should. An
invariant is admitted by a person and recorded in the tree. It is not discovered
by a query.

## State machine

```text
SOURCE_AND_RIGHTS_BOUND
→ INVARIANTS_BOUND
→ DETERMINISTIC_FACTS_DERIVED
→ SEMANTIC_CONTEXT_BOUND_OR_NOT_APPLICABLE
→ VIOLATION_CANDIDATES_NOMINATED
→ CANDIDATES_CONFIRMED_OR_REFUTED
→ REFACTOR_PROPOSALS_BOUNDED
→ CHANGE_UNITS_APPLIED
→ VERIFIED_ON_TWO_INDEPENDENT_ARRIVALS
→ CLOSED_WITH_STATED_CEILING
```

Fail-closed terminals:

```text
NO_CHANGE_WARRANTED
BLOCKED
REPLAN_REQUIRED
HUMAN_ADMIT_REQUIRED
```

A missing prerequisite blocks advancement. `NOMINATED`, `INDEXED`, `PACKET
COMPILED` and `CHECKS GREEN` are not completion states; each names a step that
finished, and none names a question that was answered.

## Procedure

1. **SOURCE_AND_RIGHTS_BOUND.** Admit each external artifact as a source packet
   bound to its content digest and byte count, never to a path. Adjudicate its
   claims into dispositions before any of them is used. Record each external
   technology as a candidate with its nine rights planes separate: reading a
   permissive source-code licence clears source-code copying and leaves
   employment and intellectual property, patent, trademark, service terms, model
   weights, distribution terms, privacy and release exactly where they were.

2. **INVARIANTS_BOUND.** Write each architecture invariant out in full. A rule
   referred to only by identifier is a rule nobody can disagree with, and one
   nobody disagreed with is one nobody read.

3. **DETERMINISTIC_FACTS_DERIVED.** Derive structural facts from an exact
   commit, and record for each derived edge how it was obtained. An edge a
   compiler resolved and an edge inferred by nesting a reference inside the
   nearest enclosing definition are indistinguishable once both are rows in a
   table, and only one of them is a fact about calling.

4. **SEMANTIC_CONTEXT_BOUND_OR_NOT_APPLICABLE.** Retrieve recorded decisions,
   incidents, budgets and telemetry, marked non-authoritative on arrival. A pass
   with no retrieval surface records `NOT_APPLICABLE` and continues; it does not
   record silence as agreement.

5. **VIOLATION_CANDIDATES_NOMINATED.** Nominate suspected breaches against named
   invariants at that exact commit. Nomination is the analysis speaking about
   itself.

6. **CANDIDATES_CONFIRMED_OR_REFUTED.** Confirm only against a deterministic
   fact. Refutation is a first-class result and stays in the denominator: a run
   that reports only what it confirmed reports its own hit rate as its accuracy.

7. **REFACTOR_PROPOSALS_BOUNDED.** Write the remedy before touching a file, with
   its paths and its explicit out-of-scope list. Name both the mechanism and the
   property that mechanism establishes. A mechanism that is correct in its own
   domain becomes a category error the moment it is pointed at a different
   property, and it reads as competent work right up until somebody asks which
   property it establishes.

   Two remedy shapes recur. Within one repository: extract the method set the
   caller actually uses, define the smallest interface over it, invert the
   dependency through construction, and update the composition root. Across
   repositories, where no single commit can span the change: expand the
   contract, implement it in parallel beside the old path, migrate the consumer
   onto an adapter, run both until the new path is observed carrying real
   traffic, and only then contract the old one.

8. **CHANGE_UNITS_APPLIED.** One change unit implements one proposal, bound to
   exact base and head and to the complete list of paths it touched. The
   complete list, not the interesting subset: a review of the paths someone
   chose to list is a review of the summary.

9. **VERIFIED_ON_TWO_INDEPENDENT_ARRIVALS.** A graph query returning zero and a
   test suite returning green are two arrivals of the static and sandbox kinds,
   and neither reaches the change's effect on anything real. Load-bearing
   invariants want two arrivals that the same mistake could not fool.

10. **CLOSED_WITH_STATED_CEILING.** Report every lane, including the ones
    nothing entered. A lane omitted from a record is a lane the reader fills in
    with the lanes that passed.

## Hard laws

- **A finding needs a deterministic fact.** Retrieval, similarity and model
  agreement may add context to a violation and may never be the reason one
  exists.

- **A heuristic edge set is a lower bound.** Range nesting recovers edges an
  index already resolved and located. It does not recover dynamic dispatch,
  interface satisfaction, callbacks, reflection, or code generated after
  indexing. Its transitive closure is a lower bound on impact, and the failure
  worth naming is not an inaccurate number, it is a floor being read as a
  ceiling by somebody deciding a change is safe.

- **A ratio without a denominator is a claim about whatever the reader
  imagines,** and what the reader imagines is always the whole system. A
  numerator over a named denominator is a fact about that denominator.

- **A number travels with its receipt or it does not travel.** Method, sample
  size, environment and exact commit, or the literal value meaning nothing was
  measured. There is no third form, because a figure quoted without its receipt
  survives every later change to the thing it described.

- **Green checks make a change eligible for a person to look at.** They never
  make it merged, released, compliant, secure or valuable. Merge admission is
  single-valued so that no evidence combination expressible here can reach it.

## Stop conditions

Stop and return the item to its owner when:

- a violation has no deterministic fact in its basis;
- an edge set's provenance is unknown, so its completeness cannot be stated;
- a remedy's mechanism and target property do not match;
- a number arrives without the method, sample size, environment and commit that
  produced it;
- a rights plane needed for the chosen relationship is unadmitted;
- a private locator or private content would have to enter a public artifact for
  the work to be describable;
- three qualifying failures land against the same invariant or acceptance
  target, at which point blind repair stops and a fresh diagnosis begins on a
  new isolated worktree.

## Evidence ceiling

```text
two-track separation and grading      contract-level, enforced by schema
refusal controls                      replayed against the shipped schemas
concrete parser/index/graph binding   NOT_IMPLEMENTED
concrete retrieval binding            NOT_IMPLEMENTED
applied refactor on a real codebase   NOT_EXERCISED
cross-repository contract migration   NOT_EXERCISED
live consumer canary                  NOT_EXERCISED
independent review                    NOT_EXERCISED
legal, employment and IP clearance    HUMAN_ADMIT_REQUIRED
merge, release, production            HUMAN_ADMIT_REQUIRED
```

This body defines how the method may speak. It has not yet been pointed at a
codebase, and a contract that survives its own refusal controls has survived its
own refusal controls.
