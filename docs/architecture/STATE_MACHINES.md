# State machines — skills-shared document and Skill routing

Detailed Skill Eval/Evolution transitions remain in [`../AGENT_INTEGRATION_STATE.md`](../AGENT_INTEGRATION_STATE.md). This route summarizes the ownership boundaries needed by all four repositories.

## Document-loading state machine

```text
TASK_RECEIVED
→ ROOT_ROUTES_READ
→ TASK_CLASSIFIED
→ NEAREST_README_SELECTED
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

Owner: root `AGENTS.md`, `docs/INDEX.md`, nearest READMEs. Human boundary: admitting a missing route, changing authority, or accepting a new cross-repository contract.

## Skill-loading state machine

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

## Skill evolution state machine

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

## Cross-repository publication state machine

```text
SKILL_RELEASE_PREPARED
→ RUNTIME_REQUIREMENTS_RESOLVED
→ BETTOR_COMPOSITION_LOCKED
→ EXTERNAL_CONSUMER_INITIALIZED
→ CONSUMER_CANARY_OBSERVED
→ ACCEPTANCE_RECEIPT_EMITTED
→ HUMAN_PROMOTION
```

A local symlink, declaration, or package presence cannot skip a transition.
