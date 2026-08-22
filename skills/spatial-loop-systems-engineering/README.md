# spatial-loop-systems-engineering

Portable **Constraint-First Spatial Systems Engineering** with a monitor-first **Shadow Architecture Control Loop** and an explicit **Intent–Case–Proof Graph (ICPG)** for use-case/edge-case/semantic-preservation closure.

`MONITOR` remains the default: the Builder may explore, design, implement, test and refactor while Shadow Architect observes material architecture, intent, case, evidence and procedural-grounding deltas. `PRECHECK` gates high-risk/irreversible transitions; `POSTMORTEM` reconstructs implicit architecture after failure or first-green.

## Read order

1. [`AGENTS.md`](AGENTS.md) — local Agent obligations and current #407 program.
2. [`SKILL.md`](SKILL.md) — universal method and hard laws.
3. [`references/intent-case-proof-graph.md`](references/intent-case-proof-graph.md) — prompt intent → cases → implementation → proof contract.
4. [`references/architecture-watch-loop.md`](references/architecture-watch-loop.md) — live-monitor semantics and L0–L3 intervention.
5. [`references/spec-packet-template.md`](references/spec-packet-template.md) and machine contracts.
6. `scripts/`, `tests/`, and [`evals.json`](evals.json).

## Canonical flow

```text
User Prompt / PDF / PRD / Diagram / Repo / Source Behavior
        ↓
Constraint Compiler
        ├── domain expansion
        ├── unknown probes
        └── hard laws
        ↓
Intent–Case–Proof Graph
        ├── Intent Atoms
        ├── Semantic Axes
        ├── Use / Edge Cases
        ├── Source Behavior Dispositions
        ├── State Paths / Invariants
        ├── Implementation Owners
        └── Oracles / Evidence
        ↓
Executable Spec
        ↓
Tech Lead Task DAG when composed
        ↓
Builder implementation
        ↕
Shadow Architecture Watch Loop
        ├── architecture/evidence deltas
        ├── intent/case/semantic-parity deltas
        └── optional Procedural Grounding Shadow Plane
        ↓
Harness / Evals
        ↓
FIRST_GREEN + BEFORE_PR reconciliation
```

The governing transformation is:

```text
WHAT THE USER WANTS
→ WHAT MUST ALWAYS REMAIN TRUE
→ WHICH CASES WOULD FALSIFY THAT
→ WHO IMPLEMENTS EACH CASE OBLIGATION
→ HOW WE KNOW IT REMAINS TRUE

Intent
→ Boundary
→ State
→ Invariant
→ Case
→ Failure
→ Implementation Binding
→ Oracle
→ Evidence
```

A short prompt may reduce wording. It may not reduce semantic obligations.

## Runtime State Machine vs provenance DAG

Runtime/state behavior may cycle:

```text
OBSERVE
→ DIFF
→ RECONCILE
→ VERIFY
├─ PASS → next checkpoint
└─ FAIL → bounded retry / postmortem / escalation
          ↘ may return to OBSERVE
```

ICPG provenance must be acyclic:

```text
Prompt / Source Behavior
→ Intent Atom
→ Semantic Axis
→ Case
→ State Path / Invariant
→ Implementation Binding
→ Oracle
→ Evidence Receipt
```

Do not force retry/rollback/reconciliation into a DAG. Do not permit provenance cycles that make an obligation depend on its own proof.

## Prompt-brevity and semantic-preservation law

For copy/migrate/port/replace/sync/merge/refactor/rewrite work, explicitly classify every applicable axis:

```text
INTERFACE_COMPATIBILITY
DATA_AND_STATE_SEMANTICS
CONTROL_FLOW_AND_DECISION_LOGIC
FAILURE_AND_RECOVERY_SEMANTICS
LIFECYCLE_AND_CONCURRENCY
SIDE_EFFECT_AND_IDEMPOTENCY
AUTHORITY_AND_PERMISSION
OBSERVABILITY_AND_ERROR_CONTRACT
PERFORMANCE_AND_RESOURCE_BEHAVIOR
```

Compatibility cannot silently substitute for the remaining applicable axes.

Every material source behavior has exactly one disposition:

```text
PRESERVE_EXACT
PRESERVE_OBSERVABLE
ADAPT_WITH_COMPATIBILITY
INTENTIONAL_CHANGE
DEFER_EXPLICIT
DROP_EXPLICIT
UNKNOWN_BLOCKING
```

`UNMAPPED`, implicit drop and assumed-irrelevant are forbidden terminal states. `INTENTIONAL_CHANGE`, `DEFER_EXPLICIT`, `DROP_EXPLICIT`, and explicit scope reduction require a decision record from an admitted authority/source.

## Case-basis enumeration

Where relevant enumerate over:

```text
Actor × Entry Point × Preconditions × Lifecycle State × Input Class × Authority
× Ordering/Timing × Concurrency × Dependency State × Resource Pressure
× Source Version × Target Version × Side-Effect Outcome × Recovery Path
```

Retain every generated member as one of:

```text
REQUIRED_CASE
INVALID_INPUT_CASE
IMPOSSIBLE_BY_INVARIANT
OUT_OF_SCOPE_EXPLICIT
DUPLICATE_EQUIVALENCE_CLASS
UNKNOWN_BLOCKING
```

Use exhaustive enumeration for critical bounded spaces. Large spaces may use declared pairwise/covering-array, property-based, fuzz, model-based, fault-injection, differential or mutation strategies; denominator accounting remains explicit.

## Shadow Architecture monitor

Base delta classes remain:

```text
ASSUMPTION_DELTA
STATE_DELTA
AUTHORITY_DELTA
OWNERSHIP_DELTA
LIFECYCLE_DELTA
CONCURRENCY_DELTA
RESOURCE_DELTA
EXTERNAL_SIDE_EFFECT_DELTA
FAILURE_SURFACE_DELTA
EVIDENCE_DELTA
PROCEDURAL_GROUNDING_DELTA
```

ICPG adds:

```text
INTENT_INTERPRETATION_DELTA
SCOPE_REDUCTION_DELTA
USE_CASE_DELTA
EDGE_CASE_DELTA
SEMANTIC_PARITY_DELTA
CASE_COVERAGE_DELTA
CASE_ORACLE_DELTA
SOURCE_BEHAVIOR_DISPOSITION_DELTA
```

At each material delta ask:

```text
What became newly possible?
What must now remain true?
How would we know it is false?
Which intent/source behavior made this path necessary?
Which case covers it?
Which semantic axis changed?
Which oracle can detect its loss?
Did the implementation silently narrow scope?
```

Intervention remains:

```text
L0 OBSERVE
→ L1 WARN
→ L2 REVIEW
→ L3 BLOCK
```

Use L2 for missing required case/oracle or unauthorized semantic narrowing. Use L3 at a material boundary for unresolved `UNKNOWN_BLOCKING`, implicit source-logic drop, critical case without oracle, authority widening, destructive/security-sensitive unbound behavior, or false coverage/evidence promotion.

## Mandatory checkpoints

```text
SKILL_DISCOVERY when external/retrieved procedures are material
ARCHITECTURE_CHOICE
FIRST_VERTICAL_SLICE
PERSISTENCE_INTRODUCED
ASYNC_OR_CONCURRENCY_INTRODUCED
EXTERNAL_INTEGRATION_INTRODUCED
NOVELTY_OR_DIVERGENCE
FIRST_GREEN
BEFORE_COMMIT when critical procedure/case proof owns eligibility
BEFORE_PR_OR_PUBLICATION
CI_OR_RUNTIME_FAILURE_WITH_DESIGN_IMPACT
```

At `FIRST_GREEN`, green code paths remain green for their bound subject but do not erase untested failure states, missing source behaviors, orphan cases, unexercised runtime lanes or case-oracle gaps. `BEFORE_PR_OR_PUBLICATION` recomputes ICPG coverage against current implementation/evidence.

## Machine contracts

System contract:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_system_contract.py \
  check path/to/system-contract.json
```

Case graph:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_case_graph.py \
  check path/to/case-graph.json
```

Both use `0` for admitted contract closure, `2` for checked semantic/contract failure and `64` for missing/malformed input where supported. A checker does not prove referenced external evidence is truthful.

## Migration semantic-loss canary

The #408 fixture requires this defect to turn red:

```text
source decision branch B exists
→ candidate removes B
→ interface compatibility remains green
→ semantic-parity / case-graph oracle turns red
```

If this defect cannot be distinguished, migration completeness is not proven.

## Tech Lead and data-flow composition

When `agentic-tech-lead-orchestration` is selected:

```text
ICPG exact subject + digest
→ architecture invariants + required-case obligations
→ typed task contracts
→ true dependency DAG
→ path/resource/interface leases
→ bounded Workers
→ independent result oracles
→ one convergence owner
→ global objective + case coverage reconciliation
```

Every required case has one implementation owner or one explicit convergence owner. A Worker/task PASS cannot close global case coverage by itself.

Case dependency is not automatically Git ancestry. A true Git Town child exists only when it consumes a parent's unmerged bytes/contracts. Path-disjoint work remains sibling work.

## #407 issue / implementation DAG

```text
#407  P0 global objective: Intent–Case–Proof closure
│
├─ #408  CONTRACT/CORE/EVAL
│    case schema + checker + semantic-loss canary
│
├─ #409  MONITOR
│    Shadow intent/case/semantic delta integration
│    consumes #408 contract vocabulary
│
├─ #410  TECH-LEAD / STACK TRACEABILITY
│    case obligations → task DAG → molecular Stack index
│    path ownership determines sibling/child/convergence topology
│
└─ #411  LIVE EVIDENCE
     exact-subject continuous Shadow canary
     not a Git child merely because it is later in process order
```

Current implementation branch:

```text
agent/spatial-intent-case-proof-graph-v1
```

## Molecular terminal implementation plan

| Atom | Issue | Type | Owned responsibility | Stack relation | Proof ceiling now |
|---|---:|---|---|---|---|
| `ICPG-C1` | #408 | `C` | schema/reference contract | root | IMPLEMENTED on branch |
| `ICPG-K1` | #408 | `K` | deterministic semantic checker | same terminal leaf | IMPLEMENTED on branch |
| `ICPG-E1` | #408 | `E` | migration positive + planted mutations | same terminal leaf | IMPLEMENTED, execution pending |
| `ICPG-M1` | #409 | `K/E` | Shadow case-delta monitor | true child of contract semantics | IMPLEMENTED contract text; runtime pending |
| `ICPG-D1` | #410 | `D/K` | Tech Lead/DAG/Molecular Stack integration | sibling or convergence by path lease | PARTIAL |
| `ICPG-X1` | #411 | `X` | live independent Shadow canary | external/live evidence lane | NOT_EXERCISED |

The canonical portable molecular vocabulary and branch laws remain owned by [`../git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md`](../git-town-stacked-pr-worker/references/MOLECULAR_STACK_INDEX.md).

## Directory map

```text
skills/spatial-loop-systems-engineering/
├── AGENTS.md
├── README.md
├── SKILL.md
├── evals.json
├── modes/
│   ├── monitor.md
│   ├── precheck.md
│   └── postmortem.md
├── references/
│   ├── README.md
│   ├── architecture-watch-loop.md
│   ├── intent-case-proof-graph.md
│   ├── case-graph.schema.json
│   ├── procedural-grounding-shadow-plane.md
│   ├── procedural-grounding-receipt.schema.json
│   ├── system-prompt.md
│   ├── system-prompt-monitor-overlay.md
│   ├── system-prompt-recovery-overlay.md
│   ├── three-failure-escalation.md
│   └── spec-packet-template.md
├── modules/
│   ├── README.md
│   ├── agent-host-procedural-grounding.md
│   └── linux-isolation-runtime.md
├── scripts/
│   ├── README.md
│   ├── check_case_graph.py
│   ├── check_procedural_grounding.py
│   └── check_system_contract.py
└── tests/
    ├── run-all.sh
    ├── architecture-watch/verify.sh
    ├── case-graph/
    │   ├── verify.py
    │   ├── verify.sh
    │   └── fixtures/good.json
    ├── procedural-grounding/**
    ├── universal-entry/verify.sh
    ├── recovery-escalation/verify.sh
    ├── refactor-proof/**
    └── system-contract/**
```

## Coverage and evidence boundary

Report these separately:

```text
Intent Coverage
Source Behavior Disposition Coverage
Required Case Coverage
Implementation Binding Coverage
Oracle Coverage
Executed Evidence Coverage
Unknown Blocking Count
```

Current repository/branch evidence classes:

```text
monitor-first operating contract                   IMPLEMENTED
Shadow Architecture architecture deltas            IMPLEMENTED
Intent–Case–Proof reference/schema/checker          IMPLEMENTED_ON_BRANCH
migration semantic-loss mutation controls           IMPLEMENTED_ON_BRANCH / NOT_EXERCISED_BY_CI_YET
Shadow intent/case delta contract                    IMPLEMENTED_ON_BRANCH
Tech Lead case-DAG consumption                      PARTIAL / #410
Git Town README/index integration                    PARTIAL / #410
live continuous Shadow Architect runtime             NOT_EXERCISED / #411
matched live model/runtime refactor A/B              NOT_IMPLEMENTED
physical Linux isolation behavior                   NOT_EXERCISED
real hardware performance                           NOT_EXERCISED
model-weight/private-reasoning introspection        OUT_OF_SCOPE
security or production acceptance                   HUMAN_ADMIT_REQUIRED
```

Run all owning deterministic controls with:

```bash
bash skills/spatial-loop-systems-engineering/tests/run-all.sh
```

A green suite proves only the checked repository bytes and declared deterministic fixtures. It does not establish universal edge-case discovery, all real-world unknown unknowns, continuous live Shadow monitoring, external provider behavior, physical substrate behavior, production safety or Human acceptance.
