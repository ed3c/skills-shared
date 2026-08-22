# `dual-track-code-review-loop`

Portable method for reviewing code with a deterministic track and a semantic
track that are structurally forbidden from standing in for each other, so that a
finding always carries the grade its evidence supports.

Status: `C0_CONTRACT_ADMITTED / FIVE_ADAPTERS_LANDED / R1_R2_COMPILERS_LANDED / NOT_REGISTERED`.

Five adapters are landed and committed, each with its own selftest routed
through [`tests/run-all.sh`](tests/run-all.sh): `adapters/tree-sitter/`
(parser/syntax-match facts), `adapters/sqlite-ledger/` (queryable graph-ledger
fact plane), and — landed in the 2026-08-22 wave under Human-admitted provider
prerequisites — `adapters/scip/` (symbol/relationship facts on a real
scip-python round-trip), `adapters/buf/` (contract compatibility with a typed
`NOT_APPLICABLE` lane) and `adapters/semantic-context/` (zero-network,
structurally non-authoritative retrieval). The same wave landed the `#524` R2
Expand & Contract compiler under [`expand-contract/`](expand-contract/) with
two more contracts; its live lanes stay `NOT_EXERCISED`/`NOT_OBSERVED`. The `#522`
synthesis and problem-closure compilers landed in an earlier wave under
[`synthesis/`](synthesis/), with their three contracts under
`references/schemas/` counted by the committed harness. The `#523` bounded
single-repository refactor protocol landed the same way under
[`refactor/`](refactor/) with four more contracts. Its terminal
`DTCR_SINGLE_REPO_REFACTOR_PROTOCOL_READY` is **not** claimed here: that
admission belongs to a person reading the issue's exit criteria, and one of
those criteria is a real bounded consumer canary, which no lane in this tree has
exercised. Every receipt the compiler emits pins `protocol_ready` and
`applied_on_real_codebase` false for exactly that reason.

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
6. [`references/schemas/`](references/schemas/) — the machine half, 33 frozen
   schemas (8 C0 contract + 16 D1/M1 interface + 3 X1 synthesis + 4 R1 bounded
   refactor + 2 R2 cross-repository).
7. [`references/source-disposition/refused-claims.json`](references/source-disposition/refused-claims.json)
   — the seven refused source claims and their replayable controls.
8. [`adapters/`](adapters/) — the five landed adapters, each with its own
   selftest and fixtures.
9. [`references/prompts/README.md`](references/prompts/README.md) — the common
   session envelope and the nine zero-context stage prompts, P0 through P8.
10. [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md),
   [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md)
   and
   [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md)
   for orchestration, independent review and delivery.
11. The exact issue, pull request base and head, and evidence subject.

## Directory map → ownership

```text
skills/dual-track-code-review-loop/
├── AGENTS.md
│   └── read order, Builder and Shadow roles, writer/adapter-lease laws, required change packet
├── README.md
│   └── directory map, State Machine, DAG, data flow, evidence ceiling, handoff
├── SKILL.md
│   └── the two-track separation, the ten-state procedure, the hard laws
├── cases.json
│   └── readable index of every denominator tests/selftest.py counts on the run
├── evals.json
│   └── local eval plane meta: what this suite decides and what it does not
├── adapters/
│   ├── tree-sitter/
│   │   ├── adapter.py, selftest.py, bundles/, fixtures/
│   │   └── receipts/live-05c56c37.json
│   │       └── landed parser/syntax-match capability class; live receipt binds
│   │           digests to a real `tree-sitter` run over committed fixtures
│   ├── sqlite-ledger/
│   │   ├── ledger.py, selftest.py, fixtures/
│   │   │   └── landed queryable graph-ledger capability class; planted-mutation
│   │   │       knockouts and a real ingested/traversed database file
│   ├── scip/
│   │   ├── adapter.py, selftest.py, normalization/, bindings/, fixtures/
│   │   └── receipts/live-ee9afe43.json
│   │       └── landed symbol/relationship capability class on a real
│   │           scip-python index round-trip; coverage ceilings and unresolved
│   │           denominators preserved, nesting never promoted to a call graph
│   ├── buf/
│   │   ├── adapter.py, selftest.py, fixtures/
│   │   │   └── landed contract-compatibility capability class: a real breaking
│   │   │       finding on a committed .proto pair plus the typed NOT_APPLICABLE
│   │   │       lane; live lane self-reports NOT_EXERCISED where buf is absent
│   └── semantic-context/
│       ├── adapter.py, selftest.py, fixtures/, receipts/
│       │   └── landed SemanticContextPort with a deterministic zero-network
│       │       reference backend; LanceDB lane typed NOT_EXERCISED
├── synthesis/
│   ├── compile_synthesis.py, selftest.py, fixtures/
│   │   └── the X1 review-synthesis and problem-closure compilers
├── refactor/
│   ├── compile_r1.py, selftest.py, fixtures/
│   │   └── the R1 bounded single-repository refactor protocol: one compiler
│   │       walking VIOLATION_BOUND through CANDIDATE_RECEIPT | BLOCKED |
│   │       ROLLED_BACK over five synthetic requests, four of the adapter law's
│   │       eight declared languages, and no vendored adapter implementation
├── expand-contract/
│   ├── compile_r2.py, fixture_repos.py, selftest.py, fixtures/, receipts/
│   │   └── the R2 cross-repository Expand & Contract compiler over a
│   │       two-repository disposable git fixture: multi-binding subject,
│   │       dual-run lane closed over OBSERVED/NOT_OBSERVED/NOT_EXERCISED,
│   │       STOPPED_WITH_ROLLBACK truthful-stop terminal, protocol_ready
│   │       pinned false
├── tests/
│   ├── run-all.sh
│   │   └── one entrypoint: replays the C0 contract, then routes the five
│   │       adapter selftests, the X1 synthesis selftest and the R1 and R2
│   │       compiler selftests through the same CI arrival — nine lanes
│   └── selftest.py
│       └── dynamic discovery over references/; prints every denominator it counted
└── references/
    ├── README.md
    │   └── contract index, schema identity convention, control-case convention
    ├── contracts/
    │   ├── controlled-vocabulary.md
    │   └── public-private-capability.md
    │       └── closed terms and plane ownership; the half a person reads
    ├── schemas/
    │   └── 33 frozen JSON Schemas — 8 C0 contract schemas (source-packet,
    │       candidate-record, violation-candidate, refactor-proposal,
    │       change-unit, verification-receipt, closure-record,
    │       source-disposition) plus 16 D1/M1 interface schemas (syntax-match,
    │       symbol-fact, fact-plane-receipt, coverage-ceiling,
    │       semantic-document, retrieval-query/-result,
    │       semantic-freshness-ceiling, semantic-index-lifecycle-receipt,
    │       architecture-invariant, blast-radius-path,
    │       contract-compatibility-result, consumed-context-row,
    │       exact-source-subject, projection-receipt, source-back-reference)
    │       plus 3 X1 synthesis schemas (review-card, synthesis-packet,
    │       problem-closure-row) plus 4 R1 bounded-refactor schemas
    │       (refactor-usage-signature, refactor-minimal-port,
    │       refactor-changeset-lease, refactor-r1-receipt) plus 2 R2
    │       cross-repository schemas (refactor-r2-binding, refactor-r2-receipt)
    │       └── the half a machine enforces, with positive and refusal controls
    ├── source-disposition/
    │   └── refused-claims.json
    │       └── seven refused source claims, each bound to a control that refuses
    └── prompts/
        └── README.md
            └── common session envelope + nine zero-context stage prompts (P0–P8)
```

Markdown and JSON Schema route and enforce the contract. `adapters/` is
concrete implementation against that contract — where external tools
(`tree-sitter`, `scip-python`, `buf`, `git`) are actually invoked and real
database and index files are actually created. Consumer repositories still own
applying a proposal to their own code; nothing here has ever done that.

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

A committed test suite now exists at [`tests/run-all.sh`](tests/run-all.sh),
routed by `skill-suites.yml` continuous integration. It replays the C0
contract via `tests/selftest.py` — dynamic discovery over `references/`, no
denominator hand-copied into the script — and then routes the five landed
adapters' selftests, the X1 synthesis selftest (`synthesis/selftest.py`), the
R1 bounded-refactor selftest (`refactor/selftest.py`) and the R2
expand-contract selftest (`expand-contract/selftest.py`) through the same CI
arrival — nine lanes. On this worktree's exact head each lane's denominator
line reads:

```text
schemas=33 positives=37 controls=151 knockouts=151 leak_scan_files=38 mutable_subject_probes=115 promotion_probes=184
tree-sitter:      fixtures=2 matches=5 schema_validations=9 falsifier_rows=14 live=EXERCISED
sqlite-ledger:    fixtures=2 cases=46 planted_mutations=22 knockouts=5/5
scip:             fixtures=1 facts=76 schema_validations=78 falsifier_rows=17 crosscheck=EXERCISED live=EXERCISED
buf:              fixtures=2 falsifier_rows=16 live=NOT_EXERCISED
semantic-context: 90 cases, 41 planted falsifiers refused, 12 required falsifiers all planted, zero network, LanceDB NOT_EXERCISED (PROVIDER_ABSENT)
synthesis:        stability_checks=9 schema_compositions=8 refusal_codes=16 projections=3
refactor:         requests=5 stability_checks=15 schema_compositions=20 state_values_covered=44 refusal_codes=26 languages_exercised=4/8 applied_on_real_codebase=NOT_EXERCISED
expand-contract:  requests=4 stability_checks=12 consumed_verdicts=8 state_values_covered=56 unreachable_at_this_head=15 refusal_deltas=29 knockouts=28 two_repository_fixture=EXERCISED applied_on_real_codebase=NOT_EXERCISED dual_run_observation=NOT_OBSERVED contraction_authorization=HUMAN_ADMIT_REQUIRED
```

`buf` reads `live=NOT_EXERCISED` on a host without the buf executable; the
landing run's real buf 1.72.0 outputs are committed as fixtures and the lane
replays them deterministically. Those are the nine denominator lines the run
prints, with host-specific
fragments elided so this file stays machine-neutral: the first line's
`subject=<absolute path>`, the tail of the sqlite line (three per-host digests
and a row-count map), and some trailing `failures=0`-class tokens. Every token
quoted above appears verbatim in the run's output; the block is a trimmed
quotation, not a transcript.

`cases.json` reconciles the schema and control lists by name against what the
run counted and fails on any drift in either direction; the knockout and probe
floors are read from the guards themselves rather than hand-maintained, so a
guard that disappears removes its own floor and the CI arrival goes red rather
than silently shrinking. This is what a Molecular Worker or CI run should
invoke — do not hand-roll a narrower replay of it.

An earlier, uncommitted scratch harness run against the C0 contract alone (32
knockouts, 32 discriminating) is recorded in
[`../../docs/traceability/dual-track-code-review-loop/implementation-preflight.json`](../../docs/traceability/dual-track-code-review-loop/implementation-preflight.json)
as historical evidence from before this suite was committed. It is superseded
by the committed suite above for anything the committed suite also covers, and
kept only because the C0 refusal results were independently re-derived against
it once, which the committed suite's own single derivation does not replace.

## Evidence ceiling

```text
controlled vocabulary and plane contract     ADMITTED_AS_CANDIDATE
schema shape and refusal controls            VERIFIED_ON_THESE_BYTES
mutation controls over the refusals          VERIFIED_BY_COMMITTED_SUITE
                                             + INDEPENDENTLY_RE_DERIVED_HISTORICALLY
committed mutation harness                   PRESENT (tests/run-all.sh, CI-routed)
parser/syntax-match adapter (tree-sitter)    LANDED, selftest + live receipt
graph-ledger adapter (sqlite-ledger)         LANDED, selftest, planted mutations
SCIP adapter (#547)                          LANDED — selftest + live scip-python receipt (live-ee9afe43)
Buf adapter (#549)                           LANDED — selftest; landing-run buf 1.72.0 outputs committed, live lane NOT_EXERCISED where buf absent
semantic-context adapter (#550)              LANDED — zero-network reference backend; LanceDB lane NOT_EXERCISED
dual-track synthesis compiler (#522)         LANDED — synthesis/ + three schemas, suite-counted
bounded R1 refactor protocol (#523)          LANDED — refactor/ + four schemas, suite-counted
R2 expand-contract compiler (#524)           LANDED — expand-contract/ + two schemas, suite-counted; two-repository fixture EXERCISED
R2 dual-run / telemetry observation          NOT_OBSERVED (fixture serves no traffic)
R1 language adapter implementations          BLOCKED_ON_PROVIDER (declared capability classes only)
R1 live consumer canary (#523 exit)          NOT_EXERCISED
applied refactor on a real codebase          NOT_EXERCISED
cross-repository contract migration          NOT_EXERCISED (fixture only)
live consumer canary (#528)                  NOT_EXERCISED
independent Shadow (#525)                    NOT_EXERCISED
registry admission                           ABSENT
legal, employment and IP clearance           HUMAN_ADMIT_REQUIRED
merge, release, production, visibility       HUMAN_ADMIT_REQUIRED
```

The mutation line changed shape because its evidence changed shape: a suite is
now committed and CI-routed, so the line reads `VERIFIED_BY_COMMITTED_SUITE`
rather than the uncommitted-scratch-harness label it replaced. The earlier,
narrower C0-only harness was independently re-derived once by the Shadow on the
H0-003 review before this suite existed; that historical fact is kept as a
second derivation behind the C0 slice only, not as evidence for the
adapters, which have never been through an independent Shadow pass.
`NOT_IMPLEMENTED`, `BLOCKED_ON_PROVIDER`, `NOT_EXERCISED` and `IN_FLIGHT` are
distinct states here on purpose: a blocked provider dependency, an unbuilt
adapter, a built-but-unexercised path, and another Worker's concurrent open
issue are four different reasons a lane has not closed, and collapsing them
would hide which one applies.

## Current handoff

Five adapters, the X1 synthesis compilers and the R1 and R2 protocol compilers
are landed with all nine selftests green in the committed suite above; the
2026-08-22 wave landed `#547`/`#549`/`#550`/`#524` under Human-admitted
provider prerequisites. The next owner for *this contract* is still an
independent Shadow on this exact head (`#525`, open), reading the audit list in
[`AGENTS.md`](AGENTS.md) and returning `ADMIT_FOR_DOWNSTREAM`, `BLOCK` or
`REPLAN_REQUIRED`; a same-context review may warn and cannot satisfy that role.
Remaining open, path-disjoint lanes on this same head: `#525` (independent
Shadow), `#527` (bootstrap profile — landed as a `shared-skills-infra` sibling
profile with its own suite, completion-dependent on `#525` admission) and
`#528` (live consumer canary, the eventual Local Handoff owner). None of them
is promoted by this file landing, and this file's landing does not promote any
of them either — each closes only on its own issue's evidence.
