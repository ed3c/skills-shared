# AGENTS.md — Dual-Track Code Review Loop traceability

Owner: `ed3c/skills-shared#517` (parent). This convergence: `#526`.

## Mandatory read order

For any Dual-Track Code Review Loop task, read in order:

1. repository root `AGENTS.md`;
2. root `README.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
3. `docs/INDEX.md`, document routing, State Machines, traceability;
4. this file;
5. [`README.md`](README.md);
6. [`implementation-preflight.json`](implementation-preflight.json) — historical
   C0 admission receipt, superseded by the committed suite for anything the
   committed suite also covers;
7. [`../../../skills/dual-track-code-review-loop/AGENTS.md`](../../../skills/dual-track-code-review-loop/AGENTS.md),
   [`README.md`](../../../skills/dual-track-code-review-loop/README.md) and
   [`SKILL.md`](../../../skills/dual-track-code-review-loop/SKILL.md) — the
   Skill body this directory only indexes and never duplicates;
8. [`SESSION_PROMPTS.md`](SESSION_PROMPTS.md) — routes to the substantive
   prompts, does not repeat them;
9. [`ISSUE_DAG.json`](ISSUE_DAG.json) and
   [`MOLECULAR_STACK_INDEX.md`](MOLECULAR_STACK_INDEX.md) for current lane
   status;
10. [`LOCAL_HANDOFF_EXECUTION_QUEUE.json`](LOCAL_HANDOFF_EXECUTION_QUEUE.json)
    for what remains before `#528` Local Handoff;
11. the exact owning Issue, parent/sibling Issue, PR base/head and evidence
    subject.

Never reconstruct an exact subject, dependency, lease, or evidence claim from
prior chat. This directory's job is routing and traceability only; it is not a
second copy of the Skill's contract, procedure or prompt bodies.

## Authority boundary

This directory owns the navigation surface: read order, Issue/PR DAG, Molecular
Stack index and prompt routing for `dual-track-code-review-loop`. It does not
own the Skill's contract (`SKILL.md`), its schemas, its adapters, or any
consumer repository's state, private source URL, model/provider Session,
GitHub merge, or legal/rights admission.

Aggregate indexes — root `docs/INDEX.md`, `registry.json`, and other
repositories' own aggregate indexes — are never edited from here. This
directory is a leaf under `docs/traceability/`, not an aggregator.

## Worker laws

- one active writer per mutation subject; path leases must be disjoint from
  `skills/dual-track-code-review-loop/adapters/**` and
  `skills/dual-track-code-review-loop/references/schemas/**`, which are a
  separate implementation lease this directory never touches;
- a doc-convergence change here may describe a landed adapter's or an open
  issue's status and evidence ceiling, and may never promote a lane that has
  not itself produced that evidence — `#522` (synthesis compiler), `#547`/`#549`
  (provider adapters), `#550` (semantic adapter) and `#525` (independent
  Shadow) each close only on their own issue's receipt;
- process/external-evidence dependencies (a private projection, a provider
  receipt, a Shadow pass, Human admission) never create Git ancestry;
- start dependency means a readable interface exists; completion dependency
  means the prerequisite's own evidence lane has produced its receipt;
- a private intent, redacted promotion request, or CodexDoc/Google Doc
  projection digest is never GitHub task completion, and GitHub technical
  state is never private strategic truth;
- public tracked files here know only opaque binding IDs and resolver-variable
  names for any private capability resolver; they never carry a private
  document, Sheet, folder or source URL.

## Evidence vocabulary

Use repository-standard `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`,
`NOT_EXERCISED`, `BLOCKED_ON_PROVIDER`, `IN_FLIGHT`, `SKIPPED_BY_POLICY`,
`HUMAN_ADMIT_REQUIRED`. `IN_FLIGHT` names a sibling Worker's concurrently open
issue on the same head; it is not evidence of anything landing.

## Shadow L3 blocks

Block promotion or dispatch on any of:

```text
private locator or private content in a public tracked file
adapter/schema edit performed from a documentation-convergence lease
a sibling open issue's lane reported as landed because this file mentions it
a landed adapter's receipt restated with different numbers than its own file
a projection digest promoted to GitHub task completion
GitHub technical state promoted to private strategic truth
aggregate index (docs/INDEX.md, registry.json) edited from a leaf directory
stale directory map or evidence ceiling left uncorrected after a landing
```

## Completion packet

Every Worker returns: exact input subjects, issue/branch/base/head, complete
changed-path denominator, which stale items were repaired and how they were
verified against the tree, evidence ceiling per lane, failed/blocked/stale
attempts, cleanup, rollback subject, next owner, and all remaining
Human-owned operations.
