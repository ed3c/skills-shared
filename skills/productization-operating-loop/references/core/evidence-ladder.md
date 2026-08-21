# The ten-rung evidence ladder

Ten rungs, ordered, and the order is the content. Each rung answers a question
the rung below it cannot answer, which is why reaching one never implies the
next and why a cheaper one may never stand in for a later one.

The lanes in [`controlled-vocabulary.md`](controlled-vocabulary.md) say which
kind of claim a piece of evidence belongs to. This file says how far up the
claim goes.

## The substitution law

> No cheaper rung substitutes for a later rung.

Stated negatively, because that is the form it gets violated in: the violation
is never "we skipped a rung", it is "we already have strong evidence here, so
the next one is a formality". Strong evidence at rung six is complete evidence
about rung six.

Three things enforce it in
[`../productization-program.schema.json`](../productization-program.schema.json),
and it is worth knowing exactly how far each reaches.

```text
all ten rungs are required            a rung cannot be dropped, so a ladder
                                      cannot be reported as complete by
                                      reporting only its high end

monotone by construction              each rung above the first carries an
                                      if/then pinning its predecessor to
                                      REACHED, so REACHED at rung N with a gap
                                      below it is a validation error

one receipt kind per rung             a REACHED rung must contain a receipt of
                                      that rung's own kind, so a command exit
                                      cannot be filed as evidence of a payment
```

What none of them reaches: whether a receipt describes anything real. The
schema refuses a missing rung, a skipped rung and a receipt of the wrong kind.
It does not refuse a REACHED written beside a receipt that names a commit and
says nothing. That gap is what independent review is for, and pretending the
schema closes it would be the same overclaim the ladder exists to prevent.

## The rungs

```text
SOURCE_FOUND
  means         an artifact bearing on the question was located at an exact
                identity
  producer      source discovery
  consumer      SOURCE_VERIFIED
  receipt       SOURCE_LOCATED
  never becomes SOURCE_VERIFIED. Finding is not reading. A search result is
                evidence that a search matched.

SOURCE_VERIFIED
  means         the artifact was read back from the primary thing rather than
                from a summary of it, and says what it was said to say
  producer      independent read-back
  consumer      JOB_SUPPORTED
  receipt       INDEPENDENT_SOURCE_READBACK
  never becomes a claim about this system. A verified source is a verified
                statement about whatever the source describes.

JOB_SUPPORTED
  means         a specific job somebody is trying to get done is supported by
                traced evidence, not by a plausible story
  producer      reverse engineering, user scenario work
  consumer      WEDGE_SUPPORTED
  receipt       JOB_EVIDENCE_TRACE
  never becomes demand. That the job exists says nothing about whether anyone
                will change what they use to get it done.

WEDGE_SUPPORTED
  means         a stated reason to switch survives comparison against named
                comparator cases and a named switching cost
  producer      comparator analysis
  consumer      MECHANISM_REPRODUCED
  receipt       COMPARATOR_CASE_TRACE
  never becomes USER_VALIDATED. A wedge that survives analysis is a hypothesis
                that has not yet been falsified by anyone who had to pay for
                the switch.

MECHANISM_REPRODUCED
  means         the capability was made to work again, outside the system it
                was observed in
  producer      mechanism replay
  consumer      MVP_TECH_VERIFIED
  receipt       MECHANISM_REPLAY
  never becomes MVP_TECH_VERIFIED. A mechanism reproduced under chosen
                conditions is not a product that holds under conditions
                somebody else picks.

MVP_TECH_VERIFIED
  means         a named command ran against an exact commit and exited zero
  producer      deterministic execution
  consumer      LIVE_WORKFLOW_VERIFIED
  receipt       DETERMINISTIC_COMMAND_EXIT
  never becomes LIVE_WORKFLOW_VERIFIED, USER_VALIDATED or anything commercial.
                This is the cheapest rung above the middle and it is the one
                most often promoted, because it is the one that most feels like
                being finished.

LIVE_WORKFLOW_VERIFIED
  means         the whole workflow ran end to end where it matters, with real
                values, and was observed doing so
  producer      runtime observation
  consumer      USER_VALIDATED
  receipt       LIVE_WORKFLOW_TRACE
  never becomes USER_VALIDATED. That the machinery works is a precondition for
                somebody using it and is not somebody using it. A dispatched
                run is not an observed one.

USER_VALIDATED
  means         a real person, not a fixture, did the thing in their own
                circumstances and the result was observed
  producer      real user observation
  consumer      PAID_VALIDATED
  receipt       REAL_USER_OBSERVATION
  never becomes PAID_VALIDATED. Every study of stated intent that has ever been
                compared against behaviour has found the gap; this rung exists
                on one side of it and the next on the other.

PAID_VALIDATED
  means         money moved, once, for this
  producer      a transaction
  consumer      REPEATABLE_COMMERCIAL
  receipt       PAYMENT_RECORD
  never becomes REPEATABLE_COMMERCIAL. One payment establishes that one person
                paid once. It is the strongest single-observation rung on this
                ladder and it is still one observation.

REPEATABLE_COMMERCIAL
  means         it happened again, from a source that was not the first one,
                under conditions somebody could describe
  producer      a repeated series
  consumer      the outcome disposition
  receipt       REPEATED_PAYMENT_SERIES
  never becomes a business that will keep working, a market size, or evidence
                that the same wedge holds for anyone outside the series. The
                top of this ladder is still a bounded measurement, and the
                ladder deliberately has no rung called PRODUCT_MARKET_FIT.
```

## How a rung is legitimately claimed

Two lanes are involved in every rung and they are not the same lane. The rung
records how far the evidence goes; the lane records which kind of claim it
supports. A COMPARATOR_CASE_TRACE raises WEDGE_SUPPORTED and belongs to MARKET;
it does not raise anything in USER, no matter how convincing the comparison is.

A rung that is not reached says why, in the same closed vocabulary the lanes
use: NOT_REACHED when the work was attempted and did not get there,
NOT_EXERCISED when nobody attempted it, BLOCKED when an external dependency
stopped it, UNKNOWN when it was attempted and the result cannot be read either
way. Four different facts, and the fourth is the one most often written as the
third.

## The ladder and the ceiling

An evidence ceiling is the highest rung a program is allowed to claim, stated
before the work rather than after it. A contract freeze has a ceiling at the
interface: it can prove that a shape is fixed and that a control is refused,
and it cannot reach SOURCE_VERIFIED about a market or MVP_TECH_VERIFIED about a
product that has not been written. Stating the ceiling first is what makes a
later overclaim visible as a contradiction rather than as enthusiasm.
