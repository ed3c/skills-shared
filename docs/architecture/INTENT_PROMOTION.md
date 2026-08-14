# Intent Promotion: Subject-Bound Design Intent and Durable Writeback

## Status

This document defines the portable governance contract implemented by:

```text
evals/schema/intent-promotion-contract.schema.json
evals/schema/intent-promotion-receipt.schema.json
scripts/check_intent_promotions.py
tests/test_intent_promotions.py
```

The source PDF proposes that an intent can move from a working hypothesis through
local checks, PR/CI review, and permanent `CONTEXT.md` or memory writeback. This
repository retains that lifecycle idea, but separates events from authority.

```text
PR opened             != durable intent
CI green              != owning exact-head evidence
caller flag           != Human approval
semantic similarity   != permission to overwrite history
```

The PDF remains `SOURCE_PROPOSAL`. This contract does not perform a memory write,
edit `CONTEXT.md`, approve a business rule, or establish official compliance.

## Lifecycle

```text
HYPOTHESIS
  -> CANDIDATE
  -> PROPOSED
  -> VERIFIED
  -> ADMITTED
  -> CANONICAL

ADMITTED | CANONICAL
  -> SUPERSEDED | REVOKED
```

| Target state | Required evidence | Durable writeback |
|---|---|---|
| `CANDIDATE` | local evaluator on the exact candidate | forbidden |
| `PROPOSED` | local evaluator plus exact PR head | forbidden |
| `VERIFIED` | local plus registered owning CI on the exact head | forbidden |
| `ADMITTED` | exact PR, owning CI, and admitted merge/release subject | declared module/project destinations only |
| `CANONICAL` | admitted subject plus exact Human approval | declared root/global destinations when explicitly authorized |
| `SUPERSEDED` | admitted subject and append-only supersession lineage | history only; never current projection |
| `REVOKED` | admitted subject, Human approval, and reason | history only; never current projection |

`VERIFIED` is evidence about a candidate. It is not permission to mutate durable
memory. The minimum durable state is `ADMITTED`.

## Exact identity

The contract binds:

```text
repository + contract commit + contract tree
Intent-Bound contract path + Git blob SHA
evaluator id + version + implementation path + implementation digest
candidate commit + tree + PR head
admitted merge/release identity
Human approval subject and allowed actions
writeback content digest + locator + authority subject
supersession receipt lineage
```

A parent, candidate, evaluator, bound Intent-Bound contract, or contract-byte
change invalidates older receipts.

## Evaluator authority

The contract owns an evaluator registry. A receipt cannot invent an evaluator
name or reuse another green workflow.

```text
LOCAL
  deterministic candidate evidence

OWNING_CI
  exact-head hosted execution for this contract

EXTERNAL
  separately admitted observation; never implied by LOCAL or OWNING_CI
```

The gate requires exact equality for evaluator version, implementation path,
implementation digest, authority, and `owning` state. Every evaluator receipt
must bind the promoted candidate commit.

## PR and admission boundary

An exact PR subject includes:

```text
repository
PR number
head SHA
base ref
state
observation digest
```

An admitted subject includes:

```text
MERGE_COMMIT | RELEASE_ARTIFACT
repository
source head SHA
admitted identity
ADMITTED status
receipt digest
```

`ADMITTED` is refused when the admitted subject came from a different candidate
head. A merge-shaped object with no source-head binding cannot authorize
writeback.

## Writeback policy

Destinations declare:

```text
destination id
scope
TRANSIENT | DURABLE
allowed states
locator prefix
Human-owned flag
```

Each writeback declares:

```text
locator
content digest
APPEND | SUPERSEDE | REVOKE
authority subject
current_projection
```

Rules:

1. A transient writeback binds the candidate commit.
2. A durable writeback binds the admitted merge/release identity.
3. Durable writeback starts at `ADMITTED`.
4. Root/global writeback requires `CANONICAL`.
5. A Human-owned destination requires an approval action
   `WRITE:<destination-id>`.
6. `SUPERSEDE` requires exact prior receipt lineage.
7. Terminal transitions may append history only.
8. A terminal history record sets `current_projection: false`.
9. Similarity is discovery evidence only. Similarity never authorizes update or
   deletion.

## Human Admit

A caller may request approval. A caller cannot create approval.

```text
--allow-root-override
--approve
approve=true
```

These values are non-authoritative inputs. A valid Human approval receipt binds:

```text
Human identity
approval state ADMITTED
exact admitted subject
allowed actions
receipt digest
```

An Agent or automation-generated approval is rejected. Approval for a different
commit or admitted identity is rejected.

## Stable exits

```text
0   admitted subject passed
2   readable subject violated contract or policy
64  usage, missing file, invalid UTF-8, or malformed JSON
70  evaluator implementation failed
```

This distinction prevents an absent input from being reported as a policy
failure and prevents a checker crash from being reported as a document failure.

## Controls

The selftest and unit tests cover at least:

- PR-open to durable-memory false promotion;
- foreign green workflow replacing owning CI;
- stale evaluator version/digest or old candidate SHA;
- stale PR head;
- admitted subject from another head;
- durable locator outside its declared scope;
- root write with only a caller flag;
- Agent-created approval;
- approval for another admitted subject;
- similarity-style overwrite without lineage;
- terminal intent retained as current projection;
- changed contract bytes;
- changed Intent-Bound contract identity;
- private reasoning persistence;
- exit-code collapse between refusal and unusable input.

## Evidence boundary

```text
lifecycle/schema mechanism            IMPLEMENTED
cross-file semantic gate              IMPLEMENTED
exact evaluator registry              IMPLEMENTED
exact PR/admitted-subject binding      IMPLEMENTED
durable writeback gate                IMPLEMENTED
Human approval shape                  IMPLEMENTED
actual mem0 write                     NOT_IMPLEMENTED
actual CONTEXT.md mutation            NOT_IMPLEMENTED
production writeback                  NOT_EXERCISED
business-rule semantic admission      HUMAN_ADMIT_REQUIRED
merge/release promotion               HUMAN_ADMIT_REQUIRED
```
