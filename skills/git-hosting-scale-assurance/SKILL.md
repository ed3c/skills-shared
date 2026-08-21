---
name: git-hosting-scale-assurance
description: |
  Verify a declared Git-hosting architecture and exact runtime receipts for durability, ref consistency, disposable-cache freshness, gossip non-authority, compaction reachability, recovery, and bounded benchmark claims. This Skill is host-neutral: it does not implement a Git server, object store, cloud topology, or Cursor's proprietary system. Contract PASS can only request a live canary; merge, release, provider activation, production adoption, and scope exceptions remain Human-owned.
---

# Git Hosting Scale Assurance

## Contract

Use this procedure when a repository or hosting design claims that Git writes survive acknowledgement, refs publish atomically, local repositories are disposable caches, propagation is not correctness authority, compaction preserves reachable objects, failures can be replayed, or a benchmark supports a scale/performance claim.

This Skill verifies evidence supplied by a consumer. It never turns an architecture diagram, provider name, successful push, green fixture, source article, or benchmark summary into physical proof.

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

A deterministic PASS proves only that one evidence packet is internally consistent with this portable contract. Physical durability, linearizability, cache recovery, arbitrary scale, production safety, Cursor production behavior, merge and release require separately bound evidence.