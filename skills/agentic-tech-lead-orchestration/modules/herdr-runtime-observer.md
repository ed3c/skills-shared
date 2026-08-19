# Herdr runtime observer

Herdr is an optional execution-surface observer. It can make multi-worktree/multi-agent activity visible and attachable, but it never becomes completion authority.

## Authority boundary

Allowed:

- observe one configured agent target;
- bind workspace/pane/PID/PID-start/native-session identity to task + attempt + worktree;
- bind `foreground_cwd` to the expected worktree;
- require a fresh source observation and live process for nonterminal states;
- observe terminal cleanup/residue before emitting `DONE_CANDIDATE`;
- report `RUNNING`, `BLOCKED`, `IDLE`, `DONE_CANDIDATE`, or `UNKNOWN`.

Forbidden:

- deciding semantic dependencies;
- converting terminal `done` into implementation PASS;
- accepting stale/reused PID or orphan-session state;
- hiding residue behind a terminal state;
- closing issues, merging PRs, releasing, or promoting evidence;
- persisting credentials, terminal transcripts, screen text, or private reasoning as control-plane truth.

## State machine

```text
WORKTREE_ALLOCATED
  -> HERDR_WORKSPACE_BOUND
  -> AGENT_PROCESS_OBSERVED
  -> WORKTREE_AND_SESSION_IDENTITY_BOUND
  -> FRESHNESS_AND_LIVENESS_BOUND
  -> RUNNING | BLOCKED | IDLE | DONE_CANDIDATE | UNKNOWN
  -> CLEANUP_RESIDUE_OBSERVED_WHEN_TERMINAL
  -> CONTROLLER_SOURCE_DIFF_TEST_READBACK_REQUIRED
  -> RECEIPT_VERIFIED
```

`DONE_CANDIDATE` means only that Herdr reported terminal state **and** the observer saw a fresh, identity-consistent terminal observation with `cleanup_state=CLEAN` and `residue_count=0`. The Tech Lead controller must still read source/diff/tests/results independently.

## Optional fallback

`../scripts/herdr_runtime_observer.py` first checks whether `herdr` exists. If absent it emits `UNAVAILABLE_FALLBACK`; that is not success and does not change the controller completion boundary.

When Herdr is available, the adapter reads `agent get` and `agent explain --json`, then reduces them to identity/freshness/liveness/cleanup fields only. A nonterminal observation without a live process is refused; a session bound to a dead nonterminal process is classified as an orphan and refused. PID start-time can be frozen to reject PID reuse. Source observation age is bounded by `max_observation_age_seconds`.

The host-neutral receipt contract is `../references/contracts/herdr-observer-receipt.schema.json`. `../references/examples/herdr-runtime-binding.example.json` is an abstract runtime binding example only; it carries no consumer live state.

`../tests/herdr_observer_selftest.py` covers fallback, fresh running/done observations, exact 40-hex Git subjects, worktree/session/process identity, stale/future observations, dead/orphan process state, cleanup residue, credentials/transcripts, and authority denial. Live Herdr execution remains `NOT_EXERCISED` until a consumer/runtime receipt proves it.

## Live-probe operational facts (2026-08-20, #466 attempt)

Observed on a real macOS host with herdr 0.8.0 while attempting the #466 live lifecycle leg; recorded so the next attempt does not rediscover them.

- `herdr_runtime_observer.py` and `collect_herdr_lifecycle.py` invoke bare `herdr agent get/explain` with no `--session` flag, so they only ever observe herdr's `default` session. A safe live probe must isolate through a scratch `$HOME` (not herdr's own `--session` flag) or it reads — and can disturb — the operator's real persistent session.
- Under the Claude Code Bash sandbox, `~/.config/herdr/herdr.sock` is outside the write allowlist; every socket call needs the sandbox disabled. The failure otherwise surfaces as `PermissionDenied` on the socket, not as a herdr defect.
- The manual `herdr pane report-agent --state <idle|working|blocked|unknown>` fallback structurally cannot produce `DONE_CANDIDATE`: its state enum has no terminal value and it carries no `cleanup_state`/`residue_count`. Only a real managed agent lifecycle can reach the terminal branch of `herdr-lifecycle-receipt.schema.json`.
- An unattended automated session may be unable to drive a nested managed agent at all (send-keys into its pane, spawning it under real credentials, and even read-only `pane process-info` can each be refused by host permission policy). In that case the live leg stays truthfully `NOT_EXERCISED`; a human-attended terminal is the unblocking lane.
