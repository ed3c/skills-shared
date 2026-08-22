# AGENTS.md — Issue closure audit ledger

This directory stores provider-read closure packets governed by `../issue-closure-contract.schema.json` and `../../scripts/assert_issue_closure_contract.py`.

## Read order

1. repository root `AGENTS.md`;
2. `skills/agentic-tech-lead-orchestration/AGENTS.md` and README;
3. `../ISSUE_CLOSURE_CONTRACT.md`;
4. `../issue-closure-contract.schema.json`;
5. this directory README;
6. the exact Issue/PR/commit provider subjects represented by a packet.

## Writer law

A packet is a projection of independently read provider facts, never a replacement for GitHub or Git. Do not infer a missing merge, tree, successor, workflow result or acceptance item. Cross-repository PRs and landings must carry `owner/repo` identity. Mutable PR heads are not durable landing authority.

## Shadow law

Independent Shadow checks the same immutable provider subjects and rejects unresolved acceptance hidden by `completed`, closed-unmerged candidates presented as landed, ambiguous PR identities, evidence promotion, erased rejected history, or prose-only successor transfer.

A `PASS` verdict names the Shadow that produced it: `shadow_identity` distinct from `packet_author`, plus a `receipt` path that exists and matches its `sha256` (see the README's Shadow binding section). A packet the writer reviewed alone records `HUMAN_ADMIT_REQUIRED`. Do not invent a reviewer to reach `PASS`, and do not edit the verdict of a packet grandfathered in `enforced-from.json`.

A green deterministic packet proves closure-contract consistency only. It does not execute live/provider/production lanes or authorize merge/release.
