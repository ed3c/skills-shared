# Herdr runtime observer

Herdr is an optional execution-surface observer. It can make multi-worktree/multi-agent activity visible and attachable, but it never becomes completion authority.

## Authority boundary

Allowed:

- observe the configured agent target;
- bind workspace/pane/process/native-session identity to task + attempt + worktree;
- bind `foreground_cwd` to the expected worktree when the live observer is used;
- report `RUNNING`, `BLOCKED`, `IDLE`, `DONE_CANDIDATE`, or `UNKNOWN`;
- expose operator attach/takeover routing outside durable receipts.

Forbidden:

- deciding semantic dependencies;
- converting terminal `done` into implementation PASS;
- closing issues, merging PRs, releasing, or promoting evidence;
- persisting credentials, terminal transcripts, screen text, or private reasoning as control-plane truth.

## State machine

```text
WORKTREE_ALLOCATED
  -> HERDR_WORKSPACE_BOUND
  -> AGENT_PROCESS_OBSERVED
  -> WORKTREE_AND_SESSION_IDENTITY_BOUND
  -> RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
  -> CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
  -> RECEIPT_VERIFIED
```

`DONE_CANDIDATE` means only that Herdr classified the agent lifecycle as done. The Tech Lead controller must still read source/diff/tests/results independently.

## Optional fallback

`../scripts/herdr_runtime_observer.py` first checks whether the `herdr` binary exists. If absent it emits `UNAVAILABLE_FALLBACK` and leaves the controller path unchanged. Herdr is therefore never a hard dependency for Codex SDK + standard git worktree execution.

When available, the adapter uses Herdr's JSON-oriented CLI (`agent get` plus `agent explain --json`) and reduces the response to identity/state fields only. The live path requires `foreground_cwd` by default and verifies it against the expected worktree. Exact expected pane/workspace/process/native-session IDs may also be supplied and any mismatch fails closed.

The host-neutral receipt contract is `../references/contracts/herdr-observer-receipt.schema.json`. `../references/examples/herdr-runtime-binding.example.json` shows a Bettor-style runtime binding shape without importing Bettor domain state into shared core.

`../tests/herdr_observer_selftest.py` covers fallback, `done -> DONE_CANDIDATE`, authority denial, credential/transcript rejection, missing/wrong worktree identity, native-session mismatch, and pane mismatch. Live Herdr execution remains a separate consumer/provider evidence lane.
