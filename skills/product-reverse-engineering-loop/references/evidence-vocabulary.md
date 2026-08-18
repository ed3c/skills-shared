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
