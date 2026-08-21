# Controlled productization vocabulary

Every term below is closed. A value outside a set is a contract error rather
than a new nuance, and a term used outside its producer is a claim wearing
someone else's authority.

Each entry names four things. The fourth is the one that decays. A reader who
never sees what a term can *never* become fills the gap with whatever the term
sounded most confident about, and that gap is where a page view becomes demand,
a green suite becomes a product, and one invoice becomes a business.

Where a schema can reach a rule, the rule is in the schema.
[`../productization-program.schema.json`](../productization-program.schema.json)
holds the machine half; this file is the half a person reads before writing one.
[`evidence-ladder.md`](evidence-ladder.md) owns the ten rungs and the
substitution law.

## The twelve lanes

Twelve, reported separately, always. The schema requires all twelve keys and
refuses any thirteenth, so a program cannot drop a lane it never entered and
cannot invent a fused lane that answers for two. Lane collapse is the failure
this method exists to prevent: every one of the authority laws below is a pair
of lanes somebody merged.

```text
SOURCE
  means         what an external artifact says, restated in this method's words
                and bound to the artifact's exact identity
  produced by   intake of an article, export, repository, specification or
                vendor document
  consumed by   MECHANISM, POLICY, MARKET
  never becomes MARKET, USER or TECHNICAL. Confidence, repetition and internal
                consistency are properties of a source, not evidence about a
                market, a user or a running system. Locating a source is not
                reading it, and reading it is not verifying it.

MARKET
  means         who else is in the arena, what they charge for, and where the
                arena is thin
  produced by   comparator enumeration against named cases
  consumed by   the differentiation wedge, COMMERCIAL
  never becomes demand. Attention, traffic, funding and incumbent count measure
                that an arena exists and is being contested. None of them
                measures that anybody will move. A feature difference is not a
                switching wedge either: difference is measured against a
                product, and a wedge is measured against the cost of leaving
                the one somebody already has.

USER
  means         one named scenario, the work being attempted in it, and what
                adoption would cost the person attempting it
  produced by   scenario construction and, at the higher rungs, observation of
                real behaviour
  consumed by   the wedge, COMMERCIAL, RUNTIME
  never becomes MARKET or COMMERCIAL. Interest is not adoption, pain is not
                willingness to switch, and the person who uses a thing is not
                by default the person who buys it. A scenario somebody wrote is
                a hypothesis about a user; only a user is evidence about a user.

MECHANISM
  means         how an observed capability actually works, reproduced closely
                enough to be re-run
  produced by   reverse engineering against an exact subject
  consumed by   TECHNICAL, the wedge
  never becomes TECHNICAL feasibility here. Knowing how somebody else's system
                works does not establish that this one can be built, and a
                mechanism reproduced once under chosen conditions is not a
                mechanism that holds.

TECHNICAL
  means         what this implementation does, at an exact commit, when a named
                command runs it
  produced by   deterministic execution with recorded exit codes
  consumed by   RUNTIME, the MVP stop-loss
  never becomes USER, COMMERCIAL or RUNTIME. A green suite is a statement about
                the checks that ran on synthetic input. It is the single most
                over-promoted lane in this method, because it is the cheapest
                one to turn green and the one that most resembles being done.

POLICY
  means         what a published rule currently says, read directly, with the
                date and revision it was read at
  produced by   fetching the primary rule, not a summary of it
  consumed by   RIGHTS, capability revalidation
  never becomes RIGHTS. Policy is a moving subject: an answer obtained before a
                revision is a fact about the old revision, and reusing it after
                a change is the most common quiet failure in this lane. Nor is
                a rule's visibility permission to rely on it.

RIGHTS
  means         whether this use is actually permitted, decided by whoever can
                grant it
  produced by   a person with authority to admit or refuse
  consumed by   HUMAN_ADMIT, RELEASE
  never becomes derivable from POLICY, TECHNICAL or RUNTIME. Reading a licence
                is not being granted the rights beside it. A platform that
                technically permits an access has not thereby licensed the
                content reached through it. This lane's honest default is
                UNKNOWN, and UNKNOWN here is a finding, not a gap to fill.

COMMERCIAL
  means         what the value ladder is, what the friction to buy is, and what
                somebody actually paid
  produced by   pricing hypotheses, then real transactions
  consumed by   the outcome disposition
  never becomes MARKET or USER. Interest is not payment, a quote is not a sale,
                one payment is not a repeatable business, and a consumer
                subscription is not an entitlement to the interface behind it.

RUNTIME
  means         that a named workflow executed end to end, in the environment
                that matters, with these values
  produced by   observing a real run, not a dispatch of one
  consumed by   USER, the outcome read-back
  never becomes TECHNICAL, and TECHNICAL never becomes it. A prompt packet is
                not a running session, a dispatch queue is not execution, and a
                bootstrap that succeeded is not a model, provider or agent that
                did anything.

HUMAN_ADMIT
  means         a decision that belongs to a person and that no evidence this
                method can gather will move
  produced by   a person, on the record
  consumed by   MERGE, RELEASE
  never becomes PASS by accumulation. Rights, legal exposure, credential and
                confidential-data authorisation, independent reviewer identity,
                real user truth, payment truth, permission widening and
                production sit here permanently. No process may manufacture one
                of these to complete a diagram.

MERGE
  means         one specific operation a person performs on a mutable branch
  produced by   a person with merge authority
  consumed by   RELEASE
  never becomes a state this method reaches. Every gate green is the condition
                somebody merges under, not the merge.

RELEASE
  means         one specific operation that puts a version in front of people
  produced by   a person with release authority
  consumed by   the outcome read-back
  never becomes implied by MERGE. A thing that is on a default branch is not a
                thing that shipped, and a thing that shipped is not a thing in
                production.
```

The last three carry a narrower state vocabulary in schema than the other nine:
no PASS and no FAIL, and no rung. Widening them is a validation error rather
than a matter of judgement.

## Lane states

```text
PASS                this lane was entered and cleared, at its stated rung
FAIL                this lane was entered and did not clear
UNKNOWN             the question was asked and the answer is not established
BLOCKED             work stopped on a named external dependency
ABSENT              the thing this lane measures is not present at all
NOT_IMPLEMENTED     the capability this lane measures has not been built
NOT_EXERCISED       the lane was available and nobody entered it
SKIPPED_BY_POLICY   the lane was deliberately not entered, with a reason
NOT_APPLICABLE      the lane cannot apply to this subject
HUMAN_ADMIT_REQUIRED the answer belongs to a person
```

Eight of the ten are ways of not being PASS, and the distinctions between them
are the point. UNKNOWN, BLOCKED and NOT_EXERCISED describe three different
worlds: nobody could answer, nobody could start, nobody tried. Collapsing them
into one value is how a gap becomes a pass, because a single "not yet" reads to
the next person as scheduling rather than as absence.

None of the eight is a defect report either. A lane nobody could enter did not
fail; recording it as FAIL invites a repair for a defect that does not exist,
and recording it as PASS hides the dependency entirely.

## The fifteen program states

Fourteen progression states and one four-valued outcome disposition.

```text
REQUEST_BOUND
  means         the request exists as an exact subject rather than as a topic
  produced by   intake
  consumed by   control binding
  never becomes evidence of anything. A bound request is a question with an
                address, not an answer.

CONTROL_AND_AUTHORITY_BOUND
  means         subjects, evidence ceiling, budget, writer leases, stop
                conditions, rollback and Human-owned operations are all fixed
  produced by   the control binder
  consumed by   every later state
  never becomes permission. Binding who may write does not create authority to
                write anything in particular.

SOURCE_AND_POLICY_BOUND
  means         the source set and the governing published rules are identified
                at exact revisions
  produced by   SOURCE and POLICY intake
  consumed by   MARKET, MECHANISM, RIGHTS
  never becomes RIGHTS admission or MARKET truth.

MARKET_ARENA_BOUND
  means         the arena and its participants are enumerated
  produced by   the market lane
  consumed by   comparator cases
  never becomes demand.

USER_SCENARIOS_BOUND
  means         named scenarios and their adoption costs are written down
  produced by   the user lane
  consumed by   the wedge, commercial friction
  never becomes USER_VALIDATED. A scenario is authored; a validation is
                observed.

COMPARATOR_CASES_BOUND
  means         specific comparator cases are fixed, so a later claim has
                something to be measured against
  produced by   MARKET and MECHANISM together
  consumed by   the wedge
  never becomes a wedge on its own.

DIFFERENTIATION_WEDGE_BOUND
  means         one stated reason somebody would move, expressed against a
                named comparator and a named switching cost
  produced by   synthesis over comparators and scenarios
  consumed by   commercial friction, MVP scoping
  never becomes USER or COMMERCIAL evidence. A wedge is the hypothesis those
                lanes exist to test.

COMMERCIAL_FRICTION_BOUND
  means         the value ladder and the friction to buy are stated
  produced by   the commercial lane
  consumed by   the MVP stop-loss, the outcome read-back
  never becomes PAID_VALIDATED.

CAPABILITY_AND_RIGHTS_BOUND
  means         what can be built and what is permitted are separately answered
  produced by   TECHNICAL and RIGHTS
  consumed by   MVP scoping
  never becomes one answer. This state requires two, and the RIGHTS half may
                legitimately be UNKNOWN.

MVP_AND_STOP_LOSS_BOUND
  means         the smallest thing that could test the wedge, and the condition
                under which it stops
  produced by   MVP scoping
  consumed by   the build
  never becomes a commitment to build. KILL is available from here.

SHADOW_CLOSURE_AUDITED
  means         an independent read-only pass reviewed the claimed closure and
                the planted controls
  produced by   an independent reviewer
  consumed by   the session DAG
  never becomes admission. Shadow reports findings; it does not admit its own
                findings, and it does not repair what it found.

ISSUE_AND_SESSION_DAG_BOUND
  means         the work is decomposed into atoms with one owner, one lease and
                one writer each, with the start and completion graphs separate
  produced by   orchestration
  consumed by   the build
  never becomes execution. A dispatch queue is a plan for sessions.

BUILD_OR_EXPERIMENT_RUNNING
  means         a writer is actually working, or an experiment is actually live
  produced by   the writers
  consumed by   the outcome read-back
  never becomes an outcome. Running is not finishing, and finishing is not
                working.

OUTCOME_READ_BACK
  means         what actually happened was read from the thing that happened,
                not from the plan that predicted it
  produced by   RUNTIME, USER and COMMERCIAL observation
  consumed by   the disposition
  never becomes a disposition by itself. Reading the outcome and deciding what
                to do about it are separate acts, and merging them is how a
                disappointing result becomes ITERATE by default.

PRESERVE | NARROW | ITERATE | KILL
  means         the four dispositions available after the outcome is read
  produced by   a decision over the read-back
  consumed by   the next program
  never becomes optional. Every program ends in one of these four, and KILL is
                a real outcome rather than a failure of the method. A program
                that cannot reach KILL is not measuring anything.
```

Five further states describe a program that did not progress: UNKNOWN,
BLOCKED, NOT_EXERCISED, REPLAN_REQUIRED and HUMAN_ADMIT_REQUIRED. There is
deliberately no state meaning merged, released or in production. Those are
operations somebody performs, so a program record cannot be filed as the
evidence for one.

## The authority laws in one place

Each line is two lanes that must not be joined. They are listed together
because in practice they are violated the same way: by a sentence that has one
lane's evidence in the first half and another lane's conclusion in the second.

```text
market attention           is not  demand
feature difference         is not  a switching wedge
pain                       is not  willingness to switch
a technical PASS           is not  user validation
user interest              is not  payment
one payment                is not  a repeatable business
policy visibility          is not  rights admission
an external projection     is not  machine authority
a prompt packet            is not  a running session
a bootstrap PASS           is not  agent, model or provider execution
a carrier's UI state       is not  source, work or method truth
a start dependency         is not  a completion dependency
a process dependency       is not  an ancestry edge
```

## What a number is allowed to mean

A numerator over a denominator somebody named is a fact about that denominator.
The same ratio with no denominator is a claim about whatever the reader
imagines, and what the reader imagines is always the whole market. A conversion
rate, a retention figure, an adoption percentage or a performance number is
either a measurement carrying its method, sample size, environment and exact
subject, or it is the literal value meaning nothing was measured. There is no
third form, because a figure quoted without its receipt survives every later
change to the thing it described.
