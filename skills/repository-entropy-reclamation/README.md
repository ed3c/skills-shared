# `repository-entropy-reclamation`

Evidence-first, cross-language method for discovering and safely removing accidental repository complexity without treating scanner output, file count, line count, or model opinion as deletion authority.

Status: `SHARED_METHOD_ADMITTED_ON_MAIN / GENERAL_CONSUMER_DELETION_NOT_CLAIMED`.

## Read order

1. [`AGENTS.md`](AGENTS.md) — Agent authority, writer, Shadow, and completion rules.
2. [`SKILL.md`](SKILL.md) — portable entropy-reclamation procedure.
3. [`references/entropy-audit.schema.json`](references/entropy-audit.schema.json) — exact audit packet shape.
4. [`references/UPSTREAM_LINEAGE.md`](references/UPSTREAM_LINEAGE.md) — immutable upstream method lineage and exclusions.
5. [`modules/domain-profile.md`](modules/domain-profile.md) — trigger-selected repository/language/framework bindings.
6. [`scripts/assert_entropy_audit.py`](scripts/assert_entropy_audit.py) — deterministic schema/semantic gate.
7. [`tests/run-all.sh`](tests/run-all.sh) and [`tests/test_assert_entropy_audit.py`](tests/test_assert_entropy_audit.py).
8. [`../universal-refactor-controller/README.md`](../universal-refactor-controller/README.md) for the admitted thin composition and bounded canaries.
9. [`../skill-refactor-proof-loop/README.md`](../skill-refactor-proof-loop/README.md) when the cut materially changes a Skill or repository contract.
10. [`../agentic-tech-lead-orchestration/README.md`](../agentic-tech-lead-orchestration/README.md), [`../procedural-shadow-runtime/README.md`](../procedural-shadow-runtime/README.md), and [`../git-town-stacked-pr-worker/README.md`](../git-town-stacked-pr-worker/README.md) for orchestration, independent review, and delivery.
11. Current issue/PR/workflow/receipt subjects.

## Directory → State Machine ownership

```text
skills/repository-entropy-reclamation/
├── AGENTS.md
│   └── Agent read order, Tech Lead/Shadow roles, writer laws, evidence ceiling
├── README.md
│   └── directory map, State Machines, DAG, data flow, terminal Stack index
├── SKILL.md
│   └── portable REQUEST → PROOF → SHADOW → CUT → VERIFY → HANDOFF law
├── references/
│   ├── entropy-audit.schema.json
│   ├── example-audit.json
│   └── UPSTREAM_LINEAGE.md
│       └── packet contract, positive treatment, and source-proposal lineage
├── modules/
│   ├── README.md
│   └── domain-profile.md
│       └── trigger-selected consumer/language/framework/policy ports
├── scripts/
│   ├── README.md
│   └── assert_entropy_audit.py
│       └── deterministic shape + semantic admission State Machine
└── tests/
    ├── README.md
    ├── run-all.sh
    └── test_assert_entropy_audit.py
        └── positive, hollow, mutation, and fault controls
```

Markdown routes. Schema/checker/tests decide deterministic contract state. Consumer repositories own actual code/runtime evidence.

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

`AUDIT_COMPLETE` is valid when no safe cut survives. Running the Skill does not create an obligation to delete.

## Candidate proof DAG

```text
exact subject + nearest instructions
        ↓
contract boundary inventory
        ↓
broad entropy survey
        ↓
candidate
├─ production/non-production/ambiguous consumers
├─ static + dynamic/generated/persisted/compatibility evidence
├─ history/rationale/ownership evidence
├─ lifecycle/trust/accessibility/data-loss evidence
├─ capability effect
└─ conceptual reduction versus replacement burden
        ↓
REJECT / KEEP / HUMAN_ADMIT / SHADOW_ELIGIBLE
        ↓
independent Shadow contradiction + global-objective review
        ↓
one ownership-boundary implementation
        ↓
decisive + broad + residue + global checks
        ↓
verified result / rollback / Local Handoff
```

A scanner is a candidate producer, never deletion authority.

## Molecular implementation DAG — #386/#403

```text
C  #387 contract/schema/source lineage
├─ K  #388 deterministic semantic gate
│   └─ E  #390 positive + mutation/fault controls
└─ A  #389 domain ports/adapters
     \                         /
      \                       /
       └────── X #391 convergence
               registry + CI + shared routes
               ↓
             D #403 / PR #404 Agent routes and traceability
               ↓ rebuilt on current governance
             UCR #398 / PR #477 checked current-main admission
```

Terminal publication state:

| Atom | PR | Terminal classification | Current authority |
|---|---:|---|---|
| C | #387 | `CLOSED_UNMERGED / CONSUMED` | contract bytes present through later landing |
| K | #388 | `CLOSED_UNMERGED / CONSUMED` | checker blob matches current main |
| A | #389 | `CLOSED_UNMERGED / CONSUMED` | domain-profile blob matches current main |
| E | #390 | `CLOSED_UNMERGED / CONSUMED` | control suite present and routed by current CI |
| X | #391 | `CLOSED_UNMERGED / SUPERSEDED` | shared registry/CI bytes rebuilt for current governance |
| D | #404 | `CLOSE_AFTER_CURRENT_DOC_LANDING` | this nearest README/AGENTS is the corrected current projection |
| Admission | #477 | `MERGED / HUMAN_ADMITTED` | entropy method + UCR/registry/CI on merge `2bf90d7182d42dfc3a908ffa68d7ea4b26898042` |

Closed-unmerged does not mean individually merged. It preserves Molecular provenance while removing duplicate merge authority.

## End-to-end data flow

```text
article / issue / user request / observed repository pain
→ SOURCE_PROPOSAL
→ exact repository commit/tree + instructions
→ boundary inventory
→ analyzer/search/history/runtime evidence
→ entropy audit packet
→ schema + semantic assertion
→ Tech Lead candidate/dependency DAG
→ independent Shadow on same subject
→ admitted ownership-boundary cut
→ exact diff/source/test/runtime readback
→ residue + global-objective reconciliation
→ verified receipt
→ Molecular Stack or Local Handoff Queue
→ Human merge/release authority
```

For a material refactor:

```text
entropy candidate
→ skill-refactor-proof treatment freeze
→ old strengths + route + contract + matched proof
→ Complexity Delta
→ admitted result or rollback
```

## Current admitted scope

The shared method was admitted in `registry.json` on 2026-08-18. The UCR current-main landing PR #477 admitted the entropy method, registry/entry route, Skill Suites arrival, and one bounded ordinary-repository/Skill transfer line.

```text
portable method/schema                       ADMITTED_ON_MAIN
semantic gate + mutation controls            ADMITTED_AND_CI_ROUTED
domain decoupling                            ADMITTED_ON_MAIN
nearest Agent/README/Stack traceability      THIS_CURRENT_DOC_CANDIDATE
bounded UCR transfer canaries                REMOTE_BOUNDED_EVIDENCE
arbitrary consumer safe deletion             NOT_CLAIMED
unseen language/framework adoption           NOT_EXERCISED
real local Git Town worktree/sync            NOT_EXERCISED
live provider/model uplift                   NOT_EXERCISED
release/production                           NOT_PERFORMED
```

A bounded canary does not prove every repository is safe to simplify.

## Local Handoff boundary

When decisive proof needs a real checkout, compiler/index, runtime, device, provider session, Git Town/Forgejo, secret-bearing host, or Human decision:

```text
exact admitted subject
→ asserted Local Handoff Queue
→ one ACTIVE item
→ materialized bounded command contract
→ durable receipt + cleanup
→ independent readback
→ next item or blocked Human handoff
```

Queue validation proves the continuation contract, not execution.
