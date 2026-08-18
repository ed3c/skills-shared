# `repository-entropy-reclamation`

Evidence-first, cross-language method for discovering and safely removing accidental repository complexity without treating scanner output, file count, line count, or model opinion as deletion authority.

## Read order

1. [`AGENTS.md`](AGENTS.md) — Agent authority, writer, Shadow and completion rules.
2. [`SKILL.md`](SKILL.md) — portable entropy-reclamation procedure.
3. [`references/entropy-audit.schema.json`](references/entropy-audit.schema.json) — exact audit packet shape.
4. [`references/UPSTREAM_LINEAGE.md`](references/UPSTREAM_LINEAGE.md) — immutable upstream method lineage and exclusions.
5. [`modules/domain-profile.md`](modules/domain-profile.md) — trigger-selected repository/language/framework bindings.
6. [`scripts/assert_entropy_audit.py`](scripts/assert_entropy_audit.py) — deterministic schema/semantic gate.
7. [`tests/run-all.sh`](tests/run-all.sh) and mutation controls.
8. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) when the cut is itself a material refactor.
9. [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md), [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md), and [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md) for orchestration, independent review and delivery.
10. Exact issue/PR/workflow/receipt subjects.

## Directory → State Machine ownership

```text
skills/repository-entropy-reclamation/
├── AGENTS.md
│   └── Agent read order, Tech Lead/Shadow roles, writer laws, evidence ceiling
├── README.md
│   └── directory map, State Machines, DAG, data flow, Stack index and current handoff
├── SKILL.md
│   └── portable REQUEST → PROOF → SHADOW → CUT → VERIFY → HANDOFF law
├── references/
│   ├── entropy-audit.schema.json
│   ├── example-audit.json
│   └── UPSTREAM_LINEAGE.md
│       └── exact packet contract, positive treatment and source-proposal lineage
├── modules/
│   └── domain-profile.md
│       └── trigger-selected consumer/language/framework/policy ports
├── scripts/
│   └── assert_entropy_audit.py
│       └── deterministic shape + semantic admission state machine
└── tests/
    ├── run-all.sh
    └── test_entropy_audit.py
        └── positive, hollow and mutation/fault controls
```

The directories have different authority. Markdown describes routing; schema/checker/tests decide deterministic contract state; consumer repositories own actual code/runtime evidence.

## Primary State Machine

```text
REQUEST_BOUND
→ EXACT_SUBJECT_AND_INSTRUCTIONS_BOUND
→ CONTRACT_BOUNDARIES_CLASSIFIED
→ ENTROPY_SURVEYED
→ CANDIDATES_PROVED_OR_REJECTED
→ INDEPENDENT_SHADOW_REVIEWED
    ├── HOLD
    ├── REJECT
    ├── HUMAN_ADMIT_REQUIRED
    └── IMPLEMENTATION_ELIGIBLE
→ ONE_OWNERSHIP_BOUNDARY_APPLIED_END_TO_END
→ DECISIVE_CHECK
→ BROAD_GATES
→ RESIDUE_SEARCH
→ GLOBAL_OBJECTIVE
→ IMPLEMENTATION_VERIFIED
→ STACK_OR_LOCAL_HANDOFF
```

`AUDIT_COMPLETE` is a valid terminal state when no safe cut survives evidence and Shadow review. A repository is not required to delete something merely because the Skill ran.

## Candidate proof DAG

```text
exact subject + nearest instructions
        ↓
contract boundary inventory
        ↓
broad entropy survey
        ↓
┌──────────────────────────────────────────────────────┐
│ candidate                                            │
│  ├─ symbol/path/config/wire searches                 │
│  ├─ production/non-production/ambiguous consumers    │
│  ├─ dynamic/generated/persisted/compatibility proof  │
│  ├─ history/rationale/ownership proof                │
│  ├─ lifecycle/trust/accessibility/data-loss proof    │
│  ├─ capability effect                                │
│  └─ conceptual reduction vs replacement burden       │
└──────────────────────────────────────────────────────┘
        ↓
REJECT / KEEP / HUMAN_ADMIT / SHADOW_ELIGIBLE
        ↓
independent Shadow contradiction + global-objective review
        ↓
one ownership-boundary implementation task
        ↓
decisive check + broad gates + residue + global objective
        ↓
verified result / rollback / Local Handoff
```

A static analyzer is only a candidate producer. It never has an edge directly to deletion or `PASS`.

## Tech Lead task DAG

```text
C  contract/schema/source lineage
├─ K  deterministic semantic gate
│   └─ E  positive + mutation/fault controls
└─ A  trigger-selected domain ports/adapters
     \                         /
      \                       /
       └────── X convergence ┘
               registry + CI + shared machine routes
               ↓
             D docs/Agent routes/Stack traceability
```

Git ancestry follows consumed unmerged bytes, not convenient chronology:

```text
C → K → E
C → A
E + A → X     explicit multi-parent convergence
X → D         documentation consumes the converged route/index facts
```

`A` and `K/E` are siblings after `C` because the adapter and deterministic checker own path-disjoint implementation surfaces. `X` is the only convergence owner.

## End-to-end data flow

```text
article / issue / user request / observed repository pain
→ SOURCE_PROPOSAL classification
→ exact repository commit/tree + instructions
→ boundary inventory
→ analyzer/search/history/runtime evidence
→ entropy audit packet
→ deterministic schema/semantic assertion
→ Tech Lead candidate and dependency DAG
→ independent Shadow review on same immutable subject
→ admitted ownership-boundary cut
→ exact diff/source/test/runtime readback
→ residue + global-objective reconciliation
→ verified receipt
→ molecular Stack or Local Handoff Queue
→ Human merge/release authority
```

For a material Skill refactor, the flow composes with `skill-refactor-proof-loop`:

```text
entropy finding
→ safe cut candidate
→ A OLD_CANONICAL / B0 REFACTOR_AS_LANDED / B1+ REPAIRED_CANDIDATE
→ old-strength + route + contract + hermetic matched proof
→ complexity reduction result
```

The entropy Skill decides whether complexity is removable; the refactor-proof Skill proves the retained behavior/strengths. Neither substitutes for the other.

## Molecular implementation Stack — issue #386

Provider state observed during the current integration line:

| Atom | Issue / PR | Branch relation | Owns | Current ceiling |
|---|---|---|---|---|
| `C` | #386 / PR #387 | root from `main` | portable `SKILL.md`, audit schema/example, upstream lineage | contract bytes frozen; no live consumer deletion |
| `K` | #386 / PR #388 | true child of #387 | deterministic `assert_entropy_audit.py` core | local semantic gate evidence |
| `A` | #386 / PR #389 | sibling of K, child of #387 | domain ports/profile | routing/monotonicity contract only |
| `E` | #386 / PR #390 | true child of #388 | positive/hollow/mutation controls | deterministic falsification evidence |
| `X` | #386 / PR #391 | explicit convergence over E + A | registry, entry route, CI arrival, third-party notice | integration definition; draft/provider state is not merge/live consumer proof |
| `D` | #403 / current branch | true child of X | `AGENTS.md`, this README, Git Town Stack index | documentation/traceability only |

Open PR heads remain provider-read mutable state and are not embedded as durable SHA receipts here. Read current PR metadata before execution or merge decisions.

## Universal refactor continuation

Issue #398 tracks the next abstraction layer: a thin capability-preserving universal refactor controller. It composes this Skill with `skill-refactor-proof-loop` rather than replacing either.

Current leaves:

```text
#399 UCR-C   controller + Complexity Delta contract
#400 UCR-K/E executable composition gate + false-simplification controls
#401 UCR-A   SkillTargetAdapter + RepositoryTargetAdapter
#402 UCR-LIVE one Skill + one ordinary-repository matched golden canary
```

That program remains separate from #386. The existence of those issues is not evidence that universal cross-domain refactoring already works.

## Evidence ceiling and unresolved closure lanes

```text
portable entropy method/schema                 IMPLEMENTED on integration Stack
semantic gate + mutation controls              DETERMINISTIC EVIDENCE
method/domain decoupling                       IMPLEMENTED
Agent/README/Stack traceability                IMPLEMENTED on #403 branch
consumer repository safe deletion              NOT_EXERCISED
cross-language live adoption                    NOT_EXERCISED
capability-preserving universal controller      NOT_IMPLEMENTED / #398-#402
real local Git Town worktree/sync execution     NOT_EXERCISED / #234 owns live delivery class
live model/provider uplift                      NOT_EXERCISED
merge/release/production                        HUMAN_ADMIT_REQUIRED
```

Do not collapse these lanes. A green deterministic audit packet cannot prove a real deletion, and a merged method PR cannot prove an unseen consumer is safe to simplify.

## Local Handoff boundary

When a required proof needs a real checkout, runtime, compiler/index, provider session, device, Forgejo, Git Town, secret-bearing host or Human decision unavailable to the current Agent:

```text
current exact subject
→ validated Tech Lead Local Handoff Queue
→ one ACTIVE item
→ exact runtime/command lane
→ durable receipt + cleanup
→ next item or blocked Human handoff
```

Queue validation proves the continuation contract only. It does not prove the command executed.
