# Market lane vocabulary

The terms this lane owns, in the same four-part form the core vocabulary uses.
The fourth part is the one that decays: a reader who never sees what a term can
*never* become fills the gap with whatever the term sounded most confident
about, and in this lane that gap is where a search volume becomes demand and a
shorter feature list becomes a reason to switch.

Nothing here redefines a core term. The lane name, the ten lane states, the ten
rungs and the fifteen program states belong to
[`../core/controlled-vocabulary.md`](../core/controlled-vocabulary.md) and
[`../core/evidence-ladder.md`](../core/evidence-ladder.md); this file names only
what the MARKET lane adds inside them. The seven evidence classes are the signal
kinds already owned by
[`../../../product-reverse-engineering-loop/references/evidence-vocabulary.md`](../../../product-reverse-engineering-loop/references/evidence-vocabulary.md),
reused rather than restated, and the grade stays a function of the kind alone.

Where a schema can reach a rule, the rule is in the schema:
[`market-lane.schema.json`](market-lane.schema.json) holds the machine half.

## The terms

```text
market arena
  means         the set of things somebody could use to get this job done, and
                what counts as being inside that set
  produced by   enumeration against a written boundary
  consumed by   comparator cases, the underserved segment
  never becomes a size. An arena with a boundary is a set somebody counted; the
                same arena quoted with a number and no boundary is a claim about
                whatever the reader imagined, and what the reader imagines is
                always the whole market.

arena boundary
  means         the sentence that says what was counted as inside and what was
                excluded
  produced by   the author, before the enumeration rather than after it
  consumed by   every later ratio or count in this lane
  never becomes optional. A boundary written after the count is a boundary
                fitted to the count.

occupant
  means         one thing already doing this job: an incumbent product, an
                adjacent alternative, a manual workaround, or nonconsumption
  produced by   arena enumeration
  consumed by   the switching trigger, the wedge
  never becomes a competitor list. The occupant that actually holds a segment is
                routinely the spreadsheet, the mailbox rota or nobody at all,
                and a record that lists only products has enumerated the vendors
                rather than the arena. NONCONSUMPTION is a state of the arena,
                not missing data.

comparator case
  means         one named case, at a stated identity, that a later claim can be
                measured against
  produced by   reading a source and recording where it was read
  consumed by   the wedge, transferability
  never becomes a general law. One case shows what happened in that case. It
                carries no conditions distinguishing itself from the class it
                resembles, because those conditions are exactly what a single
                case cannot show.

underserved or noncustomer segment
  means         one group and its relation to the arena's existing customers
  produced by   segmentation against the enumerated occupants
  consumed by   the wedge, the distribution hypothesis
  never becomes demand or a user. Underserved is a reading of the supply side.
                A segment nobody has spoken to is a hypothesis about people, and
                only a person is evidence about a person.

switching trigger
  means         the event after which somebody would reconsider what they use
  produced by   hypothesis, or at the higher rungs by observation
  consumed by   the wedge
  never becomes a purchase. A trigger says when the question gets asked, not
                what the answer is.

switching cost
  means         what leaving the current occupant costs, and who bears it
  produced by   naming the cost kind and the payer separately
  consumed by   the wedge, COMMERCIAL friction
  never becomes a price. The person who pays the switching cost is frequently
                not the person who chooses the tool, and a wedge aimed at the
                chooser reduces nothing the payer bears.

wedge hypothesis
  means         one stated reason to move, measured against a named comparator
                case and a named switching cost
  produced by   synthesis over comparators, segments and triggers
  consumed by   the USER and COMMERCIAL lanes, MVP scoping
  never becomes evidence. It is the hypothesis those lanes exist to test, which
                is why its state vocabulary has two values and neither is a
                pass. A feature difference is measured against a product; a
                wedge is measured against the cost of leaving one.

distribution or access hypothesis
  means         the path by which this would reach the segment, and who can
                close that path
  produced by   naming the path, the gatekeeper and how far the governing rule
                has actually been read
  consumed by   MVP scoping, RIGHTS
  never becomes availability or permission. A channel is a thing somebody else
                controls. Reading its published rule at a stated revision is a
                POLICY fact about that revision; it is not an admission that
                this use is allowed, and rules move.

copyable mechanism
  means         the part of a comparator case that would work here too
  produced by   separating mechanism from circumstance
  consumed by   MECHANISM, MVP scoping
  never becomes the case's outcome. Copying the mechanism copies the mechanism.

non-transferable condition
  means         the part of a comparator case that would not travel: a timing
                window, an existing distribution list, capital, a regulatory
                position, or something unexplained
  produced by   the same separation, from the other side
  consumed by   the generalization scope
  never becomes empty. A case with nothing recorded that would not travel was
                read as a recipe, and the unexplained condition is the one that
                gets attributed to whichever mechanism is written down beside
                it.

counterexample
  means         a case where this wedge, or one shaped like it, did not produce
                the movement claimed
  produced by   looking for one on purpose
  consumed by   the falsifier, the wedge state
  never becomes optional. That nobody has tried it here is an admissible
                answer and a different answer from having tried and failed.

falsifier
  means         the observation that would show this wedge false, and the lane
                it would have to be made in
  produced by   the author, before the evidence rather than after it
  consumed by   the USER, PAID and BEHAVIORAL oracles
  never becomes closable in the technical lane. A market claim does not close
                against a green suite; that substitution is the cheapest
                laundering path in the method, and the schema's oracle set has
                no deterministic value in it.
```

## What the contract makes structurally impossible

Five refusals from the issue this lane was frozen for, each held by one keyword
rather than by prose. Each row names the keyword that refuses it, and each was
checked by deleting exactly that keyword and confirming the refused instance
then validates.

```text
MARKET_ATTENTION_AS_DEMAND        $defs.market_signal.allOf[0].then
FEATURE_DIFFERENCE_AS_WEDGE       $defs.wedge_hypothesis.allOf[0].then
ONE_SUCCESS_CASE_AS_GENERAL_LAW   allOf[0].then
COMPARATOR_WITHOUT_SOURCE         $defs.comparator_case.required
DISTRIBUTION_ASSUMED_AVAILABLE    $defs.distribution_hypothesis.allOf[0].then
```

Each refusal is narrower than its name, and the schema says so where it enforces
it. The first refuses an attention-class signal filed against a behavioural
slot, not an OBSERVED_ARTIFACT row that describes no observation. The second
refuses a feature difference carried as a live hypothesis, not one relabelled as
a switching-cost reduction. The fourth refuses an absent source reference, not a
locator that leads nowhere. What none of them reaches is a well-formed record
that is simply wrong, and pretending otherwise would be the same overclaim this
lane exists to refuse.

## The ceiling

This lane's ceiling is `MARKET_HYPOTHESIS_CONTRACT`, and it is structural rather
than advisory: the rung enum stops at `WEDGE_SUPPORTED`, the wedge state
vocabulary contains no pass, and nine authority constants are pinned false. No
instance of this schema can report demand, product-market fit, user truth,
payment truth or a product choice. A frozen contract proves that a shape is
fixed and that a control is refused. It proves nothing about a market.
