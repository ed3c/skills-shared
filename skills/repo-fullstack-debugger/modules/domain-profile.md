# Full-stack diagnosis domain profile

Historical browser/provider/repository-specific diagnosis detail remains recoverable from pre-refactor blob `ebee1e73056208ee3a39c0517f3f968ec1e0e633`.

## Trigger
Load when a concrete browser/runtime trace source, repository execution surface, provider adapter, automation stack, or consumer artifact format must be interpreted.

## Non-trigger
Do not load for generic trace-driven diagnosis, failure classification, hypothesis testing, rollback, or playbook promotion.

## Assumptions
- A cheaper deterministic or direct-source path has already been attempted when applicable.
- Diagnosis consumes observable traces rather than private reasoning.
- Concrete runtime tools and provider sessions are optional capabilities.

## Specialization inventory
Browser automation traces, selector/timing/auth/bot classes, concrete automation scripts, semantic search adapters, repository execution commands, screenshots, and consumer output layouts belong here.

## Evidence ceiling
A trace classification or tool output is diagnostic evidence only until a bounded change is executed and the owning assertion verifies the exact subject.

## Fallback
If a specialized runtime is unavailable, retain the generic failure packet and route to direct logs, source reads, compiler/test output, or a human/operator handoff.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, weaken rollback or evidence requirements, alter tests to fit an implementation, or widen runtime/secret/merge authority.
