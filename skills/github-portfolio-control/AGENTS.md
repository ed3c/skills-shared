# AGENTS.md — portfolio control operating contract

Read this before changing anything under `github-portfolio-control`, before
recording a portfolio epoch, join receipt, CI epoch or composition this plane
judges, and before citing any of them to justify an advance, a merge or a claim
about coverage.

## Mandatory read order

1. repository root `AGENTS.md`, `README.md`, `CONTEXT.md` and the architecture
   routes;
2. this `AGENTS.md`;
3. this directory's [`README.md`](README.md);
4. [`references/controlled-vocabulary.md`](references/controlled-vocabulary.md)
   — the closed word lists; every schema below assumes them;
5. [`references/coordinator-instruction.json`](references/coordinator-instruction.json)
   before writing, dispatching or quoting a coordinator prompt for this plane;
6. whichever contract documents the artifact being written —
   [`references/schemas/portfolio-epoch.schema.json`](references/schemas/portfolio-epoch.schema.json),
   [`references/schemas/subagent-join.schema.json`](references/schemas/subagent-join.schema.json),
   [`references/schemas/one-shot-ci-epoch.schema.json`](references/schemas/one-shot-ci-epoch.schema.json),
   [`references/schemas/authority-composition.schema.json`](references/schemas/authority-composition.schema.json);
7. [`references/README.md`](references/README.md) for the full routing table and
   the generated fixtures;
8. [`scripts/compile_portfolio_control.py`](scripts/compile_portfolio_control.py)
   — read its refusal codes before assembling a bundle, not after it is refused;
9. the six composed owners named at the end of [`README.md`](README.md);
10. the exact Issue, pull request, commit and tree subject being worked on.

Chat history, a branch name, an Issue title, a model's self-description and
agreement between two agents are not evidence substitutes.

## Before you edit

State, in the change itself:

- the exact commit and tree the change is bound to;
- which of the five laws the change touches, and whether it tightens or loosens
  it — loosening requires a Human Admit, not a rationale;
- every denominator the change moves. The suite counts schemas, positives,
  controls and knockouts from the bytes, and `references/README.md`,
  `README.md` and this file all state numbers. A schema added without its three
  routing rows turns the suite red, which is the intended outcome: an unrouted
  contract is one nobody reads.

## Laws this directory may not weaken

1. **One subject per epoch.** Every control decision binds to an exact commit
   and tree. A branch name, a PR mergeability verdict, an Issue title, a queue
   position and model prose are mutable readbacks: recordable, never durable,
   never the subject of a decision. Movement retires an epoch through a typed
   delta naming at least one invalidated state — never by overwriting it.
2. **Dispatch is not completion.** No Issue, PR, path lease, epoch, merge or
   closure advances until every requested agent is terminal, identity-bound,
   schema-valid and consolidated. Cancelled, blocked, stale, failed and
   unavailable agents stay in the denominator. A missing required result is
   `JOIN_INCOMPLETE`, never implicit agreement.
3. **One deliberate hosted run per candidate.** Converge locally, freeze the
   candidate and its changed-path denominator, publish as Draft, mark ready
   exactly once, read back run, jobs, non-empty steps, artifacts and the exact
   tested head. A failure returns to a new local candidate epoch. Only a proven
   infrastructure flake earns the same head twice. Hosted success is execution
   evidence and nothing else.
4. **Compose, never duplicate.** The six authorities in the composition schema
   are routed, not restated. A copied canonical body is refused; a second
   authority of an existing kind is refused; redefining one locally is refused.
5. **The coordinator instruction is data.** It is pinned as a `const`, stored as
   bytes and routed by `const`. Paraphrasing it is a refusal, not a style
   choice — the half that gets dropped is the half that makes the work joinable.

Every artifact here pins `merge`, `release`, `promotion`, `provider_execution`
and `production` to `false`. Human Admit owns all five.

## Roles

**Author.** Owns the contracts, the checker, the fixtures and the suite. May
tighten a law, add a refusal control, or add a contract with its routing rows.
May not add a field that carries a private reasoning transcript, may not admit a
mutable subject into an evidence position, and may not widen an authority
constant.

**Independent verifier.** Runs the suite at the exact candidate head and reads
the printed denominators against the tree. A verifier who reads the summary line
without the counts has verified the sentence, not the contracts.

**Human Admit.** Owns merge, release, promotion, provider and data-egress
admission, adding a composed authority kind, and closing an Issue against
unresolved acceptance.

## Verification

```sh
bash skills/github-portfolio-control/tests/run-all.sh
```

Exit 0 is the only pass. The suite prints its denominators; a change that moves
one and does not move the prose that states it is the failure this repository
has already paid for twice.
