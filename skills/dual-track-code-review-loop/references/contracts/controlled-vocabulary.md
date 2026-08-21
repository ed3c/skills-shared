# Controlled authority and evidence vocabulary

Every term below is closed. A value outside the set is a contract error, not a
new nuance, and a term used outside its producer is a claim wearing someone
else's authority.

Each entry names four things. The fourth is the one that decays: a reader who
never sees what a term can *never* become fills the gap with whatever the term
sounded most confident about. That gap is where a retrieval hit becomes a rule,
a static pass becomes a guarantee, and a green suite becomes a merge.

`never becomes` is enforced in schema where a schema can reach it. The
[`../schemas/`](../schemas/) documents carry the machine half; this file is the
half a person reads before writing one.

## Source plane

```text
SOURCE_STATEMENT
  means         one claim about the world, extracted from an external artifact
                and restated in this method's words
  produced by   reading a SOURCE_PROPOSAL packet
  consumed by   source disposition
  never becomes OFFICIAL_PRIMARY_SOURCE, REPOSITORY_OBSERVATION,
                DETERMINISTIC_FACT or ARCHITECTURE_INVARIANT. Confidence,
                repetition and internal consistency are properties of the
                source, not evidence about this repository.

SOURCE_PROPOSAL
  means         one whole external artifact, or one recommendation inside it,
                admitted as raw material
  produced by   intake of an article, transcript, slide deck, conversation
                export or vendor document
  consumed by   source disposition, candidate records
  never becomes any repository state. A packet is identified by content digest
                and byte count, never by where a copy of it sits.

OFFICIAL_PRIMARY_SOURCE
  means         the authoritative specification, reference implementation or
                vendor document for one external contract, read directly
  produced by   fetching the primary artifact, not a summary of it
  consumed by   candidate records, remediation rationale
  never becomes DETERMINISTIC_FACT about this repository. A specification says
                what a protocol requires; only this tree says what this tree
                does. Nor does it become clearance: reading a licence is not
                being granted the rights beside it.
```

## Repository plane

```text
REPOSITORY_OBSERVATION
  means         something read off this tree at an exact commit
  produced by   reading files, history, configuration or index output
  consumed by   deterministic facts, violation candidates
  never becomes DETERMINISTIC_FACT on its own. An observation is what one pass
                saw; a fact survives being checked a second way.

DETERMINISTIC_FACT
  means         a structural property that a named tool derived from an exact
                commit and that re-running the tool reproduces
  produced by   parser, compiler-backed index, or graph query over either
  consumed by   violation candidates, verification receipts
  never becomes a complete account of behaviour. Every fact carries how it was
                obtained, because an edge a compiler resolved and an edge a
                script inferred from range nesting are indistinguishable once
                they are both rows in a table.

SEMANTIC_CONTEXT_CANDIDATE
  means         a stored document, incident record, budget or telemetry series
                that retrieval ranked as possibly relevant
  produced by   keyword, vector or hybrid retrieval
  consumed by   violation candidates, as colour and never as basis
  never becomes DETERMINISTIC_FACT, ARCHITECTURE_INVARIANT or a verdict.
                Ranking answers which stored text resembles the query. It does
                not answer whether that text is current, whether it was
                superseded, or whether it ever bound this subsystem.

ARCHITECTURE_INVARIANT
  means         a rule this repository has agreed to hold, written out in full
  produced by   a human decision recorded in this tree
  consumed by   violation candidates
  never becomes self-establishing. An invariant a retrieval pass found is a
                candidate invariant; an invariant is admitted, not discovered.
```

## Finding and change plane

```text
VIOLATION_CANDIDATE
  means         a suspected breach of one named invariant at one exact commit
  produced by   the deterministic track, optionally coloured by the semantic one
  consumed by   refactor proposals
  never becomes a defect report on its own authority. The word candidate is
                load-bearing: this is what the analysis nominated, not what the
                repository owes.

REFACTOR_PROPOSAL
  means         a bounded remedy for one confirmed violation, written before
                any file is touched
  produced by   synthesis over the confirmed candidate
  consumed by   change units
  never becomes an obligation. NO_CHANGE is a real outcome: a violation whose
                remedy costs more than the violation is a finding.

CHANGE_UNIT
  means         one applied bounded change, bound to exact base and head and to
                the complete list of paths it touched
  produced by   implementing one admitted proposal
  consumed by   verification receipts, closure records
  never becomes merged. Merge admission is single-valued, so no combination of
                evidence expressible here can set it to anything else.
```

## Evidence plane

```text
VERIFICATION_RECEIPT
  means         what one arrival observed against one exact commit
  produced by   running checks and recording their exit codes
  consumed by   change units, closure records
  never becomes authority over merge, permission, secrets, production, user
                value, paid demand or release. Those are stated as constants
                in the receipt, so overclaiming is unrepresentable rather than
                discouraged. A receipt whose checks all passed is a receipt
                about the checks that ran.

CLOSURE_RECORD
  means         the terminal statement for one pass: what was reached, by which
                independent arrivals, and which lanes were never entered
  produced by   reconciling receipts against the lane inventory
  consumed by   handoff and human admission
  never becomes evidence of merge, release or production. The terminal
                vocabulary deliberately contains no such value, because those
                are operations somebody performs rather than states a record
                reaches.
```

The three arrivals a receipt can carry are also closed, and none implies either
other:

```text
STATIC    a thing is possible; the type, rule or query says so
SANDBOX   a thing executes, under input somebody synthesised
PROD      a thing ran, with these values, where it matters
```

A load-bearing conclusion that costs something to get wrong wants two arrivals
that the same mistake could not fool. Two runs of one arrival are one arrival
observed twice.

## Terminal states

```text
BLOCKED
  means         work stopped on a named external dependency
  produced by   any stage
  consumed by   handoff
  never becomes FAIL. A stage nobody could enter did not fail; recording it as
                failure invites a repair for a defect that does not exist, and
                recording it as pass hides the dependency entirely.

NOT_APPLICABLE
  means         this lane, check or plane cannot apply to this subject
  produced by   any stage, with a rationale beside it
  consumed by   closure records
  never becomes PASS. A hardware lane a contract change could not possibly
                enter is not a hardware lane that was available and cleared.

HUMAN_ADMIT_REQUIRED
  means         the decision belongs to a person and no evidence this method
                can gather will move it
  produced by   any stage
  consumed by   closure records, handoff
  never becomes PASS by accumulation. Merge, release, production, visibility,
                private account authorisation, employment and intellectual
                property, patent, trademark, service terms, independent review
                identity, real user behaviour and payment all sit here
                permanently. No process may manufacture one of these to
                complete a diagram.
```

## What a percentage is allowed to mean

A numerator over a denominator someone named is a fact about that denominator.
The same ratio with no denominator is a claim about whatever the reader imagines,
and what the reader imagines is always the whole system. The receipt therefore
has no field in which to write a bare percentage, and the words that turn a
bounded measurement into a guarantee are refused in its prose.

The same rule governs every other number. A latency, throughput or productivity
figure is either a measurement carrying its method, sample size, environment and
exact commit, or the literal value meaning nothing was measured. There is no
third form, because a figure quoted without its receipt survives every later
change to the thing it described.
