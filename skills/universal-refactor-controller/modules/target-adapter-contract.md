# Target Adapter Contract

Target adapters map observable target-domain surfaces into the domain-neutral `universal-refactor-controller` contract. They do not decide whether a refactor is safe or simpler.

## State Machine

```text
UNBOUND
→ TARGET_KIND_SELECTED
→ EXACT_SUBJECT_BOUND
→ OBSERVABLE_SURFACES_MAPPED
→ CONSTRAINTS_EMITTED
→ EVIDENCE_CEILING_BOUND
→ CORE_HANDOFF
```

A transition fails closed when the adapter cannot identify the exact subject, when a required surface is ambiguous, or when the adapter would need to invent a capability/consumer/authority claim.

## DAG and data flow

```text
exact subject + target kind
        ↓
trigger-selected adapter
        ↓
observable surface inventory
        ├─ capability surfaces
        ├─ state/persistence surfaces
        ├─ runtime/lifecycle surfaces
        ├─ test/CI/build arrival
        └─ trust/security/authority surfaces
        ↓
monotonic constraints + evidence ceiling
        ↓
universal-refactor-controller
        ↓
repository-entropy-reclamation / skill-refactor-proof-loop / Shadow / Tech Lead
```

Adapters are one-way translators. The portable controller core must not acquire target-specific mutable state.

## Required adapter envelope

Every adapter manifest uses `schema_version = universal-refactor/target-adapter/v1` and binds:

```text
id
accepted_target_kinds
trigger
surface_groups
required_outputs
authority
monotonicity
evidence_ceiling
```

## Authority law

Adapters may:

- enumerate observable surfaces;
- add stricter constraints;
- narrow an effect or authority boundary;
- attach exact evidence locations;
- report ambiguity as `HOLD`.

Adapters may not:

- decide `PASS`, safe deletion, or simplification by themselves;
- turn `FAIL`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, or `HUMAN_ADMIT_REQUIRED` into `PASS`;
- remove a core Complexity Delta dimension or frozen invariant;
- hide dynamic, persisted, generated, compatibility, lifecycle, or security consumers;
- treat tool installation or file presence as proof of applicability;
- widen filesystem, network, secret, merge, release, promotion, rollback, or permission authority;
- copy mutable consumer state into the portable core.

## Monotonicity

For every owner receipt or controller constraint:

```text
adapter_output_strength >= input_strength
adapter_authority <= input_authority
adapter_effect_scope <= admitted_effect_scope
adapter_evidence_ceiling <= available_evidence
```

If an adapter cannot preserve those inequalities, it must emit `HOLD` rather than guess.

## Evidence boundary

Adapter contracts prove routing and surface mapping only. They do not prove that a particular Skill or repository was safely simplified. Cross-domain effectiveness belongs to the UCR-LIVE canary stage.
