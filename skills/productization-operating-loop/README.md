# `productization-operating-loop`

Host-neutral vocabulary and machine contract for taking an opportunity from
source discovery through differentiated design, feasibility, monetization and
bounded implementation, by composing methods that already exist rather than
restating them.

Status: `CORE_CONTRACT_FROZEN / COMPILER_LANDED / ROUTING_PROMPT_TRACE_LANDED
/ EVIDENCE_PLANE_LANDED`.

The twelve-lane contract is frozen and replayed by
[`tests/run-all.sh`](tests/run-all.sh); the deterministic composer
([`scripts/compile_pol_composition.py`](scripts/compile_pol_composition.py))
is landed and replays its own fixtures via `--selftest`; this convergence
(`#429`) adds the zero-context read route, the pasteable per-stage prompts and
the CodexDoc/GitHub trace law as prose. The independent evidence/Shadow
plane (`#428`, [`tests/evidence_plane.py`](tests/evidence_plane.py)) is an
ancestor of this tree and replayed by the same suite entry point; the run
this tree produces is quoted in [`AGENTS.md`](AGENTS.md)'s Ancestry note. No
market, user, mechanism, session, payment or release lane is cleared by any
of this — a contract, a compiler and a prompt set are each a shape later
evidence must fit, not evidence that the later work happened.

## Read order

1. [`AGENTS.md`](AGENTS.md) — read order authority, agent roles, writer/lease
   law, the CodexDoc/GitHub trace law, the Ancestry note, stop conditions and
   the completion report.
2. [`SKILL.md`](SKILL.md) — the portable state machine, the twelve stages, the
   hard laws and the evidence ceiling.
3. [`references/core/controlled-vocabulary.md`](references/core/controlled-vocabulary.md)
   — the twelve lanes, the ten lane states, the fifteen program states, and the
   authority laws. Read this first of the references/ files; every other file
   assumes its words.
4. [`references/core/evidence-ladder.md`](references/core/evidence-ladder.md)
   — the ten rungs, the receipt kind bound to each, and the substitution law.
5. [`references/productization-program.schema.json`](references/productization-program.schema.json)
   — the machine contract, with its positive example and its eleven refusal
   controls inline.
6. [`references/composition-manifest.json`](references/composition-manifest.json)
   — the ten composed methods, each by content digest and declared interface.
7. [`references/core/source-proposal-audit.md`](references/core/source-proposal-audit.md)
   — what the preparation branch contained, and what this freeze admitted and
   refused from it.
8. The four Stage-1 lane contracts —
   [`references/market/market-lane.schema.json`](references/market/market-lane.schema.json),
   [`references/user/user-lane.schema.json`](references/user/user-lane.schema.json),
   [`references/commercial/commercial-lane.schema.json`](references/commercial/commercial-lane.schema.json),
   [`references/policy/policy-lane.schema.json`](references/policy/policy-lane.schema.json)
   — each beside its own vocabulary file.
9. The three Stage-2 session contracts —
   [`references/session/closure-matrix.schema.json`](references/session/closure-matrix.schema.json),
   [`references/session/session-dag.schema.json`](references/session/session-dag.schema.json),
   [`references/session/outcome-foldback-request.schema.json`](references/session/outcome-foldback-request.schema.json)
   — what [`scripts/compile_pol_composition.py`](scripts/compile_pol_composition.py)
   emits and refuses against: byte-stable canonical JSON, `--check`, and named
   K-code refusals with exit 2, never a silent downgrade.
10. [`prompts/README.md`](prompts/README.md) — the common system envelope and
    the twelve pasteable stage prompts, common-system-envelope through
    stage-11-outcome-foldback.
11. [`modules/README.md`](modules/README.md) — trigger-gated domain instances;
    read only the module a concrete consumer binding actually requires.

## What is here

```text
AGENTS.md                             zero-context read route, agent roles,
                                       CodexDoc/GitHub trace law, Ancestry note
SKILL.md                               portable state machine, twelve stages,
                                       hard laws, evidence ceiling
modules/
├── README.md                          trigger-gated module index
└── domain-profile.md                  what a concrete consumer must bind,
                                       never who the consumer is
prompts/
└── README.md                          common system envelope + twelve
                                       pasteable stage prompts
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
├── evidence_plane.py               Shadow-side evidence plane: 19 planted
│                                   cases, all 14 preregistered false
│                                   promotions, reopen-first-green law
├── fixtures/                       evidence-plane base composition
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

`INTERFACE_LOCK_ONLY` for the contract itself: freezing it proves that a shape
is fixed and that eleven named refusals are refused by the keywords they
cite. The compiler's own ceiling is `DETERMINISTIC_COMPOSITION` (six artifacts,
byte-stable, eight K-code refusals — see [`SKILL.md`](SKILL.md)'s Evidence
ceiling table). This convergence's own ceiling is
`ROUTING_PROMPT_TRACE_CONVERGENCE` (see [`AGENTS.md`](AGENTS.md)). The
evidence plane ([`tests/evidence_plane.py`](tests/evidence_plane.py)) adds
`DETERMINISTIC_FALSE_PROMOTION_REFUSAL`: nineteen planted cases covering all
fourteen preregistered false promotions plus a hollow case, each refused by
the exact guard it names, nine of them green to the admitted stack until the
reopen pass. None of the
four proves that the method exists end to end, that an arena is attractive,
that a user would switch, that anyone would pay, that a rule permits
anything, that any session actually ran, or that any of this may be merged or
released. Those lanes are reported by this directory; they are not cleared by
it.
