# Issue #375 — Codex SDK execution packet

Base: `85e6723869bdd545666e07b7c5c6a8f491256cb9`
Branch: `ctl/375-codex-sdk-runtime-adapter`
Prep: #381 / #382
Convergence: #379

## Read order

Root `AGENTS.md` → root README/CONTEXT/ARCHITECTURE → document State Machines/closure routes → nearest Agentic Tech Lead `AGENTS.md`/README/SKILL → task/scheduler contracts → domain profile → issue #375.

## Writable lease

Only issue-owned Codex adapter/session/result/checker/test/fixture files under this Skill. Shared README/AGENTS/traceability/Git Town indexes, `SKILL.md`, golden fixtures and unrelated scheduler authority are read-only; #379 owns convergence documentation.

## State machine

`TASK_NODE_READY → SESSION_PACKET_COMPILED → WORKTREE_BOUND → CODEX_THREAD_STARTED → ATTEMPT_EXECUTED → STRUCTURED_RESULT_COLLECTED → SOURCE_DIFF_TEST_READBACK → CAPABILITY_RECEIPT_EMITTED → SHADOW_REVIEW → ADMITTED | BLOCKED | RETRYABLE`.

## Required contract

Bind task, attempt, repo/base/tree, worktree, predecessor receipts, allowed/read-only paths, prompt digest and thread identity. New task defaults to a new thread; retry may resume only a compatible immutable task and still creates a new attempt. One writer per lease. Process exit, model prose, structured result, filesystem readback, deterministic tests and receipt remain distinct. ChatGPT-subscription/local signed-in Codex must not require repository-stored API keys. Never persist auth/session material or private reasoning.

## Shadow controls

Refuse stale subject, wrong worktree, duplicate writer, overlapping lease, missing predecessor, self-reported PASS without readback, fixture→live promotion, malformed structured result, incompatible thread reuse, or credential persistence.

## Zero-context worker prompt

Implement issue #375 on this branch only. Follow the read order and lease above. Build a trigger-selected Codex SDK runtime adapter without replacing planner/DAG/scheduler/merge authority. Add deterministic positive and mutation controls. Do not edit convergence docs. Return exact base/head/tree, changed paths, test denominator, evidence ceiling, cleanup/rollback and #379 handoff. Do not claim live SDK execution from static evidence.

## Completion gate

Positive contract/checker/tests PASS; every planted mutation turns red; affected Skill suites remain green; no secret/auth/private-reasoning durable fields; live SDK execution remains `NOT_EXERCISED` until an admitted runtime receipt exists.
