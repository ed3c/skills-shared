# AGENTS.md — Agentic Tech Lead runtime handoff

Read this file before executing or modifying any queue in this directory.

## Read order

1. repository root `AGENTS.md`, `CONTEXT.md`, and `ARCHITECTURE.md`;
2. `../AGENTS.md`, `../README.md`, and `../SKILL.md`;
3. `../../../docs/traceability/current-runtime-handoff/AGENTS.md` and `README.md`;
4. this directory's `README.md`;
5. exactly one selected queue;
6. the owning script/module/contracts and their tests;
7. for Spatial #407, `../../spatial-loop-systems-engineering/integration/AGENTS.md`, `README.md`, and the Spatial Molecular index;
8. current issue comments and exact current GitHub/Git/runtime subjects.

## Subject authority

Queues in this directory do not necessarily share one Git subject. The `subject` object inside the selected queue is the continuation contract for that queue, and current Git/GitHub readback decides whether it is still fresh.

The Wave-3/Codex/Herdr/source queues were originally compiled against:

```text
commit    249abc47847f8295b1c75c9d4c84457c5126fd89
tree      a24b9b7ace6f4022967d41262ecdc704d5c11646
rollback  d5993267e03b217dcdab9702dab0400ab03df860
```

`spatial-407-local-handoff-queue.json` binds its own #407 candidate subject and rollback. Do not substitute the older shared subject above for the Spatial queue.

Any change to an owning script/schema, required semantic tree, admitted main, or predecessor result may invalidate a queue. Recompile rather than running a stale queue.

## Queue admission

- Validate shape against `../references/local-handoff-queue.schema.json`.
- Validate semantics with `../scripts/assert_local_handoff_queue.py`.
- Require exactly one `ACTIVE` item.
- Respect `BLOCKED_BY_PREDECESSOR`; do not execute a dependent item early.
- Resolve every unresolved operation into a concrete command contract before execution.
- Re-read current main/PR/runtime subjects before materialization.
- Never insert credentials, tokens, auth/session material, raw prompts, private reasoning, terminal transcript, or final model prose into a queue or receipt.
- Preserve failed, blocked, skipped, and partial attempts; never rewrite them to PASS.

## Writer and runtime authority

```text
Tech Lead        queue/task/lease/receipt contract + predecessor ordering
local operator   admitted runtime, actual machine identity, host permission, source packet, cleanup
controller       source/diff/test or closure readback
Shadow           independent read-only same-subject review
Human/repo       semantic conflict, provider activation, merge, release, rollback, permission changes
```

No queue owns `merge`, `force_push`, `issue_close`, `queue_advance`, `provider_activation`, `semantic_conflict_resolution`, or permission widening.

## Provenance law

For a rewritable PR branch that fails the repository commit-role gate:

- rebuild/squash through a runtime that can emit the actual repository-required machine author identity and `Driven-By` / `Driven-On` trailers;
- do not add rewritable commits to `known_unclassified`;
- do not move `enforced_from`;
- do not relabel machine work as Human;
- do not weaken `check_commit_roles.py` or any admission workflow;
- preserve the red run and original source tree as forensic/semantic evidence.

This law stays in force for any future rewritable branch that fails the gate. Its Spatial #407/#412 binding was RESOLVED on 2026-08-22 without violating it: the #412 semantics reached `main` through a superseding replayed carrier (terminal merge `c27f8c3`, machine identity `agent-macro@claude-code.invalid`), the connector lineage classifies as declared-owner human writes, no rewritable commit entered `known_unclassified`, `enforced_from` did not move, and PR #412 remains preserved as first-red forensic evidence. See `data/handoff/spatial-407/publication-provenance-receipt.json`.

## Subject-mutation law

If an ACTIVE item changes implementation bytes or contracts, the queue normally ends after that item and a successor is rebound to the admitted result. A multi-item queue is valid only when the later item explicitly declares `BLOCKED_BY_PREDECESSOR` and its subject is revalidated/recompiled before execution.

For Spatial #407:

```text
provenance-compliant publication rebuild  ACTIVE
→ admitted main / exact-main receipts
→ #411 live independent Shadow canary      currently BLOCKED_BY_PREDECESSOR
```

The #411 item cannot reuse a stale pre-admission subject merely because it is already present in the JSON queue.

## Exit law

Only a validated receipt with verdict `PASS` satisfies an item exit. `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `HUMAN_ADMIT_REQUIRED`, process completion, terminal text, model agreement, a static selftest, or another evidence lane's PASS cannot satisfy a live item.

For publication/admission work, all named load-bearing repository gates must pass on the exact publication subject. Three ordinary green workflows do not override a red Skill Eval Contract.

Report exact subject, command contract, receipt path/digest, cleanup, failed attempts, next owner, and evidence ceiling.