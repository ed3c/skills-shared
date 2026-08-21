# AGENTS.md — dual-track code review operating contract

Read this file before changing `dual-track-code-review-loop`, before recording a
finding this method produced, and before using it to justify a change, a merge
or a claim about coverage.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md` and architecture
   routes;
2. this `AGENTS.md`;
3. this directory's [`README.md`](README.md);
4. [`SKILL.md`](SKILL.md);
5. [`references/contracts/controlled-vocabulary.md`](references/contracts/controlled-vocabulary.md)
   and
   [`references/contracts/public-private-capability.md`](references/contracts/public-private-capability.md);
6. [`references/schemas/`](references/schemas/), whichever documents the artifact
   being written;
7. [`references/source-disposition/refused-claims.json`](references/source-disposition/refused-claims.json)
   before repeating anything the admitted source said;
8. [`adapters/`](adapters/), whichever adapter the change touches, and its own
   `selftest.py` before editing landed adapter code;
9. [`references/prompts/README.md`](references/prompts/README.md) before
   authoring or dispatching a Session prompt for this Skill;
10. [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md)
    for the task and capability graph and for Local Handoff;
11. [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md)
    for independent review;
12. [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md)
    for branch and Stack publication;
13. the exact issue, pull request, commit and tree subject.

Chat history, a branch name, an issue title, a scanner's output and model
agreement are not evidence substitutes.

## Agent roles

### Builder

Owns exact-subject binding, source disposition, invariant inventory, the
deterministic and semantic passes, nomination, bounded proposals, change units,
receipts and the closure record.

The Builder may not confirm its own violation on retrieval alone, may not state
an edge set's completeness without stating its provenance, and may not certify
the global objective it was asked to reach.

### Independent Shadow

Read-only, on the same immutable subject, with no writer lease and no repair
authority. Independently attacks:

```text
source digest and exact candidate subject
complete changed-path denominator
private locator or private content leak
absolute coverage, zero-error and compliance overclaims
mechanism-to-property category errors in remedies
heuristic edge sets recorded as complete
retrieval promoted to basis
one observed stack promoted to universal practice
numbers carried without benchmark receipts
rights planes cleared by the wrong plane
positive, refuted, blocked and stale cases all present in the denominator
commit-role provenance
current-main drift and other open writers
```

Shadow outputs findings plus `ADMIT_FOR_DOWNSTREAM`, `BLOCK` or
`REPLAN_REQUIRED`. A same-context review may warn and can never satisfy this
role.

## Writer and mutation laws

- One active writer per mutation subject; path leases must be disjoint.
- One change unit implements one proposal. Unrelated cleanup is separate work.
- A read-only Shadow, a private projection, provider evidence and human
  admission are process edges. None of them is a git parent.
- Do not weaken a schema, a refusal control, a test or an evidence requirement
  to make a finding land.
- Domain modules and consumer bindings may only narrow this body: add evidence,
  strengthen a constraint, reduce authority. A module that relaxes a core law is
  a fork wearing an extension's name.

### Adapter-lease pattern

`adapters/` holds concrete implementations of this contract's capability
classes, and each landed adapter is its own path lease:

- one adapter directory is one lease; `tree-sitter/` and `sqlite-ledger/` are
  disjoint and may be worked concurrently, and a third adapter (`#547` SCIP,
  `#549` Buf, `#550` semantic-context) is a new disjoint lease, never an edit
  inside an existing adapter's directory;
- an adapter selftest is that adapter's own contract with `tests/run-all.sh`;
  changing an adapter's public behaviour without updating its `selftest.py` in
  the same change unit breaks that contract silently;
- a doc-convergence change (this file, `README.md`, `references/prompts/`) may
  describe a landed adapter's status and evidence ceiling and may never edit
  `adapters/**`, `references/schemas/**` or an adapter's fixtures — those are a
  disjoint lease from documentation convergence, held by whichever Worker is
  implementing that capability class;
- a live receipt (for example
  [`adapters/tree-sitter/receipts/live-ac62c87f.json`](adapters/tree-sitter/receipts/live-ac62c87f.json))
  is evidence for that one provider binary at that one commit; it is not
  transferable to a different adapter or a different provider version, and
  documentation may report it but never re-derive or restate its numbers from
  memory.

## Required change packet

```text
exact base commit and tree
exact head commit and tree
complete changed-path denominator
source packet digest and byte count
invariants touched
violation candidates, confirmed and refuted
remedy mechanism and target property
verification arrivals and their exit codes
lanes, including every lane nothing entered
refusal controls replayed, and the count that were refused
rollback subject
human-owned operations
```

A field with no answer is `ABSENT`. Do not infer one.

## Stop conditions

Stop when a violation has no deterministic fact behind it, when an edge set's
provenance cannot be stated, when a remedy's mechanism does not establish the
property it is aimed at, when a number arrives without its benchmark, when a
rights plane the chosen relationship needs is unadmitted, or when describing the
work would require a private locator or private content in a public artifact.
After three qualifying failures against the same invariant or acceptance target,
stop blind repair and open a fresh diagnosis on a new isolated worktree.

## Evidence ceiling

Preserve the states `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`,
`NOT_EXERCISED`, `SKIPPED_BY_POLICY`, `NOT_APPLICABLE` and
`HUMAN_ADMIT_REQUIRED`. This directory currently establishes contract and schema
evidence only. It does not establish a working adapter, an applied refactor, a
live consumer, an independent review, legal clearance, merge, release or
production, and no accumulation of contract evidence reaches any of them.

## Completion report

Report the exact base and head commit and tree, the complete changed-path
denominator, the source packet digest, every disposition and its control, which
refusal controls were replayed and how many were refused, which planted defects
turned the checks red, every check command with its exit code, every lane
including the empty ones, failed attempts, the rollback subject, and the
operations that remain human-owned.
