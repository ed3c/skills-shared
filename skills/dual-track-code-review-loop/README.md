# `dual-track-code-review-loop`

Portable method for reviewing code with a deterministic track and a semantic
track that are structurally forbidden from standing in for each other, so that a
finding always carries the grade its evidence supports.

Status: `C0_CONTRACT_CANDIDATE / ADAPTERS_NOT_IMPLEMENTED / NOT_REGISTERED`.

The failure this Skill exists to stop is not sloppiness. It is that both tracks
produce output that reads identically once it lands in a report. A dependency
edge a compiler resolved and one inferred by nesting a reference inside the
nearest enclosing definition become the same row in the same table. A retrieved
decision record and an admitted invariant become the same bullet in the same
review comment. A suite that passed and a system that works become the same
green. Each of those collapses is cheap to produce, which is exactly why it is
the one most often reported as progress.

## Read order

1. [`AGENTS.md`](AGENTS.md) — writer authority, Shadow role, stop conditions,
   completion rules.
2. [`SKILL.md`](SKILL.md) — the portable procedure and its hard laws.
3. [`references/README.md`](references/README.md) — contract index.
4. [`references/contracts/controlled-vocabulary.md`](references/contracts/controlled-vocabulary.md)
   — the fifteen closed terms and what each can never become.
5. [`references/contracts/public-private-capability.md`](references/contracts/public-private-capability.md)
   — plane ownership and the locator laws.
6. [`references/schemas/`](references/schemas/) — the machine half.
7. [`references/source-disposition/refused-claims.json`](references/source-disposition/refused-claims.json)
   — the seven refused source claims and their replayable controls.
8. [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md),
   [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md)
   and
   [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md)
   for orchestration, independent review and delivery.
9. The exact issue, pull request base and head, and evidence subject.

## Directory map → ownership

```text
skills/dual-track-code-review-loop/
├── AGENTS.md
│   └── read order, Builder and Shadow roles, writer laws, required change packet
├── README.md
│   └── directory map, State Machine, DAG, data flow, evidence ceiling, handoff
├── SKILL.md
│   └── the two-track separation, the ten-state procedure, the hard laws
└── references/
    ├── README.md
    │   └── contract index, schema identity convention, control-case convention
    ├── contracts/
    │   ├── controlled-vocabulary.md
    │   └── public-private-capability.md
    │       └── closed terms and plane ownership; the half a person reads
    ├── schemas/
    │   ├── source-packet.schema.json
    │   ├── candidate-record.schema.json
    │   ├── violation-candidate.schema.json
    │   ├── refactor-proposal.schema.json
    │   ├── change-unit.schema.json
    │   ├── verification-receipt.schema.json
    │   ├── closure-record.schema.json
    │   └── source-disposition.schema.json
    │       └── the half a machine enforces, with positive and refusal controls
    └── source-disposition/
        └── refused-claims.json
            └── seven refused source claims, each bound to a control that refuses
```

Markdown routes. Schemas decide the deterministic contract state. Consumer
repositories own actual code, tooling and runtime evidence.

Registry admission is a separate governance fact from directory presence. This
directory's registry classification is `ABSENT` until a human-admitted
governance change, and its presence here decides nothing.

## Primary State Machine

```text
SOURCE_AND_RIGHTS_BOUND
→ INVARIANTS_BOUND
→ DETERMINISTIC_FACTS_DERIVED
→ SEMANTIC_CONTEXT_BOUND_OR_NOT_APPLICABLE
→ VIOLATION_CANDIDATES_NOMINATED
→ CANDIDATES_CONFIRMED_OR_REFUTED
    ├── REFUTED
    ├── NOT_APPLICABLE
    ├── BLOCKED
    └── CONFIRMED_AGAINST_DETERMINISTIC_FACT
→ REFACTOR_PROPOSALS_BOUNDED
    └── NO_CHANGE_WARRANTED is a terminal, not a failure
→ CHANGE_UNITS_APPLIED
→ VERIFIED_ON_TWO_INDEPENDENT_ARRIVALS
→ CLOSED_WITH_STATED_CEILING
```

Running the method creates no obligation to change anything.

## Evidence DAG

```text
exact commit + admitted source packet
        ↓
source disposition ── refused claims stay refused, with a replayable control
        ↓
architecture invariants (admitted by a person, written out in full)
        ↓
        ├── deterministic track ── parser facts, resolved symbols, graph edges
        │       each edge tagged with how it was obtained
        │
        └── semantic track ── decisions, incidents, budgets, telemetry
                each item marked NON_AUTHORITATIVE_CANDIDATE on arrival
        ↓
violation candidate ── basis MUST contain a deterministic fact
        ↓
confirmed / refuted / not applicable / blocked   (all stay in the denominator)
        ↓
bounded refactor proposal ── mechanism paired to the property it establishes
        ↓
change unit ── exact base, exact head, complete changed-path denominator
        ↓
verification receipts ── one arrival each, denominators behind every ratio
        ↓
closure record ── two distinct arrivals, every lane reported
        ↓
independent Shadow → human admission
```

Retrieval is a candidate producer. It is never confirmation authority.

## The seven refusals

Each is refused by a schema keyword rather than by advice, and each ships a
control instance that the schema rejects. The controls are replayable, so
removing a guard and leaving its refusal prose behind is visible in one diff.

Read the right-hand column literally. Three of these seven are structural — the
shape genuinely cannot express the claim. The other four refuse a recorded list
of spellings or pairs, which stops the reflex phrasing and does not stop a
paraphrase. Which kind each one is:

| Refused claim | Refused by | Kind |
|---|---|---|
| Absolute coverage, zero false reports, settled compliance | receipt coverage requires a named denominator, so a bare percentage has no field; the summary additionally refuses ten listed spellings | structural on coverage, word list on the prose |
| Automatic merge from one graph count plus a green suite | change-unit merge admission is single-valued | structural |
| Deterministic signature-nonce derivation aimed at authenticated-encryption nonce reuse | three named mechanism-to-property pairs out of fifty-four are blacklisted | list of three pairs |
| Occurrence nesting recorded as a complete call graph | heuristic provenance is bound to a partial completeness value | structural |
| Retrieval promoted to truth | a violation's basis must contain a deterministic fact; retrieved items are fixed non-authoritative | structural |
| One observed stack promoted to universal practice | applicability scope is fixed to observed targets; the target list refuses four exact lowercase wildcard spellings | structural on scope, word list on the targets |
| Fixed performance and productivity numbers | every figure is a full measurement object or the literal unmeasured value | structural |

The word-list halves were probed and are known to be passable. A summary reading
`complete coverage ... no false positives whatsoever` matches none of the ten
spellings and is accepted. A target list of `["Universal", "all languages",
"every runtime"]` matches none of the four wildcard spellings and is accepted,
because that pattern is anchored and case-sensitive. A remediation pairing
`BOUNDED_LOCAL_EDIT` with `AEAD_NONCE_UNIQUENESS` was accepted before it was
added to the blacklist, and the fifty-one unlisted pairs are still accepted. In
each of those cases the reviewer, not the schema, is the thing standing between
the claim and the record.

## Local verification

There is no committed test suite here yet, because a suite in this tree has to
be routed by continuous integration before it means anything, and that routing
is not this stage's to arrange. That routing belongs to whoever owns the
workflow matrix and `evals/`, and until they take it the harness stays absent
rather than pending.

What was run against these bytes was run from an uncommitted scratch harness
and is recorded in
[`../../docs/traceability/dual-track-code-review-loop/implementation-preflight.json`](../../docs/traceability/dual-track-code-review-loop/implementation-preflight.json),
including the per-control knockout denominators (32 knockouts, 32
discriminating). An uncommitted harness is a claim about a run nobody else can
repeat from this tree, which is why the refusal results here rest on a second,
independent derivation rather than on that harness alone.

## Evidence ceiling

```text
controlled vocabulary and plane contract     ADMITTED_AS_CANDIDATE
schema shape and refusal controls            VERIFIED_ON_THESE_BYTES
mutation controls over the refusals          VERIFIED_BY_UNCOMMITTED_SCRATCH_HARNESS
                                             + INDEPENDENTLY_RE_DERIVED
committed mutation harness                   ABSENT
parser / index / graph adapter               NOT_IMPLEMENTED
retrieval adapter                            NOT_IMPLEMENTED
applied refactor on a real codebase          NOT_EXERCISED
cross-repository contract migration          NOT_EXERCISED
live consumer canary                         NOT_EXERCISED
independent Shadow                           NOT_EXERCISED
registry admission                           ABSENT
legal, employment and IP clearance           HUMAN_ADMIT_REQUIRED
merge, release, production, visibility       HUMAN_ADMIT_REQUIRED
```

`VERIFIED_BY_UNCOMMITTED_SCRATCH_HARNESS + INDEPENDENTLY_RE_DERIVED` is the
whole provenance of the mutation line, written out because the shorter label it
replaced read as though a suite in this tree had produced it. The mutation
results were produced by a harness that was never committed, and were then
re-derived from these bytes by the independent Shadow on the H0-003 review
without reusing that harness. Two derivations that do not share code are what
the line rests on. A committed harness, routed by continuous integration, is
`ABSENT` and stays that way until the suite and workflow owner takes it.

## Current handoff

The next owner is an independent Shadow on this exact head, reading the audit
list in [`AGENTS.md`](AGENTS.md) and returning `ADMIT_FOR_DOWNSTREAM`, `BLOCK` or
`REPLAN_REQUIRED`. A same-context review may warn and cannot satisfy that role.
Deterministic-fact and semantic-context adapters are path-disjoint sibling work
and are released only after this contract is admitted and their shared interface
is frozen.
