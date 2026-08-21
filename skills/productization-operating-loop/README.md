# `productization-operating-loop`

Host-neutral vocabulary and machine contract for taking an opportunity from
source discovery through differentiated design, feasibility, monetization and
bounded implementation, by composing methods that already exist rather than
restating them.

Status: `CORE_CONTRACT_FROZEN / METHOD_NOT_IMPLEMENTED`.

This directory currently holds a contract and nothing else. There is no
procedural body here yet, no compiler, no evals, no prompts and no consumer
binding; those are separately owned atoms and each will arrive with its own
receipt. A contract is a shape that later work must fit. It is not evidence
that the later work exists.

## Read order

1. [`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md)
   — the twelve lanes, the ten lane states, the fifteen program states, and the
   authority laws. Read this first; every other file assumes its words.
2. [`references/core/evidence-ladder.md`](references/core/evidence-ladder.md)
   — the ten rungs, the receipt kind bound to each, and the substitution law.
3. [`references/productization-program.schema.json`](references/productization-program.schema.json)
   — the machine contract, with its positive example and its eleven refusal
   controls inline.
4. [`references/composition-manifest.json`](references/composition-manifest.json)
   — the ten composed methods, each by content digest and declared interface.
5. [`references/core/source-proposal-audit.md`](references/core/source-proposal-audit.md)
   — what the preparation branch contained, and what this freeze admitted and
   refused from it.
6. The four Stage-1 lane contracts —
   [`references/market/market-lane.schema.json`](references/market/market-lane.schema.json),
   [`references/user/user-lane.schema.json`](references/user/user-lane.schema.json),
   [`references/commercial/commercial-lane.schema.json`](references/commercial/commercial-lane.schema.json),
   [`references/policy/policy-lane.schema.json`](references/policy/policy-lane.schema.json)
   — each beside its own vocabulary file.
7. The three Stage-2 session contracts —
   [`references/session/closure-matrix.schema.json`](references/session/closure-matrix.schema.json),
   [`references/session/session-dag.schema.json`](references/session/session-dag.schema.json),
   [`references/session/outcome-foldback-request.schema.json`](references/session/outcome-foldback-request.schema.json)
   — what [`scripts/compile_pol_composition.py`](scripts/compile_pol_composition.py)
   emits and refuses against: byte-stable canonical JSON, `--check`, and named
   K-code refusals with exit 2, never a silent downgrade.

## What is here

```text
references/
├── core/
│   ├── controlled-vocabulary.md    lanes, lane states, program states, laws
│   ├── evidence-ladder.md          the ten rungs and the substitution law
│   └── source-proposal-audit.md    what the source proposal contributed
├── market/                         market-lane.schema.json + vocabulary
├── user/                           user-lane.schema.json + vocabulary
├── commercial/                     commercial-lane.schema.json + vocabulary
├── policy/                         policy-lane.schema.json + vocabulary
├── session/                        closure-matrix, session-dag,
│                                   outcome-foldback-request (Stage-2 outputs)
├── productization-program.schema.json
│                                   pol/productization-program/v1
└── composition-manifest.json       pol/composition-manifest/v1
scripts/
└── compile_pol_composition.py      deterministic Stage-2 composition compiler
tests/
├── selftest.py                     tree-derived suite: every schema, every
│                                   control, per-control knockout
└── run-all.sh                      CI entrypoint, routed by skill-suites.yml
```

## What the contract makes structurally impossible

Three shapes, each enforced by a keyword rather than by prose:

```text
lane collapse        twelve lanes required, no thirteenth admitted, so a lane
                     can be neither dropped nor fused with its neighbour
rung skipping        each rung above the first pins its predecessor to REACHED
rung promotion       each rung admits only its own receipt kind, so a command
                     exit cannot be filed as evidence that somebody paid
```

Two more are narrower than they sound, and the schema says so where it enforces
them: a method reference is closed and its interface field is capped, which
refuses a pasted body but cannot detect one paraphrased into four hundred
characters; and the Human-owned lanes carry a state vocabulary with no PASS in
it, which refuses the widening and not the intent behind it.

## Evidence ceiling

`INTERFACE_LOCK_ONLY`. Freezing this contract proves that a shape is fixed and
that eleven named refusals are refused by the keywords they cite. It does not
prove that the method exists, that an arena is attractive, that a user would
switch, that anyone would pay, that a rule permits anything, that any runtime
executed, or that any of this may be merged or released. Those lanes are
reported by this contract; they are not cleared by it.
