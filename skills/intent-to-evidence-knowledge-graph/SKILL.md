# Intent-to-Evidence Knowledge Graph

Use this Skill when a task must connect evidence-rich knowledge cards or source analysis to implementation traceability across Spatial Loop ICPG, Tech Lead tasks/issues, Git Town Stack PRs, governed Agent documentation and exact-subject evidence.

## Core law

Never create a second truth graph when a lower-level authority already exists.

- Spatial Loop ICPG owns the canonical intent/case/proof denominator.
- Tech Lead owns admitted task/case ownership, leases and convergence.
- Git Town/Git owns branch ancestry and delivery topology.
- repository bytes/verifiers/workflows/receipts own implementation/evidence state.
- Human/repository authority owns semantic promotion, merge, release and rollback.
- this Skill owns semantic projections and typed multi-hop traversal contracts only.

## Required graph classes

### Semantic nodes
Human-facing cards such as Narrative, Concept, Detail, Strategy, Practice, Roadmap, Governance, Verification, Conflict and Knowledge Gap.

### Intent projection
A stable projection of desired outcome, non-goals, invariants, acceptance and Human authority boundary. For implementation-oriented work it binds an exact ICPG subject/digest.

### Artifact projection
A semantic bridge to external/repository artifacts. Supported types include:

```text
ISSUE TASK PR BRANCH COMMIT FILE
AGENTS README SKILL SCHEMA SCRIPT TEST
WORKFLOW RECEIPT HUMAN_ADMIT
```

An Artifact Projection is not the external artifact authority and must carry freshness/identity metadata appropriate to mutability.

## Execution edge vocabulary

Do not collapse these into generic `DEPENDS_ON`:

```text
SIBLING
TRUE_CHILD
CONVERGENCE
PROCESS_DEPENDENCY
EXTERNAL_EVIDENCE
HISTORICAL
```

Use semantic bridge relations only for their declared meaning, including:

```text
DERIVED_FROM
TRACKED_BY
OWNS_CASE
REALIZED_BY
TOUCHES
DOCUMENTED_BY
PROTECTS_CASE
DOCUMENTS_INVARIANT
ROUTED_BY
GOVERNED_BY
VERIFIED_BY
PRODUCES
CONSUMES
BLOCKED_BY
UNBLOCKS
ROLLS_BACK_TO
CURRENT_VERSION_OF
HISTORICAL_VERSION_OF
```

A semantic relation between cases, concepts or artifacts never creates Git parentage.

## Authority precedence

When graph nodes disagree, resolve by subject and authority rather than relevance density. A current exact receipt/verifier result outranks stale Markdown. An exact GitHub/Git readback outranks a cached Artifact Projection for mutable state. A Human Admit event does not convert unexecuted lower-layer proof into runtime evidence.

## Freshness law

Mutable artifacts require a refresh before decision use:

- Issue/PR state;
- open branch head;
- workflow/check state;
- current AGENTS/README/SKILL bytes when they govern the target path.

Immutable commit SHA or merged commit identities may be retained durably when their provenance is exact.

## ICPG bridge law

For implementation work:

```text
semantic card / Intent projection
→ exact spatial-loop-case-graph subject
→ graph digest
→ case IDs
```

Do not copy the case denominator into the card registry. A card may summarize or group cases for human readability, but the machine denominator remains the ICPG.

## Bidirectional trace law

Before declaring an implementation trace closed, prove both directions:

```text
Intent → Case → Invariant → Task/Issue → PR/File → Oracle/Evidence
```

and

```text
PR/File → Task/Issue → Case → Invariant → Intent
```

A missing reverse path is a graph-integrity failure even if the forward implementation path exists.

## Evidence ceiling law

Use repository proof layers L0–L5. The graph answer must report the minimum relevant ceiling across the traversed implementation/proof chain. Prose, semantic similarity, model consensus, issue closure, PR publication or merge metadata cannot promote evidence beyond the exact receipt/runtime layer.

## Connectivity law

Do not optimize for graph degree. Keep an edge only if it supports at least one declared causal, implementation, authority, evidence, contradiction or retrieval traversal. If removing an edge changes no valid multi-hop answer, the edge is likely noise.

## Shadow Architect questions

At every material graph change ask:

1. Did this projection duplicate a canonical truth owned elsewhere?
2. Did semantic relevance silently become execution authority?
3. Did a process dependency become fake Git ancestry?
4. Is any mutable external state stale?
5. Can every changed implementation artifact trace back to an admitted ICPG case/Intent?
6. Can every required case trace forward to an owner, oracle and evidence state?
7. Did a low proof layer get promoted by aggregation or prose?
8. Did we add weak links only to make GraphRAG appear more connected?

## Completion boundary

Static completion requires graph contracts, exact identities, bidirectional trace, authority/freshness checks and deterministic negative controls on exact bytes. Live GraphRAG retrieval, live provider behavior, unknown-unknown discovery, continuous Shadow execution, production safety and Human approval remain separate evidence lanes.
