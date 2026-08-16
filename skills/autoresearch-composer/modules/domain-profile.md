# Iterative-research composition domain profile

Historical command, host, and consumer-specific details remain recoverable from pre-refactor blob `0ac4a2cd41f5cc2664d8e40868c67bc0040558aa`.

## Trigger
Load when a concrete optimization command surface, host prompt carrier, consumer family registry, or experiment runner must be bound.

## Non-trigger
Do not load for generic metric selection, candidate generation, bounded iteration, experiment validation, or stopping logic.

## Assumptions
The optimization objective and evaluator are explicit and not owned by the candidate generator.

## Specialization inventory
Host command names, user-level prompt locations, consumer family registries, and runtime-specific iteration runners belong here.

## Evidence ceiling
A generated candidate or host command success is not improvement proof; matched evaluator evidence is required.

## Fallback
If a specialized runner is absent, emit the frozen objective/candidate/eval packet for another executor and preserve the lane as unavailable.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, change the evaluator after observing results, hide regressions, or widen runtime/secret/merge authority.
