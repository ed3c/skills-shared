# Codex SDK controller adapter

Use this module only after the Tech Lead core has already frozen the task contract and admitted the task into a ready wave.

## Authority boundary

The adapter owns runtime execution only. It may bind a frozen task to a worktree, create or resume a compatible Codex thread, run one attempt, and return a runtime receipt. It does **not** own semantic decomposition, DAG edges, lease admission, acceptance PASS, GitHub issue closure, PR merge, release, or evidence promotion.

## Authentication boundary

The live implementation uses the official `openai-codex` Python SDK and relies on existing Codex authentication. Repository state must never contain API keys, access/refresh tokens, browser-login artifacts, or private reasoning. When no valid Codex account is available, execution fails closed and instructs the operator to sign in through Codex/ChatGPT outside repository state.

## State machine

```text
TASK_NODE_READY
  -> SESSION_PACKET_COMPILED
  -> WORKTREE_BOUND
  -> CODEX_THREAD_STARTED | COMPATIBLE_THREAD_RESUMED
  -> ATTEMPT_EXECUTED
  -> STRUCTURED_RESULT_COLLECTED
  -> RUNTIME_RECEIPT_EMITTED
  -> CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
  -> SHADOW_REVIEW
  -> ADMITTED | BLOCKED | RETRYABLE
```

A returned SDK turn is never sufficient proof of implementation correctness. `RUNTIME_RESULT_ONLY` is the maximum evidence ceiling before independent source/diff/test readback.

## Thread policy

- A new task defaults to `thread_policy=new`.
- Retry may use `resume-compatible` only when the immutable task contract, repo/base/tree, worktree, lease, and predecessor receipts remain compatible.
- Every retry receives a fresh `attempt_id` even when a thread is resumed.
- One writable lease has one writing worker at a time.

## Durable receipt rules

Durable state may contain IDs and digests required for orchestration: task/attempt IDs, exact git subjects, worktree identity, prompt digest, thread/turn IDs, turn status, and a digest of the final response. Do not persist full model prose or private reasoning as control-plane truth.

## Public implementation

`../scripts/run_codex_sdk_worker.py` provides two modes:

1. static mode: validates the frozen manifest and emits `STATIC_CONTRACT_ONLY` without requiring the SDK;
2. `--execute`: imports `openai_codex`, reuses existing Codex auth, runs in `Sandbox.workspace_write`, and emits a runtime-only receipt that still requires controller readback.

`../tests/codex_sdk_controller_selftest.py` plants credential, digest, lease-overlap, and incompatible-thread mutations. Live Codex execution is intentionally outside that deterministic fixture denominator and remains `NOT_EXERCISED` until a consumer/runtime receipt proves it.
