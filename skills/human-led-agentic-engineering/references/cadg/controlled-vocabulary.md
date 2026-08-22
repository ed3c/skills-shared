# Context–Assumption–Decision Provenance vocabulary

Contract ID: `cadg/v1`  
Owner: `human-led-agentic-engineering` composition  
Parent program: `ed3c/skills-shared#578`

CADG records the causal backbone of a **material engineering decision** without storing private chain of thought. It connects observable context, declared assumptions, admitted decisions, architecture deltas, PR subjects and exact evidence.

```text
CTX --supports--> ASM --supports/challenges--> DEC
DEC --causes--> DELTA --implemented-by--> PR
PR --verified-by--> EV
EV --confirms/falsifies/expires--> ASM
```

The packet is a declared causal record. Its validity proves that the declarations are complete and internally consistent under this contract; it does not prove every declaration is true.

## Owner boundaries

| Concern | Canonical owner | CADG use |
|---|---|---|
| source-bound Context Capsule and read-only Shadow | `procedural-shadow-runtime` | reference exact capsule identities; do not copy the complete schema |
| hidden assumptions and architecture delta classes | `spatial-loop-systems-engineering` | bind declared assumptions, falsifiers and selected delta classes |
| decision/design admission and living context | `human-led-agentic-engineering` | own the composed CADG packet and decision admission |
| task/capability DAG, leases and convergence | `agentic-tech-lead-orchestration` | reference exact task and DAG contracts |
| branch/PR graph and delivery state | `git-town-stacked-pr-worker` | reference exact PR subjects and molecular relations |
| thin consumer binding | `shared-skills-infra` | generate consumer-owned packet/receipt routes while Skills remain canonical here |

No owner may be replaced by an equivalent-looking local implementation.

## Materiality

`MATERIAL` applies when a change alters at least one of:

```text
architecture boundary or dependency direction
canonical state or source-of-truth ownership
public or persisted contract
port, adapter, provider or runtime selection
allowed side effects or authority
cross-repository protocol or migration
security, privacy, data-loss or lifecycle boundary
significant deletion/refactor whose safety depends on an assumption
```

`TRIVIAL` and `ROUTINE` remain on the normal PR lane unless consumer policy tightens the trigger. A material change may not be labeled routine merely to avoid CADG.

## Context modes

- `OBSERVED_CONTEXT`: forward provenance compiled from observable repository, Issue, PR, test, workflow or runtime artifacts on the bound subject.
- `RECONSTRUCTED_CONTEXT`: bounded historical archaeology assembled later from observable and inferred artifacts.

A reconstructed packet must grade each source:

```text
OBSERVED
DETERMINISTIC_DERIVATION
INFERENCE
HYPOTHESIS
UNKNOWN
CONTRADICTION
```

`RECONSTRUCTED_CONTEXT` is never `ORIGINAL_CONTEXT`. Neither mode permits raw private reasoning, scratchpads or chain-of-thought fields.

## Assumption states

- `UNVERIFIED`: declared but not closed by an admissible exact-subject evidence edge.
- `CONFIRMED`: one or more matching evidence edges confirm it for the bound subject and lane.
- `FALSIFIED`: exact evidence contradicts it.
- `STALE`: the context or evidence subject changed, or later evidence expired its supporting reason.
- `HUMAN_ADMITTED`: a Human accepted the unresolved assumption within the Human's authority; this is not technical confirmation.

Every assumption names observable basis IDs, missing evidence and a falsifier. Confidence is diagnostic only. A blocking assumption may advance only as `CONFIRMED` or `HUMAN_ADMITTED`; a falsified, stale or unverified blocking assumption stops admission.

## Evidence lanes

```text
STATIC
DETERMINISTIC
LOCAL_RUNTIME
PRIVATE
LIVE_PHYSICAL
HUMAN_ADMIT
DELIVERY
RELEASE
PRODUCTION
```

Lanes are compared literally. A cheaper lane never satisfies a stronger lane. `CI_GREEN`, `PR_MERGED`, provider availability and model agreement are not synonyms for live, Human, release or production evidence.

## Decision and delta

A decision binds:

```text
problem
context IDs
all blocking assumption IDs
invariants
at least two alternatives
one selected alternative
reason
trade-offs
reversal conditions
Human design-admission reference when required
```

A delta records the concern, canonical state owner, ports, effects, authority, evidence requirements and touched paths that changed because of the decision. A state has at most one canonical writer. `WIDENED` effect or authority requires an exact Human admission reference.

## Historical reason status

```text
REASON_CURRENT
REASON_STALE
REASON_FALSIFIED
INSUFFICIENT_EVIDENCE
```

These statuses describe the bounded reconstruction only. They do not authorize code deletion, migration, merge or release.

## Stable refusal IDs

| ID | Meaning |
|---|---|
| `CADG001` | `MUTABLE_OR_MISSING_SUBJECT` |
| `CADG002` | `CONTEXT_MODE_LAUNDERED` |
| `CADG003` | `BLOCKING_ASSUMPTION_UNRESOLVED` |
| `CADG004` | `ASSUMPTION_WITHOUT_FALSIFIER` |
| `CADG005` | `DECISION_WITHOUT_CONTEXT` |
| `CADG006` | `DECISION_WITHOUT_ASSUMPTION_DISPOSITION` |
| `CADG007` | `DELTA_WITHOUT_DECISION` |
| `CADG008` | `STATE_OWNER_COLLISION` |
| `CADG009` | `AUTHORITY_WIDENED_WITHOUT_ADMISSION` |
| `CADG010` | `EVIDENCE_LANE_SUBSTITUTION` |
| `CADG011` | `RECONSTRUCTED_HISTORY_CLAIMED_AS_ORIGINAL` |
| `CADG012` | `PRIVATE_REASONING_OR_SECRET_FIELD` |
| `CADG013` | `STALE_CONTEXT` |
| `CADG014` | `PR_SUBJECT_MISMATCH` |
| `CADG015` | `ROLLBACK_ABSENT_OR_MUTABLE` |
| `CADG016` | `CI_OR_MERGE_PROMOTED_TO_LATER_LANE` |
| `CADG017` | `CAUSAL_EDGE_REFERENCES_UNKNOWN_NODE` |
| `CADG018` | `MATERIAL_CHANGE_BYPASSED` |

## Evidence ceiling

A schema-valid packet or deterministic checker PASS proves only contract compliance for the exact bytes supplied. It cannot establish that a live Agent read the context, that an independent Shadow ran, that a Human admitted a design, or that a PR was merged/released/observed in production. Preserve `NOT_EXERCISED`, `HUMAN_ADMIT_REQUIRED` and `NOT_RELEASED` explicitly.
