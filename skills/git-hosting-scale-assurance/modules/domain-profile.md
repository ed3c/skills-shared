# Git hosting assurance domain profile

The portable body decides what a receipt must prove and what a PASS may claim.
This module decides which concrete storage backend, runtime, replication
topology, benchmark harness, source proposal and Human authority a run is bound
to. Nothing here is loaded unless its trigger matches.

## Trigger

Load when a named subject must be bound to a run: choosing which object store or
log backend the durability receipt speaks about, which runtime and image digests
identify the implementation, which replication or propagation topology the
gossip observations came from, which harness produced a benchmark run, which
source article is being treated as `SOURCE_PROPOSAL`, or which consumer owns a
physical lane the deterministic checker cannot enter.

## Non-trigger

Do not load to decide whether a receipt is admissible, which `GS-C..` code a
violation earns, what the state machine allows next, or what a contract PASS may
claim. Those are core transitions, and attaching a backend name to them narrows a
portable law into one deployment's habits.

## Assumptions

The subject is an implementation that can be pinned to an immutable commit/tree
plus runtime digests, and whose storage backend states a consistency class its
operator can name. When that is untrue — the topology is described only in prose,
the backend's consistency class is unknown, or the runtime moves between the
receipt and the readback — the honest output is a closure record with fewer bound
receipts, not one with looser ones.

## Selection inventory

| Frozen need | Bind | Produced state |
|---|---|---|
| durable persistence boundary for one write | consumer storage/log adapter | `DURABLE_ACK_BOUND` |
| ref transaction and CAS precondition record | consumer ref-backend adapter | `REF_TRANSACTION_BOUND` |
| stale-read validation and catch-up behavior | consumer read-path adapter | `READ_FRESHNESS_AND_CACHE_MODEL_BOUND` |
| propagation observations under drop/delay/duplicate | consumer propagation adapter | `GOSSIP_AUTHORITY_CEILING_BOUND` |
| compaction with reachability preservation | consumer maintenance adapter | `COMPACTION_AND_REACHABILITY_BOUND` |
| corruption, partial write, restart replay | consumer recovery adapter | `FAILURE_RECOVERY_MODEL_BOUND` |
| topology, workload, faults, metrics, exclusions | consumer benchmark harness | `WORKLOAD_AND_BENCHMARK_DENOMINATOR_BOUND` |
| execution against real infrastructure | consumer canary owner | `LIVE_CANARY_RECEIPTS_REQUIRED` consumed |
| merge, release, provider activation, adoption | Human admission record | leaves `HUMAN_ADMIT_REQUIRED` |

Each row names a role, not a product. A consumer adapter binds the concrete
backend in its own repository and passes back only the typed receipt; a vendor
name in this table would make the shared body describe one deployment.

## Source proposal binding

The method was derived from a third-party hosting article (the Cursor
Git-at-scale write-up). Its status here is `SOURCE_PROPOSAL` and nothing more:

```text
article locator                bound by the consumer issue
immutable article bytes        ABSENT
article performance numbers    SOURCE_PROPOSAL, never a local result
Cursor's production behavior   NOT_EXERCISED, and unreachable from this repository
```

The absent immutable packet is a completion dependency for article-claim
disposition. It is not a reason to reconstruct the article from memory, and no
state above `SOURCE_PROPOSAL` may be recorded for a claim whose bytes were never
materialized.

## Evidence ceiling

A backend's own success code, a completed push, a finished repack, a delivered
propagation message or a finished benchmark process is transport evidence about
one run on one topology. It never becomes evidence that the data survives power
loss, that concurrent histories linearize, that a rebuilt cache is complete, or
that the numbers hold at another size. A consumer receipt closes exactly the lane
it was produced in. Fixture evidence never becomes live evidence, and a lane this
repository cannot enter stays `NOT_EXERCISED` rather than being softened into
something that reads as decided.

## Fallback

When a backend cannot expose its durability boundary, record the receipt as
absent with its owner named and let the checker return `BLOCKED` — a closure
record that is honestly incomplete is usable, one padded with inference is not.
When no consumer owns the live canary, the run terminates at
`LIVE_CANARY_RECEIPTS_REQUIRED` with that lane listed as remaining. When a
benchmark cannot reproduce its declared topology, drop the performance claim
rather than restating it with a wider caveat.

## Forbidden overrides

This module and any module it links may not override `CORE-LAW-001` through
`CORE-LAW-005`. It may not move an acknowledgement boundary earlier than durable
persistence, admit a ref read before its transaction commits, promote a cache or
a propagation channel to authority, close a lane with a receipt from another
lane, promote a source proposal or a fixture to a live result, extend one
measured topology to arbitrary scale, or substitute reviewer agreement for Human
admission — and it may not activate itself because a particular backend happens
to be reachable.
