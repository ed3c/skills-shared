---
name: universal-refactor-controller
description: |
  Thin domain-neutral controller for capability-preserving complexity reduction. Compose repository-entropy-reclamation to discover and admit safe cuts, skill-refactor-proof-loop to freeze treatments and preserve old strengths, agentic-tech-lead-orchestration for task/capability DAGs and Local Handoff, procedural-shadow-runtime for independent contradiction/global-objective review, and git-town-stacked-pr-worker for molecular delivery. Use only when a repository or Skill should become simpler without silently losing required capability, observable behavior, safety, compatibility, lifecycle or evidence strength.
---

# Universal Refactor Controller

## Contract

This Skill owns **composition**, not the implementations it composes. It must not copy entropy analysis, treatment-proof, Shadow, scheduler, Stack, provider, analyzer or consumer-domain logic from their owner Skills.

The global objective is `CAPABILITY_PRESERVING_COMPLEXITY_REDUCTION`.

A refactor is admissible only when all declared required capabilities, old strengths, safety/compatibility/lifecycle invariants and evidence ceilings are preserved or strengthened, while at least one frozen non-LOC complexity dimension strictly decreases and replacement burden does not cancel the reduction.

Line count and file count are diagnostics only.

## Owner composition

```text
repository-entropy-reclamation
  safe-cut discovery, consumer/history/ownership/boundary evidence

skill-refactor-proof-loop
  A/B0/B1+ treatment freeze, old-strength preservation, proof layers, golden proof

agentic-tech-lead-orchestration
  exact task/capability DAG, leases, attempts, convergence, global objective, Local Handoff

procedural-shadow-runtime
  independent read-only applicability/contradiction/global-objective/evidence review

git-town-stacked-pr-worker
  molecular branch/PR graph and publication handoff

universal-refactor-controller
  identity binding + composition admission + Complexity Delta proof
```

No owner may be silently replaced by an equivalent-looking local implementation.

## State Machine

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

A missing prerequisite blocks the transition. A lower evidence lane cannot satisfy a later one.

## Global invariants

### Capability preservation

For every required baseline capability or old strength, the candidate binds one of:

```text
PRESERVED_WITH_EXACT_EVIDENCE
STRENGTHENED_WITH_EXACT_EVIDENCE
INTENTIONALLY_CHANGED_WITH_HUMAN_AUTHORITY
```

`ASSUMED`, `UNTESTED`, or a missing entry cannot advance the controller.

### Complexity reduction

The machine contract is `references/complexity-delta.schema.json`.

Core dimensions are:

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

A target may add typed domain dimensions through an adapter, but the adapter cannot weaken the core rules.

For each declared dimension, bind before/after counts or another deterministic typed measurement, measurement source, confidence/evidence class, and whether the dimension is a reduction target or protected non-regression dimension.

Admission requires:

1. at least one `REDUCTION_TARGET` strictly decreases;
2. every `NON_REGRESSION` dimension satisfies its frozen rule;
3. new sources of truth, ownership edges, synchronization paths or policy authorities are never hidden by an aggregate score;
4. replacement burden is explicitly measured and is lower than the removed burden;
5. relocation of the same obligation behind a wrapper, adapter, generated file, caller fan-out, configuration layer or external service is `COMPLEXITY_RELOCATED`, not reduction.

## Procedure

1. Bind target kind, repository, exact commit/tree, dirty state, nearest instructions and Human-owned decisions.
2. Ask the target adapter for observable capability/boundary surfaces only; it cannot decide simplification.
3. Compose `repository-entropy-reclamation` in `AUDIT` mode. Retain rejected and ambiguous candidates.
4. Bind the baseline capability/old-strength matrix before selecting a cut. For Skill targets this includes executable routes and method strengths; for ordinary repositories it includes public/persisted/runtime/lifecycle/security contracts.
5. Build the root-cause/ownership graph. Prefer deleting or collapsing the underlying duplicate truth/owner/state over moving symptoms.
6. Obtain an independent `procedural-shadow-runtime` verdict on the same immutable subject. Shadow must be read-only and must not reuse the Tech Lead conclusion as independent evidence.
7. If eligible, freeze `A=OLD_CANONICAL`, `B0=REFACTOR_AS_LANDED`, and `B1+=REPAIRED_CANDIDATE` through `skill-refactor-proof-loop` semantics. The proof method applies to ordinary repositories as a treatment contract even when the target is not itself a Skill.
8. Use `agentic-tech-lead-orchestration` to decompose one ownership-boundary refactor into true dependencies and disjoint leases. One convergence owner retains the global objective.
9. Execute structural/executable/hermetic proof required by the claim. Preserve failed, stale, cancelled, superseded and rejected attempts in the denominator.
10. Assert the global objective before Complexity Delta; a simpler failed system is not successful.
11. Validate `complexity-delta/v1`. Do not use LOC as the deciding dimension.
12. Search residue and regressions. Reject synchronization glue, hidden recomputation, duplicate source truth, missing dynamic/persisted consumers or increased semantic blast radius.
13. Hand the admitted molecular graph to `git-town-stacked-pr-worker`; use Local Handoff when required evidence belongs to another physical/runtime/Human lane.
14. Register a Golden Refactor Case only when its owner proof is replayable and content-bound. Store identities/evidence, not copied implementation logic.

## Target adapters

Adapters are trigger-selected and monotonic. Expected initial classes:

```text
SkillTargetAdapter
RepositoryTargetAdapter
```

They may map domain surfaces and add stricter constraints. They may not:

```text
turn FAIL/NOT_EXERCISED into PASS
remove a core complexity dimension or protected invariant
hide an ambiguous consumer
make tool installation proof of applicability
widen filesystem/network/secret/merge/release authority
copy mutable consumer state into this portable core
```

## Shadow Architect rejection set

At minimum reject:

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

## Evidence ceiling

A valid controller packet proves composition semantics for its exact subject and evidence lanes. It does not by itself prove a live repository refactor, cross-domain generalization, model uplift, Git Town execution, merge, release or production safety.

Keep `NOT_EXERCISED`, `NOT_IMPLEMENTED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED` visible.
