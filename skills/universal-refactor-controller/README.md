# `universal-refactor-controller`

Thin composition layer for capability-preserving complexity reduction across Skills and ordinary repositories. It does not replace the mechanisms owned by `repository-entropy-reclamation`, `skill-refactor-proof-loop`, `agentic-tech-lead-orchestration`, `procedural-shadow-runtime`, or `git-town-stacked-pr-worker`.

## Current evidence ceiling

The method has bounded cross-domain evidence from one Skill canary and one ordinary-repository canary. That proves the same composition can survive two materially different target classes under the declared oracles. It does **not** prove universal correctness, unseen repositories, production safety, live-model uplift, release, promotion, or rollback.

Current durable states:

```text
UCR-C contract/schema                         IMPLEMENTED
UCR-K/E deterministic composition gate       LOCAL_DETERMINISTIC_VERIFIED
UCR-A target adapters                         STATIC_CONTRACT_VERIFIED
Skill canary                                  REMOTE_SKILL_SUITE_VERIFIED
ordinary-repository canary                    REMOTE_REPOSITORY_VERIFIED
whole-subject Skill Suites / shared infra     REMOTE_REPOSITORY_CI_VERIFIED
UCR-X/D shared convergence                    REMOTE_INTEGRATION_VERIFIED
current-main landing / PR #477                PR_DRAFT / REVERIFY_CURRENT_MAIN
Golden Refactor promotion                     HOLD_UNMERGED
live provider / production                    NOT_EXERCISED
release / promotion / rollback                HUMAN_ADMIT_REQUIRED
```

The canary ledger under `evals/canaries/` records issue/PR/workflow identities without embedding mutable open PR head SHAs as durable truth. Mutable landing state is read from GitHub; this README records only the stable routing identity.

## Read order

1. [`AGENTS.md`](AGENTS.md) — writer/read-only roles, leases, evidence rules and Human boundary.
2. This README — directory ownership, State Machine, DAG, data flow and current handoff.
3. [`SKILL.md`](SKILL.md) — portable composition law.
4. [`references/controller-contract.schema.json`](references/controller-contract.schema.json) — controller packet contract.
5. [`references/complexity-delta.schema.json`](references/complexity-delta.schema.json) — non-LOC reduction contract.
6. [`modules/target-adapter-contract.md`](modules/target-adapter-contract.md) and `adapters/` — target surface mapping only.
7. [`scripts/assert_controller_gate.py`](scripts/assert_controller_gate.py) — deterministic cross-owner admission gate.
8. `tests/` — positive, hollow and false-simplification controls.
9. [`evals/canaries/golden-refactor-corpus.index.json`](evals/canaries/golden-refactor-corpus.index.json) — bounded canary ledger; entries remain unpromoted while their delivery subjects are open.
10. Exact GitHub issues/PRs for mutable publication state.

## Directory ownership

```text
skills/universal-refactor-controller/
├── AGENTS.md                         Agent procedure and authority boundary
├── README.md                         navigation, State Machine, DAG and current evidence
├── SKILL.md                          portable controller procedure
├── references/
│   ├── controller-contract.schema.json
│   └── complexity-delta.schema.json
├── adapters/
│   ├── skill-target-adapter.json
│   └── repository-target-adapter.json
├── modules/
│   └── target-adapter-contract.md
├── scripts/
│   └── assert_controller_gate.py
├── tests/
│   ├── run-all.sh
│   ├── test_assert_controller_gate.py
│   └── test_golden_refactor_corpus.py
└── evals/canaries/
    ├── README.md
    ├── golden-refactor-corpus.schema.json
    └── golden-refactor-corpus.index.json
```

Authority is deliberately split:

```text
entropy discovery / safe-cut proof      repository-entropy-reclamation
old-strength / treatment proof          skill-refactor-proof-loop
task/capability DAG + convergence       agentic-tech-lead-orchestration
independent contradiction review        procedural-shadow-runtime
branch/PR molecular delivery            git-town-stacked-pr-worker
composition + Complexity Delta          universal-refactor-controller
semantic conflict / merge / release     Human or trusted operator
```

## Controller State Machine

```text
REQUEST_BOUND
→ EXACT_TARGET_BOUND
→ BASELINE_FROZEN
→ CAPABILITIES_AND_OLD_STRENGTHS_BOUND
→ ENTROPY_FINDINGS_ADMITTED
→ ROOT_CAUSE_GRAPH_BOUND
→ CANDIDATE_REFACTORS_BOUND
→ INDEPENDENT_SHADOW_REVIEWED
    ├── HOLD
    ├── REJECT
    ├── HUMAN_ADMIT_REQUIRED
    └── REFACTOR_ELIGIBLE
→ TREATMENTS_FROZEN
→ STRUCTURAL_AND_CONTRACT_PROOF
→ HERMETIC_MATCHED_TASK
→ GLOBAL_OBJECTIVE_ASSERTED
→ COMPLEXITY_DELTA_ASSERTED
→ RESIDUE_AND_REGRESSION_ASSERTED
→ DELIVERY_HANDOFF
→ LIVE_AB_WHEN_CLAIMED
→ HUMAN_ADMIT_REQUIRED
```

A lower evidence lane cannot satisfy a later transition. `PASS` is not the default value for missing work.

## Implementation DAG

The current program is a fan-out/fan-in graph, not a fake linear Stack:

```text
#318 skill-refactor-proof-loop ─┐
#386 entropy method ────────────┼─→ #399 / PR #405  UCR-C
                                │
                                ├─→ #400 / PR #441  UCR-K/E
                                └─→ #401 / PR #442  UCR-A
                                      \           /
                                       \         /
                                        #402 / PR #458  UCR-LIVE
                                           │
                                           ├─ validation PR #461
                                           └─→ #406 / PR #463  UCR-X/D
                                                   │
                                                   └─→ #398 / PR #477  current-main landing
```

PR #477 is deliberately rebuilt on the then-current admitted `main` rather than importing the stale UCR branch ancestry. The landing preserves the independently admitted #375–#379 Tech Lead/Shadow/Codex control-plane bytes and revalidates the combined exact subject before checked-head merge.

Independent support/evidence leaves discovered by the canaries stay outside the semantic ancestry:

```text
skills-shared #459 / PR #460                 entropy fixture CI repair
blackbox-auto-research #62 / PR #63          ordinary-repo canary
blackbox-auto-research #64 / PR #65          baseline Apache-2.0 CI repair
blackbox-auto-research validation PR #66     exact combined canary receipt
```

They are process/evidence dependencies, not permission to rewrite the controller's parent graph.

## Data flow

```text
exact target + target kind
        ↓
SkillTargetAdapter / RepositoryTargetAdapter
        ↓ observable surfaces + stricter constraints only
repository-entropy-reclamation AUDIT
        ↓ admitted finding + root cause + rejected alternatives
frozen capabilities / old strengths / A-B0-B1 treatments
        ↓
independent procedural-shadow-runtime verdict
        ↓
agentic-tech-lead-orchestration task/capability DAG + path leases
        ↓
structural + executable + hermetic proof
        ↓
global objective
        ↓
Complexity Delta
        ↓ strict non-LOC reduction + protected-dimension non-regression
residue/regression search
        ↓
git-town-stacked-pr-worker delivery graph
        ↓
remote receipts / Local Handoff / Human Admit
        ↓
current-main semantic union / exact-head revalidation / checked-head merge
```

Adapters may add constraints or reduce authority. They never decide simplification, hide a consumer, turn missing/live evidence into PASS, or copy consumer mutable state into the portable core.

## Complexity Delta

The decision is not line count. Core dimensions are:

```text
concepts
states
sources_of_truth
ownership_edges
coordination_paths
compatibility_branches
synchronization_paths
runtime_dependencies
policy_authorities
```

At least one frozen `REDUCTION_TARGET` must strictly decrease, protected dimensions must not regress, and added replacement burden must remain below removed burden. Moving the same obligation behind a wrapper, caller fan-out, generated/config layer, adapter, or service is `COMPLEXITY_RELOCATED`.

## Bounded canary evidence

### Skill target

`repository-capability-audit` reduced generic JSON/schema transport maintenance authority from two checker-local implementations to one private helper while retaining checker-specific semantic rules, prefixes, exits, schemas and CLIs. Its exact validation subject passed the repository Skill Suite; the canary also carries a regression that fails if duplicate transport truth returns.

### Ordinary repository target

`blackbox-auto-research` reduced canonical JSON/SHA-256 primitive maintenance authority from two package-local implementations to one private helper. The acceptance oracle independently recomputes pre-refactor canonical bytes and digests using the Python standard library. A validation-only Stack subject passed the repository's full verify workflow after an unrelated baseline license-gate drift was isolated and repaired separately.

These cases remain `HOLD_UNMERGED` in the Golden Refactor corpus. A successful open PR is evidence, not an immutable golden treatment.

## Shadow Architect monitor

Shadow is read-only and evaluates the same immutable subject as Tech Lead. It rejects at least:

```text
LOC_ONLY_SIMPLIFICATION
COMPLEXITY_RELOCATED
SOURCE_OF_TRUTH_ADDED
OWNERSHIP_EDGE_HIDDEN
STATE_RECOMPUTED_IN_MULTIPLE_PLACES
WRAPPER_WITH_EQUAL_OR_GREATER_BURDEN
CAPABILITY_NOT_FROZEN
OLD_STRENGTH_UNBOUND
DYNAMIC_OR_PERSISTED_CONSUMER_UNPROVED
GLOBAL_OBJECTIVE_NOT_EXERCISED
LOWER_EVIDENCE_PROMOTED
SEMANTIC_BLAST_RADIUS_INCREASED_WITHOUT_ADMISSION
DOMAIN_VALUE_IN_PORTABLE_CORE
```

A Shadow conclusion cannot be reused as a writer receipt, and Tech Lead's conclusion cannot be relabelled as independent Shadow evidence.

## Local Handoff

Use Local Handoff when the next required lane cannot be executed in the current subject, for example:

```text
live provider/model runtime
private repository evidence
hardware/device/session-bound verification
production or secret-bearing environment
real Git Town local worktree execution unavailable to the current carrier
Human semantic conflict, merge, release, promotion or rollback admission
```

A handoff records exact subject, required command/oracle, expected receipt, blocker and authority owner. It does not mark the missing lane PASS.

## Completion rule

A repository or Skill refactor is not closed because code became shorter or tests are green. Closure requires exact-subject capability preservation, admitted entropy/root-cause evidence, independent Shadow review, matched proof at the claimed layer, strict non-LOC Complexity Delta, residue/regression proof, and delivery state appropriate to the claim. Unseen domains, live production, release and promotion remain separate claims; merge state is read from the forge rather than inferred from this document.