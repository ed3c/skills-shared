# Prompt surface catalogue

Ten prompt surfaces exist: one common envelope every surface inherits, and nine
stage surfaces, one per state-machine transition. The machine authority is
[`example-prompt-packet.json`](example-prompt-packet.json) validated against
[`prompt-packet.schema.json`](prompt-packet.schema.json); this file is the
reading order and the reason each surface exists. When the two disagree, the
packet wins — a table cannot hold a lease.

`python3 scripts/check_prel_contract.py --catalogue references/prompt-catalogue.md`
asserts that every surface named by the schema is still named here, so a surface
cannot be added to the contract and quietly left undocumented.

## What every surface must bind

```text
exact subject          artifact name + sha256 digest, never a description
lease                  the paths this surface may write, disjoint from every other
start dependencies     what must be readable before it may begin
completion dependencies what must be receipted before it may claim done
evidence lanes         which lanes its output is allowed to speak in
negative controls      what it must refuse, stated before it runs
rollback               how to undo it without touching anything it did not lease
Human-owned operations what it must escalate rather than perform
```

Two of these are the same list in most plans and must not be here.
A start dependency is cheap and reversible: the prerequisite is readable and its
paths are free. A completion dependency is expensive and irreversible: the
prerequisite is itself closed by a receipt naming the same subject in the
prerequisite's own lane. Collapsing them reports every stage as finishable the
moment the one before it exists.

## `COMMON_SYSTEM_ENVELOPE`

Carries the evidence vocabulary, the refusal codes, the Human-owned operation
list, and the authority object in which merge, permission, secret and production
are all false. Every stage surface inherits it and no stage surface may widen it.
This is also the only place a consumer identifier may appear, inside
`consumer_binding`; anywhere else it is `CONSUMER_TOPOLOGY_IN_PORTABLE_CORE`.

## `STAGE_1_CONTROL_BINDER`

Binds the objective, the scope, the refusal codes and the evidence ceiling
*before* any signal is read. A control list written after the evidence is a
description of what was found, not a control on it.

## `STAGE_2_SOURCE_INTAKE`

Turns product surfaces into typed signals. It records what was seen and how it
could be refuted, never a conclusion. It refuses a source statement filed with an
observation block, and it refuses a retrieval the surface's published terms do
not allow.

## `STAGE_3_EVIDENCE_COMPILER`

Grades every signal from its kind alone, using the frozen table in
[`evidence-vocabulary.md`](evidence-vocabulary.md). Grading is mechanical on
purpose: a grade argued case by case is a grade that drifts toward whatever the
author already believed.

## `STAGE_4_YC_PRODUCT_REVERSE_ENGINEER`

Binds job, pain, workflow and magic moment. Its central refusal is the feature
clone: a workflow and mechanism list assembled while job or pain is `ABSENT`
describes what a product does and says nothing about why anyone would leave what
they already use.

## `STAGE_5_TECHNICAL_SYSTEMS_ARCHITECT`

Classifies mechanism hypotheses, builds the capability graph from declared
dependencies only, and records usage rights as `HUMAN_ADMIT_REQUIRED`. A
mechanism nobody can refute is `UNOBSERVABLE_MECHANISM`, not a design input.

## `STAGE_6_SHADOW_MONITOR`

Reviews the same immutable subject and writes no state of its own. It owns the
lane-substitution refusal: a deterministic oracle closing a user or paid
requirement is the cheapest laundering path available and the one most likely to
be reported as progress. When the subject is a product claiming a problem is
closed, this surface produces a `product-closure-audit.schema.json` artifact and
nothing else — findings, reopened obligations and proposed issue deltas, none of
which carry write authority.

## `STAGE_7_TECH_LEAD_PLANNER`

Compiles bounded implementation packets. It refuses an edge that consumes
nothing the parent produces, two packets holding overlapping leases, and a
convergence with more or fewer than one owner.

## `STAGE_8_MOLECULAR_WORKER`

Executes exactly one packet inside exactly one lease against exactly one subject
digest. A stale digest stops the packet; it does not get re-pointed at whatever
the artifact became.

## `STAGE_9_CONVERGENCE_OWNER`

The single writer of shared indexes. It may not promote a remaining item to
`PASS`, and it may not close a lane owned by a consumer or a Human — those exit
the loop as named remaining items with named owners.

## What no surface may do

No surface requests private chain of thought, hidden reasoning or an inner
monologue. Asking a model to produce reasoning nobody is allowed to inspect
makes the one artifact that would falsify its conclusion unavailable, which is
the opposite of every other control in this Skill.

No surface grants merge, permission, secret or production authority. A prompt
that hands out an authority is not a smaller Human gate; it is no Human gate.
