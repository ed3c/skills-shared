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

## Carrier/runtime contract mismatch (2026-08-21, #466 attempt 2)

Host permission is not the innermost blocker. Herdr 0.8.0's own bundled API schema (`herdr api schema --output <path>`) and its real `agent explain --json` output together show that the agent surface publishes none of the facts this observer requires:

```text
AgentInfo (published)   agent, agent_session, agent_status, cwd, display_agent, focused,
                        foreground_cwd, interactive_ready, launch_pending, name, pane_id,
                        revision, screen_detection_skipped, state_change_seq, state_labels,
                        tab_id, terminal_id, terminal_title, terminal_title_stripped, title,
                        tokens, workspace_id
success envelope        {id, result}
absent everywhere       observed_at_unix/updated_at_unix/last_seen_at_unix, process_alive,
                        process_started_at_unix, cleanup_state, residue_count
                        (whole-schema occurrence count 0 each; `_at` appears 0 times)
absent from AgentInfo   process_id/pid — `pid` does exist in herdr 0.8.0, but only on
                        PaneProcessInfoProcess (required [pid, name]), which this observer
                        never reads: it calls `agent get` and `agent explain` only
```

Two literal corrections that do not move the blocker: `pid` is not absent from the schema, only from the observer's reachable surface; and `AgentInfo` declares no `additionalProperties` keyword, so the list above is the property set herdr 0.8.0 publishes, not a formally closed set.

Consequence: `reduce_observation` fails at `_observed_at` (`Herdr source observation timestamp must be a positive integer`) on **every** sample, however healthy the managed agent is, and the `LIVE_HERDR_LIFECYCLE_OBSERVED_CANDIDATE` branch of `../references/contracts/herdr-lifecycle-receipt.schema.json` additionally requires `process_id` and `process_started_at_unix`, which no herdr 0.8.0 response can supply. `AgentStatus` does carry `done`, so the terminal *state* exists; the terminal *receipt* does not.

Signal → action: before spending another attempt on host permission for a managed-agent lifecycle, run `herdr api schema` and diff its agent surface against the observer's required field names. If the facts are absent, the correct outcome is a blocked receipt naming the missing fields, not a permission escalation. Unblocking lane is upstream herdr publishing those facts, or an admitted renegotiation of the observer/lifecycle contract against a real herdr capability set.

## The blocked state is now schema-representable and gate-verified (2026-08-22, #466 contract repair)

A blocked attempt had nowhere to land. The receipt contract offered two `oneOf` branches — fallback and live candidate — and both demand at least one sample, so the receipt landed by PR #516 named a schema it failed with 12 Draft-2020-12 errors. Nothing noticed, because nothing in the repository read `data/handoff/` at all.

- The contract has a third branch: `lifecycle_state: BLOCKED_NO_SAMPLE`, `sample_count: 0`, `sample_digests: []`, `evidence_ceiling: NO_HERDR_LIFECYCLE_SAMPLE`, `blockers` required. Zero samples is now expressible; an empty receipt with no stated blockers still is not.
- Two planes, two vocabularies, one mapping. The receipt plane speaks `lifecycle_state`. The queue plane speaks the repository evidence vocabulary, and `scripts/assert_local_handoff_queue.py` hard-requires `PASS ∈ required_states` for a live lane plus `exit.required_verdict == "PASS"`, while `references/local-handoff-queue.schema.json` sets `receipt.additionalProperties: false`. **Rewriting the queue's `required_states`/`required_verdict` into `lifecycle_state` values turns that gate red with three FAILs** — verified by mutating a copy and running the gate. The mapping therefore lives where there is room for it: `lifecycle_state`'s own `description`, plus the queue's `forbidden_promotions` entry `blocked_no_sample_or_unavailable_fallback_receipt_to_pass_verdict`.
- Signal → action: when a lane is blocked at the provider, do not leave its receipt un-gated. `../tests/herdr_lifecycle_selftest.py` now resolves the ACTIVE queue item, instance-validates the receipt it names against the contract it names, checks that contract is this one, and refuses a receipt whose `lifecycle_state` is the live value. A committed receipt can no longer drift from its declared schema, and a blocked receipt cannot be laundered into the queue-plane `PASS`.
- Signal → action: a receipt binds to a frozen plan by `plan.sha256`. When you touch either, re-check that the receipt's identity fields still equal the plan manifest's — the selftest asserts it, because a receipt that quietly describes a different subject than the plan it names is the failure this contract exists to prevent.
- Provider re-probe of 2026-08-22 (third independent arrival, at repository commit `674cfe14`): `herdr api schema --json` is 251527 bytes, sha256 `88ff414aa996e390c2db05a37b95d28dbe4e81b98329f6ed7f7a2cc5c6ebf51a`, still zero occurrences of every observation, liveness, start-time and cleanup token. `AgentStatus` remains `[idle, working, blocked, done, unknown]`. The lane stays `BLOCKED_ON_PROVIDER`.
