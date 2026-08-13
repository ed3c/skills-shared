# repo-agent-native modules

Modules are optional, trigger-selected instances of the portable procedure in [`../SKILL.md`](../SKILL.md). They reduce context and adapt a capability or deeper method without changing core law.

## Document authority

- `../SKILL.md` owns evidence levels, workflow order, failure semantics, and Human boundaries.
- This README owns module shape and selection rules.
- Each module owns only its declared trigger, inputs, outputs, evidence ceiling, and fallback.
- Consumer bindings own concrete provider names, versions, launch commands, credentials, policies, paths, and live receipts.

## Mandatory read order

```text
../README.md
→ ../SKILL.md
→ this README
→ matching module only
→ consumer binding
→ current source/provider evidence
```

## Module contract

Every module contains:

```text
Trigger
Non-trigger
Inputs
Outputs
Evidence ceiling
Fallback
Authoritative laws
```

A capability module should also name health/freshness checks and the exact transition that remains blocked until source readback.

## Directory state machine

```text
MODULE CANDIDATES DISCOVERED
→ TRIGGERS EVALUATED
    ├── none → CORE ONLY
    ├── one or compatible set → SELECTED
    └── conflicting → BLOCK
→ INPUTS/ASSUMPTIONS VERIFIED
→ BOUNDED MODULE CONTEXT LOADED
→ MODULE OUTPUT PRODUCED
→ EVIDENCE CEILING ENFORCED
→ CORE PROCEDURE CONTINUES
```

Failure states:

```text
MODULE_TRIGGER_AMBIGUOUS
MODULE_INPUT_ABSENT
MODULE_PROVIDER_UNHEALTHY
MODULE_CONTEXT_STALE
MODULE_LAW_OVERRIDE
MODULE_EVIDENCE_OVERPROMOTED
MODULE_SECRET_OR_PATH_LEAK
```

## Selection rules

- Select by required capability and task shape, not by product popularity.
- Multiple modules may compose only when their outputs and evidence ceilings do not conflict.
- A provider may satisfy more than one capability, but each capability observation remains separate.
- Provider absence must route to the declared fallback or terminate explicitly.
- A module may narrow permissions or evidence; it may never widen core law.

## Data flow

```text
task + consumer binding
→ module trigger
→ capability health/freshness observation
→ bounded candidate or hint output
→ source/document/test/runtime readback
→ evidence-level decision in core procedure
```

## Current evidence

Module files prove only that a procedure is defined. They do not prove a provider is installed, healthy, complete, authorized, or better than alternatives.

## Change contract

A module change requires a distinct trigger, non-trigger, inputs, outputs, evidence ceiling, fallback, positive case, unavailable/stale/conflicting negative cases, privacy boundary, and traceability.
