# Migration/copy semantic-loss canary

This suite owns the two prerequisites issue #411's live Shadow canary was
blocked on: a case graph bound to an exact committed implementation subject,
and a migration/copy task fixture whose planted decision-branch removal a
deterministic oracle can actually detect.

The bound subject is main commit `a9db0bd9` — the wave-1 Local Handoff landing.
The graph itself is [`references/case-graph-local-handoff-wave1.json`](../../references/case-graph-local-handoff-wave1.json).

`case_graph_evidence.py` binds claims to bytes:

- every path pinned in `subject.manifest` is re-read with `git cat-file` at
  `subject.revision`, and must reproduce its recorded blob name and sha256;
- the manifest must recompute to `subject.digest`;
- every `readback_assertions` pointer must resolve inside those committed bytes
  and equal the recorded value, and may not reference an unpinned path.

Bytes come from the commit, never the working tree, so unrelated churn in a
sibling worker's lease can neither redden nor green this suite.

`migration_canary.py` runs two oracles over one migration pair:

- `compat` — the legacy caller surface only (`PASS`/`FAIL`/`ABSENT`, the
  human-admit override, the unknown-input rejection);
- `parity` — a differential over the source's whole declared input domain,
  enumerated from the source module rather than from the oracle's own copy.

The controls prove:

- deleting the `SKIPPED_BY_POLICY` row from a throwaway copy of the target
  leaves the interface intact, keeps `compat` green, and turns `parity` red
  naming the input and both outputs — a compatibility-only PASS cannot close a
  semantic-copy obligation;
- a drifted content digest in a copy of the graph is refused;
- a copy of the graph claiming the #464 Shadow lane executed is refused,
  because the committed receipt says `NOT_EXERCISED`.

A green suite proves fixture-level detection and committed-byte binding. It
does not exercise the live #411 Shadow canary: `CASE-005` stays
`HUMAN_ADMIT_REQUIRED`, its receipt is `ABSENT`, and no independent
Builder/Shadow identity pair is admitted at this subject.
