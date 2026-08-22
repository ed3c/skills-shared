---
name: git-hosting-scale-assurance
description: |
  Verify a declared Git-hosting architecture and exact runtime receipts for durability, ref consistency, disposable-cache freshness, gossip non-authority, compaction reachability, recovery, and bounded benchmark claims. This Skill is host-neutral: it does not implement a Git server, object store, cloud topology, or Cursor's proprietary system. Contract PASS can only request a live canary; merge, release, provider activation, production adoption, and scope exceptions remain Human-owned.
---

# Git Hosting Scale Assurance

<!-- PORTABLE_CORE_START -->

## Contract

Use this procedure when a repository or hosting design claims that Git writes survive acknowledgement, refs publish atomically, local repositories are disposable caches, propagation is not correctness authority, compaction preserves reachable objects, failures can be replayed, or a benchmark supports a scale/performance claim.

This Skill verifies evidence supplied by a consumer. It never turns an architecture diagram, provider name, successful push, green fixture, source article, or benchmark summary into physical proof.

The core owns the state machine, the required-receipt set, the `GS-C01..GS-C20`
refusal vocabulary and the evidence ceiling. Named storage backends, runtimes,
replication topologies, benchmark harnesses, source vendors and the consumer who
owns each physical lane live in [`modules/domain-profile.md`](modules/domain-profile.md).

Two deterministic mechanisms carry the law:

1. `scripts/check_hosting_assurance.py` validates a closure record against
   `references/hosting-assurance.schema.json` and then against the refusal
   vocabulary, emitting one stable `GS-C..` code per violation;
2. structural core/domain separation is asserted separately and substitutes for
   neither:

   ```bash
   python3 scripts/check_skill_core_boundaries.py --skill git-hosting-scale-assurance
   ```

A resolvable route proves reachability. It does not prove that a byte reached a
disk, that a ref was ever published, or that any measured number was produced by
the topology it is attributed to.

## Authority split

```text
source article / design prose          SOURCE_PROPOSAL
this Skill + schemas + checker         METHOD_PLANE
Git commit/tree/blob                   IMPLEMENTATION_IDENTITY
consumer runtime/storage receipts      PHYSICAL_EVIDENCE
operation history + fault schedule     CONSISTENCY_EVIDENCE
benchmark runs                         PERFORMANCE_EVIDENCE
independent Shadow                     ADVISORY_EVIDENCE
merge/release/infrastructure decision  HUMAN_ADMIT
```

## State Machine

```text
REQUEST_BOUND
→ EXACT_HOSTING_SUBJECT_BOUND
→ STORAGE_AND_CONSISTENCY_MODEL_DECLARED
→ DURABLE_ACK_BOUND
→ REF_TRANSACTION_BOUND
→ READ_FRESHNESS_AND_CACHE_MODEL_BOUND
→ GOSSIP_AUTHORITY_CEILING_BOUND
→ COMPACTION_AND_REACHABILITY_BOUND
→ FAILURE_RECOVERY_MODEL_BOUND
→ WORKLOAD_AND_BENCHMARK_DENOMINATOR_BOUND
→ DETERMINISTIC_CONTRACT_AND_MUTATION_PASS
→ LIVE_CANARY_RECEIPTS_REQUIRED
→ SHADOW_REVIEW_REQUIRED
→ HOSTING_ASSURANCE_CANDIDATE | BLOCKED | REJECTED
```

`CONTRACT_PASS`, `SERVER_AVAILABLE`, `PUSH_RETURNED_0`, `REPO_CLONED`, `GOSSIP_DELIVERED`, `REPACK_FINISHED`, and `BENCHMARK_COMPLETED` are not final assurance states.

## Required evidence

A consumer closure record binds an immutable implementation subject plus receipts for:

1. acknowledgement after durable persistence;
2. ref publication after transaction/CAS commit;
3. stale-read authority validation and catch-up/fail-closed behavior;
4. cache destruction and rebuild from declared authority;
5. gossip delivery as optimization only;
6. compaction with reachable-object/ref preservation;
7. corruption/partial-write/restart detection and recovery;
8. benchmark topology, workload, durability, consistency, failures, exclusions, raw metrics and cleanup.

## Hard laws

- **CORE-LAW-001 — acknowledgement follows durability.** A write is acknowledged
  only after the receipt shows it persisted where the declared model says the
  data survives. A returned exit code, an accepted connection or a queued record
  is transport evidence; treating it as durability is `GS-C02`, and it is the
  cheapest confusion to make because both look identical to the client.
- **CORE-LAW-002 — visibility follows a committed transaction.** A ref becomes
  readable only after the transaction or CAS that publishes it commits, and a
  multi-ref publication is one visibility event or it is refused. A receipt
  without its CAS precondition cannot distinguish a serialized update from a lost
  one, so the absent precondition is itself the defect (`GS-C03`, `GS-C04`,
  `GS-C05`).
- **CORE-LAW-003 — caches and propagation are never authority.** A local
  repository is a rebuildable cache and gossip is an optimization. A read served
  from either without validation against the declared authority, or a rebuild
  claimed without object/ref reachability proof, is refused (`GS-C06`..`GS-C09`)
  regardless of whether the served bytes happened to be correct.
- **CORE-LAW-004 — lanes do not substitute.** Deterministic contract evidence,
  live runtime receipts, benchmark measurements and Human admission are
  independent. A fixture PASS is not a live PASS, one measured topology is not
  arbitrary scale, and a number quoted from a source proposal is not a local
  result (`GS-C16`..`GS-C18`). A claim closes only through evidence produced in
  its own lane.
- **CORE-LAW-005 — no agreement substitutes for admission.** Contract PASS may
  request a live canary and nothing more. Independent review is advisory, and two
  reviewers agreeing is still advisory (`GS-C20`); merge, release, provider
  activation, production adoption and scope exceptions stay Human-owned.

## Hard refusals

The deterministic checker uses stable `GS-C01..GS-C20` refusal IDs. It rejects mutable subjects, acknowledgement before durable persistence, visibility before commit, non-atomic publication, absent CAS preconditions, stale reads without authority validation, local-cache authority, gossip authority, rebuild without reachability proof, compaction loss, omitted replica repack cost, hidden corruption, replay gaps, unmatched benchmark subjects, missing durability/error denominators, source-performance promotion, fixture-to-live promotion, arbitrary-scale promotion, absent cleanup/rollback, and Shadow/model agreement promoted to Human Admit.

## Data flow

```text
hosting declaration + exact subject
+ durability/ref/read/cache/gossip/compaction/recovery receipts
+ operation history + benchmark denominator
→ deterministic checker
→ CONTRACT_READY | LIVE_CANARY_REQUIRED | BLOCKED | REJECTED
→ real runtime canary
→ independent Shadow
→ Human admission
```

## Stop conditions

Stop rather than infer when the implementation subject is mutable, a required receipt is absent, a physical claim is supported only by a fixture, a benchmark changes topology or durability semantics, failed runs are omitted, or another authority is being substituted for Human admission.

## Evidence ceiling

```text
portable contract and refusal vocabulary        PASS by the suite in tests/
physical durability and linearizability         NOT_EXERCISED, consumer-owned
cache destruction and rebuild on real storage   NOT_EXERCISED, consumer-owned
arbitrary scale and production safety           NOT_EXERCISED, consumer-owned
the source vendor's own implementation          ABSENT, and never a lane this body can enter
merge, release, provider activation, adoption   HUMAN_ADMIT_REQUIRED
```

A deterministic PASS proves only that one evidence packet is internally consistent with this portable contract. Which consumer owns each `NOT_EXERCISED` lane, and what the source proposal for this method may and may not close, are bound in [`modules/domain-profile.md`](modules/domain-profile.md).

<!-- PORTABLE_CORE_END -->

## Local verification

```bash
bash tests/run-all.sh
```