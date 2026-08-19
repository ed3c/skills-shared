# Herdr runtime observer

Herdr is an optional execution-surface observer. It can make multi-worktree/multi-agent activity visible and attachable, but it never becomes completion authority.

## Authority boundary

Allowed:

- observe the configured agent target;
- bind workspace/pane/process identity to task + attempt + worktree;
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
  -> RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
  -> CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
  -> RECEIPT_VERIFIED
```

`DONE_CANDIDATE` means only that Herdr classified the agent lifecycle as done. The Tech Lead controller must still read source/diff/tests/results independently.

## Optional fallback

`../scripts/herdr_runtime_observer.py` first checks whether the `herdr` binary exists. If absent it emits `UNAVAILABLE_FALLBACK` and leaves the controller path unchanged. Herdr is therefore never a hard dependency for Codex SDK + standard git worktree execution.

When available, the adapter uses Herdr's JSON-oriented CLI (`agent get` plus `agent explain --json`) and reduces the response to identity/state fields only. Exact expected pane/workspace/process IDs may be supplied and mismatches fail closed.

`../tests/herdr_observer_selftest.py` covers fallback, `done -> DONE_CANDIDATE`, authority denial, credential/transcript rejection, missing identity, and pane mismatch. Live Herdr execution remains a separate provider/runtime evidence lane.
