# AGENTS.md — product reverse-engineering operating contract

Read this file before changing `product-reverse-engineering-loop` or using it to
reverse-engineer a product.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md`, `ARCHITECTURE.md`;
2. this `AGENTS.md`;
3. this directory's [`README.md`](README.md);
4. [`SKILL.md`](SKILL.md);
5. [`references/evidence-vocabulary.md`](references/evidence-vocabulary.md) — the
   four vocabularies decide what every later artifact is allowed to say;
6. the schema for the artifact being written, in
   [`references/README.md`](references/README.md);
7. [`references/prompt-catalogue.md`](references/prompt-catalogue.md) when a
   prompt surface is being run or changed;
8. only the module whose trigger matches, via [`modules/README.md`](modules/README.md);
9. [`scripts/README.md`](scripts/README.md), [`tests/README.md`](tests/README.md),
   and the exact issue/PR subject.

Chat history, a branch name, an issue title and a Markdown claim are not evidence
substitutes. Neither is a plan somebody remembers: if it is not a digest-bound
artifact, it does not exist.

## Writer and authority rules

- One Worker owns one branch, one worktree and one disjoint path lease.
- Compiled projections have exactly one producer. Editing
  `example-dossier.json`, `example-closure-matrix.json` or `example-handoff.json`
  by hand is refused by `--check`; regenerate them from their input.
- Grades come from the kind table alone. Nobody argues a grade upward.
- A requirement closes only through an oracle in its own lane. A green
  deterministic suite is never user, paid or market evidence.
- Usage, licensing and commercial rights are `HUMAN_ADMIT_REQUIRED`. No script,
  no module and no prompt admits one.
- Prompt surfaces reserve merge, permission, secret and production authority.
  They never grant it, and they never ask for private reasoning.
- Consumer branches, issues, remotes and machine paths live only inside a typed
  consumer binding. The shared body carries none.

## Required change packet

Before implementation, bind:

```text
exact subject artifact and digest
state-machine transition being attempted
signal set and its compatibility binding
lanes this run may speak in, and who owns the rest
refusal codes in force
path lease and convergence owner
stop-loss condition and action
remaining evidence owners
rollback subject
Human Admit boundary
```

A field with no answer is `ABSENT`. Do not infer one.

## Stop conditions

Stop and hand the item back when a needed slot is `ABSENT` with no further signal
available, when the only oracle speaks another lane, when a subject digest no
longer matches its artifact, when an unadmitted right would be exercised, when
the same invariant has failed three times, or when the next action would need
merge, permission, secret or production authority.

## Completion report

Report the state reached, the artifacts written with their digests, the commands
run and their verdicts, every refusal that fired, every closure row that is still
`OPEN_WITH_ORACLE` or blocked with its owner, and every lane that remains
`NOT_EXERCISED`, `ABSENT` or `HUMAN_ADMIT_REQUIRED`. A report that omits the open
rows is a report that its own handoff contradicts.
