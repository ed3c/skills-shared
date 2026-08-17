# `skill-refactor-proof-loop`

Portable proof-carrying procedure for refactoring a Skill without losing old behavior, executable routes, evidence ceilings, denominator completeness, or delivery authority. The generalized procedure lives here; concrete golden proofs remain in their owning Skills and are referenced through content-bound registries.

The first golden proof is the `agentic-tech-lead-orchestration` refactor:

```text
PR #308  reachability + executable causal-DAG repair
└─ PR #315 matched production-shaped hermetic real-task proof
   └─ PR #323 portable refactor-proof contract + golden registry
      └─ PR #324 Agent routes + directory State Machines/DAG/data flow
         └─ issue #321 molecular Stack convergence/index branch
```

The proof implementation remains under `../agentic-tech-lead-orchestration/tests/`. This Skill does not copy or fork it.

## Read order

1. [`AGENTS.md`](AGENTS.md)
2. [`SKILL.md`](SKILL.md)
3. [`references/README.md`](references/README.md)
4. [`references/refactor-proof-contract.schema.json`](references/refactor-proof-contract.schema.json)
5. [`references/golden-proof-registry.json`](references/golden-proof-registry.json)
6. [`references/refactor-proof-stack.json`](references/refactor-proof-stack.json)
7. [`evals/proof-standard-admission.json`](evals/proof-standard-admission.json)
8. [`modules/README.md`](modules/README.md), then only the selected golden/domain module
9. [`scripts/README.md`](scripts/README.md)
10. [`tests/README.md`](tests/README.md)
11. exact issue, PR base/head, workflow and evidence subject

## Directory map → State Machine ownership

```text
skills/skill-refactor-proof-loop/
├── AGENTS.md
│   └── mandatory Agent read order, writer leases and authority boundary
├── README.md
│   └── navigation, integration state, State Machine, DAG, data flow and Stack index
├── SKILL.md
│   └── portable transition law and stop conditions
├── cases.json
│   └── deterministic proof-case inventory
├── references/
│   ├── refactor-proof-contract.schema.json
│   │   └── treatment, layer, matched-task and authority shape
│   ├── golden-proof-registry.schema.json
│   ├── golden-proof-registry.json
│   │   └── content-bound proof identities and evidence ceilings
│   ├── refactor-proof-stack.schema.json
│   ├── refactor-proof-stack.json
│   │   └── molecular issue/PR/artifact/evidence graph
│   ├── skill-adoption-ledger.schema.json
│   ├── skill-adoption-ledger.json
│   │   └── per-Skill adoption classifications, evidence paths and gap owners
│   └── COMPLETION_REPORT.template.md
│       └── handoff fields; never a verifier
├── evals/
│   └── proof-standard-admission.json
│       └── the owner decision that made this standard canonical; carries no evidence
├── modules/
│   └── agentic-tech-lead-golden-proof.md
│       └── selected instance pointing to the original proof owner
├── scripts/
│   ├── check_refactor_proof.py
│   │   └── contract semantics and layer monotonicity
│   ├── check_golden_proof_registry.py
│   │   └── path/blob/runner/denominator/authority registry assertions
│   ├── check_refactor_proof_stack.py
│   │   └── true-child, convergence, exact-head-policy and traceability assertions
│   ├── check_skill_adoption_ledger.py
│   │   └── adoption scope, evidence, executability, layer-ceiling and gap-owner assertions
│   └── render_adoption_audit.py
│       └── renders the adoption report from the ledger; --check byte-compares it
└── tests/
    ├── run-all.sh
    ├── selftest.py
    ├── stack_selftest.py
    ├── adoption_selftest.py
    └── render_selftest.py
        └── positive, hollow, mutation, Stack, adoption and report-drift falsifiers
```

## Refactor proof State Machine

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

A proof declares its highest achieved layer. Every higher layer remains explicit; no prose, package presence, fixture, old SHA, open PR, or successful lower-layer test can promote it.

## Work DAG

```text
freeze old/as-landed treatments
├─ structural reachability assertions
├─ executable contract + receipt causality
├─ matched hermetic real-task canary
└─ registry/documentation binding
      └─ one molecular traceability convergence owner

matched live model/runtime A/B
├─ live scheduler receipts
├─ independent Shadow/global-objective receipts
├─ exact-subject code-intelligence/executor receipts
└─ Git Town/dual-forge delivery receipts
      └─ Human merge/release admission
```

The L0-L3 leaves may be siblings when path-disjoint. A Git child edge exists only when it consumes an unmerged schema, checker, treatment, proof, or documentation artifact from its parent. Central registry/index updates have one convergence owner. Process prerequisites and external evidence are recorded without inventing Git ancestry.

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
molecular issue/PR/artifact/evidence graph
        ↓ optional matched live scheduler/Shadow/provider/delivery receipts
external Human/trusted authority
        ↓
merge / release / rollback
```

## Molecular delivery Stack

The canonical machine index is [`references/refactor-proof-stack.json`](references/refactor-proof-stack.json), validated by `scripts/check_refactor_proof_stack.py`.

```text
#307/#309 → PR #308
└─ #312 → PR #315
   └─ #319 → PR #323
      └─ #320 → PR #324
         └─ #321 → agent/321-refactor-proof-stack-index
            └─ #322 cross-Skill adoption audit; standard admitted 2026-08-17,
               ledger and rendered report landed, every gap handed to a leaf
               ├─ #343 agentic-tech-lead-orchestration
               ├─ #344 controlled-technical-language-harness
               ├─ #345 dual-forge-repository-loop
               ├─ #346 forgejo-delivery-loop
               ├─ #347 git-town-stacked-pr-worker
               ├─ #348 github-delivery-loop
               ├─ #349 knowledge-continuity
               ├─ #350 procedural-shadow-runtime
               ├─ #351 repository-capability-audit
               └─ #352 spatial-loop-systems-engineering
```

Open PR heads are deliberately not self-embedded in the same branches; the index records `READ_FROM_GITHUB_PR_METADATA`. A merged node may record an immutable merge SHA only after the state is actually observed. External issues #231, #232, #234 and #256 feed L4/L5 evidence but are not fake Stack children.

## Current integration state

```text
Tech Lead L0 source freeze              PASS
Tech Lead L1 structural reachability    PASS
Tech Lead L2 executable contract        PASS
Tech Lead L3 hermetic real task         PASS on the PR #315 suite subject
Tech Lead L4 matched live runtime       NOT_EXERCISED
Tech Lead L5 delivery/Human Admit       HUMAN_ADMIT_REQUIRED
```

For the matched deterministic carrier, A, B1 and B2 produce equivalent final bytes. B0 is blocked by an absent dispatch route. B2 improves receipt-gated causal and evidence closure; it does not establish live model/provider quality uplift.

Open live owners remain issue #312 Phase 2 and issues #231, #232, #234 and #256.

## Cross-Skill adoption

[`references/skill-adoption-ledger.json`](references/skill-adoption-ledger.json) classifies the ten Skills named by issue #322 against the adoption matrix, and `scripts/check_skill_adoption_ledger.py` replays every classification against current bytes.

```text
10 Skills classified, 100 findings, 68 non-PASS
1 Skill (agentic-tech-lead-orchestration) carries frozen treatments, a matched hermetic task and a registered golden proof
9 Skills reach L2 executable contract: routes, gates and hollow-route controls, but no frozen refactor treatments
0 Skills carry live model/runtime evidence
```

Every gap names an existing owning issue; the checker refuses an owner that is not already known, so the audit cannot invent a duplicate. Gaps whose evidence lane already had an owner stay with it (#231, #232, #234, #256). Every other gap is owned by its Skill's own migration leaf — #343 `agentic-tech-lead-orchestration`, #344 `controlled-technical-language-harness`, #345 `dual-forge-repository-loop`, #346 `forgejo-delivery-loop`, #347 `git-town-stacked-pr-worker`, #348 `github-delivery-loop`, #349 `knowledge-continuity`, #350 `procedural-shadow-runtime`, #351 `repository-capability-audit`, #352 `spatial-loop-systems-engineering` — so no gap is parked on the audit issue that measured it.

[`docs/traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md`](../../docs/traceability/SKILL_REFACTOR_ADOPTION_AUDIT.md) is that ledger rendered for humans by `scripts/render_adoption_audit.py`. It is a generated file: `--check` re-renders and byte-compares it from the suite, so a hand-edited or stale report is a red suite rather than a second source. Opening the remaining migration leaves stays outside this ledger.

The standard the audit applies was admitted for adoption governance in [`evals/proof-standard-admission.json`](evals/proof-standard-admission.json) (`ed3c (repository owner)`, 2026-08-17, subject `main@ce68a05`). That record is a decision: it carries no run, no receipt and no measurement, and it promoted no Skill's proof level. Every state in the ledger stays exactly as measured.

## Local verification

```bash
python3 scripts/check_refactor_proof.py \
  --contract references/example-refactor-proof.json

python3 scripts/check_golden_proof_registry.py \
  --registry references/golden-proof-registry.json

python3 scripts/check_refactor_proof_stack.py \
  --stack references/refactor-proof-stack.json

python3 scripts/check_skill_adoption_ledger.py \
  --ledger references/skill-adoption-ledger.json

python3 scripts/render_adoption_audit.py --check

bash tests/run-all.sh
```

A green suite proves the portable mechanism, registered L3 golden proof, molecular traceability graph, adoption ledger and its rendered report remain connected to current repository bytes. It does not prove live providers, model quality, Git Town/Forgejo execution, merge, release or production.
