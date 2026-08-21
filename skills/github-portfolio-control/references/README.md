# References

Host-neutral contracts for the repository portfolio control plane. Nothing here
names a product, a provider account or a machine. Every schema is Draft 2020-12,
every object is closed at every level, every authority constant is pinned false,
and every positive example and refusal control travels inside the schema that
judges it — so a schema and its own evidence cannot be separated by an edit.

## Vocabulary

| File | Owns |
|---|---|
| [`controlled-vocabulary.md`](controlled-vocabulary.md) | the 24 ordered portfolio states, the 17 drift kinds, the durable and mutable subject lists, the 7 subagent roles, the 8 agent terminal states, the 3 routing aliases, the 4 evidence ceilings and the 9 checker refusal codes |
| [`coordinator-instruction.json`](coordinator-instruction.json) | the one non-optional coordinator instruction, preserved verbatim as data, and the three arrivals that have to agree before it can be paraphrased |

## Schemas

| File | Owns |
|---|---|
| [`schemas/portfolio-epoch.schema.json`](schemas/portfolio-epoch.schema.json) | one snapshot epoch, the content-addressed subjects a decision may be bound to, the mutable readbacks it may not, and the typed deltas that retire an epoch instead of overwriting it |
| [`schemas/subagent-join.schema.json`](schemas/subagent-join.schema.json) | the barrier between dispatching agents and acting on what they said: identity-bound results, a denominator that keeps its failures, model aliases that cannot be promoted to exercised identities, and nothing advancing before consolidation |
| [`schemas/one-shot-ci-epoch.schema.json`](schemas/one-shot-ci-epoch.schema.json) | one deliberate hosted run per candidate — draft-guarded, exact-head bound, capped at one ready toggle and zero pushes after it — and the semantic acceptance a green run never becomes |
| [`schemas/authority-composition.schema.json`](schemas/authority-composition.schema.json) | the six existing authorities this plane composes by route, exactly one owner each, and the copied body that would make a seventh |

## Fixtures

Both files are generated, never edited. `--emit-bundle` rebuilds the first from
the schemas' own `examples[0]`; `--bundle ... --out` rebuilds the second. The
checker's `--selftest` refuses a fixture that has drifted from either source, so
hand-editing one is caught on the next run rather than at the next reader.

| File | Owns |
|---|---|
| [`fixtures/example-bundle.json`](fixtures/example-bundle.json) | the four members assembled into one `ghpc/portfolio-bundle/v1`, derived from the committed examples |
| [`fixtures/example-bundle.verdict.json`](fixtures/example-bundle.verdict.json) | the byte-stable verdict that bundle produces, which `--check` compares a fresh run against |

## The checker

[`../scripts/compile_portfolio_control.py`](../scripts/compile_portfolio_control.py)
judges a bundle. Each member is validated against its own schema first; a member
that fails its own contract exits 64, because a bundle whose parts are unusable
is not a bundle that was refused. What the checker adds is the nine
contradictions no single member can see, each of which needs two documents
visible at once — a mixed subject, an advance past the join barrier, a delta
that starts at the wrong digest, a route to nothing, a paraphrased instruction, a
receipt from another head, a required role nobody dispatched, a reserved
shape-only identifier used as a receipt, and two exclusive writers over the same
bytes. It makes no network call, invents no timestamp, and decides nothing
semantic.

Exits: 0 green, 2 refused with a named `K` code, 64 the input is unusable, 70
`jsonschema` is absent.

## Evidence boundary

These contracts are repository bytes. Admitting them proves that the control
problem is written down in a form a machine can refuse. It does not prove that
any subagent ran, that any alias resolved to an available model, that any hosted
workflow executed, that any PR is mergeable, or that anything merged.
