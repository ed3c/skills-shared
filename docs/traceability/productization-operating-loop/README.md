# Productization Operating Loop — implementation preflight

Owner: `#421`  
Target milestone: `PRODUCTIZATION_PREIMPLEMENTATION_READY`

This directory freezes the implementation plan for a thin composition method. It does not implement `skills/productization-operating-loop/` yet and does not upgrade any market, user, paid, provider, rights, merge or release lane.

## Method composition

```text
source discovery / research
  unknown-discovery-composer + dr-research-loop + truth-verify-loop
        ↓
product mechanism / job / closure
  product-reverse-engineering-loop
        ↓
bounded MVP
  dr-to-mvp
        ↓
independent closure review
  procedural-shadow-runtime
        ↓
execution decomposition
  agentic-tech-lead-orchestration
        ↓
Stack / delivery
  git-town-stacked-pr-worker + dual-forge-repository-loop
        ↓
new-repo adoption
  shared-skills-infra
```

The Productization loop owns the transitions between these methods plus the missing market, adoption, commercial and policy-drift contracts. It does not copy their bodies.

## Target State Machine

```text
REQUEST_BOUND
→ CONTROL_AND_AUTHORITY_BOUND
→ SOURCE_AND_POLICY_BOUND
→ MARKET_ARENA_BOUND
→ USER_SCENARIOS_BOUND
→ COMPARATOR_CASES_BOUND
→ DIFFERENTIATION_WEDGE_BOUND
→ COMMERCIAL_FRICTION_BOUND
→ CAPABILITY_AND_RIGHTS_BOUND
→ MVP_AND_STOP_LOSS_BOUND
→ SHADOW_CLOSURE_AUDITED
→ ISSUE_AND_SESSION_DAG_BOUND
→ BUILD_OR_EXPERIMENT_RUNNING
→ OUTCOME_READ_BACK
→ PRESERVE | NARROW | ITERATE | KILL
```

## Start-readiness DAG

```text
#421 POL-0 preparation
├─ #432 POL-R predecessor reconciliation ─────────────────────┐
└─ #422 POL-C0 portable composition contract                 │
    ├─ #423 POL-M market/comparator          ┐               │
    ├─ #424 POL-U user/adoption              ├─ siblings     │
    ├─ #425 POL-B commercial friction        │               │
    └─ #426 POL-P policy drift               ┘               │
                     │                                       │
                     └────────────→ #427 POL-K compiler      │
                                          │                  │
                                          └→ #428 POL-E      │
                                                │            │
                                   #432 ─────────┴→ #429 POL-D
                                                     │
                                                     ├→ #430 POL-A bootstrap
                                                     └→ KAW #135 carrier
                                                            │
                                            #430 + KAW evidence + #366
                                                            ↓
                                                     #431 POL-LIVE
```

`#432`, KAW `#135`, and `#431` are process/evidence dependencies, not Git parents unless future concrete branches consume unmerged bytes.

## Completion-readiness DAG

```text
C0 receipt
+ M/U/B/P receipts
→ K deterministic replay receipt
→ E complete mutation/Shadow denominator
+ R current Product Reverse reconciliation receipt
→ D route/prompt/trace convergence receipt
→ admitted method identity
→ A bootstrap-profile receipt
+ KAW carrier receipt where selected
+ generic real-consumer bootstrap evidence (#366 or successor)
→ LIVE bounded user/payment experiment
→ outcome foldback
```

Later receipts cannot be substituted with earlier-lane PASS.

## Planned directory ownership

```text
skills/productization-operating-loop/
├── AGENTS.md / README.md / SKILL.md           # POL-D
├── references/
│   ├── core/                                  # POL-C0
│   ├── market/                                # POL-M
│   ├── user/                                  # POL-U
│   ├── commercial/                            # POL-B
│   ├── policy/                                # POL-P
│   └── session/                               # POL-K
├── scripts/                                   # POL-K
├── tests/ / evals/ / cases.json / evals.json # POL-E
├── modules/                                   # POL-D
└── prompts/                                   # POL-D

skills/shared-skills-infra/**                  # POL-A only after admission
kotlin-auto-webview consumer paths             # KAW #135, external repo
```

## Parallel Session division

After `POL-C0` is readable, launch four independent sessions:

```text
Session M → market/comparator/wedge
Session U → user/adoption/friction
Session B → pricing/value/sales-friction
Session P → official-policy/freshness/retest
```

Do not create child Stack ancestry between M/U/B/P. `POL-K` is the first consumer of all four admitted artifacts.

## Data flow

```text
Article / PDF / Repo / official docs / CodexDoc / GitHub
→ source identity + evidence ceiling
→ Product Reverse job/pain/mechanism signals
→ M market/comparator
→ U user/adoption
→ B commercial friction
→ P policy drift
→ K Productization program + Session DAG
→ E independent Shadow/evals
→ D zero-context prompts + trace routes
→ Tech Lead molecular implementation / experiment packets
→ consumer repo + KAW carrier + external providers
→ exact receipts
→ user / payment outcome
→ PRESERVE | NARROW | ITERATE | KILL
```

## External projections

```text
canonical Git subject / receipt
→ projection request
→ CodexDoc / Google Doc / Sheet external ID + revision
→ write/read-back/export digest
→ backlink to canonical Git subject
```

External projection is never source, implementation, user, paid, merge or release authority.

## Current states

```text
POL-0 #421        PREPARATION_ACTIVE
POL-C0 #422       READY_TO_START_AFTER_PREP
POL-M/U/B/P       BLOCKED_ON_C0_INTERFACE
POL-K             BLOCKED_ON_STAGE1
POL-E             BLOCKED_ON_K
POL-D             BLOCKED_ON_C0/M/U/B/P/K/E/R
POL-A             BLOCKED_ON_ADMITTED_METHOD_AND_BOOTSTRAP_WRITER
POL-R #432        READY_TO_START
KAW #135          PROCESS_DEPENDENCY / BLOCKED_ON_PORTABLE_INTERFACE
POL-LIVE #431     EXTERNAL_EVIDENCE / BLOCKED
POL-T #433        PREP_VERIFIER
```

## Evidence ceiling

Preparation artifacts can prove ownership, routing, dependency and refusal completeness. They cannot prove the new portable Skill exists, a market is attractive, a user will switch, anyone will pay, a policy is legally sufficient, KAW/provider/runtime behavior, merge/release or production readiness.
