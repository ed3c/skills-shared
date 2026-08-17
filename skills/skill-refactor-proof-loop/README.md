# `skill-refactor-proof-loop`

Portable proof-carrying procedure for refactoring a Skill without losing old behavior, executable routes, evidence ceilings, or delivery authority. The generalized procedure lives here; concrete golden proofs remain in their owning Skills and are referenced through a content-bound registry.

The first golden proof is the `agentic-tech-lead-orchestration` refactor:

```text
PR #308  reachability + executable causal-DAG repair
└─ PR #315 matched production-shaped hermetic real-task proof
```

The proof implementation remains under `../agentic-tech-lead-orchestration/tests/`. This Skill does not copy or fork it.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. [`references/README.md`](references/README.md)
4. [`references/refactor-proof-contract.schema.json`](references/refactor-proof-contract.schema.json)
5. [`references/golden-proof-registry.json`](references/golden-proof-registry.json)
6. [`modules/README.md`](modules/README.md), then only the selected golden/domain module
7. [`scripts/README.md`](scripts/README.md)
8. [`tests/README.md`](tests/README.md)
9. exact issue, PR base/head, workflow and evidence subject

## Directory map → state ownership

```text
skills/skill-refactor-proof-loop/
├── AGENTS.md
│   └── mandatory Agent read order, writer leases and authority boundary
├── README.md
│   └── navigation, current integration state, State Machine, DAG and data flow
├── SKILL.md
│   └── portable transition law and stop conditions
├── cases.json
│   └── deterministic proof-case inventory
├── references/
│   ├── refactor-proof-contract.schema.json
│   │   └── treatment, layer, matched-task and authority shape
│   ├── golden-proof-registry.schema.json
│   │   └── canonical golden-proof entry shape
│   ├── golden-proof-registry.json
│   │   └── content-bound proof identities and evidence ceilings
│   └── COMPLETION_REPORT.template.md
│       └── handoff fields; never a verifier
├── modules/
│   └── agentic-tech-lead-golden-proof.md
│       └── selected instance pointing to the original proof owner
├── scripts/
│   ├── check_refactor_proof.py
│   │   └── contract semantics and layer monotonicity
│   └── check_golden_proof_registry.py
│       └── path/blob/runner/denominator/authority registry assertions
└── tests/
    ├── run-all.sh
    └── selftest.py
        └── positive, hollow and mutation controls
```

## State machine

```text
REFRACTOR_PROPOSED
→ OLD_BEHAVIOR_FROZEN
→ TREATMENTS_FROZEN
→ OLD_STRENGTHS_BOUND
→ ROUTES_ASSERTED
→ CONTRACTS_ASSERTED
→ HERMETIC_TASK_EXECUTED
→ DENOMINATOR_RECONCILED
→ GOLDEN_PROOF_REGISTERED
→ ADOPTION_READY
    ├── higher layer absent/not exercised → LIVE_AB_PENDING
    └── matched live receipts             → LIVE_AB_VERIFIED
→ DELIVERY_EVIDENCE_BOUND
→ HUMAN_ADMIT_REQUIRED
```

Fail-closed terminals include:

```text
BLOCKED_MISSING_TREATMENT
BLOCKED_OLD_STRENGTH_LOST
BLOCKED_DEAD_ROUTE
BLOCKED_UNFAIR_COMPARISON
BLOCKED_DENOMINATOR_ERASURE
BLOCKED_EVIDENCE_PROMOTION
BLOCKED_RESIDUE
BLOCKED_AUTHORITY_WIDENING
```

## Proof layers

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A proof declares its highest achieved layer. Every higher layer remains explicit; no prose, package presence, fixture, old SHA, or successful lower-layer test can promote it.

## Work DAG

```text
freeze old/as-landed treatments
├─ structural reachability assertions
├─ executable contract + receipt causality
├─ matched hermetic real-task canary
└─ registry/documentation binding
      └─ one traceability convergence owner

matched live model/runtime A/B
├─ live scheduler receipts
├─ independent Shadow/global-objective receipts
├─ exact-subject code-intelligence/executor receipts
└─ Git Town/dual-forge delivery receipts
      └─ Human merge/release admission
```

The first four L0-L3 leaves may be siblings when path-disjoint. A child edge exists only when it consumes an unmerged schema, checker, or proof artifact from its parent. Central registry/index updates have one convergence owner.

## Data flow

```text
old canonical bytes + refactor-as-landed bytes + repaired candidate bytes
        ↓ freeze and content bind
protected old strengths + route graph + semantic contracts
        ↓ deterministic assertions
same base/tree + contracts + immutable tests + budget + carrier
        ↓ matched hermetic execution
local/global oracles + attempts + denominator + cleanup
        ↓ golden registry admission
optional matched live scheduler/Shadow/provider/delivery receipts
        ↓ external Human/trusted authority
merge / release / rollback
```

## Current integration state

```text
Tech Lead L0 source freeze             PASS
Tech Lead L1 structural reachability   PASS
Tech Lead L2 executable contract       PASS
Tech Lead L3 hermetic real task        PASS on exact PR #315 suite subject
Tech Lead L4 matched live runtime       NOT_EXERCISED
Tech Lead L5 delivery/Human Admit       HUMAN_ADMIT_REQUIRED
```

For the matched deterministic carrier, A, B1 and B2 produce equivalent final bytes. B0 is blocked by an absent dispatch route. B2 improves receipt-gated causal and evidence closure; it does not establish live model/provider quality uplift.

Open live owners remain issue #312 Phase 2 and issues #231, #232, #234 and #256.

## Local verification

```bash
python3 scripts/check_refactor_proof.py \
  --contract references/example-refactor-proof.json

python3 scripts/check_golden_proof_registry.py \
  --registry references/golden-proof-registry.json

bash tests/run-all.sh
```

A green suite proves this portable contract and the registered L3 golden proof remain connected to current repository bytes. It does not prove live providers, model quality, Git Town/Forgejo delivery, merge, release or production.
