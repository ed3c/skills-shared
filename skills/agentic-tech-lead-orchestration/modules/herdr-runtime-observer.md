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

- `herdr_runtime_observer.py` and `collect_herdr_lifecycle.py` invoke bare `herdr agent get/explain` with no `--session` flag, so they only ever observe herdr's `default` session. **Correction (2026-08-22 read-only probe, herdr 0.8.0): isolation does NOT require a scratch `$HOME`.** `herdr --session <name> status` reports `socket: ~/.config/herdr/sessions/<name>/herdr.sock`, distinct from the `default` `~/.config/herdr/herdr.sock`; `herdr session list` prints a per-session directory and socket column. Threading `--session <name>` through the observer argv is the admitted isolation lane, and `herdr --skill` line 194 names it ("Use named test sessions for experiments that need an isolated server"). The earlier "scratch `$HOME` is mandatory, not herdr's own `--session` flag" claim is FALSIFIED and must not be reused.
- Under the Claude Code Bash sandbox, `~/.config/herdr/herdr.sock` is outside the write allowlist; every socket call needs the sandbox disabled. The failure otherwise surfaces as `PermissionDenied` on the socket, not as a herdr defect.
- The manual `herdr pane report-agent --state <idle|working|blocked|unknown>` fallback structurally cannot produce `DONE_CANDIDATE`: its state enum has no terminal value and it carries no `cleanup_state`/`residue_count`. Only a real managed agent lifecycle can reach the terminal branch of `herdr-lifecycle-receipt.schema.json`.
- An unattended automated session may be unable to drive a nested managed agent at all (send-keys into its pane, spawning it under real credentials, and even read-only `pane process-info` can each be refused by host permission policy). In that case the live leg stays truthfully `NOT_EXERCISED`; a human-attended terminal is the unblocking lane.

## Carrier/runtime contract mismatch (2026-08-21, #466 attempt 2)

Host permission is not the innermost blocker. Herdr 0.8.0's own bundled API schema (`herdr api schema --output <path>`) and its real `agent explain --json` output together show that the agent surface publishes none of the facts this observer requires:

```text
AgentInfo (closed set)  agent, agent_session, agent_status, cwd, display_agent, focused,
                        foreground_cwd, interactive_ready, launch_pending, name, pane_id,
                        revision, screen_detection_skipped, state_change_seq, state_labels,
                        tab_id, terminal_id, terminal_title, terminal_title_stripped, title,
                        tokens, workspace_id
success envelope        {id, result}
absent from AgentInfo   observed_at_unix/updated_at_unix/last_seen_at_unix, process_id/pid,
                        process_alive, process_started_at_unix, cleanup_state, residue_count
published elsewhere     PaneProcessInfo, via API method `pane.process_info` / CLI
                        `herdr pane process-info --pane <ID>`: pane_id, tty, shell_pid,
                        foreground_process_group_id,
                        foreground_processes[]{pid, name, argv, argv0, cmdline, cwd}.
                        PID is therefore NOT absent from herdr 0.8.0 — only from AgentInfo.
ordering anchor         AgentInfo.state_change_seq (uint64) and AgentInfo.revision (uint64);
                        note `herdr pane report-agent --seq <N>` lets a manual reporter set
                        the seq, so monotonicity is trustworthy only for herdr-managed agents
                        (bind agent_session.source to reject manual reporters).
absent from all of 0.8.0 any wall-clock observation timestamp, process_alive, process start
                        time, cleanup_state, residue_count
```

Consequence: `reduce_observation` fails at `_observed_at` (`Herdr source observation timestamp must be a positive integer`) on **every** sample, however healthy the managed agent is, and the `LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE` branch of `../references/contracts/herdr-lifecycle-receipt.schema.json` additionally requires `process_id` and `process_started_at_unix`. `process_id` IS obtainable (`pane.process_info`); `process_started_at_unix` is not, and must be carried as a typed OS_AUXILIARY substitution (`ps -o lstart= -p <pid>`) rather than treated as an upstream blocker. `AgentStatus` does carry `done`, so the terminal *state* exists; the terminal *receipt* does not.

Signal → action: before spending another attempt on host permission, run `herdr api schema --json` and diff its **whole** surface — not only `AgentInfo` — against the observer's required field names; `pane.process_info` and `--session` were both missed by the 2026-08-21 pass. Only facts absent from every published surface justify a blocked receipt, and each such fact must be carried as an explicitly typed substitution (`observation_time_source`, `process_facts_source`, `cleanup_source`) rather than silently invented in a fixture.

## Amended contract (2026-08-22, #466)

The frozen surface snapshot lives at `../references/contracts/herdr-agent-surface.observed.json` (captured read-only from `herdr api schema --json`, digest recorded in its `provenance` block). `../tests/herdr_surface_conformance_selftest.py` is the falsifier: it fails whenever the observer or a fixture names a herdr field that is neither in that snapshot nor a key of its typed-substitution table. That test is STATIC evidence — it proves the contract matches a captured schema, never that a live socket returns those fields.

Also observed 2026-08-22 and worth not rediscovering: the herdr CLI **exits non-zero** on failure and writes its error envelope `{id, error:{code,message}}` to **stderr** (`herdr agent get <missing>` → exit 1, `code: server_not_running`). `_run` therefore already fails closed on the returncode; the additional stdout error-envelope refusal in `herdr_runtime_observer._run` is defence in depth against a shape that has not been observed, not a repair of an observed exit-0 failure.
