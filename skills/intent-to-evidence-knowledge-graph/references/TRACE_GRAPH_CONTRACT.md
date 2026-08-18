# Intent-to-Evidence Trace Graph Contract

## Node classes

```text
SEMANTIC_CARD
INTENT_PROJECTION
ICPG_SUBJECT
ICPG_CASE
TASK
ISSUE
STACK_ATOM
PULL_REQUEST
BRANCH
COMMIT
FILE
AGENT_DOC
PORTABLE_METHOD
SCHEMA
SCRIPT
TEST
WORKFLOW
RECEIPT
SHADOW_VERDICT
HUMAN_ADMIT
```

`ICPG_SUBJECT` and `ICPG_CASE` are projections of the canonical Spatial Loop case graph. Their truth is never re-authored here.

## Authority classes

```text
NAVIGATION
PROCEDURE
PORTABLE_METHOD
CONTRACT
IMPLEMENTATION
VERIFIER
TEST
EXECUTION_ARTIFACT
EVIDENCE_RECEIPT
DELIVERY_ARTIFACT
HUMAN_AUTHORITY
```

Authority is subject-specific. A high-authority receipt for one SHA does not prove another SHA.

## Artifact projection minimum fields

```text
projection_id
artifact_type
external_identity
repository
subject_ref
observed_version
observed_at
mutability: MUTABLE | IMMUTABLE
refresh_policy
freshness_state
artifact_authority_class
current_state
proof_layer
source_authority
```

Do not fabricate missing values. Mutable nodes with unknown freshness are unusable for decision-grade current-state claims.

## Intent projection minimum fields

```text
intent_id
desired_outcome
non_goals[]
invariants[]
acceptance_criteria[]
prohibited_outcomes[]
human_authority_boundary
icpg_subject
icpg_digest
case_ids[]
```

`case_ids` are references into the admitted ICPG, not a copied denominator.

## Edge families

### Semantic/provenance

```text
DERIVED_FROM
TRACKED_BY
PROTECTS_CASE
DOCUMENTS_INVARIANT
ROUTED_BY
GOVERNED_BY
VERIFIED_BY
TOUCHES
REALIZED_BY
PRODUCES
CONSUMES
BLOCKED_BY
UNBLOCKS
ROLLS_BACK_TO
CURRENT_VERSION_OF
HISTORICAL_VERSION_OF
```

### Delivery topology

```text
SIBLING
TRUE_CHILD
CONVERGENCE
PROCESS_DEPENDENCY
EXTERNAL_EVIDENCE
HISTORICAL
```

Delivery topology is not inferred from semantic dependencies. `TRUE_CHILD` requires explicit consumption of unmerged parent bytes/contracts/state.

## Required invariants

1. **Canonical case authority** — every ICPG case projection binds exact case-graph subject/digest/case ID.
2. **No orphan implementation** — an implementation artifact used in an implementation answer must trace to an admitted task/issue and ICPG case or an explicit non-case exception contract.
3. **No false ancestry** — semantic dependency never implies `TRUE_CHILD`.
4. **One convergence owner** — shared integration/index convergence has one explicit owner.
5. **Fresh mutable state** — decision-grade mutable artifacts are refreshed from authority.
6. **Authority precedence** — README/card projection cannot override exact verifier/receipt/Git truth.
7. **Evidence ceiling** — reported closure equals the minimum proven layer required by the claim.
8. **Bidirectional trace** — implementation-oriented subjects support both forward and reverse routes.
9. **No connectivity inflation** — every retained edge serves at least one declared query/traversal.
10. **Unknown is blocking where required** — missing exact identity/freshness/case binding cannot be silently inferred.

## Standard query contracts

### Q1 Why did this implementation exist?

```text
FILE/PR
→ task/issue owner
→ ICPG case
→ invariant/state path
→ Intent projection
→ semantic card/source evidence
```

### Q2 Where was this concept implemented and what proves it?

```text
SEMANTIC_CARD
→ Intent
→ ICPG case
→ task/issue
→ Stack atom/PR
→ file
→ oracle/test/workflow
→ receipt
→ proof ceiling
```

### Q3 What does an unresolved case block?

```text
ICPG UNKNOWN_BLOCKING
→ task/issue
→ Stack atom/convergence
→ downstream Intent closure
```

### Q4 What instructions govern this path?

```text
target FILE
→ nearest AGENTS
→ parent/root AGENTS route
→ Skill/portable method
→ current issue/PR
→ exact case/evidence subject
```

## Freshness rules

Before a query answer is used for implementation, publication, merge, rollback or completion:

- refresh Issue and PR state;
- refresh open head SHA;
- refresh workflow/check state;
- refresh governing AGENTS/README/SKILL bytes when current behavior depends on them;
- treat dated snapshots as `HISTORICAL` unless explicitly rebound.

## Proof-layer propagation

```text
L0 SOURCE_FREEZE
L1 STRUCTURAL_REACHABILITY
L2 EXECUTABLE_CONTRACT
L3 HERMETIC_REAL_TASK
L4 MATCHED_LIVE_MODEL_RUNTIME
L5 DELIVERY_AND_HUMAN_ADMIT
```

A route may cite stronger evidence for one subclaim while the overall answer retains a lower ceiling for a broader claim. Never average proof layers.

## Deterministic negative controls required by #414–#416

```text
duplicate_icpg_denominator
fabricated_case_id
stale_pr_projection
stale_open_head
readme_overrides_failed_receipt
semantic_dep_becomes_true_child
orphan_implementation
missing_reverse_trace
multiple_convergence_owners
weak_connectivity_only_edge
evidence_ceiling_laundering
```

These controls are requirements until executable schemas/checkers land; this Markdown does not satisfy them by itself.
