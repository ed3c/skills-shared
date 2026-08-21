# `github-portfolio-control`

Host-neutral contracts and one deterministic checker for the join protocol that
sits above per-task work: reconciling Issues, pull requests, local
implementation, subagent results, hosted CI and closure against **one** exact
repository subject, without becoming a second Tech Lead, Shadow, Git Town,
delivery, closure or bootstrap authority.

Status: `CORE_CONTRACT_FROZEN / METHOD_NOT_IMPLEMENTED`.

This directory holds a contract plane and its verification, and nothing else.
There is no procedural body here yet, no provider caller, no workflow, no
prompts and no consumer binding; each of those is a separately owned atom and
each will arrive with its own receipt. A contract is a shape that later work
must fit. It is not evidence that the later work exists.

## The problem this refuses

Per-task contracts in this repository are strong. What was missing is one
portfolio-level join, and its absence produces failures that every individual
gate reports as green:

- **snapshot epoch drift** — an Issue read on Monday and a PR read on Tuesday,
  combined into one picture that never existed at either moment;
- **the missing join barrier** — one useful agent result promoted while other
  requested agents are still running, or have already failed quietly;
- **runtime and model laundering** — an installed tool, a generated prompt or a
  routing alias reported as an exercised environment or an exact identity;
- **CI amplification** — repeated pushes, draft/ready toggles and blind reruns
  spending hosted minutes before local convergence;
- **duplication** — a controller that carries its own copy of an authority that
  already has an owner, and drifts from it invisibly.

Five laws answer those, and each one is a keyword something has to fail on
rather than a paragraph somebody has to remember.

## Read order

1. [`references/controlled-vocabulary.md`](references/controlled-vocabulary.md)
   — the 24 ordered portfolio states, the 17 drift kinds, the durable and
   mutable subject lists, the 7 subagent roles, the 8 agent terminal states, the
   3 routing aliases, the 4 evidence ceilings and the 9 checker refusal codes.
   Read this first; every other file assumes its words.
2. [`references/coordinator-instruction.json`](references/coordinator-instruction.json)
   — the one non-optional coordinator instruction, preserved verbatim as data
   rather than described, with the three arrivals that must agree.
3. [`references/schemas/portfolio-epoch.schema.json`](references/schemas/portfolio-epoch.schema.json)
   — **law 1, epoch subject binding.** Every decision is bound to an exact
   commit and tree; a branch name, a mergeability verdict and model prose are
   recorded as mutable readbacks and can never be marked durable; movement
   retires an epoch through a typed delta that must name at least one
   invalidated state.
4. [`references/schemas/subagent-join.schema.json`](references/schemas/subagent-join.schema.json)
   — **law 2, the subagent barrier.** Dispatch is not completion: one
   non-terminal agent pins the join to `JOIN_INCOMPLETE`, nothing advances
   before `FINDINGS_CONSOLIDATED`, cancelled and failed agents stay in the
   denominator, and an absent alias cannot carry an exact model.
5. [`references/schemas/one-shot-ci-epoch.schema.json`](references/schemas/one-shot-ci-epoch.schema.json)
   — **law 3, one-shot CI frugality.** One deliberate hosted run per candidate:
   draft-guarded, frozen denominator, at most one ready toggle, zero pushes
   after it, no empty or skipped run promoted to a pass, no blind rerun, and a
   green run that never becomes semantic acceptance.
6. [`references/schemas/authority-composition.schema.json`](references/schemas/authority-composition.schema.json)
   — **law 4, composition not duplication.** Six existing authorities, exactly
   one owner each, routed rather than restated, with a copied canonical body
   refused outright.
7. [`references/README.md`](references/README.md) — the routing table for every
   file above plus the two generated fixtures.
8. [`AGENTS.md`](AGENTS.md) — what an agent must read and bind before changing
   anything here.

**Law 5** is not a schema of its own: the coordinator instruction is pinned as a
`const` inside the join schema, stored as data in
`references/coordinator-instruction.json`, and routed by `const` from the
composition schema, so a paraphrase has to survive three independent arrivals.

## What is here

```text
references/
├── controlled-vocabulary.md              the closed word lists
├── coordinator-instruction.json          the pinned sentence, as data
├── schemas/                              four contracts, closed at every depth
└── fixtures/                             two generated files, never hand-edited
scripts/
└── compile_portfolio_control.py          the bundle checker
tests/
├── run-all.sh                            one entrypoint, three arrivals
└── selftest.py                           the contracts executed as gates
```

## Verification

```sh
bash skills/github-portfolio-control/tests/run-all.sh
```

Three arrivals, none of which can be satisfied by the other two:

- `tests/selftest.py` executes the committed schemas. It counts the schemas,
  positives, controls and knockouts from the bytes at run time, requires every
  refusal control to be refused, then deletes exactly the one keyword each
  control names and requires the instance to become valid — a control that
  survives its own knockout is not discriminating the guard it claims. It also
  checks that every schema is routed from all three documents, that the pinned
  instruction agrees across its arrivals, and finally plants a defect on a
  throwaway copy and requires the suite to go red.
- `scripts/compile_portfolio_control.py --selftest` plants one defect per
  refusal code and requires each to fire as itself, asserts the derived bundle
  still equals the committed fixture, asserts the verdict is byte-stable, and
  reads its own import statements to assert that none names a network module.
- The same checker run as a caller would run it, `--bundle` against `--check`.

## Evidence boundary

Admitting this plane proves that the control problem is written down in a form a
machine refuses, and that the refusals discriminate. It does not prove that any
subagent was dispatched or terminated, that `FABLE_5`, `OPUS_5` or `SONNET_5`
resolved to an available model, that any hosted workflow executed, that any
pull request is mergeable, or that anything merged. Human Admit still owns
merge, release, promotion, provider execution and production.

## What this does not own

| Question | Owner |
|---|---|
| task and capability DAG, Issue closure, Local Handoff | [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md) |
| read-only adversarial review and its deltas | [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md) |
| trusted provider snapshot and exact-head hosted evidence | [`../github-delivery-loop/SKILL.md`](../github-delivery-loop/SKILL.md) |
| real Git ancestry, worktrees and path leases | [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md) |
| thin consumer binding and new-repository bootstrap | [`../shared-skills-infra/SKILL.md`](../shared-skills-infra/SKILL.md) |
| post-landing Issue disposition and residual ownership | [`../agentic-tech-lead-orchestration/references/ISSUE_CLOSURE_CONTRACT.md`](../agentic-tech-lead-orchestration/references/ISSUE_CLOSURE_CONTRACT.md) |

Those six are what the composition schema declares by route. The checker
resolves each route against the tree and refuses an absent one, because a route
to a file that does not exist reads exactly like a route to one that does.
