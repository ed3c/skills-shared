# `product-reverse-engineering-loop`

Portable procedure for converting evidence-bound product signals into a
falsifiable product dossier, a classified mechanism and capability graph, a
problem-closure matrix and bounded implementation packets — without embedding any
consumer's repository topology, and without letting cheap evidence stand in for
expensive evidence.

The failure this Skill exists to stop is not sloppiness. It is that the evidence
which is easy to produce (a page read, a feature list, a green suite, a busy
discussion board) reads exactly like the evidence that decides whether a product
is worth building (an observed mechanism, a job someone will switch for, a person
who paid). Every law here is one substitution refused by name.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. [`references/evidence-vocabulary.md`](references/evidence-vocabulary.md)
4. [`references/README.md`](references/README.md)
5. [`references/prompt-catalogue.md`](references/prompt-catalogue.md)
6. [`modules/README.md`](modules/README.md), then only the module whose trigger matches
7. [`scripts/README.md`](scripts/README.md)
8. [`tests/README.md`](tests/README.md), [`cases.json`](cases.json), [`evals.json`](evals.json)
9. the exact issue, PR base/head, and evidence subject

## Directory map → ownership

```text
skills/product-reverse-engineering-loop/
├── AGENTS.md
│   └── read order, writer leases, stop conditions, completion report
├── README.md
│   └── navigation, State Machines, DAGs, data flow, evidence ceiling, handoff
├── SKILL.md
│   └── portable transition law, CORE-LAW-001..008, stop conditions
├── cases.json
│   └── deterministic case inventory and expected verdicts
├── evals.json
│   └── claim inventory, controls, and the lane each claim may speak in
├── references/
│   ├── product-signal.schema.json          intake + producer compatibility binding
│   ├── reverse-engineering-dossier.schema.json
│   ├── problem-closure-matrix.schema.json
│   ├── product-closure-audit.schema.json   read-only Shadow audit: levels, lanes, findings, handoff
│   ├── prompt-packet.schema.json
│   ├── reverse-engineering-handoff.schema.json
│   ├── evidence-vocabulary.md              four controlled vocabularies, every refusal code
│   ├── prompt-catalogue.md                 what each prompt surface exists to refuse
│   └── example-*.json                      two hand-authored inputs, three compiled projections, one packet, one audit
├── modules/
│   ├── domain-profile.md                   concrete surfaces, owners and adapters, on demand
│   └── shadow-closure-audit.md             the read-only closure monitor and its review handoff
├── evals/
│   └── receipts/                           consumer canary receipts, one lane per file
├── scripts/
│   ├── check_prel_contract.py              schema + controlled-law refusals
│   └── compile_prel.py                     the three byte-stable compilers
└── tests/
    ├── run-all.sh
    └── selftest.py                         positive, hollow, mutation and stale-subject controls
```

## Core State Machine

```text
INPUT_BOUND
→ VERIFIED_BASE_BUILT
→ PRODUCT_JOB_AND_PAIN_BOUND
→ WORKFLOW_AND_MAGIC_MOMENT_BOUND
→ MECHANISM_HYPOTHESES_CLASSIFIED
→ CAPABILITY_AND_RIGHTS_GRAPH_BOUND
→ MVP_AND_STOP_LOSS_BOUND
→ CLOSURE_CONTRACT_BOUND
→ EXECUTABLE_HANDOFF
```

Fail-closed terminals:

```text
BLOCKED_UNGRADED_INPUT
BLOCKED_NO_JOB_HYPOTHESIS
BLOCKED_NO_OBSERVABLE_ORACLE
BLOCKED_RIGHTS_UNADMITTED
BLOCKED_LANE_SUBSTITUTION
BLOCKED_OVERLAPPING_LEASE
BLOCKED_STALE_SUBJECT
```

## Closure State Machine

Second state machine, over one row of the closure matrix rather than the run:

```text
                        ┌── no oracle ─────────────→ BLOCKED_NO_ORACLE
                        ├── unfalsifiable claim ───→ BLOCKED_NOT_FALSIFIABLE
requirement admitted ───┼── oracle in another lane → BLOCKED_LANE_MISMATCH
                        ├── person owns it ────────→ HUMAN_ADMIT_REQUIRED
                        └── oracle in its own lane → OPEN_WITH_ORACLE
                                                        │
                                    consumer executes the oracle
                                                        ↓
                                                  CLOSED_BY_ORACLE
```

The last edge is the one this repository cannot walk. `compile_prel.py` reaches
`OPEN_WITH_ORACLE` at its strongest, because compiling an oracle is not running
one. `CLOSED_BY_ORACLE` stays in the contract for a consumer that actually ran
one, and its producer here is `NOT_IMPLEMENTED` — recorded rather than repaired,
so nobody reads a validated state as a reachable one.

## Data flow

```text
consumer capture (consumer-owned)
        ↓ typed signals + producer compatibility binding
product-signal.json
        ↓ compile_prel.py --stage dossier      grades fixed by kind, never argued
reverse-engineering-dossier.json
        ↓ compile_prel.py --stage closure      one row per requirement and excluded mechanism
problem-closure-matrix.json
        ↓ compile_prel.py --stage handoff      technical-lane rows become packets, the rest become remaining
reverse-engineering-handoff.json
        ↓ consumer runtime, user/paid evidence owners, Human admission
consumer receipts (consumer-owned, one lane each)
```

Every arrow narrows. No arrow upgrades a lane, and the artifact at each step
records which lanes it did not enter.

One read-only branch leaves this flow and never rejoins it:

```text
any subject that claims a problem is closed
        ↓ modules/shadow-closure-audit.md          read-only, findings only
product-closure-audit.json
        ↓ check_prel_contract.py --resolve-subjects
findings, reopened obligations, issue delta        proposals with no write authority
```

The audit is a monitor, not a second writer: it produces no state the loop
consumes, and the repairs it proposes are performed — or refused — by whoever
owns the subject.

## Work DAG

```text
PREL-C contracts, schemas, examples, controlled vocabulary
└─ PREL-K deterministic dossier/closure/handoff compilers
   └─ PREL-E positive, hollow, mutation and stale-subject controls
      └─ PREL-D AGENTS/README/routes/prompt catalogue and exact handoff
```

These are true child edges: K consumes C's frozen schemas, E consumes K's
compiled projections as its positive control, and D consumes E's refusal-code set
for the prompt envelope. Path-disjoint work may be siblings only once the
interfaces above it are frozen; `PREL-D` is the single shared-index owner.

## Prompt surfaces

```text
COMMON_SYSTEM_ENVELOPE
STAGE_1_CONTROL_BINDER
STAGE_2_SOURCE_INTAKE
STAGE_3_EVIDENCE_COMPILER
STAGE_4_YC_PRODUCT_REVERSE_ENGINEER
STAGE_5_TECHNICAL_SYSTEMS_ARCHITECT
STAGE_6_SHADOW_MONITOR
STAGE_7_TECH_LEAD_PLANNER
STAGE_8_MOLECULAR_WORKER
STAGE_9_CONVERGENCE_OWNER
```

The machine authority is
[`references/example-prompt-packet.json`](references/example-prompt-packet.json);
[`references/prompt-catalogue.md`](references/prompt-catalogue.md) explains what
each surface exists to refuse. No surface grants merge, permission, secret or
production authority, and no surface requests private chain of thought.

## Local verification

```bash
python3 skills/product-reverse-engineering-loop/scripts/check_prel_contract.py \
  --artifact skills/product-reverse-engineering-loop/references/example-prompt-packet.json \
  --resolve-subjects skills/product-reverse-engineering-loop/references

python3 scripts/check_skill_core_boundaries.py --skill product-reverse-engineering-loop
python3 scripts/check_skill_entry_routes.py --skill product-reverse-engineering-loop --print-index

bash skills/product-reverse-engineering-loop/tests/run-all.sh
```

## Current integration state

```text
portable procedure and directory contract        PASS
six schemas with validating positive examples    PASS
deterministic compilers, byte-stable             PASS
55 planted controls refused by their own code    PASS
prompt catalogue reconciled with the packet      PASS
CI arrival for tests/run-all.sh                  ABSENT
registry.json classification                     ABSENT
mechanism reproduction on a real product         NOT_EXERCISED
user, paid or market validation                  NOT_EXERCISED
product-market fit                               ABSENT
live provider or runtime execution               NOT_EXERCISED
merge, release, rights admission                 HUMAN_ADMIT_REQUIRED
```

`CI arrival` is `ABSENT` on purpose and is the one open mechanical item: this
Skill ships `tests/run-all.sh`, and `scripts/check_suite_ci_coverage.py` requires
every such suite to be named by a workflow job. The lane that owns
`.github/workflows/` must add this Skill to the `Skill Suites` matrix and its
path filters. Until then the suite runs locally through the repository
`verify.sh` and has no CI arrival, which is exactly what that gate exists to say
out loud.

`registry.json` classification is `ABSENT` because shared/repo-owned
classification is a Human-admitted governance change, not a side effect of
landing a directory.

## Evidence boundary

A green suite proves these contracts hold against current repository bytes. It
cannot prove product-market fit, live provider execution, cross-domain uplift,
delivery-runtime behavior, merge safety or production readiness. Those lanes are
consumer-owned and stay `NOT_EXERCISED` or `ABSENT` here.
