# AGENTS.md — Agentic Tech Lead runtime handoff

Read this file before executing or modifying any queue in this directory.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. `../AGENTS.md`, `../README.md`, and `../SKILL.md`;
3. `../../../docs/traceability/current-runtime-handoff/AGENTS.md` and `README.md`;
4. this directory's `README.md`;
5. exactly one selected queue;
6. the owning script/module/contracts and their tests;
7. current issue comments and exact current GitHub/Git/runtime subjects.

## Bound implementation subject

```text
commit    249abc47847f8295b1c75c9d4c84457c5126fd89
tree      a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback  d5993267e03b217dcdab9702dab0400ab03df860
```

These queues do not bind the later documentation commit. They bind the implementation that the local runtime must execute or harden. Any change to an owning script/schema invalidates the queue and requires recompilation.

## Queue admission

- Validate shape against `../references/local-handoff-queue.schema.json`.
- Validate semantics with `../scripts/assert_local_handoff_queue.py`.
- Require exactly one `ACTIVE` item.
- Resolve every unresolved operation into a concrete command contract before execution.
- Never insert credentials, tokens, auth/session material, raw prompts, private reasoning, terminal transcript, or final model prose into a queue or receipt.
- Preserve failed, blocked, and partial attempts; never rewrite them to PASS.

## Writer and runtime authority

```text
Tech Lead        queue/task/lease/receipt contract
local operator   admitted runtime, host permission, source packet, cleanup
controller       source/diff/test or closure readback
Shadow           independent read-only same-subject review
Human/repo       provider activation, merge, release, rollback, permission changes
```

No queue owns `merge`, `force_push`, `issue_close`, `queue_advance`, `provider_activation`, or `semantic_conflict_resolution`.

## Subject-mutation law

If the ACTIVE item changes implementation bytes or contracts, the queue ends after that item. Compile a new queue against the admitted result before running a successor. This is why #508 and #464 are not placed into one stale two-item queue.

## Exit law

Only a validated receipt with verdict `PASS` satisfies an item exit. `NOT_EXERCISED`, `HUMAN_ADMIT_REQUIRED`, process completion, terminal text, model agreement, or a static selftest cannot satisfy a live item.

Report exact subject, command contract, receipt path/digest, cleanup, failed attempts, next owner, and evidence ceiling.
