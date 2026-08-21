# Intent–Case–Proof Graph (ICPG)

The `spatial-loop-case-graph/v1` sidecar makes prompt intent, source behavior, use/edge cases, implementation ownership and proof obligations first-class traceable state.

## Why this exists

A short request may omit prose, but it does not authorize semantic loss. In copy, migration, port, replace, sync, merge, refactor or rewrite work, compatibility is only one semantic axis. The Builder must not silently trade away source decision logic, state/data semantics, failure/recovery, lifecycle/concurrency, side-effect/idempotency, authority, observability, or resource/performance behavior merely because the prompt is brief.

## Two graphs, two laws

Runtime behavior is a state graph and may contain cycles for retry, rollback and reconciliation. ICPG is a provenance graph and must be acyclic:

```text
User Prompt / Source Behavior
→ Intent Atom
→ Semantic Axis
→ Use Case
→ Edge Case / Scenario
→ State Path / Invariant
→ Implementation Binding
→ Oracle / Negative Control
→ Exact-Subject Evidence
```

Do not force runtime state into a DAG. Do not permit provenance cycles that make an obligation depend on its own proof.

## Semantic axes

For migration/copy/refactor-class work, select every applicable axis explicitly:

```text
INTERFACE_COMPATIBILITY
DATA_AND_STATE_SEMANTICS
CONTROL_FLOW_AND_DECISION_LOGIC
FAILURE_AND_RECOVERY_SEMANTICS
LIFECYCLE_AND_CONCURRENCY
SIDE_EFFECT_AND_IDEMPOTENCY
AUTHORITY_AND_PERMISSION
OBSERVABILITY_AND_ERROR_CONTRACT
PERFORMANCE_AND_RESOURCE_BEHAVIOR
```

An axis may be `NOT_APPLICABLE` only with a reason bound to the task subject. It may not disappear from the denominator because the model preferred another axis.

## Source behavior dispositions

Every material source behavior has exactly one disposition:

```text
PRESERVE_EXACT
PRESERVE_OBSERVABLE
ADAPT_WITH_COMPATIBILITY
INTENTIONAL_CHANGE
DEFER_EXPLICIT
DROP_EXPLICIT
UNKNOWN_BLOCKING
```

`UNMAPPED`, implicit drop and assumed-irrelevant are forbidden terminal states. `INTENTIONAL_CHANGE`, `DEFER_EXPLICIT`, and `DROP_EXPLICIT` require an explicit decision record naming authority/source and rationale. `UNKNOWN_BLOCKING` blocks a material transition until resolved or Human-admitted outside the Skill.

## Case basis

Enumerate where relevant over:

```text
Actor
× Entry Point
× Preconditions
× Lifecycle State
× Input Class
× Authority
× Ordering / Timing
× Concurrency
× Dependency State
× Resource Pressure
× Source Version
× Target Version
× Side-Effect Outcome
× Recovery Path
```

Each generated member is retained as exactly one classification:

```text
REQUIRED_CASE
INVALID_INPUT_CASE
IMPOSSIBLE_BY_INVARIANT
OUT_OF_SCOPE_EXPLICIT
DUPLICATE_EQUIVALENCE_CLASS
UNKNOWN_BLOCKING
```

Use exhaustive enumeration for critical bounded dimensions. For large combinatorial spaces, use a declared covering strategy such as pairwise/covering array, property-based generation, fuzzing, model-based testing, fault injection, differential testing or mutation testing. The strategy changes the generation method, not the denominator accounting law.

## Coverage lanes

Report separately:

```text
Intent Coverage
Source Behavior Disposition Coverage
Required Case Coverage
Implementation Binding Coverage
Oracle Coverage
Executed Evidence Coverage
Unknown Blocking Count
```

Never compress these to one score that can hide a missing critical lane.

## Required case closure

Every `REQUIRED_CASE` must bind:

```text
at least one intent
at least one semantic axis
at least one state path or invariant
exactly one implementation owner or explicit convergence owner
at least one oracle
its current evidence state
```

A case may exist before implementation. It may not be called implemented or verified until its exact-subject binding and owning evidence lane exist.

## Shadow Architecture integration

During implementation the Shadow Architect watches these additional material deltas:

```text
INTENT_INTERPRETATION_DELTA
SCOPE_REDUCTION_DELTA
USE_CASE_DELTA
EDGE_CASE_DELTA
SEMANTIC_PARITY_DELTA
CASE_COVERAGE_DELTA
CASE_ORACLE_DELTA
SOURCE_BEHAVIOR_DISPOSITION_DELTA
```

For each material delta ask:

```text
Which intent or source behavior made this path necessary?
Which existing or new case covers it?
Which semantic axis changed?
Which oracle can detect its loss?
Did this change silently narrow scope?
```

New/removed branches, validation, state transitions, errors, retries, timeouts, background work, schema/version paths, authority checks, side effects, persistence/cache rules, fallbacks, ordering, defaults and error mappings are case-delta trigger surfaces.

## Intervention

```text
L0 OBSERVE
  current case binding and proof obligations still close

L1 WARN
  new candidate case discovered but no material transition relies on it yet

L2 REVIEW
  required case/oracle missing, source disposition changed, or semantics narrowed without authority

L3 BLOCK
  material/irreversible transition with UNKNOWN_BLOCKING, implicit source-logic drop,
  critical required case without oracle, or false coverage/evidence promotion
```

`FIRST_GREEN` and `BEFORE_PR_OR_PUBLICATION` always reconcile the case graph against current implementation and evidence.

## Migration semantic-loss canary

A load-bearing negative control must demonstrate:

```text
source has decision branch B
→ candidate removes B
→ interface compatibility test remains green
→ semantic-parity/case-graph oracle turns red
```

If the repository cannot distinguish this defect, migration completeness is not proven.

## Composition

```text
spatial-loop-systems-engineering
  owns intent/case/invariant/monitor closure

unknown-discovery-composer
  discovers missing material dimensions/unknowns and bounded probes

agentic-tech-lead-orchestration
  consumes admitted case obligations when compiling task DAGs and Worker packets

git-town-stacked-pr-worker
  maps terminal implementation owners to molecular branch/Stack topology

skill-refactor-proof-loop
  preserves old strengths and matched treatment evidence for Skill refactors
```

Case dependency is not automatically Git ancestry. A Git child exists only when it consumes unmerged parent bytes/contracts.

## Machine route

The deterministic checker is:

```bash
python3 skills/spatial-loop-systems-engineering/scripts/check_case_graph.py \
  check path/to/case-graph.json
```

Exit contract:

```text
0   contract closes for the declared exact subject
2   evaluable semantic/traceability violation
64  missing, malformed or unusable input
```

A green checker proves contract closure for the supplied bytes. It does not prove all real-world unknown unknowns were discovered, continuous live Shadow execution, live model behavior, production safety or Human approval.
