# Privacy routing

## Trigger

Load whenever any evaluator lane other than the local deterministic one may run.
The routing decision is made **before** any evaluator executes, and an undecided
lane is `PRIVACY_LANE_UNDECIDED` — never an implicit `LOCAL_ONLY`.

## Classes and lanes

```text
PUBLIC        → LOCAL_ONLY | PRIVATE_ENDPOINT | EXTERNAL_APPROVED
INTERNAL      → LOCAL_ONLY | PRIVATE_ENDPOINT
CONFIDENTIAL  → LOCAL_ONLY | PRIVATE_ENDPOINT | EXTERNAL_APPROVED*
RESTRICTED    → LOCAL_ONLY only, network disabled
```

\* `CONFIDENTIAL` may reach an external lane only with a human approval receipt
naming the **same document digest** being sent. An approval for a different
subject is refused.

A class may always be processed more privately than its ceiling. It may never be
processed less privately.

## Health is not permission

The two states most often collapsed:

```text
provider health      is the endpoint reachable and working
privacy admission    is this document allowed to go there
```

Neither implies the other, and neither substitutes for the other. An admitted
provider that is unhealthy **blocks** — it does not license a fallback to a lane
this document was never admitted to. A reachable provider that is not admitted
is refused however well it responds.

`scripts/check_privacy_routing.py` tracks the two fields separately and requires
both.

## Durable receipts carry no operational identity

A receipt is written once and read for a long time afterwards. Tokens, session
identifiers, cookies, API keys, and machine paths must never reach one; the
checker refuses a receipt field whose name looks like any of those.

## Fallback is an evidence downgrade

If a selected parser or provider is absent and a fallback runs, the fallback must
be declared. An undeclared fallback is refused, because the resulting evidence is
weaker than the evidence the request asked for and nothing else records that.

## Evidence boundary

```text
routing contract and controls     IMPLEMENTED
health / admission separation     IMPLEMENTED
real provider, endpoint, session  NOT_EXERCISED
credentials                       never held by this repository
legal or privacy approval         HUMAN_ADMIT_REQUIRED
```

Runtime identities for pinned parsers and models are bound by the host
environment, not stored here.
