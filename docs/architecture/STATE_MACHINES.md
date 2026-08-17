# State machines — skills-shared document, Skill, refactor and publication routing

Detailed Skill Eval/Evolution transitions remain in [`../AGENT_INTEGRATION_STATE.md`](../AGENT_INTEGRATION_STATE.md). This route summarizes the ownership boundaries needed by all four repositories and the proof-carrying refactor protocol.

## Document-loading State Machine

```text
TASK_RECEIVED
→ ROOT_ROUTES_READ
→ TASK_CLASSIFIED
→ NEAREST_AGENTS_AND_README_SELECTED
→ MACHINE_AUTHORITY_SELECTED
→ EVIDENCE_SUBJECT_SELECTED
→ WORK_ADMITTED
```

Failure terminals:

```text
ROUTE_ABSENT
BROKEN_LINK
OWNER_AMBIGUOUS
MACHINE_AUTHORITY_ABSENT
EVIDENCE_SUBJECT_ABSENT
SOURCE_PROPOSAL_ONLY
```

Owner: root `AGENTS.md`, `docs/INDEX.md`, nearest `AGENTS.md`/README. Human boundary: admitting a missing route, changing authority, or accepting a new cross-repository contract.

## Skill-loading State Machine

```text
SKILL_NAME_RESOLVED
→ REGISTRY_CLASSIFICATION_RESOLVED
→ PROCEDURAL_CORE_LOADED
→ OPTIONAL_REFERENCE_LOADED
→ DOMAIN_TRIGGER_EVALUATED
    ├── no match → CORE_ONLY
    └── match    → DOMAIN_MODULE_LOADED
→ CONSUMER_BINDING_APPLIED
```

A domain module cannot modify registry classification or silently become global passive context.

## Proof-carrying Skill-refactor State Machine

Canonical owner: [`../../skills/skill-refactor-proof-loop/`](../../skills/skill-refactor-proof-loop/README.md).

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
    ├── no matched live receipts → LIVE_AB_PENDING
    └── matched live receipts    → LIVE_AB_VERIFIED
→ DELIVERY_EVIDENCE_BOUND
→ HUMAN_ADMIT_REQUIRED
```

Proof layers are strictly separated:

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

Fail-closed states include missing/as-landed treatment, lost old strength, dead route, unfair comparison, denominator erasure, local-PASS/global-FAIL, predecessor non-consumption, fixture-to-live promotion, residue, authority widening, artificial Stack ancestry, and duplicated golden-proof implementation.

Directory ownership:

```text
SKILL.md      transition law
references/   treatment/layer/matched-task/registry contracts
modules/      selected owner-specific golden instances
scripts/      deterministic transition producers/checkers
tests/        positive/hollow/mutation/matched-task falsifiers
registry      canonical proof identity and evidence ceiling
issues/PRs    molecular implementation/publication state
```

## Agentic Tech Lead execution State Machine

Canonical owner: [`../../skills/agentic-tech-lead-orchestration/`](../../skills/agentic-tech-lead-orchestration/README.md).

```text
REQUEST_BOUND
→ SYSTEM_CONTRACT_EXTRACTED
→ CAPABILITY_PLAN_COMPILED
→ CAPABILITY_PLAN_ASSERTED
→ CONTEXT_ADMITTED
→ TASK_DAG_COMPILED
→ TASK_SCHEMA_ASSERTED
→ TASK_SEMANTICS_ASSERTED
→ WORKERS_ADMITTED
→ LEASES_BOUND
→ ATTEMPTS_EXECUTED
→ RESULTS_VERIFIED
→ CANDIDATES_COMPARED
→ CONVERGENCE_APPLIED
→ GLOBAL_OBJECTIVE_ASSERTED
→ DELIVERY_HANDOFF
→ HUMAN_ADMIT_REQUIRED
```

Independent path-disjoint Workers are siblings. Tournament replicas share one frozen contract but remain isolated. A convergence owner consumes only verified prerequisite bytes and starts from the integrated prerequisite state. Fixture receipts cannot advance live runtime state.

## Skill evolution State Machine

```text
CLAIM_REGISTERED
→ CASE_BOUND
→ VERIFIER_CALIBRATED
→ EXECUTABLE
→ EVIDENCE_COLLECTED
→ MUTATION_EVALUATED
→ CAPABILITY_UNLOCKED
→ RELEASE_ADMITTED
→ CANONICAL_RELEASED
```

The optimizer, verifier, holdout, release, and Human Admit authorities remain separate. Read the live handoff for exact current state.

## Cross-repository publication State Machine

```text
SKILL_RELEASE_PREPARED
→ RUNTIME_REQUIREMENTS_RESOLVED
→ BETTOR_COMPOSITION_LOCKED
→ EXTERNAL_CONSUMER_INITIALIZED
→ CONSUMER_CANARY_OBSERVED
→ ACCEPTANCE_RECEIPT_EMITTED
→ HUMAN_PROMOTION
```

A local symlink, declaration, package presence, hermetic proof, or lower evidence layer cannot skip a transition.
