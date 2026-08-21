# Controlled evidence and closure vocabulary

Four vocabularies run through this Skill and none of them substitutes for
another. Every one is closed: a value outside its set is a contract error, not a
new nuance.

## 1. Repository evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
HUMAN_ADMIT_REQUIRED
```

These are the repository's states and this Skill does not extend them. The three
that get confused are worth separating explicitly. `ABSENT` means the evidence
does not exist. `NOT_EXERCISED` means the mechanism exists and nobody ran it.
`NOT_IMPLEMENTED` means the mechanism does not exist to be run. A row that says
`ABSENT` when it means `NOT_EXERCISED` reads as a dead end when it is a queue.

## 2. Signal kinds and their grades

The grade is a function of the kind alone. It is not argued per signal, because
a per-signal argument reliably converges on whatever the author already believed.

| Signal kind | Grade | What it actually asserts |
|---|---|---|
| `OBSERVED_ARTIFACT` | `OBSERVED` | someone drove the surface and recorded what it did |
| `PAID_CONVERSION` | `OBSERVED` | money moved, which is the only demand signal that is not a proxy |
| `USER_INTERVIEW` | `REPORTED` | a user said this about their own behavior |
| `THIRD_PARTY_REPORT` | `REPORTED` | someone else says they observed it |
| `SOURCE_STATEMENT` | `CLAIMED` | the vendor says so about itself |
| `MARKET_ATTENTION` | `CLAIMED` | the category is being discussed |
| `INFERENCE` | `INFERRED` | a reading of other signals, with no observation of its own |

Two refusals fall straight out of this table.

`SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE` — a vendor's description of its own
architecture is the vendor's marketing surface, and treating it as a system trace
imports every simplification the vendor made on purpose. A `SOURCE_STATEMENT`
carrying an `observation` block is refused.

`MARKET_ATTENTION_AS_DEMAND` — attention measures how loudly a category is
discussed. Demand measures whether anyone will leave what they already use.
Attention filed under a job or a pain slot is refused, which is why the compiler
projects no `MARKET` signal into the dossier at all.

## 3. Mechanism classifications

```text
OBSERVABLE_MECHANISM        an oracle exists in a technical lane and can refute it
VENDOR_CLAIMED_MECHANISM    only the vendor asserts it; nothing here can refute it
UNOBSERVABLE_MECHANISM      it may be true and no procedure would show it false
```

Only `OBSERVABLE_MECHANISM` enters the MVP scope. The other two are recorded, not
deleted: an excluded mechanism that disappears from the dossier comes back as a
rediscovery next time.

## 4. Closure states

```text
CLOSED_BY_ORACLE            an oracle in the row's own lane ran and did not refute it
OPEN_WITH_ORACLE            an oracle exists in the row's own lane and has not run
BLOCKED_NO_ORACLE           nothing would show this row false
BLOCKED_NOT_FALSIFIABLE     the claim's own shape admits no refutation
BLOCKED_LANE_MISMATCH       the only available oracle speaks a different lane
OUT_OF_SCOPE                deliberately excluded, with the exclusion recorded
HUMAN_ADMIT_REQUIRED        a person owns the decision, not a procedure
```

`compile_prel.py` emits four of these: `OPEN_WITH_ORACLE`, `BLOCKED_NO_ORACLE`,
`BLOCKED_NOT_FALSIFIABLE` and `HUMAN_ADMIT_REQUIRED`. The other three arrive only
from a consumer, and the difference matters: a state no production code emits is
a state that exists in the schema and nowhere else, and a checker that validates
it looks green whether or not anything can ever reach it.

`CLOSED_BY_ORACLE` is not produced by anything in this repository, and that is
recorded rather than repaired. Compiling an oracle is not running one, so
`compile_prel.py` emits `OPEN_WITH_ORACLE` at its strongest. The state stays in
the contract because a consumer that actually executed an oracle needs somewhere
to say so, and `check_prel_contract.py` validates the state when it arrives. In
this repository's lane the producer of `CLOSED_BY_ORACLE` is `NOT_IMPLEMENTED`.

## 5. Oracle lanes, and why they do not substitute

```text
DETERMINISTIC   a procedure with a byte-comparable verdict
BEHAVIORAL      a repeatable observation of a surface's response
USER            a person used it and something happened
PAID            a person paid, renewed, or churned
HUMAN_ADMIT     a person decided
```

A row closes only through an oracle in its own lane. The named refusal is
`TECHNICAL_PASS_AS_USER_VALIDATION`: a deterministic suite proves the mechanism
reproduces, and proves nothing at all about whether anyone wants it. This is the
cheapest laundering path in the whole loop, because the technical evidence is the
evidence that is easy to produce, and it is the one most often reported as
progress.

## Refusal codes

Every code below is emitted by `scripts/check_prel_contract.py` and planted as a
defect by `tests/selftest.py`, so each one is proven to go red.

```text
SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE
FEATURE_CLONE_WITHOUT_JOB_HYPOTHESIS
MARKET_ATTENTION_AS_DEMAND
MECHANISM_WITHOUT_OBSERVABLE_ORACLE
TECHNICAL_PASS_AS_USER_VALIDATION
FALSE_SERIALIZATION_OF_INDEPENDENT_LEAVES
HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE
PRIOR_CHAT_PROSE_AS_HANDOFF
CONSUMER_TOPOLOGY_IN_PORTABLE_CORE
PROMPT_GRANTS_RESERVED_AUTHORITY
PROMPT_REQUESTS_PRIVATE_REASONING
PROMPT_SURFACE_SET_DRIFT
PROMPT_DEPENDENCY_UNBOUND
CLOSURE_STATE_UNSUPPORTED
CAPABILITY_EDGE_UNBOUND
SIGNAL_DEPENDENCY_UNBOUND
COMPATIBILITY_FIELD_UNKNOWN
HANDOFF_EDGE_UNBOUND
HANDOFF_CYCLE
UNGRADED_SLOT
CEILING_OVERCLAIM
HOLLOW_EVIDENCE
STALE_SUBJECT
```

## Pre-registered refusal classes

The codes above are what `check_prel_contract.py` emits today. The classes below
are the frozen identities for the failures a *dispatched session* can commit, and
they are declared before the session runs rather than named afterwards. They are
machine-readable in `session-dispatch-request.schema.json` (`refusal_classes`,
which the request watches) and in `session-receipt.schema.json`
(`refusals_observed`, which the receipt reports actually fired). Persisted
mutation execution is owned elsewhere; what is frozen here is the id set and what
each id means.

```text
C01_MUTABLE_SUBJECT                        a subject named by a branch, tag or latest rather than an exact object
C02_SOURCE_STATEMENT_PROMOTED_TO_INTERNAL_FACT   a vendor claim reported as an observed internal
C03_TECH_PASS_PROMOTED_TO_USER_OR_PAID_VALIDATION  a deterministic pass reported as demand
C04_START_DEPENDENCY_USED_AS_COMPLETION_PROOF     a prerequisite for starting reported as evidence of finishing
C05_MISSING_EXACT_RECEIPT                  a state asserted with no exact artifact, digest or exit behind it
C06_OVERLAPPING_WRITER_LEASE               two concurrent writers holding the same path or resource
C07_HIDDEN_MULTI_PARENT_CONVERGENCE        a request consuming more than one parent without an owner for the merge
C08_PROJECTION_USED_AS_MACHINE_AUTHORITY   an external document read as implementation or completion truth
C09_SESSION_REQUEST_PROMOTED_TO_RUNNING    a launch request reported as a running session
C10_CONSUMER_STATE_LEAK_IN_PORTABLE_CORE   consumer topology or a machine-local path inside portable bytes
C11_PROMPT_GRANTS_MERGE_SECRET_PERMISSION_OR_PRODUCTION_AUTHORITY   a packet widening reserved authority
C12_PRIVATE_REASONING_FIELD                a field asking for or persisting private chain of thought
C13_ROLLBACK_SUBJECT_ABSENT_OR_EQUAL_TO_MUTABLE_ALIAS   nothing exact to return to
C14_SOURCE_OR_FIXTURE_USED_AS_LIVE_PASS    a fixture or a source statement reported as live evidence
```

`C04` and `C09` are the two the schemas enforce structurally rather than by
convention: `start_dependencies` and `completion_dependencies` are separate
arrays, and a dispatch request pins `lifecycle_state` to `LAUNCH_REQUESTED` with
`running_session` pinned to `null`. The rest are declarations a consumer's
checker binds to — a class with no producer is a class that exists in the
vocabulary and nowhere else, and that is recorded here rather than repaired.
