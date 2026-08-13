# Extraction methodology

## Trigger

Use after direct source discovery when the task requires implicit dependencies, optional-parameter routing, shared-state coupling, silent-failure chains, or negative invariants.

## Non-trigger

Do not infer before the known source facts and unresolved candidates are separated. Do not use this module to attribute runtime root cause without source or controlled evidence.

## Inputs

```text
confirmed source facts with references
entrypoints and outgoing calls
configuration and optional parameters
tests, exits, timeouts, and effects
current candidate ledger
```

## Method

### Three-pass invariant scan

1. **Interface pass** — inputs, outputs, public names, effects, exits, compatibility, and error shape.
2. **State pass** — transitions, persistence, ordering, idempotency, concurrency, timeout, cleanup, and rollback.
3. **Counterexample pass** — tests, forbidden paths, guard branches, missing inputs, stale data, and conditions that turn a claim red.

Classify records as:

```text
INV-MSG-*    message/event invariant
INV-STATE-*  state-transition invariant
INV-API-*    API/interface invariant
NEG-*        bounded negative invariant
IMPL-*       implicit dependency or inferred constraint
```

### Optional-parameter branch exhaustion

For each optional argument, flag, environment variable, or configuration field:

1. locate its declaration and default;
2. enumerate every conditional/switch use;
3. trace the selected downstream path;
4. record behavior, dependency, effect, exit, and source reference per value class;
5. leave the relation inferred when a branch cannot be read back.

Optional values often act as routing keys. Treating the default path as the entire contract is incomplete.

### Implicit-dependency inference

For every outgoing call or shared state whose behavior is outside the read scope:

1. classify the dependency as internal source, external interface, shared state, generated artifact, environment capability, or ambiguous;
2. record known facts separately from inferred prerequisites;
3. ask who writes every state that the current code reads;
4. recover ordering and freshness constraints;
5. inspect fire-and-forget calls, swallowed exits, retry loops, and output-existence checks;
6. identify timeout chains and which component observes failure first;
7. record the next evidence required to confirm the inference.

A recommended record:

```json
{
  "id": "IMPL-001",
  "kind": "shared-state|external-call|routing|timeout|silent-failure",
  "subject": "...",
  "known_facts": [],
  "inferred_prerequisites": [],
  "failure_chain": [],
  "evidence_level": "C",
  "resolution": "UNRESOLVED",
  "next_evidence": []
}
```

### Negative invariants

A negative invariant is valid only within a declared boundary. Record:

```text
search scope
queries and edge kinds
files/languages excluded
counterexample sought
result
confidence limitation
```

Empty semantic, symbol, or graph output cannot prove absence. Use direct search and source inspection to define the boundary.

### Observation versus attribution

- One runtime trace may establish an observation.
- Source may establish a mechanism.
- Controlled positive and negative runs may support attribution.
- Performance, convergence, race, and environment claims require execution under the relevant subject; static source alone is insufficient.

## Outputs

Typed invariants, negative invariants, optional-parameter route table, implicit-dependency records, and unresolved evidence requests.

## Evidence ceiling

Inference remains `C` until source, interface, test, or runtime readback upgrades the specific relation. Do not copy an inferred prerequisite into an `A` invariant.

## Fallback

When the analysis budget is exhausted, preserve the candidate ledger and unresolved records. Emit `BUDGET_EXHAUSTED` rather than an empty or falsely complete artifact.

## Authoritative laws

The Core laws in [`../SKILL.md`](../SKILL.md) remain authoritative, including source readback, bounded absence, observation/attribution separation, and no self-admission.
