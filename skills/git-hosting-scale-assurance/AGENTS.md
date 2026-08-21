# AGENTS.md — git-hosting-scale-assurance

This directory owns the portable deterministic assurance contract for Git-hosting durability, consistency, cache, compaction, recovery and benchmark evidence. It does not own a hosting runtime.

## Read order

1. repository root `AGENTS.md` and exact current Git subject;
2. this file;
3. `README.md`;
4. `SKILL.md`;
5. `references/hosting-assurance.schema.json`;
6. `scripts/check_hosting_assurance.py`;
7. `tests/run-all.sh` and fixtures;
8. issue #531 then implementation owner #532;
9. physical owner #534 and independent Shadow #535 before any live claim;
10. current PR/head/workflow state.

## Writer and authority law

One Worker owns this Skill directory for the #532 atom. Do not edit root/shared indexes or canonical Git Town README from this atom. A physical consumer/runtime, cloud account, object store, credentials, production repository, merge or release remains outside this writer lease.

```text
schema/checker PASS != physical hosting PASS
source statement != benchmark truth
Git object DAG != task/issue DAG != Stack PR DAG
local cache != source of truth
gossip arrival != correctness
Shadow agreement != Human Admit
```

## Required completion packet

Report exact base/head/tree, changed paths, schema/checker version, positive/hollow/mutation counts, first-red and repair lineage, workflow arrival, remaining physical lanes, cleanup/rollback and next owner. Never report `LIVE_CANARY_VERIFIED` without #534 exact runtime receipts.